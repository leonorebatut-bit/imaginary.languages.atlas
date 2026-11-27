#!/usr/bin/env python
"""Reconstruit l'ensemble des analyses : `python scripts/rebuild_all.py`.

Options :
  --force            relance toutes les étapes même si leurs entrées n'ont pas changé
  --offline          n'utilise que le cache local (aucun téléchargement)
  --only STEP ...    n'exécute que les étapes nommées
  --weights PROFILE  profil de pondération (config/weights.yaml)
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from atlas.pipeline import STEPS, Runner  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--only", nargs="+", choices=STEPS)
    ap.add_argument("--weights", default=None)
    args = ap.parse_args()

    log_dir = ROOT / "outputs" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"run_{datetime.now():%Y%m%d_%H%M%S}.log"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(log_file, encoding="utf-8")])
    runner = Runner(force=args.force, offline=args.offline, weights_profile=args.weights)
    try:
        status = runner.run(args.only)
    except Exception as exc:  # noqa: BLE001
        logging.error("pipeline interrompu : %s (journal : %s)", exc, log_file)
        logging.info("état des étapes : %s", runner.status)
        return 1
    logging.info("état des étapes : %s", status)
    return 0


if __name__ == "__main__":
    sys.exit(main())
