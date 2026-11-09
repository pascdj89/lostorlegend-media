# lostorlegend-media

Öffentliche Medienablage für den Geografie-Quizkanal **LOST or LEGEND**
(YouTube @LostorLegend, Instagram @lostorlegend).

Seit 09.11.2026 rendert der Wochenlauf komplett in der Cloud und legt die
fertigen Reels hier ab. Buffer holt die Videos über die raw-URL:

```
https://raw.githubusercontent.com/pascdj89/lostorlegend-media/main/reels/woche-NN/<Nr>_<Tag>_<stufe>.mp4
```

| Pfad | Inhalt |
|---|---|
| `reels/woche-NN/` | sieben Reels einer Sendewoche (Mo–Sa Tourist/Traveler, So Legend), ab Woche 13 |
| `test/` | Testdateien, jederzeit löschbar |

Der Sendeplan (`plan.json`) liegt weiterhin in Google Drive unter
`LOST or LEGEND / 01 Reels / Woche NN`. Wochen 1–12 liegen nur in Drive.

Nichts hier umbenennen oder verschieben, solange ein Beitrag in Buffer darauf
zeigt — sonst scheitert die Veröffentlichung. Kein Force-Push.
