#!/usr/bin/env python3
"""Fertige Reels einer Woche ins Medien-Repo kopieren (seit 09.11.2026).

  python3 ablage.py --week 13 [--repo /home/claude/lostorlegend-media]

Kopiert out/wNN/rN/reel.mp4 nach <repo>/reels/woche-NN/<Nr>_<Tag>_<stufe>.mp4
(dieselben Namen wie frueher in Drive) und gibt die raw-URLs aus. Committen
und pushen macht der Lauf selbst (git add/commit/pull --rebase/push), danach
jede URL mit `curl -sI` pruefen: HTTP 200 und content-length = lokale Groesse.
"""
import argparse
import json
import os
import shutil
import sys

import marke
from plan import dateiname, KATALOG, OUT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--repo", default="/home/claude/lostorlegend-media")
    a = ap.parse_args()
    wo = json.load(open(os.path.join(KATALOG, "w%02d.json" % a.week), encoding="utf-8"))
    ziel = os.path.join(a.repo, "reels", "woche-%02d" % a.week)
    os.makedirs(ziel, exist_ok=True)
    fehlt = []
    for reel in wo["reels"]:
        src = os.path.join(OUT, "w%02d" % a.week, "r%d" % reel["nr"], "reel.mp4")
        name = dateiname(reel["nr"], reel["stufe"])
        if not os.path.exists(src):
            fehlt.append(name)
            continue
        shutil.copyfile(src, os.path.join(ziel, name))
        print("%s  %8d Bytes  %sreels/woche-%02d/%s" % (
            name, os.path.getsize(src), marke.MEDIEN_RAW, a.week, name))
    if fehlt:
        print("  ! fehlt (nicht gerendert): %s" % ", ".join(fehlt))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
