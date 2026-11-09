#!/usr/bin/env python3
"""Sendekalender als HTML — der Stand des Kanals auf einer Seite.

  python3 kalender.py --start 2026-09-07 [--eingeplant 2026-09-20,...] [--gesendet 2026-09-19,...]
                      [--out kalender.html]

Die Seite wird aus dem echten Stand gebaut, nicht von Hand gepflegt: der
Katalog sagt, welche Stufen eine Woche hat, `out/` sagt, was gerendert ist,
und `--eingeplant` nennt die Sendetermine, die in Buffer stehen. Buffer
erreicht der Container nicht selbst, deshalb wird diese Liste hereingereicht.

Wer den Kalender aktualisiert, ruft dieses Skript auf und veroeffentlicht das
Ergebnis unter derselben Artefakt-Adresse.
"""
import argparse
import datetime
import json
import os
import sys

import make
import mischen

HIER = os.path.dirname(os.path.abspath(__file__))
KATALOG = make.KATALOG
OUT = make.OUT

TAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
MONATE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
          "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]


def dat(d):
    return "%d. %s" % (d.day, MONATE[d.month - 1])


def dat_jahr(d):
    return "%d. %s %d" % (d.day, MONATE[d.month - 1], d.year)


def wochen_sammeln(start, eingeplant, heute, fertig=(), gesendet=()):
    """fertig: Wochennummern, die anderswo schon gerendert wurden.

    Noetig, weil der Container nach jedem Bootstrap leer ist: der Wochenlauf
    rendert nur die eine neue Woche und saehe alle frueheren als ungebaut.
    Woran man es erkennt, ohne die Dateien zu haben: im Drive-Wochenordner
    liegt eine plan.json. Diese Nummern werden hereingereicht."""
    wochen = []
    n = 0
    while True:
        n += 1
        p = os.path.join(KATALOG, "w%02d.json" % n)
        if not os.path.exists(p):
            break
        wo = json.load(open(p, encoding="utf-8"))
        montag = start + datetime.timedelta(days=7 * (n - 1))
        tage = []
        for reel in wo["reels"]:
            nr = reel["nr"]
            tag = montag + datetime.timedelta(days=nr - 1)
            gebaut = n in fertig or make.done(n, nr, reel)
            offen = make.bilder_pruefen(reel)
            if tag.isoformat() in gesendet:
                zustand = "gesendet"
            elif tag < heute:
                # Ein vergangener Sendetermin mit fertigem Reel ist raus.
                # Auf --eingeplant ist dafuer kein Verlass: gesendete Beitraege
                # fallen aus Buffers scheduled-Liste, und der Wochenlauf baut
                # den Kalender ohne Buffer-Zugriff neu (er hat den Connector
                # nicht). Vorher standen deshalb alle vergangenen Tage als
                # "gerendert" da - am 19.09.2026 der ganze Kalender.
                if gebaut or tag.isoformat() in eingeplant:
                    zustand = "gesendet"
                elif offen:
                    zustand = "blockiert"
                else:
                    zustand = "offen"
            elif tag.isoformat() in eingeplant:
                zustand = "eingeplant"
            elif gebaut:
                zustand = "gerendert"
            elif offen:
                zustand = "blockiert"
            else:
                zustand = "offen"
            meta = os.path.join(OUT, "w%02d" % n, "r%d" % nr, "reel.json")
            dauer = json.load(open(meta, encoding="utf-8"))["dauer"] if os.path.exists(meta) else None
            tage.append({
                "nr": nr, "tag": TAGE[nr - 1], "datum": tag,
                "stufe": reel["stufe"], "zustand": zustand, "dauer": dauer,
                "blockiert": [m for _, _, m in offen],
            })
        wochen.append({"nr": n, "montag": montag,
                       "sonntag": montag + datetime.timedelta(days=6),
                       "tage": tage,
                       "fragen": sum(len(r["fragen"]) for r in wo["reels"]),
                       "reels": wo["reels"]})
    return wochen


ZUSTAND_TEXT = {
    "gesendet": "gesendet",
    "eingeplant": "in Buffer",
    "gerendert": "gerendert",
    "offen": "noch nicht gebaut",
    "blockiert": "blockiert",
}


