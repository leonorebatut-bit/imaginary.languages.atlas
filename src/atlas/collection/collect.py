"""Collecte : dossiers par langue, téléchargement des sources, journal des échecs.

Pour chaque langue du catalogue, crée data/languages/<id>/ avec :
- metadata.json       informations générales + état du corpus ;
- sources.csv         une ligne par source, avec date et statut de récupération ;
- corpus_manifest.csv référence de chaque extrait (source, identifiant d'origine) ;
- corpus.txt          extraits, UNIQUEMENT si la licence autorise la redistribution ;
  sinon corpus_local.txt (ignoré par git).

Une source indisponible est consignée dans outputs/collection_errors.csv et la
collecte continue avec les autres. Rien n'est inventé : sans source récupérée,
le corpus est déclaré absent avec sa justification.
"""
from __future__ import annotations

import bz2
import csv
import json
import logging
import random
from datetime import datetime, timezone
from pathlib import Path

from ..config import pipeline_config
from ..http_cache import FetchResult, fetch
from ..writing_utils import write_csv, write_json

log = logging.getLogger(__name__)

# Licences dont les termes permettent de redistribuer des extraits avec attribution.
REDISTRIBUTABLE_PREFIXES = ("CC BY ", "CC BY-SA", "CC0", "Public domain")

SOURCE_COLUMNS = ["source_id", "url", "title", "author", "published", "type", "license", "nature",
                  "retrieved_at", "status", "error", "sha256", "redistributable", "available_items", "kept_items", "raw_file"]
MANIFEST_COLUMNS = ["source_id", "origin_id", "line_no"]


def is_redistributable(license_name: str | None) -> bool:
    return bool(license_name) and any(license_name.startswith(p) or license_name == p.strip() for p in REDISTRIBUTABLE_PREFIXES)


def parse_tatoeba_tsv(data: bytes) -> list[tuple[str, str]]:
    """Export Tatoeba « per_language » : id<TAB>langue<TAB>phrase, compressé en bz2."""
    text = bz2.decompress(data).decode("utf-8")
    out = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3 and parts[2].strip():
            out.append((parts[0], parts[2].strip()))
    return out


def sample_sentences(sentences: list[tuple[str, str]], max_n: int, seed: int) -> list[tuple[str, str]]:
    """Échantillon aléatoire déterministe, renvoyé dans l'ordre des identifiants d'origine."""
    if len(sentences) <= max_n:
        return sentences
    idx = sorted(random.Random(seed).sample(range(len(sentences)), max_n))
    return [sentences[i] for i in idx]


def _source_id(lang_id: str, i: int) -> str:
    # Identifiant positionnel : on n'insère jamais une source au milieu de la liste du
    # catalogue, on l'ajoute à la fin, pour que les identifiants déjà cités restent stables.
    return f"{lang_id}-s{i:02d}"


