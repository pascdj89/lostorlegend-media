#!/usr/bin/env python3
"""Texte je Plattform zu einem fertigen Reel.

  python3 captions.py --week 1            fuer alle gebauten Reels der Woche
  python3 captions.py --week 1 --reel 3

Schreibt neben das MP4 eine texte.json und eine lesbare texte.txt.

Drei getrennte Beitraege je Reel, nicht einer mit drei Netzwerken: beide
Schnittstellen (Metricool wie Buffer) kennen nur ein text-Feld, und ein
gemeinsamer Text naehme YouTube seine einzige durchsuchbare Flaeche.

Die drei Eigenheiten, die hier haengen:
  * YouTube-Titel tragen einen Aufhaenger aus dem Reel (seit 07.09.2026 die
    neugierigste Frage, `yt_tease` im Katalog), nicht den Kanalslogan —
    sonst konkurrieren sieben identische Titel derselben Woche gegeneinander.
  * TikTok verlangt zusaetzlich einen Titel, sonst lehnt die API den
    Beitrag ab.
  * Instagram laesst hoechstens fuenf Hashtags zu, gezaehlt ueber
    Bildunterschrift und Kommentare zusammen. Mehr blockiert die
    Veroeffentlichung oder wird stillschweigend entfernt.
"""
import argparse
import json
import os
import sys

import marke

HIER = os.path.dirname(os.path.abspath(__file__))
KATALOG = os.environ.get("LOL_KATALOG", os.path.join(os.path.dirname(HIER), "katalog"))
OUT = os.path.join(HIER, "out")

YT_TITEL_MAX = 100
TT_TITEL_MAX = 90


def kuerzen(s, n):
    if len(s) <= n:
        return s
    return s[: n - 1].rstrip(" ,;:—-") + "…"


YT_SUFFIX = {
    "Tourist": "🌍 Geography Quiz",
    "Traveler": "🌍 Hard Geography Quiz",
    "Legend": "🌍 Geography Quiz for LEGENDS",
}
BILD_WORTE = ("this flag", "this outline", "pictured", "shown here")


def yt_tease(reel):
    """Der Aufhaenger im YouTube-Titel.

    Seit 07.09.2026 nicht mehr die erste Frage (die ist immer die leichteste
    und verkauft das Reel unter Wert), sondern die neugierigste Frage des
    Reels. Der Katalog kann sie je Reel als `yt_tease` vorgeben — von Hand
    formuliert, kurz, mit dem Haken vorn (Sichtfenster auf dem Handy: rund
    48 Zeichen). Fehlt das Feld, nimmt der Fallback die letzte schwere Frage
    ohne Bildverweis, notfalls die letzte mittlere.
    """
    t = (reel.get("yt_tease") or "").strip()
    if t:
        return t
    kandidaten = [q for q in reel["fragen"]
                  if not any(b in q["frage"].lower() for b in BILD_WORTE)]
    for stufe in ("schwer", "mittel", "leicht"):
        passend = [q for q in kandidaten if q["stufe"] == stufe]
        if passend:
            return kuerzen(passend[-1]["frage"], 48)
    return kuerzen(reel["fragen"][0]["frage"], 48)


IG_CHALLENGE = "Can you get 10/10?"
IG_ERSTE_ZEILE_MAX = 125


def ig_erste_zeile(reel):
    """Erste Zeile der Instagram-Bildunterschrift: Herausforderung + Aufhaenger."""
    return "%s %s 🌍" % (IG_CHALLENGE, yt_tease(reel))


def texte(reel, stufe):
    erste = reel["fragen"][0]["frage"]
    kern = "10 geography questions. 5 seconds each. No pausing."

    yt_titel = kuerzen("%s %s" % (yt_tease(reel), YT_SUFFIX[stufe]), YT_TITEL_MAX)
    yt_text = "\n".join([
        kern,
        "",
        "%s level: %s" % (stufe, marke.HOOK),
        "Score %s or better and you are a LEGEND." % _schwelle(stufe),
        "",
        "How many did you get? Leave it in the comments.",
        "",
        " ".join(marke.hashtags(stufe)),
    ])

    tt_titel = kuerzen("%s %s" % (erste, _emoji_frei(stufe)), TT_TITEL_MAX).strip()
    tt_text = "\n".join([
        "%s level. %s" % (stufe, marke.HOOK),
        kern,
        "",
        " ".join(marke.hashtags(stufe)),
    ])

    ig_tags = marke.hashtags(stufe, instagram=True)
    # Instagram zeigt nur die ersten ~125 Zeichen der Bildunterschrift. Seit
    # 10.11.2026 beginnt die erste Zeile mit der Mitspiel-Herausforderung,
    # dann der Aufhaenger (derselbe wie im YouTube-Titel). Grund: die starken
    # Geografie-Quiz-Reels (vidIQ-Ausreisser, Aug-Nov 2026) oeffnen mit
    # „Can you…" / „How many did you get…", keiner mit „QUIZ". Der HOOK-Satz
    # („Only real map readers get 10 out of 10.") faellt hier weg, er
    # wiederholte nur die Herausforderung; gesprochen bleibt er im Reel.
    ig_text = "\n".join([
        ig_erste_zeile(reel),
        "%s level. 10 geography questions, 5 seconds each, no pausing." % stufe,
        "Score %s or better and you're a LEGEND." % _schwelle(stufe),
        "Drop your score in the comments 👇",
        "",
        " ".join(ig_tags),
    ])

    alle = {
        "youtube": {"titel": yt_titel, "text": yt_text},
        "tiktok": {"titel": tt_titel, "text": tt_text},
        "instagram": {"text": ig_text},
    }
    return {k: v for k, v in alle.items() if k in marke.AKTIV}


