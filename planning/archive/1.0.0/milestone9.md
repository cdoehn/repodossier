MILESTONE 9 – Documentation Export

Ziel:
RepoContext erzeugt zusätzlich zu full.txt und ai.txt einen reinen Dokumentations-Export docs.txt.

docs.txt soll nur dokumentationsnahe Dateien enthalten, insbesondere:
- README
- ARCHITECTURE
- TASKS
- SPEC
- CHANGELOG
- CONTRIBUTING
- LICENSE
- Dateien in docs/
- relevante Planungs-/Roadmap-Dateien, sofern Git-tracked

Wichtig:
- Use RepoContext CLI exports for final checks; do not use deprecated snapshot scripts.
- TASKS.md nur lesen/exportieren, nicht ändern.
- Milestone-Dateien nicht als Fortschrittswahrheit benutzen.
- Fortschritt aus Code, Tests und aktuellem full.txt/ai.txt ableiten.
- Tests semantisch passend einsortieren.
- docs.txt darf sich nicht selbst wieder als Input aufnehmen.
- Bestehender full.txt- und ai.txt-Export darf nicht regressieren.

====================================================================
9.0 – Bestandsprüfung vor Implementierung
====================================================================

9.0.a – Exportstruktur prüfen
Ziel:
Klären, wie full.txt und ai.txt aktuell aufgebaut sind.

Zu prüfen:
- src/repocontext/exporters/full.py
- src/repocontext/exporters/ai.py
- src/repocontext/exporters/__init__.py
- src/repocontext/cli.py
- src/repocontext/gitignore.py
- tests/test_cli.py
- tests/test_ai_exporter.py
- tests/test_full_exporter.py

Akzeptanzkriterien:
- Klarheit, welche Hilfsfunktionen wiederverwendet werden können.
- docs.txt wird als eigener Exporter geplant.
- Keine Änderung an bestehenden Exportern, außer für Integration nötig.


9.0.b – Aktuelle CLI-Varianten prüfen
Ziel:
Klären, welche Kommandos sinnvoll ergänzt werden.

Aktueller Zustand:
- repocontext
- repocontext full
- repocontext export
- repocontext export-ai
- repocontext info

Empfehlung:
- Neuer expliziter Befehl: repocontext export-docs
- Optional Alias: repocontext docs
- Standardlauf repocontext/full/export kann docs.txt ebenfalls erzeugen, aber erst nach bewusstem Integrationsteil.

Akzeptanzkriterien:
- CLI-Entscheidung ist konsistent mit ai.txt.
- Bestehende Kommandos bleiben kompatibel.


====================================================================
9.1 – Documentation File Detection
====================================================================

9.1.a – Dokumentationsdatei-Heuristik definieren
Ziel:
Eine zentrale Erkennung für Dokumentationsdateien schaffen.

Neue interne Funktion, z. B.:
- is_documentation_file(path)

Erkennen:
- README.md, README.rst, README.txt, README
- ARCHITECTURE.md, architecture.md
- SPEC.md, SPEC.txt, planning/spec.md
- TASKS.md
- ROADMAP.md, REPOCONTEXT_ROADMAP.md
- CHANGELOG.md
- CONTRIBUTING.md
- LICENSE
- Dateien unter docs/
- optional Dateien unter planning/, wenn Markdown/Text

Nicht erkennen:
- full.txt
- ai.txt
- docs.txt
- changed.txt
- normale Python-Quelltexte
- Tests
- Binärdateien

Akzeptanzkriterien:
- Erkennung ist deterministisch.
- Exportdateien werden ausgeschlossen.
- Dateinamen werden case-insensitive behandelt.


9.1.b – Dokumentationskategorien definieren
Ziel:
Dokumente im Export sinnvoll gruppieren.

Kategorien:
1. Primary documentation
2. Architecture documentation
3. Specification documentation
4. Tasks and roadmap
5. Changelog and contribution docs
6. License
7. Other docs

