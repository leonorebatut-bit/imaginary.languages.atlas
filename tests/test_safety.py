"""Garde-fous de la collecte : identifiants, hôtes autorisés, reprise après échec."""
import json

import pytest
import requests

from atlas import http_cache
from atlas.collection.catalog import check_url, load_catalog
from atlas.pipeline import Runner

ALLOWED = ["en.wikipedia.org"]


def _lang(**over):
    lang = {"id": "x", "name": "X", "category": "idiolect", "universe": "u", "creator": None, "year": None,
            "description": "d", "documentation_level": "low", "corpus_type": "c", "real_language_reference": None,
            "metadata_status": "unverified", "sources": [{"url": "https://en.wikipedia.org/wiki/X"}]}
    lang.update(over)
    return {"languages": [lang]}


@pytest.mark.parametrize("bad", ["../../src/atlas", "a/b", "X", "", "a b"])
def test_unsafe_ids_rejected(bad):
    with pytest.raises(ValueError, match="identifiant invalide"):
        load_catalog(_lang(id=bad))


@pytest.mark.parametrize("url", ["http://en.wikipedia.org/wiki/X", "https://127.0.0.1/x", "https://localhost/x",
                                 "file:///etc/passwd", "https://en.wikipedia.org:8443/x", "https://u@en.wikipedia.org/x"])
def test_disallowed_urls_rejected(url):
    with pytest.raises(ValueError, match="URL refusée"):
        check_url(url, ALLOWED)
    with pytest.raises(ValueError, match="URL refusée"):
        load_catalog(_lang(sources=[{"url": url}]))


def test_redirect_outside_allowed_hosts_is_refused(tmp_path, monkeypatch):
    class Resp:
        status_code = 200
        content = b"secret"
        headers = {}
        url = "https://169.254.169.254/latest"
        history = [type("H", (), {"url": "https://en.wikipedia.org/wiki/X"})()]

    class Sess(requests.Session):
        def get(self, *a, **k):
            return Resp()

    monkeypatch.setattr(http_cache, "_throttle", lambda *a: None)
    with pytest.raises(ValueError, match="URL refusée"):
        http_cache.fetch("https://en.wikipedia.org/wiki/X", tmp_path / "x", session=Sess())
    assert not (tmp_path / "x").exists()


def test_failed_step_does_not_keep_old_marker(tmp_path):
    r = Runner(force=True)
    r.state_dir = tmp_path
    out = tmp_path / "out.txt"
    out.write_text("ancien")
    (tmp_path / "s.json").write_text(json.dumps({"fingerprint": "x"}))

    def boom():
        out.write_text("à moitié")
        raise RuntimeError("échec")

    with pytest.raises(RuntimeError):
        r.run_step("s", boom, [], [out])
    assert not (tmp_path / "s.json").exists()