def _schwelle(stufe):
    lost, trav = marke.BAENDER[stufe]
    return "%d/10" % (trav + 1)


def _emoji_frei(stufe):
    return "| " + stufe


def pruefen(t):
    """Die Regeln, an denen eine Veroeffentlichung sonst scheitert.
    Geprueft wird nur, was auch bespielt wird (marke.AKTIV)."""
    fehler = []
    if "instagram" in t:
        n_ig = t["instagram"]["text"].count("#")
        if n_ig > marke.IG_MAX_HASHTAGS:
            fehler.append("Instagram: %d Hashtags, erlaubt sind %d"
                          % (n_ig, marke.IG_MAX_HASHTAGS))
        erste = t["instagram"]["text"].split("\n", 1)[0]
        if not erste.startswith(IG_CHALLENGE):
            fehler.append("Instagram: erste Zeile beginnt nicht mit der "
                          "Herausforderung (%r)" % IG_CHALLENGE)
        if len(erste) > IG_ERSTE_ZEILE_MAX:
            fehler.append("Instagram: erste Zeile %d Zeichen — sichtbar sind nur "
                          "rund %d" % (len(erste), IG_ERSTE_ZEILE_MAX))
    if "tiktok" in t and not t["tiktok"]["titel"].strip():
        fehler.append("TikTok: Titel fehlt — die API lehnt den Beitrag sonst ab")
    if "youtube" in t:
        if len(t["youtube"]["titel"]) > YT_TITEL_MAX:
            fehler.append("YouTube: Titel %d Zeichen, erlaubt sind %d"
                          % (len(t["youtube"]["titel"]), YT_TITEL_MAX))
        if t["youtube"]["titel"].strip().lower().startswith(marke.KANAL.lower()):
            fehler.append("YouTube: Titel beginnt mit dem Kanalnamen statt mit dem "
                          "Aufhaenger — sieben gleiche Titel je Woche")
        if len(t["youtube"]["titel"]) > 70:
            fehler.append("YouTube: Titel %d Zeichen — auf dem Handy sind nur rund "
                          "48 sichtbar, der Aufhaenger gehoert nach vorn"
                          % len(t["youtube"]["titel"]))
        if not t["youtube"]["titel"].strip():
            fehler.append("YouTube: Titel fehlt")
    return fehler


def lesbar(t, w, r, stufe, dauer):
    z = ["Woche %d, Reel %d — %s, %.1f s" % (w, r, stufe, dauer), "=" * 58, ""]
    for name in ("youtube", "tiktok", "instagram"):
        if name not in t:
            continue
        z.append(name.upper())
        if "titel" in t[name]:
            z.append("Titel: " + t[name]["titel"])
        z += ["", t[name]["text"], "", "-" * 58, ""]
    return "\n".join(z)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--reel", type=int)
    a = ap.parse_args()

    kat = os.path.join(KATALOG, "w%02d.json" % a.week)
    if not os.path.exists(kat):
        sys.exit("Katalog fehlt: %s" % kat)
    wo = json.load(open(kat, encoding="utf-8"))

    schlecht = 0
    for reel in wo["reels"]:
        if a.reel and reel["nr"] != a.reel:
            continue
        arb = os.path.join(OUT, "w%02d" % a.week, "r%d" % reel["nr"])
        meta = os.path.join(arb, "reel.json")
        if not os.path.exists(meta):
            print("Reel %d — noch nicht gebaut, uebersprungen" % reel["nr"])
            continue
        m = json.load(open(meta, encoding="utf-8"))
        t = texte(reel, reel["stufe"])
        fehler = pruefen(t)
        for f in fehler:
            print("  ! Reel %d: %s" % (reel["nr"], f))
            schlecht += 1
        with open(os.path.join(arb, "texte.json"), "w", encoding="utf-8") as f:
            json.dump(t, f, ensure_ascii=False, indent=1)
        with open(os.path.join(arb, "texte.txt"), "w", encoding="utf-8") as f:
            f.write(lesbar(t, a.week, reel["nr"], reel["stufe"], m["dauer"]))
        print("Reel %d — Texte fuer %s geschrieben%s"
              % (reel["nr"], ", ".join(sorted(t)),
                 " (YT-Titel %d Zeichen)" % len(t["youtube"]["titel"])
                 if "youtube" in t else ""))
    if schlecht:
        sys.exit(2)


if __name__ == "__main__":
    main()