Akzeptanzkriterien:
- Jede Dokumentationsdatei bekommt genau eine Kategorie.
- Kategorie-Reihenfolge ist stabil.
- Unbekannte Docs landen in "Other docs".


9.1.c – Tests für Dokumentationsdatei-Erkennung
Ziel:
Die Heuristik isoliert absichern.

Testfälle:
- README.md wird erkannt.
- architecture.md wird erkannt.
- planning/spec.md wird erkannt.
- planning/archive/1.0.0/roadmap.md wird erkannt.
- docs/usage.md wird erkannt.
- src/repocontext/cli.py wird nicht erkannt.
- full.txt, ai.txt, docs.txt, changed.txt werden nicht erkannt.
- Binärdateien werden nicht erkannt.

Akzeptanzkriterien:
- Tests sind stabil.
- Keine zufällige Reihenfolge durch Sets.


====================================================================
9.2 – Documentation Export Context
====================================================================

9.2.a – Eigenes Context-Modell anlegen
Ziel:
docs.txt bekommt eine saubere interne Datenstruktur.

Neue Datei:
- src/repocontext/exporters/docs.py

Mögliche Struktur:
- DOCS_EXPORT_FILENAME = "docs.txt"
- DocumentationExportContext
- DocumentationFile
- build_docs_export_context()
- create_docs_export_context()
- render_docs_export()
- write_docs_export()
- generate_docs_export()

Context soll enthalten:
- repository_root
- repository_info
- scanned_files
- documentation_files
- skipped_files
- warnings
- total_line_count
- estimated_token_count

Akzeptanzkriterien:
- docs.txt Exporter ist getrennt von full.py und ai.py.
- Scanner-/Git-Logik wird wiederverwendet.
- Keine doppelte manuelle Dateisuche, wenn bestehende Pipeline reicht.


9.2.b – FullExportContext wiederverwenden oder leicht abstrahieren
Ziel:
Keine unnötige neue Pipeline bauen.

Empfehlung:
- build_full_export_context(repository_root) wiederverwenden.
- Danach nur Dokumentationsdateien aus scanned_files filtern.
- Kein Source-Dump von Code-Dateien.

Akzeptanzkriterien:
- docs.txt nutzt Git-tracked Files.
- docs.txt nutzt bestehende Text/Binary/Encoding-Infos.
- Fehlerhafte Dateien crashen den Export nicht.


9.2.c – Tests für Context-Erstellung
Ziel:
Absichern, dass nur Docs im Context landen.

Testfälle:
- Mini-Repo mit README.md und src/app.py
- Context enthält README.md.
- Context enthält nicht src/app.py.
- Context enthält nicht full.txt/ai.txt/docs.txt.
- Context zählt Dokumentationszeilen korrekt.

Akzeptanzkriterien:
- Context ist deterministisch sortiert.
- Leere Repos werden sauber behandelt.


====================================================================
9.3 – docs.txt Render-Struktur
====================================================================

9.3.a – Section Order definieren
Ziel:
docs.txt bekommt eine stabile, AI-freundliche Struktur.

Vorgeschlagene Reihenfolge:

# Documentation Context

## Documentation Quick Start
## Documentation Summary
## Documentation Files
## Extracted Documents
## Warnings

Akzeptanzkriterien:
- Reihenfolge ist konstant.
- Headings sind testbar.
- Keine vollständigen Code-Dateien.


9.3.b – Documentation Quick Start rendern
Ziel:
Kurz erklären, was docs.txt enthält.

Inhalt:
- Repository-Name
- Anzahl Dokumentationsdateien
- Gesamtzeilen
- geschätzte Tokens
- wichtigste Dokumenttypen

Beispiel:

# Documentation Context

## Documentation Quick Start

Repository: repo_context
Documentation files: 12
Total documentation lines: 4,200
Estimated documentation tokens: 28,000
Purpose: Documentation-only export for AI review.

Akzeptanzkriterien:
- Funktioniert auch ohne README.
- Funktioniert bei 0 Docs.
- Keine Halluzinationen.


