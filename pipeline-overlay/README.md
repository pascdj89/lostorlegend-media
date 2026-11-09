# pipeline-overlay

Geänderte Dateien der LOST-or-LEGEND-Pipeline (Stand 09.11.2026: Cloud-Ablage in
dieses Repo + Instagram). Sie werden nach dem Entpacken des Pipeline-Bundles aus
dem Claude-Projekt „Geografie Quiz“ (`claude/pipeline_bundle.b64.txt`, md5
`75141dbf…`) über `~/lostorlegend/pipeline/` kopiert:

```bash
cd /home/claude/lostorlegend-media/pipeline-overlay && md5sum -c MD5SUMS
cp *.py ~/lostorlegend/pipeline/
```

Grund: Das Bundle lässt sich aus der Cloud-Sitzung nicht zurückschreiben
(Upload per Dateipfad verlangt vollständiges Lesen, 750 kB sind dafür zu groß).
Sobald eine Sitzung das Bundle neu schreiben kann, die Dateien dort hinein und
diesen Ordner löschen.
