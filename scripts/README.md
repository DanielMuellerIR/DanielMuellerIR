# README-Linkprüfung

Python 3.10 oder neuer wird benötigt. Aus dem Repository-Verzeichnis:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r scripts/requirements.txt
.venv/bin/python -m unittest discover -s tests
.venv/bin/python scripts/check_readme_links.py
```

Optional können zwei andere Markdown-Dateien als Argumente übergeben werden.
Der Prüfer vergleicht die geordneten Ziele aller Links unter
`https://github.com/`, einschließlich mehrfach vorkommender Ziele.
Zeilenumbrüche und Linktitel beeinflussen den Vergleich nicht.

Die Auswertung nutzt `markdown-it-py` mit dem Profil `gfm-like`. Inline- und
Referenzlinks, Autolinks und Links in Tabellen werden erkannt. Kommentare,
Codebeispiele und Bildquellen zählen nicht als Links. HTML außer Kommentaren
wird mit einer Fehlermeldung abgewiesen, damit HTML-Links nicht unbemerkt fehlen.
Der Prüfer bildet keine vollständige GitHub-Seitendarstellung nach.

Fundstellen nennen die Startzeile des zugehörigen Textblocks. Bei einem
mehrzeiligen Absatz kann der Link weiter unten im selben Absatz stehen.
Exit-Code 0 bedeutet gleiche, nicht leere Linklisten; 1 bedeutet Abweichung
oder einen Lesefehler beziehungsweise nicht unterstütztes HTML; 2 bedeutet
eine falsche Anzahl von Argumenten.