9.3.c – Documentation Summary rendern
Ziel:
Kompakte Übersicht nach Kategorie.

Beispiel:

## Documentation Summary

Primary documentation:
- README.md — 521 lines, ~2,926 tokens

Architecture documentation:
- architecture.md — 403 lines, ~1,029 tokens

Specification documentation:
- planning/spec.md — 373 lines, ~1,250 tokens

Akzeptanzkriterien:
- Gruppierung nach Kategorie.
- Dateien innerhalb Kategorie stabil sortiert.
- Zeilen und Tokens werden angezeigt.


9.3.d – Documentation Files Manifest rendern
Ziel:
Alle exportierten Dokumentationsdateien maschinenlesbar auflisten.

Beispiel:

## Documentation Files

| Path | Category | Lines | Tokens |
| --- | --- | ---: | ---: |
| README.md | Primary documentation | 521 | 2926 |

Akzeptanzkriterien:
- Markdown-Tabelle ist stabil.
- Pfade sind repository-relativ.
- Sonderzeichen werden sauber escaped.


9.3.e – Extracted Documents rendern
Ziel:
Den vollständigen Inhalt der Dokumentationsdateien ausgeben.

Beispiel:

## Extracted Documents

### File: README.md

```markdown
...
```

Akzeptanzkriterien:
- Nur Dokumentationsdateien werden vollständig ausgegeben.
- Code-Dateien werden nicht ausgegeben.
- Markdown-Codefences in Markdown-Dateien brechen den Export nicht.
- Inhalte bleiben weitgehend originalgetreu.


9.3.f – Warnings rendern
Ziel:
Probleme am Ende sauber anzeigen.

Warnungen:
- Keine Dokumentationsdateien gefunden.
- Dokumentationsdatei konnte nicht gelesen werden.
- Binäre Dokumentationsdatei übersprungen.
- Generierte Exportdatei wurde ausgeschlossen.

Akzeptanzkriterien:
- Bei keinen Warnungen erscheint "No warnings."
- Warnings sind deterministisch sortiert.


====================================================================
9.4 – Schreiblogik für docs.txt
====================================================================

9.4.a – write_docs_export implementieren
Ziel:
docs.txt robust schreiben.

Anforderungen:
- UTF-8
- Repository Root als Default-Ausgabeort
- atomarer Write über temporäre Datei
- vorhandene docs.txt überschreiben
- bei Fehler temporäre Datei bereinigen

Akzeptanzkriterien:
- docs.txt landet im Repository Root.
- Bestehende docs.txt wird ersetzt.
- Kein kaputter Halbexport bleibt liegen.


9.4.b – generate_docs_export implementieren
Ziel:
Eine zentrale öffentliche Funktion bereitstellen.

Ablauf:
1. repository_root auflösen
2. .gitignore sicherstellen
3. Context bauen
4. docs.txt schreiben
5. Pfad zurückgeben

Akzeptanzkriterien:
- generate_docs_export(repository_root) schreibt docs.txt.
- docs.txt ist in .gitignore abgedeckt.
- Fehler werden nicht still verschluckt.


9.4.c – Exporter-Init aktualisieren
Ziel:
docs-Exporter öffentlich verfügbar machen.

Anpassen:
- src/repocontext/exporters/__init__.py

Exportieren:
- DOCS_EXPORT_FILENAME
- DocumentationExportContext
- build_docs_export_context
- create_docs_export_context
- generate_docs_export
- render_docs_export
- write_docs_export

Akzeptanzkriterien:
- Import aus repocontext.exporters funktioniert.
- Keine bestehenden __all__-Exports brechen.


====================================================================
9.5 – CLI Integration
====================================================================

9.5.a – export-docs Kommando ergänzen
Ziel:
docs.txt explizit erzeugen können.

Neuer Befehl:
- repocontext export-docs

Optional Alias:
- repocontext docs

Verhalten:
- schreibt docs.txt
- schreibt nicht full.txt
- schreibt nicht ai.txt
- aktualisiert .gitignore
- gibt "Wrote <path>/docs.txt" aus

