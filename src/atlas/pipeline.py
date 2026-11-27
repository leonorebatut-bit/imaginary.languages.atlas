"""Pipeline central : collecte → nettoyage/caractéristiques → WALS → similarité → régions → export.

Reprise après interruption : chaque étape enregistre dans outputs/.state/ une
empreinte de ses entrées (fichiers et configuration). Une étape dont les
entrées n'ont pas changé depuis sa dernière réussite est sautée, sauf --force.
Les téléchargements sont mis en cache (http_cache.py).
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd

from . import __version__
from .collection.catalog import load_catalog
from .collection.html_text import normalize_for_match, source_text
from .collection.collect import collect_all, read_metadata, read_sources
from .comparison.feature_mapping import load_mappings, mapping_table, validate_against_wals
from .comparison.regional_analysis import aggregate, assign_areas
from .comparison.similarity import compare_to_all, resolve_weights
from .comparison.wals_loader import download_wals, load_wals
from .config import PROJECT_ROOT, load_yaml, pipeline_config, project_path
from .export import export_all
from .site_data import build_site_data
from .features import language_features
from .http_cache import fetch
from .linguistics.writing import script_record
from .writing_utils import write_csv, write_json

log = logging.getLogger("atlas.pipeline")

STEPS = ["collect", "features", "wals", "harmonise", "similarity", "regions", "export", "site_data"]


def _fingerprint(paths: list[Path], extra: dict) -> str:
    h = hashlib.sha256(json.dumps(extra, sort_keys=True, default=str).encode())
    for p in sorted(paths):
        files = sorted(x for x in p.rglob("*") if x.is_file() and "__pycache__" not in x.parts) if p.is_dir() else ([p] if p.exists() else [])
        for f in files:
            h.update(str(f.relative_to(PROJECT_ROOT)).encode())
            h.update(f.read_bytes())
    return h.hexdigest()


class Runner:
    def __init__(self, force: bool = False, offline: bool = False, weights_profile: str | None = None):
        self.cfg = pipeline_config()
        self.force, self.offline = force, offline
        self.weights_profile = weights_profile
        self.out = project_path("outputs")
        self.state_dir = self.out / ".state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.processed = project_path("processed")
        self.processed.mkdir(parents=True, exist_ok=True)
        self.status: dict[str, str] = {}

    def run_step(self, name: str, fn: Callable[[], None], inputs: list[Path], outputs: list[Path],
                 rerun: bool = False) -> None:
        # Le code du paquet fait partie des entrées : modifier un traitement invalide les résultats.
        fp = _fingerprint(inputs + [PROJECT_ROOT / "src" / "atlas"], {"step": name, "version": __version__, "weights": self.weights_profile,
                                   "offline": self.offline})
        marker = self.state_dir / f"{name}.json"
        if not self.force and not rerun and marker.exists() and all(o.exists() for o in outputs):
            if json.loads(marker.read_text()).get("fingerprint") == fp:
                log.info("[%s] inchangé, étape sautée", name)
                self.status[name] = "skipped"
                return
        log.info("[%s] début", name)
        # Le marqueur est retiré avant l'exécution : une étape qui échoue en cours de route
        # (même avec --force) ne peut pas passer pour terminée au lancement suivant.
        marker.unlink(missing_ok=True)
        try:
            fn()
        except Exception:
            log.exception("[%s] échec", name)
            self.status[name] = "failed"
            raise
        marker.write_text(json.dumps({"fingerprint": fp, "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}))
        self.status[name] = "done"
        log.info("[%s] terminé", name)

    # --- étapes -----------------------------------------------------------
    def collect(self) -> None:
        catalog = load_catalog()
        fetcher = fetch if not self.offline else _offline_fetch
        collect_all(catalog, project_path("languages"), project_path("raw"), self.out / "collection_errors.csv", fetcher)
        write_json(project_path("scripts") / "scripts.json", [script_record(s) for s in catalog.get("scripts", [])])
        # Fond de carte du site : terres émergées Natural Earth (domaine public).
        ne = self.cfg["reference_data"]["natural_earth"]
        fetcher(ne["url"], project_path("raw") / "geography" / ne["file"])
        # Registre AUTOTYP pour les aires linguistiques.
        at = self.cfg["reference_data"]["autotyp"]
        for f in at["files"]:
            fetcher(f"{at['base_url']}/{f}", project_path("raw") / "autotyp" / f)

    def features(self) -> None:
        catalog = load_catalog()
        scripts = {s["id"]: s for s in catalog.get("scripts", [])}
        records = []
        for lang in catalog["languages"]:
            ldir = project_path("languages") / lang["id"]
            rows = read_sources(ldir)
            sources = {r["source_id"] for r in rows}
            texts = {}
            for r in rows:
                if r.get("raw_file") not in (None, "", "null") and r["type"] != "sentence_corpus":
                    texts[r["source_id"]] = normalize_for_match(source_text(project_path("raw") / r["raw_file"]))
            feats = language_features(lang, ldir, sources, scripts, self.cfg, texts)
            records.append({"language_id": lang["id"], "features": [f.to_dict() for f in feats]})
        write_json(self.processed / "features.json", records)

    def wals(self) -> None:
        if not self.offline:
            results = download_wals()
            failed = [r for r in results if not r.ok]
            if failed:
                raise RuntimeError(f"WALS indisponible : {[r.url for r in failed]}")
        w = load_wals()
        mappings = validate_against_wals(load_mappings(), w)
        write_json(self.out / "wals_mapping.json", mapping_table(mappings))
        ids = [m.wals_id for m in mappings]
        wide = w.wide(ids)
        wide.to_csv(self.processed / "wals_wide.csv")
        meta = w.languages[["ID", "Name", "Macroarea", "Latitude", "Longitude", "Glottocode", "Family", "Genus"]]
        meta.to_csv(self.processed / "wals_languages.csv", index=False)

    def harmonise(self) -> None:
        mappings = load_mappings()
        records = json.loads((self.processed / "features.json").read_text())
        profiles = {}
        for rec in records:
            by_id = {f["feature_id"]: f for f in rec["features"]}
            prof = {}
            for m in mappings:
                f = by_id.get(m.project_feature)
                if f and f["status"] != "unavailable":
                    prof[m.wals_id] = f["value"]
            profiles[rec["language_id"]] = prof
        w = load_wals()
        mappings = validate_against_wals(mappings, w)
        converted, rejected = {}, []
        for lid, p in profiles.items():
            converted[lid] = {}
            for m in mappings:
                if m.wals_id not in p:
                    continue
                label = m.convert(p[m.wals_id])
                if label is None:
                    rejected.append({"language_id": lid, "wals_id": m.wals_id, "value": p[m.wals_id]})
                else:
                    converted[lid][m.wals_id] = label
        if rejected:
            # Une valeur documentée qui ne correspond à aucun code WALS est une erreur de codage
            # ou une fourchette à cheval sur deux classes : elle est signalée, jamais devinée.
            log.warning("valeurs non convertibles en codes WALS : %s", rejected)
        write_json(self.processed / "harmonise_rejected.json", rejected)
        write_json(self.processed / "profiles.json", converted)

    def similarity(self) -> None:
        mappings = validate_against_wals(load_mappings(), load_wals())
        weights = resolve_weights(load_yaml("weights.yaml"), self.weights_profile)
        wide = pd.read_csv(self.processed / "wals_wide.csv", index_col=0, dtype=str, keep_default_na=False, na_values=[""])
        wide = wide.astype(object).where(wide.notna(), None)
        profiles = json.loads((self.processed / "profiles.json").read_text())
        min_c = self.cfg["similarity"]["min_comparable_features"]
        rows = []
        for lid in sorted(profiles):
            for r in compare_to_all(lid, profiles[lid], wide, mappings, weights, min_c):
                if r.n_compared == 0:
                    continue
                rows.append({"imaginary_id": r.a, "wals_id": r.b, "n_compared": r.n_compared, "n_same": r.n_same,
                             "n_different": r.n_different, "score": r.score,
                             "matching": r.matching, "diverging": r.diverging})
        write_csv(self.out / "pairwise_similarity.csv", rows,
                  ["imaginary_id", "wals_id", "n_compared", "n_same", "n_different", "score", "matching", "diverging"])

    def regions(self) -> None:
        rc = self.cfg["regions"]
        wl = pd.read_csv(self.processed / "wals_languages.csv", dtype={"ID": str, "Glottocode": str})
        reg_path = project_path("raw") / "autotyp" / "Register.csv"
        if not reg_path.exists():
            raise RuntimeError("registre AUTOTYP absent : aires linguistiques non calculables")
        register = pd.read_csv(reg_path, dtype={"Glottocode": str})
        areas = assign_areas(wl, register, rc["nearest_neighbour_max_km"])
        areas.to_csv(project_path("geography") / "wals_language_areas.csv", index=False)
        pairs = pd.read_csv(self.out / "pairwise_similarity.csv", na_values=["null"])
        merged = pairs.merge(areas, on="wals_id", how="left").merge(
            wl[["ID", "Genus"]].rename(columns={"ID": "wals_id", "Genus": "genus"}), on="wals_id", how="left")
        agg = aggregate(merged, rc["min_languages"], rc["min_genera"], rc["bootstrap_iterations"], rc["random_seed"])
        write_csv(self.out / "regional_similarity.csv", agg.to_dict(orient="records"), list(agg.columns))

    def export(self) -> None:
        catalog = load_catalog()
        metas = [read_metadata(project_path("languages") / l["id"]) for l in catalog["languages"]]
        export_all(catalog, metas, self.processed, self.out, self.weights_profile)

    def site_data(self) -> None:
        build_site_data(self.out, self.processed, project_path("geography"), project_path("scripts") / "scripts.json",
                        project_path("raw"), project_path("site_data"), self.cfg["similarity"]["min_comparable_features"],
                        project_path("languages"))

    def run(self, only: list[str] | None = None) -> dict[str, str]:
        L, P, O, C = project_path("languages"), self.processed, self.out, PROJECT_ROOT / "config"
        wals_dir = project_path("raw") / "wals"
        plan = {
            "collect": (self.collect, [C / "catalog.yaml"], [O / "collection_errors.csv"]),
            "features": (self.features, [C, L], [P / "features.json"]),
            "wals": (self.wals, [C / "feature_mapping.yaml", C / "pipeline.yaml"], [P / "wals_wide.csv"]),
            "harmonise": (self.harmonise, [P / "features.json", C / "feature_mapping.yaml", wals_dir], [P / "profiles.json"]),
            "similarity": (self.similarity, [P / "profiles.json", P / "wals_wide.csv", C / "weights.yaml", C / "pipeline.yaml"],
                           [O / "pairwise_similarity.csv"]),
            "regions": (self.regions, [O / "pairwise_similarity.csv", C / "pipeline.yaml", C / "regions.yaml"],
                        [O / "regional_similarity.csv"]),
            "export": (self.export, [P, L, O / "regional_similarity.csv"], [O / "language_features.csv"]),
            "site_data": (self.site_data, [O], []),
        }
        for name in STEPS:
            if only and name not in only:
                continue
            fn, inputs, outputs = plan[name]
            # La collecte est relancée tant que des sources restent indisponibles (le cache évite
            # de retélécharger celles déjà obtenues).
            rerun = name == "collect" and _has_errors(O / "collection_errors.csv")
            self.run_step(name, fn, inputs, outputs, rerun=rerun)
        return self.status


def _offline_fetch(url, dest, **_):
    from .http_cache import FetchResult
    meta = dest.with_name(dest.name + ".meta.json")
    if dest.exists() and meta.exists():
        m = json.loads(meta.read_text())
        return FetchResult(url, str(dest), True, True, m.get("status_code"), m.get("sha256"), m.get("retrieved_at"))
    return FetchResult(url, None, False, False, None, None, None, "mode hors ligne : absent du cache")


def _has_errors(path: Path) -> bool:
    return path.exists() and len(path.read_text(encoding="utf-8").splitlines()) > 1