def collect_language(lang: dict, languages_dir: Path, raw_dir: Path, fetcher=fetch) -> tuple[dict, list[dict]]:
    ldir = languages_dir / lang["id"]
    ldir.mkdir(parents=True, exist_ok=True)
    rows, errors = [], []
    corpus_lines: list[tuple[str, str, str]] = []  # (source_id, origin_id, text)
    local_only = False

    for i, src in enumerate(lang.get("sources", []), start=1):
        sid = _source_id(lang["id"], i)
        fname = src["url"].rstrip("/").split("/")[-1] or "index"
        res: FetchResult = fetcher(src["url"], raw_dir / "sources" / lang["id"] / fname)
        redistrib = is_redistributable(src.get("license"))
        rows.append({
            "source_id": sid, "url": src["url"], "title": src.get("title"), "author": src.get("author"),
            "published": src.get("published"), "type": src.get("type"), "license": src.get("license"),
            "nature": src.get("nature", src.get("type")), "retrieved_at": res.retrieved_at,
            "status": "ok" if res.ok else "unavailable", "error": res.error, "sha256": res.sha256,
            "redistributable": redistrib,
            "raw_file": str((raw_dir / "sources" / lang["id"] / fname).relative_to(raw_dir)) if res.ok else None,
        })
        if not res.ok:
            errors.append({"language_id": lang["id"], "source_id": sid, "url": src["url"], "error": res.error,
                           "logged_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
            continue
        if src.get("type") == "sentence_corpus" and src["url"].endswith(".tsv.bz2"):
            try:
                ccfg = pipeline_config()["corpus"]
                parsed = parse_tatoeba_tsv(Path(res.path).read_bytes())
                rows[-1]["available_items"] = len(parsed)
                kept = sample_sentences(parsed, ccfg["max_sentences_per_source"], ccfg["sample_seed"])
                rows[-1]["kept_items"] = len(kept)
                for origin_id, sent in kept:
                    corpus_lines.append((sid, f"tatoeba:{origin_id}", sent))
                local_only = local_only or not redistrib
            except (OSError, ValueError) as exc:
                errors.append({"language_id": lang["id"], "source_id": sid, "url": src["url"],
                               "error": f"analyse impossible : {exc}", "logged_at": datetime.now(timezone.utc).isoformat()})

    write_csv(ldir / "sources.csv", rows, SOURCE_COLUMNS)
    write_csv(ldir / "corpus_manifest.csv",
              [{"source_id": s, "origin_id": o, "line_no": n} for n, (s, o, _) in enumerate(corpus_lines, start=1)],
              MANIFEST_COLUMNS)
    corpus_name = "corpus_local.txt" if local_only else "corpus.txt"
    for stale in ("corpus.txt", "corpus_local.txt"):
        if stale != corpus_name and (ldir / stale).exists() and corpus_lines:
            (ldir / stale).unlink()
    if corpus_lines:
        (ldir / corpus_name).write_text("\n".join(t for _, _, t in corpus_lines) + "\n", encoding="utf-8")

    if corpus_lines:
        corpus_status = {"status": "available", "file": corpus_name, "lines": len(corpus_lines),
                         "redistributable": not local_only}
    else:
        n_ok = sum(r["status"] == "ok" for r in rows)
        if not rows:
            why = "aucune source identifiée dans le catalogue"
        elif n_ok == 0:
            why = "aucune source n'a pu être récupérée (voir outputs/collection_errors.csv)"
        else:
            why = "les sources récupérées sont des descriptions, pas des corpus d'extraits ; extraction à faire"
        corpus_status = {"status": "absent", "justification": why}

    meta = {k: lang.get(k) for k in ("id", "name", "category", "universe", "creator", "year", "year_note",
                                      "description", "documentation_level", "corpus_type", "real_language_reference",
                                      "real_language_inspiration_note", "scripts", "metadata_status")}
    meta["corpus"] = corpus_status
    meta["source_ids"] = [r["source_id"] for r in rows]
    write_json(ldir / "metadata.json", meta)
    return meta, errors


def collect_all(catalog: dict, languages_dir: Path, raw_dir: Path, errors_path: Path, fetcher=fetch) -> list[dict]:
    all_meta, all_errors = [], []
    for lang in catalog["languages"]:
        try:
            meta, errs = collect_language(lang, languages_dir, raw_dir, fetcher)
        except Exception as exc:  # noqa: BLE001 - une langue en échec ne bloque pas les autres
            log.exception("collecte en échec pour %s", lang["id"])
            all_errors.append({"language_id": lang["id"], "source_id": None, "url": None, "error": repr(exc),
                               "logged_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
            continue
        all_meta.append(meta)
        all_errors.extend(errs)
    write_csv(errors_path, all_errors, ["language_id", "source_id", "url", "error", "logged_at"])
    log.info("collecte : %d langues, %d erreurs de source", len(all_meta), len(all_errors))
    return all_meta


def read_sources(ldir: Path) -> list[dict]:
    p = ldir / "sources.csv"
    if not p.exists():
        return []
    with p.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def read_metadata(ldir: Path) -> dict:
    return json.loads((ldir / "metadata.json").read_text(encoding="utf-8"))
