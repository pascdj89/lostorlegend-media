#!/usr/bin/env python3
"""Die eine Stelle, an der der Kanal beschrieben ist.

Bei NOOB or PRO stand der Spielname an fuenf Stellen verteilt (make.py, reel.html,
captions.py) und genau daraus entstand die falsche Hook-Zeile, die 50 Sonntage
getroffen haette. Hier steht er einmal. make.py, captions.py und das Template
lesen alle von hier; wer den Hook aendert, aendert ihn ueberall.
"""

KANAL   = "LOST or LEGEND"
HANDLE  = "lostorlegend"
STUFEN  = ("Tourist", "Traveler", "Legend")

# Welche Plattformen bespielt werden. Stand 09.11.2026: YouTube und Instagram
# (Instagram @lostorlegend am 09.11.2026 in Buffer verbunden, weil die
# Shorts-Reichweite fuer dieses Quiz schwach blieb). TikTok bleibt aus; sein
# Text bleibt im Code und wird erzeugt, sobald hier der Name dazukommt.
# Geprueft und eingeplant wird nur, was hier steht.
AKTIV = ("youtube", "instagram")

# Medien-Ablage seit 09.11.2026: oeffentliches GitHub-Repo statt Drive, damit
# der Wochenlauf ohne Pascs Rechner auskommt (wie NOOB or PRO seit 08.11.).
MEDIEN_REPO = "pascdj89/lostorlegend-media"
MEDIEN_RAW = "https://raw.githubusercontent.com/%s/main/" % MEDIEN_REPO

# KI-Kennzeichnung. Bewusst aus, im Runbook ausfuehrlich begruendet: YouTube,
# TikTok und Meta knuepfen die Offenlegungspflicht an Realismus — reale
# Personen, veraenderte Aufnahmen, realistisch wirkende Szenen. Die Reels
# bestehen aus einem gestalteten Template, gemeinfreien Kartendaten und einer
# synthetischen Erzaehlerstimme, ohne generiertes Bildmaterial und ohne
# Personen.
#
# ACHTUNG: NOOB or PRO setzt dieses Feld in seinen Sendeplaenen auf true.
# Beide Kanaele sind technisch gleich gebaut, also kann nur eine der beiden
# Entscheidungen richtig sein. Der Widerspruch ist offen und gehoert geklaert.
KI_KENNZEICHNUNG = False

# Gesprochen wie eingeblendet — dieselbe Zeichenkette, nie zwei Fassungen.
HOOK = "Only real map readers get 10 out of 10."

def hook_gesprochen(stufe):
    """Was die Stimme im Hook sagt. Traegt die Stufe, nicht den Kanalnamen."""
    return "{} level. {}".format(stufe, HOOK)

# Score-Baender je Stufe: (obere Grenze LOST, obere Grenze TRAVELER); darueber LEGEND.
BAENDER = {"Tourist": (4, 7), "Traveler": (3, 6), "Legend": (2, 5)}

def band(stufe, score):
    lost, trav = BAENDER[stufe]
    if score <= lost:
        return "LOST"
    if score <= trav:
        return "TRAVELER"
    return "LEGEND"

# Instagram: hoechstens fuenf Hashtags, hart durchgesetzt seit Dezember 2025.
# Gezaehlt wird ueber Bildunterschrift UND Kommentare zusammen.
IG_MAX_HASHTAGS = 5

# #shorts steht nur im YouTube-Satz (HASHTAGS_LANG); Instagram nimmt die
# ersten fuenf aus Kern + Stufe. Das Reel liegt mit 105-120 s unter der
# Drei-Minuten-Grenze fuer Shorts und unter der Drei-Minuten-Grenze, bis zu
# der Instagram Reels auch Nicht-Followern empfiehlt.
HASHTAGS_KERN = ["#geography", "#geographyquiz", "#quiz"]

HASHTAGS_STUFE = {
    "Tourist":  ["#traveltrivia", "#easyquiz"],
    "Traveler": ["#worldgeography", "#triviachallenge"],
    "Legend":   ["#hardquiz", "#geonerd"],
}

HASHTAGS_LANG = ["#shorts", "#maps", "#trivia", "#quiztime",
                 "#geographyfacts", "#countries", "#didyouknow"]

def hashtags(stufe, instagram=False):
    tags = HASHTAGS_KERN + HASHTAGS_STUFE[stufe]
    if instagram:
        return tags[:IG_MAX_HASHTAGS]
    return tags + HASHTAGS_LANG