def bauen(wochen, heute, eingeplant):
    alle_tage = [t for w in wochen for t in w["tage"]]
    n_ges = len(alle_tage)
    n_geplant = sum(1 for t in alle_tage if t["zustand"] in ("gesendet", "eingeplant"))
    n_buffer = sum(1 for t in alle_tage if t["zustand"] == "eingeplant")
    n_gesendet = sum(1 for t in alle_tage if t["zustand"] == "gesendet")
    n_gerendert = sum(1 for t in alle_tage if t["zustand"] in ("gesendet", "eingeplant", "gerendert"))
    n_blockiert = sum(1 for t in alle_tage if t["zustand"] == "blockiert")
    fragen = sum(w["fragen"] for w in wochen)
    letzte = wochen[-1]["sonntag"] if wochen else heute

    # Der naechste Beitrag ist der naechste, der noch kommt - der heutige,
    # schon gesendete zaehlt nicht mehr.
    naechste = [t for t in alle_tage if t["datum"] >= heute
                and t["zustand"] == "eingeplant"]
    naechster = naechste[0] if naechste else None

    # Antwortverteilung ueber alle Wochen — die Zahl, die den Kanal fast
    # gekostet haette, gehoert sichtbar auf die Seite.
    verteilung = mischen.verteilung(
        [mischen.reel_mischen(r) for w in wochen for r in w["reels"]])[0]
    v_ges = sum(verteilung.values()) or 1

    zeilen = []
    for w in wochen:
        zust = {t["zustand"] for t in w["tage"]}
        if zust <= {"gesendet"}:
            kl, txt = "gesendet", "vollständig gesendet"
        elif zust & {"gesendet", "eingeplant"}:
            kl, txt = "laufend", "läuft"
        elif "blockiert" in zust:
            kl, txt = "blockiert", "%d Reel(s) blockiert" % sum(
                1 for t in w["tage"] if t["zustand"] == "blockiert")
        elif zust <= {"gerendert"}:
            kl, txt = "bereit", "gerendert, wartet auf Einplanung"
        else:
            kl, txt = "offen", "noch nicht gebaut"

        # Rechts steht die Laufzeitspanne, sobald die Woche gebaut ist —
        # "70 Fragen" ist in jeder Woche gleich und sagt nichts.
        dauern = [t["dauer"] for t in w["tage"] if t["dauer"]]
        if len(dauern) == len(w["tage"]):
            zusatz = "%.0f–%.0f s" % (min(dauern), max(dauern))
        elif dauern:
            zusatz = "%d von %d gebaut" % (len(dauern), len(w["tage"]))
        else:
            zusatz = "%d Fragen" % w["fragen"]

        felder = []
        for t in w["tage"]:
            titel = "%s %s · %s · %s" % (t["tag"], dat(t["datum"]), t["stufe"],
                                         ZUSTAND_TEXT[t["zustand"]])
            if t["dauer"]:
                titel += " · %.0f s" % t["dauer"]
            if t["blockiert"]:
                titel += " · fehlt: " + ", ".join(t["blockiert"])
            felder.append(
                '<div class="tag s-%s z-%s" title="%s">'
                '<span class="wt">%s</span>'
                '<span class="st">%s</span>'
                '<span class="dt">%s</span></div>'
                % (t["stufe"].lower(), t["zustand"], titel,
                   t["tag"], t["stufe"][:2].upper(), t["datum"].day))

        zeilen.append(
            '<article class="woche %s" data-st="%s">'
            '<div class="kw"><span class="nr">%02d</span>'
            '<span class="span">%s – %s</span></div>'
            '<div class="tage">%s</div>'
            '<div class="rechts"><span class="stat">%s</span>'
            '<span class="fr">%s</span></div>'
            '</article>'
            % (kl, kl, w["nr"], dat(w["montag"]), dat_jahr(w["sonntag"]),
               "".join(felder), txt, zusatz))

    balken = "".join(
        '<div class="vb"><span class="vl">%s</span>'
        '<span class="vs"><i style="width:%.1f%%"></i></span>'
        '<span class="vz">%.0f&thinsp;%%</span></div>'
        % ("ABCD"[p], 100 * verteilung[p] / v_ges, 100 * verteilung[p] / v_ges)
        for p in range(4))

    naechster_txt = ("%s %s, 16:00" % (naechster["tag"], dat(naechster["datum"]))
                     if naechster else "—")
    naechster_klein = ("%s · %s" % (naechster["stufe"], ZUSTAND_TEXT[naechster["zustand"]])
                       if naechster else "nichts eingeplant")

    werte = {
        "erzeugt": dat_jahr(heute),
        "reichweite": dat_jahr(letzte),
        "wochen": len(wochen),
        "reels": n_ges,
        "fragen": fragen,
        "gerendert": n_gerendert,
        "geplant": n_geplant,
        "buffer": n_buffer,
        "versendet": n_gesendet,
        "blockiert": n_blockiert,
        "naechster": naechster_txt,
        "naechster_klein": naechster_klein,
        "zeilen": "".join(zeilen),
        "balken": balken,
    }
    html = VORLAGE
    for k, val in werte.items():
        html = html.replace("{{%s}}" % k, str(val))
    return html


