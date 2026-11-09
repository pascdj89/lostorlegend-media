#!/usr/bin/env python3
"""Sendeplan einer Woche als plan.json — Schritt 7 des Wochenlaufs.

  python3 plan.py --week 13 --start 2026-11-30            (Medien aus GitHub, Standard seit 09.11.2026)
  python3 plan.py --week 9 --start 2026-11-02 --media drive --ids ids.json   (Altbestand bis W11)

Die Datei wird von den Buffer-Planungstasks gelesen. Sie enthaelt je Reel den
Sendetermin, die Medien-URL und den fertigen Text je Netzwerk — der Wochenlauf
plant also nicht selbst ein, er legt nur ab; die Buffer-Planung haelt sieben
Tage Vorrat je Kanal.

Medien: seit 09.11.2026 (ab Woche 12) liegen die MP4s im oeffentlichen Repo
marke.MEDIEN_REPO unter reels/woche-NN/<datei>; mediaUrl ist die raw-URL.
Fuer den Drive-Altbestand gibt es --media drive mit --ids.

--ids erwartet eine JSON-Zuordnung Dateiname -> Drive-Datei-ID, etwa
  {"01_Mo_tourist.mp4": "1jN52...", ...}
Die IDs kommen aus dem Drive-Connector, den der Container selbst nicht
erreicht; deshalb werden sie hereingereicht statt hier geholt.
"""
import argparse
import datetime
import json
import os
import sys

import marke

HIER = os.path.dirname(os.path.abspath(__file__))
KATALOG = os.environ.get("LOL_KATALOG", os.path.join(os.path.dirname(HIER), "katalog"))
OUT = os.path.join(HIER, "out")

TAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

MEDIEN_URL = "https://drive.google.com/uc?export=download&id=%s"


def dateiname(nr, stufe):
    return "%02d_%s_%s.mp4" % (nr, TAGE[nr - 1], stufe.lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--start", required=True, help="Sendedatum des Montags, JJJJ-MM-TT")
    ap.add_argument("--time", default="16:00", help="Sendezeit, Standard 16:00 (Pasc, 10.09.2026; vorher 12:00)")
    ap.add_argument("--media", choices=("github", "drive"), default="github",
                    help="Medienquelle: github (Standard seit 09.11.2026) oder drive (Altbestand)")
    ap.add_argument("--ids", help="nur --media drive: JSON Dateiname -> Drive-Datei-ID")
    ap.add_argument("--folder-id", default="", help="Drive-ID des Wochenordners")
    a = ap.parse_args()

    montag = datetime.date.fromisoformat(a.start)
    if montag.weekday() != 0:
        sys.exit("--start ist ein %s, erwartet wird ein Montag" % TAGE[montag.weekday()])

    ids = {}
    if a.ids:
        with open(a.ids, encoding="utf-8") as f:
            ids = json.load(f)

    wo = json.load(open(os.path.join(KATALOG, "w%02d.json" % a.week), encoding="utf-8"))
    eintraege = []
    fehlt = []
    for reel in wo["reels"]:
        nr = reel["nr"]
        arb = os.path.join(OUT, "w%02d" % a.week, "r%d" % nr)
        meta = os.path.join(arb, "reel.json")
        texte = os.path.join(arb, "texte.json")
        if not (os.path.exists(meta) and os.path.exists(texte)):
            fehlt.append(nr)
            continue
        m = json.load(open(meta, encoding="utf-8"))
        t = json.load(open(texte, encoding="utf-8"))
        datei = dateiname(nr, reel["stufe"])
        fid = ids.get(datei, "") if a.media == "drive" else ""
        if a.media == "github":
            url = marke.MEDIEN_RAW + "reels/woche-%02d/%s" % (a.week, datei)
        else:
            url = MEDIEN_URL % fid if fid else ""

        posts = {}
        for netz, inhalt in t.items():
            eintrag = {"text": inhalt["text"]}
            if "titel" in inhalt:
                eintrag["title"] = inhalt["titel"]
            # Bewusste Kanalentscheidung, im Runbook begruendet: die Reels
            # loesen keine Offenlegungspflicht aus und werden nicht als
            # KI-generiert gekennzeichnet. NOOB or PRO handhabt das anders —
            # wer das hier aendert, sollte dort mitziehen.
            eintrag["isAiGenerated"] = marke.KI_KENNZEICHNUNG
            if netz == "instagram":
                eintrag["type"] = "reel"
                eintrag["shouldShareToFeed"] = True
            posts[netz] = eintrag

        eintraege.append({
            "date": (montag + datetime.timedelta(days=nr - 1)).isoformat(),
            "time": a.time,
            "timezone": "Europe/Berlin",
            "file": datei,
            "stufe": reel["stufe"],
            "dauer_s": m["dauer"],
            "driveFileId": fid,
            "mediaUrl": url,
            "posts": posts,
        })

    plan = {
        "kanal": marke.KANAL,
        "woche": "w%02d" % a.week,
        "driveFolderId": a.folder_id,
        "medien": a.media,
        "hinweis": ("Sendeplan fuer die Buffer-Planung. Je Tag ein Beitrag je "
                    "Netzwerk (%s), %s Europe/Berlin. Das Buffer-Kontingent gilt "
                    "JE KANAL, nicht je Organisation."
                    % (", ".join(marke.AKTIV), a.time)),
        "erstellt": datetime.date.today().isoformat(),
        "eintraege": eintraege,
    }

    ziel = os.path.join(OUT, "w%02d" % a.week, "plan.json")
    with open(ziel, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=1)

    ohne = [e["file"] for e in eintraege if not e["mediaUrl"]]
    print("%s: %d Eintraege, %s bis %s" % (
        ziel, len(eintraege), eintraege[0]["date"], eintraege[-1]["date"]))
    if fehlt:
        print("  ! Reels ohne fertige Dateien, nicht im Plan: %s" % fehlt)
    if ohne:
        print("  ! Medien-URL leer: %s" % ", ".join(ohne))
    return 2 if (fehlt or ohne) else 0


if __name__ == "__main__":
    sys.exit(main())
