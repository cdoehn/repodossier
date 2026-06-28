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
- Kein bundle_project.sh mehr verwenden.
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
- ARCHITECTURE.md, REPOCONTEXT_ARCHITECTURE.md
- SPEC.md, SPEC.txt, REPOCONTEXT_SPEC_v1.3.txt
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
- REPOCONTEXT_ARCHITECTURE.md wird erkannt.
- REPOCONTEXT_SPEC_v1.3.txt wird erkannt.
- planning/REPOCONTEXT_ROADMAP.md wird erkannt.
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
- REPOCONTEXT_ARCHITECTURE.md — 403 lines, ~1,029 tokens

Specification documentation:
- REPOCONTEXT_SPEC_v1.3.txt — 373 lines, ~1,250 tokens

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