VORLAGE = """<title>LOST or LEGEND Sendekalender</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Archivo:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap">
<style>
:root{
  --grund:#FBF7ED; --flaeche:#FFFFFF; --tief:#F1EADA;
  --tinte:#0B1B2B; --gedaempft:#6E6857; --linie:#E3DAC6;
  --sig:#C33F1B; --gruen:#12704A; --gold:#8A6410; --gold-fl:#E8B54A;
  --schrift:'Archivo',system-ui,sans-serif;
  --display:'Archivo Black','Archivo',system-ui,sans-serif;
  --mono:'JetBrains Mono',ui-monospace,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --grund:#0B1B2B; --flaeche:#122A3E; --tief:#0E2334;
  --tinte:#F2E5C7; --gedaempft:#8DA2B4; --linie:#1D3A50;
  --sig:#E4572E; --gruen:#3BD07A; --gold:#E8B54A; --gold-fl:#E8B54A;
}}
:root[data-theme="dark"]{
  --grund:#0B1B2B; --flaeche:#122A3E; --tief:#0E2334;
  --tinte:#F2E5C7; --gedaempft:#8DA2B4; --linie:#1D3A50;
  --sig:#E4572E; --gruen:#3BD07A; --gold:#E8B54A; --gold-fl:#E8B54A;
}
*{box-sizing:border-box}
body{margin:0;background:var(--grund);color:var(--tinte);font-family:var(--schrift);
  font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:1020px;margin:0 auto;padding:48px 20px 96px}

header{border-bottom:2px solid var(--tinte);padding-bottom:20px;margin-bottom:32px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--sig);margin:0 0 10px}
h1{font-family:var(--display);font-size:clamp(30px,5.5vw,46px);line-height:1.02;margin:0;
  text-wrap:balance;letter-spacing:-.01em}
.unter{color:var(--gedaempft);margin:12px 0 0;max-width:64ch}

.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:1px;
  background:var(--linie);border:1px solid var(--linie);margin:0 0 36px}
.kpi{background:var(--flaeche);padding:18px 20px}
.kpi dt{font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--gedaempft);margin:0 0 8px}
.kpi dd{margin:0;font-family:var(--display);font-size:23px;line-height:1.1;
  font-variant-numeric:tabular-nums}
.kpi .klein{display:block;font-family:var(--schrift);font-weight:400;font-size:12.5px;
  color:var(--gedaempft);margin-top:6px;line-height:1.35}

h2{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--gedaempft);font-weight:600;margin:0 0 12px}

.liste{display:flex;flex-direction:column;gap:1px;background:var(--linie);
  border:1px solid var(--linie)}
.woche{display:grid;grid-template-columns:135px 1fr 175px;gap:18px;align-items:center;
  background:var(--flaeche);padding:12px 18px;border-left:3px solid var(--linie)}
.woche.gesendet,.woche.laufend{border-left-color:var(--gruen)}
.woche.bereit{border-left-color:var(--gold-fl)}
.woche.blockiert{border-left-color:var(--sig)}

.kw{display:flex;flex-direction:column;gap:2px}
.kw .nr{font-family:var(--display);font-size:19px;line-height:1;font-variant-numeric:tabular-nums}
.kw .span{font-family:var(--mono);font-size:11px;color:var(--gedaempft)}

/* Sieben Tage, eine Woche: die Stufe steigt von Montag bis Sonntag.
   Genau das ist die Struktur dieses Kanals — kein Themenblock, nur
   ansteigende Schwierigkeit. */
.tage{display:grid;grid-template-columns:repeat(7,1fr);gap:4px;min-width:0}
.tag{background:var(--tief);padding:6px 4px 5px;display:flex;flex-direction:column;
  align-items:center;gap:1px;border-bottom:3px solid var(--linie);cursor:default}
.tag .wt{font-family:var(--mono);font-size:9.5px;letter-spacing:.06em;color:var(--gedaempft)}
.tag .st{font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.04em}
.tag .dt{font-family:var(--mono);font-size:10px;color:var(--gedaempft);
  font-variant-numeric:tabular-nums}
.tag.s-tourist .st{color:var(--gedaempft)}
.tag.s-traveler .st{color:var(--sig)}
.tag.s-legend .st{color:var(--gold)}
.tag.z-gesendet{border-bottom-color:var(--gruen)}
.tag.z-gesendet .dt{color:var(--gruen)}
.tag.z-eingeplant{border-bottom-color:var(--gruen);
  background:color-mix(in srgb,var(--gruen) 9%,var(--tief))}
.tag.z-gerendert{border-bottom-color:var(--gold-fl)}
.tag.z-blockiert{border-bottom-color:var(--sig);
  background:color-mix(in srgb,var(--sig) 11%,var(--tief))}

.rechts{display:flex;flex-direction:column;align-items:flex-end;gap:4px;text-align:right}
.stat{font-family:var(--mono);font-size:10.5px;letter-spacing:.05em;color:var(--gedaempft)}
.gesendet .stat,.laufend .stat{color:var(--gruen)}
.bereit .stat{color:var(--gold)}
.blockiert .stat{color:var(--sig);font-weight:600}
.fr{font-family:var(--mono);font-size:10px;color:var(--gedaempft)}

.vt{margin:36px 0 0;border:1px solid var(--linie);background:var(--flaeche);padding:18px 20px}
.vt p{margin:0 0 14px;color:var(--gedaempft);font-size:13.5px;max-width:70ch}
.vb{display:grid;grid-template-columns:16px 1fr 44px;align-items:center;gap:10px;
  margin-bottom:5px}
.vl{font-family:var(--mono);font-size:12px;font-weight:600}
.vs{background:var(--tief);height:9px;display:block}
.vs i{display:block;height:100%;background:var(--sig)}
.vz{font-family:var(--mono);font-size:11px;color:var(--gedaempft);text-align:right;
  font-variant-numeric:tabular-nums}

.legende{margin-top:26px;display:flex;flex-wrap:wrap;gap:18px;font-size:12.5px;
  color:var(--gedaempft)}
.legende span{display:flex;align-items:center;gap:7px}
.sw{width:11px;height:11px;flex:none;border-bottom:3px solid}

footer{margin-top:46px;padding-top:20px;border-top:1px solid var(--linie);
  color:var(--gedaempft);font-size:13px;max-width:70ch}
footer b{color:var(--tinte)}
@media(max-width:820px){
  .woche{grid-template-columns:1fr;gap:10px}
  .rechts{align-items:flex-start;text-align:left;flex-direction:row;
    justify-content:space-between;width:100%}
}
</style>

<div class="wrap">
<header>
  <p class="eyebrow">Lost or Legend &middot; Geografie</p>
  <h1>Sendekalender</h1>
  <p class="unter">Ein Reel pro Tag auf YouTube und Instagram, 16:00 Europe/Berlin. Die Woche
  steigt an: drei Reels <b>Tourist</b>, drei <b>Traveler</b>, sonntags
  <b>Legend</b>. Jedes Feld unten ist ein Sendetag; die Farbe des Kürzels nennt
  die Stufe, der Balken darunter den Stand.</p>
</header>

<dl class="kpis">
  <div class="kpi"><dt>Material reicht bis</dt><dd>{{reichweite}}<span class="klein">Woche {{wochen}}, danach ist der Katalog leer</span></dd></div>
  <div class="kpi"><dt>Bestand</dt><dd>{{reels}} Reels<span class="klein">{{fragen}} Fragen &middot; {{gerendert}} gerendert</span></dd></div>
  <div class="kpi"><dt>Nächster Beitrag</dt><dd>{{naechster}}<span class="klein">{{naechster_klein}}</span></dd></div>
  <div class="kpi"><dt>In Buffer</dt><dd>{{buffer}} von 10<span class="klein">zehn Plätze gleichzeitig, je Kanal &middot; {{versendet}} bereits gesendet</span></dd></div>
</dl>

<h2>Sendewochen</h2>
<div class="liste">{{zeilen}}</div>

<div class="legende">
  <span><i class="sw" style="border-color:var(--gruen);background:var(--tief)"></i>gesendet oder in Buffer</span>
  <span><i class="sw" style="border-color:var(--gold-fl);background:var(--tief)"></i>gerendert, wartet</span>
  <span><i class="sw" style="border-color:var(--linie);background:var(--tief)"></i>noch nicht gebaut</span>
  <span><i class="sw" style="border-color:var(--sig);background:var(--tief)"></i>blockiert</span>
</div>

<section class="vt">
  <h2 style="margin-bottom:10px">Wo die richtige Antwort steht</h2>
  <p>Der Katalog führt die Lösung immer als erste Option. Ungemischt übernommen
  wäre die Antwort in jedem Reel A — das ist am 2. September im fertigen Video
  aufgefallen, nicht in einer Prüfung. Seitdem mischt die Pipeline, und diese
  Verteilung steht in jedem Lauf im Protokoll.</p>
  {{balken}}
</section>

<footer>
  Stand {{erzeugt}}. Erzeugt aus dem Katalog, den gerenderten Dateien und den
  Buffer-Terminen — <b>nicht von Hand gepflegt</b>. Wer etwas ändern will,
  ändert den Katalog oder den Sendeplan und lässt die Seite neu bauen:
  <code>python3 kalender.py</code>. {{blockiert}} Reel(s) sind blockiert, weil
  eine Bildfrage ohne Bild unbeantwortbar wäre.
</footer>
</div>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="Montag der Woche 1, JJJJ-MM-TT")
    ap.add_argument("--eingeplant", default="", help="Sendetermine in Buffer, kommasepariert")
    ap.add_argument("--gesendet", default="", help="bereits veroeffentlichte Sendetermine "
                    "(Buffer-Status sent), kommasepariert. Optional: ohne diese Liste gilt "
                    "jeder vergangene Tag mit fertigem Reel als gesendet.")
    ap.add_argument("--fertig", default="", help="Wochen, die schon gerendert sind (Nummern)")
    ap.add_argument("--out", default=os.path.join(HIER, "out", "kalender.html"))
    a = ap.parse_args()

    start = datetime.date.fromisoformat(a.start)
    if start.weekday() != 0:
        sys.exit("--start ist ein %s, erwartet wird ein Montag" % TAGE[start.weekday()])
    eingeplant = {s.strip() for s in a.eingeplant.split(",") if s.strip()}
    gesendet = {s.strip() for s in a.gesendet.split(",") if s.strip()}
    heute = datetime.date.today()

    fertig = {int(x) for x in a.fertig.replace(",", " ").split() if x.strip().isdigit()}
    wochen = wochen_sammeln(start, eingeplant, heute, fertig, gesendet)
    if not wochen:
        sys.exit("keine Wochendateien im Katalog gefunden")
    html = bauen(wochen, heute, eingeplant)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(html)
    print("%s — %d Wochen, %d Reels" % (a.out, len(wochen),
                                        sum(len(w["tage"]) for w in wochen)))


if __name__ == "__main__":
    main()
