"""Téléchargement avec cache disque, empreinte SHA-256 et journal des échecs.

Un fichier déjà présent dans le cache n'est jamais retéléchargé (sauf `force`).
Chaque téléchargement écrit un fichier `<nom>.meta.json` : URL, date de
récupération, statut HTTP, taille, SHA-256. Un échec ne lève pas d'exception :
il renvoie un `FetchResult` avec `ok=False` pour que le pipeline continue.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from .config import pipeline_config

log = logging.getLogger(__name__)


@dataclass
class FetchResult:
    url: str
    path: str | None
    ok: bool
    from_cache: bool
    status_code: int | None
    sha256: str | None
    retrieved_at: str | None
    error: str | None = None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _user_agent() -> str:
    http = pipeline_config()["http"]
    return os.environ.get(http["user_agent_env"]) or http["user_agent_default"]


_last_request: dict[str, float] = {}


def _throttle(url: str, min_delay: float) -> None:
    host = urlparse(url).netloc
    wait = _last_request.get(host, 0.0) + min_delay - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    _last_request[host] = time.monotonic()


def fetch(url: str, dest: Path, force: bool = False, session: requests.Session | None = None) -> FetchResult:
    meta_path = dest.with_name(dest.name + ".meta.json")
    if dest.exists() and meta_path.exists() and not force:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return FetchResult(url, str(dest), True, True, meta.get("status_code"), meta.get("sha256"), meta.get("retrieved_at"))

    http = pipeline_config()["http"]
    from .collection.catalog import check_url  # import local : évite un cycle
    check_url(url, http["allowed_hosts"])
    sess = session or requests.Session()
    last_error: str | None = None
    status: int | None = None
    for attempt in range(http["retries"] + 1):
        try:
            _throttle(url, http.get("min_delay_per_host_s", 0))
            resp = sess.get(url, timeout=http["timeout_s"], headers={"User-Agent": _user_agent()})
            status = resp.status_code
            for hop in [*resp.history, resp]:
                check_url(hop.url, http["allowed_hosts"])  # une redirection ne doit pas sortir des hôtes autorisés
            if resp.status_code == 200:
                dest.parent.mkdir(parents=True, exist_ok=True)
                tmp = dest.with_name(dest.name + ".part")
                tmp.write_bytes(resp.content)
                tmp.replace(dest)  # écriture atomique : pas de fichier à moitié écrit
                digest = sha256_file(dest)
                now = datetime.now(timezone.utc).isoformat(timespec="seconds")
                meta = {"url": url, "status_code": status, "sha256": digest, "retrieved_at": now, "bytes": dest.stat().st_size}
                meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
                return FetchResult(url, str(dest), True, False, status, digest, now)
            last_error = f"HTTP {resp.status_code}"
            if resp.status_code in (401, 403, 404, 410):
                break  # inutile de réessayer
            if resp.status_code == 429 and attempt < http["retries"]:
                retry_after = resp.headers.get("Retry-After", "")
                time.sleep(min(float(retry_after), 120) if retry_after.isdigit() else http.get("backoff_s", 10) * (attempt + 1))
        except requests.RequestException as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        log.warning("échec %s (tentative %d) : %s", url, attempt + 1, last_error)
    return FetchResult(url, None, False, False, status, None, None, last_error)


def result_as_dict(r: FetchResult) -> dict:
    return asdict(r)