Akzeptanzkriterien:
- CLI-Test grün.
- Export ist gezielt ausführbar.
- Fehler außerhalb Git-Repo werden sauber gemeldet.


9.5.b – Optional Standardexport um docs.txt erweitern
Ziel:
Prüfen, ob repocontext/full/export auch docs.txt erzeugen sollen.

Empfehlung:
Erst nach stabilem export-docs ergänzen.

Variante A:
- repocontext/full/export schreiben full.txt, ai.txt und docs.txt.

Variante B:
- docs.txt bleibt explizit über export-docs.

Empfehlung für Milestone 9:
- Standardlauf erzeugt weiterhin full.txt und ai.txt.
- docs.txt zunächst explizit über export-docs.
- Später kann Standardlauf erweitert werden, wenn gewünscht.

Akzeptanzkriterien:
- Keine überraschende Änderung am Standardlauf.
- Milestone bleibt klein und sauber.


9.5.c – CLI Fehlerbehandlung ergänzen
Ziel:
docs.txt Fehler sauber melden.

Fehler:
- kein Git-Repo
- .gitignore nicht beschreibbar
- docs.txt nicht beschreibbar

Akzeptanzkriterien:
- Exit-Code 1 bei Fehler.
- Verständliche Meldung.
- Bestehende Fehlerbehandlung bleibt konsistent.


====================================================================
9.6 – Export-Hygiene und Self-Reference-Schutz
====================================================================

9.6.a – Generierte Exporte ausschließen
Ziel:
docs.txt darf niemals full.txt/ai.txt/docs.txt/changed.txt exportieren.

Ausschließen:
- full.txt
- ai.txt
- docs.txt
- changed.txt

Akzeptanzkriterien:
- docs.txt enthält keine vorherige docs.txt.
- Wiederholter Export wächst nicht endlos.
- generated files erscheinen nicht im Manifest.


9.6.b – Nur Git-tracked Dateien berücksichtigen
Ziel:
docs.txt bleibt konsistent mit RepoContext-Grundregel.

Akzeptanzkriterien:
- Untracked README.tmp wird nicht exportiert.
- Git-tracked README.md wird exportiert.
- Ignorierte, aber getrackte Dateien folgen Git-ls-files-Logik.


9.6.c – Binärdateien und Fehlerfälle robust behandeln
Ziel:
Keine Crashes bei gemischten Repos.

Testfälle:
- docs/manual.pdf ist getrackt
- docs/broken.md kann nicht gelesen werden
- README mit Unicode-Inhalt
- Markdown mit Codefences

Akzeptanzkriterien:
- Binärdateien werden nicht als Text gedumpt.
- Fehler werden als Warning angezeigt.
- Export wird trotzdem geschrieben.


====================================================================
9.7 – Tests für docs Exporter
====================================================================

9.7.a – Neue Testdatei anlegen
Ziel:
Docs-Exporter isoliert testen.

Neue Datei:
- tests/test_docs_exporter.py

Akzeptanzkriterien:
- Tests sind semantisch sortiert.
- Keine Tests blind ans Dateiende anderer Dateien anhängen.


9.7.b – Section Order Tests
Testfälle:
- alle Pflichtsektionen vorhanden
- Reihenfolge stabil
- Headings stabil

Akzeptanzkriterien:
- docs.txt Struktur ist snapshot-freundlich.


9.7.c – Detection Tests
Testfälle:
- README erkannt
- ARCHITECTURE erkannt
- SPEC erkannt
- TASKS erkannt
- docs/ erkannt
- src/*.py ausgeschlossen
- Exportdateien ausgeschlossen

Akzeptanzkriterien:
- Heuristik funktioniert unabhängig von Groß-/Kleinschreibung.


9.7.d – Rendering Tests
Testfälle:
- Summary enthält Zeilen/Tokens.
- Manifest enthält alle Docs.
- Extracted Documents enthält Inhalte.
- Keine Code-Dateien enthalten.
- Markdown-Fences werden sicher verschachtelt.

Akzeptanzkriterien:
- Ausgabe ist lesbar.
- Keine rohen Python-Objekt-Reprs.


9.7.e – Write Tests
Testfälle:
- docs.txt wird ins Repository Root geschrieben.
- vorhandene docs.txt wird überschrieben.
- temporäre Datei wird bei Fehler bereinigt.
- Custom output path funktioniert, falls unterstützt.

Akzeptanzkriterien:
- Schreiblogik ist analog zu full/ai robust.


9.7.f – Empty Repo / No Docs Tests
Testfälle:
- Repo ohne Dokumentationsdateien
- Repo nur mit Python-Dateien
- leere README.md

Akzeptanzkriterien:
- docs.txt wird trotzdem erzeugt.
- Warnings erklären den Zustand.
- Kein Crash.


====================================================================
9.8 – CLI Tests
====================================================================

9.8.a – export-docs erzeugt docs.txt
Setup:
- Mini-Git-Repo
- README.md getrackt

Aufruf:
- main(["export-docs"])

Assert:
- docs.txt existiert
- docs.txt enthält "# Documentation Context"
- docs.txt enthält README.md
- full.txt existiert nicht
- ai.txt existiert nicht

Akzeptanzkriterien:
- export-docs ist wirklich docs-only.


9.8.b – export-docs aktualisiert .gitignore
Setup:
- Repo ohne .gitignore

Aufruf:
- main(["export-docs"])

Assert:
- .gitignore existiert
- docs.txt steht in .gitignore
- full.txt/ai.txt/changed.txt bleiben gemäß RepoContext-Block enthalten

Akzeptanzkriterien:
- Milestone 4 Integration wird wiederverwendet.


9.8.c – export-docs aus Unterordner schreibt ins Repo Root
Setup:
- Repo mit nested/dir
- chdir nach nested/dir

Aufruf:
- main(["export-docs"])

Assert:
- docs.txt liegt im Repo Root
- keine docs.txt im Unterordner

Akzeptanzkriterien:
- Repository Root Logik stimmt.


9.8.d – export-docs außerhalb Git-Repo schlägt verständlich fehl
Setup:
- temporärer Ordner ohne Git

Aufruf:
- main(["export-docs"])

Assert:
- Rückgabe 1
- Fehlermeldung verständlich
- keine docs.txt erzeugt

Akzeptanzkriterien:
- Verhalten analog zu bestehenden Export-Kommandos.


9.8.e – Optional docs Alias testen
Nur falls "repocontext docs" implementiert wird.

Aufruf:
- main(["docs"])

Assert:
- identisches Verhalten wie export-docs

Akzeptanzkriterien:
- Alias bleibt wartbar.


====================================================================
9.9 – README / Dokumentation aktualisieren
====================================================================

9.9.a – README Status aktualisieren
Ziel:
README soll docs.txt nicht mehr als "planned" aufführen, sobald implementiert.

Anpassen:
- Implemented-Liste um docs.txt / Documentation export ergänzen.
- Planned-Liste docs.txt entfernen.
- Usage-Sektion für export-docs ergänzen.
- Output: docs.txt beschreiben.

Akzeptanzkriterien:
- README stimmt mit Code überein.
- Keine übertriebene Doku.


9.9.b – README Tests ergänzen
Ziel:
Bestehende Dokumentations-Regressionstests erweitern.

Datei:
- tests/test_readme_documentation.py

Testfälle:
- README dokumentiert export-docs.
- README beschreibt docs.txt.
- README behauptet nicht mehr, docs.txt sei geplant.

Akzeptanzkriterien:
- Dokumentation bleibt konsistent.


9.9.c – Architektur-Doku optional minimal aktualisieren
Ziel:
Falls architecture.md bereits Exporter aufführt, docs.py als umgesetzt darstellen.

Akzeptanzkriterien:
- Architektur-Doku widerspricht dem Code nicht.
- Keine TASKS.md-Änderung.


====================================================================
9.10 – Gesamtvalidierung
====================================================================

9.10.a – Vollständiger Testlauf
Befehl:
python3 -m pytest --color=yes

Akzeptanzkriterien:
- Alle bestehenden Tests grün.
- Neue docs Export Tests grün.
- Keine Regression bei full.txt und ai.txt.


9.10.b – CLI Smoke Checks
Befehle:
repocontext --version
repocontext info
repocontext export-docs
repocontext full

Akzeptanzkriterien:
- export-docs schreibt docs.txt.
- full schreibt weiterhin full.txt und ai.txt.
- Keine unerwarteten zusätzlichen Dateien, außer bewusst implementiert.


9.10.c – Manuelle docs.txt Prüfung
Checkliste:
- docs.txt beginnt mit "# Documentation Context".
- README, Architecture, Spec, Roadmap erscheinen.
- Keine Python-Source-Dateien enthalten.
- full.txt, ai.txt, docs.txt, changed.txt fehlen als Input.
- Warnings sind verständlich.
- Wiederholtes Ausführen lässt docs.txt nicht wachsen.


====================================================================
Empfohlene Implementierungsreihenfolge
====================================================================

Paket 1:
- 9.1.a Dokumentationsdatei-Heuristik
- 9.1.b Kategorien
- 9.1.c Unit Tests
Ergebnis:
Die Auswahl der Dokumentationsdateien ist stabil.

Paket 2:
- 9.2.a docs.py Grundstruktur
- 9.2.b FullExportContext wiederverwenden
- 9.2.c Context Tests
Ergebnis:
Der docs Export Context funktioniert.

Paket 3:
- 9.3.a Section Order
- 9.3.b Quick Start
- 9.3.c Summary
- 9.3.d Manifest
- 9.3.e Extracted Documents
- 9.3.f Warnings
- 9.7.b bis 9.7.f Tests
Ergebnis:
docs.txt kann sauber gerendert werden.

Paket 4:
- 9.4.a write_docs_export
- 9.4.b generate_docs_export
- 9.4.c Exporter-Init
Ergebnis:
docs.txt kann programmatisch geschrieben werden.

Paket 5:
- 9.5.a export-docs CLI
- 9.5.c Fehlerbehandlung
- 9.8.a bis 9.8.d CLI Tests
Ergebnis:
docs.txt ist über CLI nutzbar.

Paket 6:
- 9.6.a Self-Reference-Schutz
- 9.6.b Git-tracked-only Verhalten prüfen
- 9.6.c Robustheit
Ergebnis:
docs.txt ist wiederholbar und sauber.

Paket 7:
- 9.9.a README aktualisieren
- 9.9.b README Tests
- 9.9.c Architektur-Doku optional
Ergebnis:
Dokumentation stimmt mit Milestone 9 überein.

Paket 8:
- 9.10.a Gesamttests
- 9.10.b CLI Smoke Checks
- 9.10.c Manuelle docs.txt Prüfung
Ergebnis:
Milestone 9 ist abschließbar.


====================================================================
Definition of Done für Milestone 9
====================================================================

Milestone 9 ist fertig, wenn:

- docs.txt wird zuverlässig erzeugt.
- Es gibt einen eigenen docs Exporter.
- docs.txt enthält nur Dokumentationsdateien.
- README, ARCHITECTURE, SPEC, TASKS/ROADMAP werden erkannt, sofern vorhanden und Git-tracked.
- docs.txt enthält:
  - Documentation Context Header
  - Documentation Quick Start
  - Documentation Summary
  - Documentation Files
  - Extracted Documents
  - Warnings
- docs.txt nimmt sich nicht selbst und keine anderen generierten Exportdateien auf.
- Binärdateien und Lesefehler crashen den Export nicht.
- export-docs CLI funktioniert.
- .gitignore bleibt korrekt/idempotent.
- full.txt und ai.txt bleiben funktionsfähig.
- README ist aktualisiert und behauptet nicht mehr, docs.txt sei ungeplant.
- Alle Tests sind grün.
- Es gibt einen Commit für die Umsetzung.
