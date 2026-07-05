# RepoDossier / RepoContext – Milestone 4

## MarkdownRenderer aus internem Modell

Stand: 2026-07-03  
Release-Linie: 1.1.0  
Empfohlener Zielpfad im Repository: `planning/1.1.0/milestone4.md`  
Roadmap-Bezug: Roadmap Next, Punkt 4  
Projektname: RepoDossier  
Legacy-Kompatibilität: RepoContext bleibt als Alias erhalten

---

## Ziel von Milestone 4

RepoDossier soll die bestehenden Markdown-/Text-Ausgaben nicht mehr dauerhaft aus verstreuter Legacy-Stringlogik erzeugen, sondern aus dem internen strukturierten `RepositoryExport`-Modell rendern.

Die sichtbaren Exportdateien bleiben für Nutzer gleich nutzbar:

- `full.txt`
- `ai.txt`
- `docs.txt`
- `changed.txt`

Der entscheidende Architekturwechsel ist:

~~~text
Scanner / Git / Config / Analyzer
        ↓
RepositoryExport Modell
        ↓
MarkdownRenderer
        ↓
full.txt / ai.txt / docs.txt / changed.txt
~~~

Milestone 3 hat das interne Modell eingeführt. Milestone 4 beweist jetzt, dass dieses Modell die bestehende Markdown-Ausgabe wirklich tragen kann.

---

## Warum dieser Milestone wichtig ist

XML in Milestone 5 soll nicht als zweiter hart verdrahteter Exporter entstehen. Vorher muss Markdown aus demselben Modell kommen, aus dem später XML gerendert wird.

Milestone 4 reduziert deshalb technische Schulden:

- weniger doppelte Rendering-Logik
- klarere Grenze zwischen Datensammlung und Darstellung
- stabilere Tests für spätere Renderer
- bessere Grundlage für XML, Zeilennummern, Test Map und Recent Commit Context

---

## Grundsatzentscheidung

Renderer dürfen nur rendern.

Der MarkdownRenderer darf nicht:

- Git aufrufen
- Dateien lesen
- Scanner starten
- Analyzer starten
- Konfiguration laden
- Secret Detection ausführen
- Import Graph oder Call Graph bauen
- Changed Files selbst sammeln

Der MarkdownRenderer darf:

- ein `RepositoryExport` lesen
- strukturierte Felder formatieren
- Markdown-Überschriften erzeugen
- Tabellen oder Listen rendern
- Code-Fences wählen
- vorhandene Reportdaten darstellen
- fehlende optionale Daten konservativ auslassen

---

## Nicht-Ziele von Milestone 4

Milestone 4 bleibt bewusst auf Markdown beschränkt.

Nicht Teil dieses Meilensteins:

- kein XMLRenderer
- kein `--format xml`
- keine optionalen Zeilennummern
- keine Test Map Implementierung
- kein Recent Commit Context
- keine tiefere JS/TS/HTML/CSS/Java/C/C++/C# Analyse
- kein Entfernen des `repocontext` Legacy-Alias
- kein neues CLI-Format als Default
- kein vollständiger Rewrite aller Analyzer
- keine Projektcode-Ausführung
- keine Netzwerkzugriffe
- keine Build-Tool-Ausführung in der Exportlogik

---

## Erwartetes Ergebnis

Nach Milestone 4 gilt:

- `repodossier full` erzeugt weiterhin `full.txt`.
- `repodossier export-ai` erzeugt weiterhin `ai.txt`.
- `repodossier export-docs` erzeugt weiterhin `docs.txt`.
- `repodossier changed` erzeugt weiterhin `changed.txt`.
- `repocontext` funktioniert weiterhin als Legacy-Alias.
- Die Markdown-Ausgaben werden aus `RepositoryExport` gerendert.
- Legacy-Funktionen bleiben als Kompatibilitätswrapper erhalten.
- Split-Exports funktionieren weiterhin.
- Secret Masking bleibt aktiv.
- Bestehende Überschriften und Reihenfolgen bleiben möglichst stabil.
- Tests belegen, dass der Renderer keine Analyse-/IO-Logik ausführt.

---

# 4.1 Bestandsaufnahme und Migrationsvertrag

## Ziel

Vor der eigentlichen Migration muss klar sein, welche Markdown-Ausgaben heute existieren, welche Überschriften stabil bleiben sollen und welche Daten bereits im Modell vorhanden sind.

## 4.1.a Bestehende Markdown-Erzeugung inventarisieren

Zu prüfen:

- `src/repodossier/exporters/full.py`
- `src/repodossier/exporters/ai.py`
- `src/repodossier/exporters/docs.py`
- `src/repodossier/changed_exporter.py`
- `src/repodossier/renderers/markdown.py`
- `src/repodossier/renderers/__init__.py`
- `src/repodossier/output_writer.py`
- `src/repodossier/cli.py`
- `src/repodossier/cli_split.py`

Aufgabe:

- Alle Funktionen notieren, die aktuell Markdown-Text zusammensetzen.
- Alle Funktionen notieren, die Daten sammeln oder analysieren.
- Rendering-Funktionen von Datensammlungs-Funktionen unterscheiden.
- Öffentliche Funktionen markieren, die nicht entfernt werden dürfen.

Wichtige öffentliche Kompatibilitätspunkte:

- `render_full_export(...)`
- `write_full_export(...)`
- `generate_full_export(...)`
- `render_ai_export(...)`
- `write_ai_export(...)`
- `generate_ai_export(...)`
- `render_docs_export(...)`
- `write_docs_export(...)`
- `generate_docs_export(...)`
- `render_changed_export(...)`
- `write_changed_export(...)`
- `collect_changed_file_scans(...)`

Akzeptanzkriterien:

- Es ist klar, welche Funktionen Daten bauen.
- Es ist klar, welche Funktionen Markdown rendern.
- Keine öffentliche Exportfunktion wird ohne Wrapper entfernt.
- Die Migration kann schrittweise erfolgen.

---

## 4.1.b Bestehende Überschriften als Stabilitätsvertrag festlegen

Ziel:

Die sichtbare Struktur der bestehenden Exporte soll stabil bleiben, damit Nutzerworkflows und Tests nicht unnötig brechen.

Für `full.txt` mindestens stabil halten:

- `# AI Quick Start`
- `# Repository Statistics`
- `# File Summary`
- `# Repository Tree`
- `# Dependencies`
- `# Database Schema`
- `# Secret Detection`
- `# Complete Source Export`
- `# Warnings`
- `## Import Graph`
- `## Call Graph`

Für `ai.txt` mindestens stabil halten:

- `# AI CONTEXT`
- `## Project`
- `## Architecture Summary`
- `## Important Files`
- `## Dependencies`
- `## Database Schema`
- `## Symbol Index`
- `## Import Graph`
- `## Call Graph`
- `## Notes`

Für `docs.txt` mindestens stabil halten:

- `# Documentation Quick Start`
- `# Documentation Summary`
- `# Documentation Files`
- `# Extracted Documents`
- `# Warnings`

Für `changed.txt` mindestens stabil halten:

- `# Changed Export`
- `Repository path`
- `Compare Mode`
- `# Changed Files Summary`
- `# Changed Files`
- `# Git Diff`
- `# Changed File Contents`
- `# Deleted Files`
- `# Binary / Skipped Files`

Akzeptanzkriterien:

- Die erwarteten Überschriften sind in Tests abgesichert.
- Die Reihenfolge wird pro Exportmodus festgelegt.
- Neue Renderer-Ausgabe entfernt keine wichtigen Legacy-Abschnitte.
- Leere Abschnitte werden nur dann ausgelassen, wenn das bisherige Verhalten das ebenfalls erlaubt oder ein Test es explizit akzeptiert.

---

## 4.1.c Aktuellen MarkdownRenderer bewerten

Ziel:

Der vorhandene generische MarkdownRenderer ist ein guter Start, aber noch nicht ausreichend für die vier bestehenden Exportformate.

Zu prüfen:

- Welche Abschnitte rendert er bereits?
- Welche Überschriften weichen vom Legacy-Format ab?
- Welche Reportbereiche fehlen?
- Wie werden Code-Fences bestimmt?
- Wie wird `masked_content` behandelt?
- Gibt es bereits Tests, die Renderer-Grenzen absichern?

Erwartete Erkenntnis:

Der vorhandene Renderer kann minimale `RepositoryExport`-Daten rendern, muss aber mode-aware werden oder um mode-spezifische Funktionen ergänzt werden.

Akzeptanzkriterien:

- Es ist dokumentiert, was am bestehenden Renderer wiederverwendet wird.
- Es ist dokumentiert, was ersetzt oder erweitert werden muss.
- Bestehende Renderer-Tests bleiben erhalten und werden nicht einfach gelöscht.

---

## 4.1.d RepositoryExport-Lücken pro Modus identifizieren

Ziel:

Festlegen, welche Daten für Full, AI, Docs und Changed im Modell fehlen oder nur als generische Reportdaten verfügbar sind.

Zu prüfen:

Full:

- AI Quick Start Daten
- Repository Statistics
- File Summary
- Repository Tree
- Dependencies
- Database Schema
- Secret Detection
- Source Export
- Warnings
- Import Graph
- Call Graph

AI:

- Project summary
- Architecture Summary
- Important Files
- Compact Dependencies
- Compact Database Schema
- Symbol Index
- Import Graph
- Call Graph
- Notes

Docs:

- Documentation file categories
- Documentation summary
- Extracted documentation contents
- Documentation warnings

Changed:

- compare mode
- changed file status
- git diff text
- changed file contents
- deleted files
- binary/skipped files
- branch comparison
- Bash call graph section, falls weiterhin vorhanden

Akzeptanzkriterien:

- Fehlende Daten werden nicht im Renderer neu analysiert.
- Fehlende Daten werden entweder im Modell ergänzt oder in einem mode-spezifischen Builder/View vorbereitet.
- Changed-spezifische Daten werden nicht als lose globale Variablen an den Renderer geschmuggelt.

---

## 4.1.e Migrationsgrenze festlegen

Ziel:

Verhindern, dass Milestone 4 zu einem unkontrollierten Komplettumbau wird.

Entscheidung:

- Exporter dürfen weiterhin Daten sammeln.
- Exporter bauen danach ein `RepositoryExport` oder eine klar definierte `RepositoryExport`-View.
- MarkdownRenderer rendert daraus Markdown.
- Alte Rendering-Hilfsfunktionen dürfen vorübergehend als Adapter genutzt werden, sollen aber nicht dauerhaft als primärer Renderer bleiben.

Akzeptanzkriterien:

- Es gibt keine neue Scanner-/Git-/Analyzer-Logik in `renderers/markdown.py`.
- Es gibt eine klare Datenübergabe an den Renderer.
- Legacy-Funktionen delegieren in Richtung Modell plus Renderer.

---

## 4.1.f Baseline-Regressionstests vor Umbau absichern

Ziel:

Vor größeren Änderungen sollen bestehende Exportverträge durch Tests sichtbar sein.

Zu prüfen und ggf. zu ergänzen:

- `tests/test_full_exporter.py`
- `tests/test_ai_exporter.py`
- `tests/test_docs_exporter.py`
- `tests/test_changed_exporter.py`
- `tests/test_markdown_renderer.py`
- `tests/test_export_model_scanner_integration.py`
- `tests/test_export_model_public_api_e2e.py`

Akzeptanzkriterien:

- Jeder Exportmodus hat mindestens einen Test auf zentrale Überschriften.
- Jeder Exportmodus hat mindestens einen Test auf erzeugte Datei.
- Renderer-Unit-Tests nutzen künstliche Modelle und kein echtes Repository.
- Integrationstests dürfen echte Fixture-Repos nutzen, aber Renderer-Tests nicht.

---

# 4.2 MarkdownRenderer-API und Renderer-Vertrag

## Ziel

Eine klare, mode-aware Renderer-API einführen, die künftig auch für XML als Vorbild dienen kann.

## 4.2.a Mode-aware MarkdownRenderer einführen

Ziel:

Der Renderer soll je nach `RepositoryExport.mode` passende Markdown-Ausgabe erzeugen.

Mögliche API:

~~~python
class MarkdownRenderer:
    def render(self, export: RepositoryExport) -> str: ...
    def render_full(self, export: RepositoryExport) -> str: ...
    def render_ai(self, export: RepositoryExport) -> str: ...
    def render_docs(self, export: RepositoryExport) -> str: ...
    def render_changed(self, export: RepositoryExport) -> str: ...
~~~

Zusätzliche Convenience-Funktionen:

~~~python
def render_markdown(export: RepositoryExport) -> str: ...
def render_full_markdown(export: RepositoryExport) -> str: ...
def render_ai_markdown(export: RepositoryExport) -> str: ...
def render_docs_markdown(export: RepositoryExport) -> str: ...
def render_changed_markdown(export: RepositoryExport) -> str: ...
~~~

Akzeptanzkriterien:

- `render_markdown(export)` dispatcht anhand von `export.mode`.
- Mode-spezifische Wrapper sind getestet.
- Ungültige Modes werden über die bestehende Modellvalidierung oder eine klare Fehlermeldung abgefangen.
- Der bestehende Import `from repodossier.renderers import MarkdownRenderer, render_markdown` bleibt funktionsfähig.

---

## 4.2.b Renderer darf keine IO-/Analyzer-Abhängigkeiten importieren

Ziel:

Der Renderer bleibt rein.

Nicht erlaubt in `renderers/markdown.py`:

- `RepositoryScanner`
- `find_repository_root`
- `get_repository_info`
- `get_diff`
- `get_diff_against_branch`
- `analyze_dependencies`
- `analyze_database_schemas`
- `build_import_graph`
- `build_call_graph`
- `mask_export_file`
- `ensure_repodossier_gitignore_entries`
- direkte `Path.read_text(...)`-Nutzung
- direkte `Path.write_text(...)`-Nutzung

Akzeptanzkriterien:

- Tests oder statische Prüfungen verhindern verbotene Imports im Renderer.
- Renderer-Tests monkeypatchen keine Analyzer, weil keine importiert werden.
- Exporter bleiben für Datensammlung zuständig.

---

## 4.2.c Section-Order-Konstanten zentralisieren

Ziel:

Die Reihenfolge der Markdown-Abschnitte soll explizit und testbar sein.

Mögliche Struktur:

- `FULL_MARKDOWN_SECTION_ORDER`
- `AI_MARKDOWN_SECTION_ORDER`
- `DOCS_MARKDOWN_SECTION_ORDER`
- `CHANGED_MARKDOWN_SECTION_ORDER`

Anforderungen:

- Reihenfolge ist deterministisch.
- Tests prüfen die wichtigsten Überschriften in Reihenfolge.
- Änderungen an der Reihenfolge sind bewusst und sichtbar.

Akzeptanzkriterien:

- Full, AI, Docs und Changed haben getrennte Section-Order-Definitionen.
- Tests prüfen nicht jedes Zeichen, aber die Reihenfolge zentraler Abschnitte.

---

## 4.2.d Gemeinsame Markdown-Hilfsfunktionen sauber halten

Ziel:

Wiederverwendbare Formatierung soll im Renderer liegen, aber keine Analyse enthalten.

Erlaubte Hilfsfunktionen:

- Markdown-Listen formatieren
- Markdown-Tabellen formatieren
- Überschriften zusammenbauen
- sichere Code-Fences wählen
- leere Werte normalisieren
- Zahlen formatieren
- Report-Items sortieren
- Content aus `FileEntry.rendered_content` verwenden

Nicht erlaubt:

- Dateiinhalt nachladen
- Sprache neu erkennen
- Secrets neu scannen
- Git-Diff erzeugen
- Symbolindex neu berechnen

Akzeptanzkriterien:

- Code-Fence-Logik ist getestet.
- `masked_content` gewinnt vor `content`.
- Sortierung ist deterministisch.

---

## 4.2.e Legacy-Überschriften bewusst statt generisch rendern

Ziel:

Die generische Ausgabe `# RepoDossier Export (full)` reicht für den eigentlichen `full.txt`-Export nicht aus.

Anforderung:

- Full-Modus rendert mit Legacy-Heading `# AI Quick Start` als erstem sichtbaren Abschnitt.
- AI-Modus rendert mit `# AI CONTEXT`.
- Docs-Modus rendert mit Documentation-Headings.
- Changed-Modus rendert mit Changed-Headings.
- Der generische Renderer kann für Debug/Tests bleiben, darf aber nicht die produktiven Exporte ersetzen.

Akzeptanzkriterien:

- `repodossier full` erzeugt keine rein generische Renderer-Ausgabe.
- `repodossier export-ai` erzeugt keine Full-Ausgabe.
- Jeder Modus hat eigene Top-Level-Struktur.

---

# 4.3 Modell-Views und Adapter für Legacy-Daten

## Ziel

Daten, die bisher in Legacy-Kontextklassen liegen, sollen in `RepositoryExport` oder klar definierte View-Helfer überführt werden, ohne dass Renderer selbst Daten sammeln.

## 4.3.a FullExportContext zu RepositoryExport überführen

Ziel:

Der bestehende Full-Kontext soll als Quelle genutzt werden, aber die Ausgabe soll aus dem Modell kommen.

Mögliche Funktion:

~~~python
def repository_export_from_full_context(context: FullExportContext) -> RepositoryExport: ...
~~~

Anforderungen:

- Repository-Metadaten übernehmen.
- Config-Zusammenfassung übernehmen.
- Summary übernehmen.
- Tree übernehmen.
- FileEntry-Daten übernehmen.
- Warnings übernehmen.
- Dependency-/Schema-/Secret-/Import-/Call-Reports befüllen, soweit vorhanden.

Akzeptanzkriterien:

- Full-Kontext kann vollständig in ein Modell konvertiert werden.
- Die Konvertierung führt keine Markdown-Formatierung aus.
- Tests prüfen mindestens Metadaten, Dateien, Warnings und Language Statistics.

---

## 4.3.b AIExportContext zu RepositoryExport überführen

Ziel:

AI-spezifische kompakte Daten sollen strukturiert vorliegen, nicht im Renderer berechnet werden.

Mögliche Funktion:

~~~python
def repository_export_from_ai_context(context: AIExportContext) -> RepositoryExport: ...
~~~

Zu modellieren:

- Projektzusammenfassung
- Architecture Summary
- Important Files mit Gründen
- kompakte Dependencies
- kompakte Database Schema Daten
- Symbol Index
- Import Graph
- Call Graph
- Notes und Warnings

Akzeptanzkriterien:

- Important-File-Ranking wird nicht im Renderer ausgeführt.
- Der Renderer bekommt die bereits berechneten wichtigen Dateien als strukturierte Items.
- AI-Ausgabe bleibt kompakt.

---

## 4.3.c DocumentationExportContext zu RepositoryExport überführen

Ziel:

Docs-Export bleibt docs-only, aber Rendering erfolgt aus dem Modell.

Mögliche Funktion:

~~~python
def repository_export_from_docs_context(context: DocumentationExportContext) -> RepositoryExport: ...
~~~

Zu modellieren:

- Dokumentationsdateien
- Kategorien
- Summary-Zahlen
- extrahierte Dokumentinhalte
- übersprungene generierte Exportdateien
- Warnings

Akzeptanzkriterien:

- Docs-Auswahl bleibt im Exporter oder Builder.
- Renderer entscheidet nicht, ob eine Datei Dokumentation ist.
- Source-Code-Dateien landen nicht versehentlich in `docs.txt`.

---

## 4.3.d Changed-Daten als RepositoryExport-kompatible Struktur modellieren

Ziel:

`changed.txt` braucht zusätzliche Review-Daten, die nicht vollständig in normalen FileEntry-Feldern stecken.

Mögliche Lösung für Milestone 4:

- generische Report-Items im Modell nutzen
- oder einen kleinen `ChangedExportReport` als neues Modellfeld einführen
- oder `RepositoryExport` um mode-spezifische `metadata` / `sections` erweitern

Wichtig:

Die Lösung soll XML in Milestone 5 nicht blockieren. Diff, Compare Mode und Changed-Status dürfen nicht nur als fertig gerenderter Markdown-Blob gespeichert werden.

Zu modellieren:

- repository path
- compare mode
- branch base, falls vorhanden
- diff text
- changed file scans
- deleted files
- binary/skipped files
- untracked files
- warning/limit notices
- Bash call graph Daten, falls aktuell ausgegeben

Akzeptanzkriterien:

- `changed.txt` wird aus modellierten Daten gerendert.
- Git-Diff wird nicht im Renderer erzeugt.
- File-Content wird nicht im Renderer gelesen.
- Deleted/Binary/Skipped erscheinen weiterhin korrekt.

---

## 4.3.e Report-Items normalisieren

Ziel:

Die vorhandenen generischen Report-Strukturen sollen rendererfreundlich werden.

Zu prüfen:

- `DependencyReport.items`
- `DatabaseSchemaReport.items`
- `SecretDetectionSummary.findings`
- `SymbolIndex.symbols`
- `ImportGraphReport.edges`
- `CallGraphReport.edges`

Anforderungen:

- Items sind sortierbar.
- Items enthalten keine unmaskierten Secrets.
- Items sind primitive Datenstrukturen, die später XML-fähig sind.
- Renderer muss nicht raten, welche Keys möglich sind.

Akzeptanzkriterien:

- Für jeden Reportbereich gibt es mindestens einen Renderer-Test mit künstlichen Items.
- Fehlende optionale Keys crashen nicht.
- Sortierung ist stabil.

---

## 4.3.f Übergangsadapter klar kennzeichnen

Ziel:

Wenn Legacy-Renderer-Hilfsfunktionen vorübergehend genutzt werden, soll das sichtbar und begrenzt sein.

Anforderungen:

- Übergangsadapter mit Namen wie `_legacy_*` oder `_adapt_*` kennzeichnen.
- Keine neuen Features in Legacy-Rendering-Helfer einbauen.
- Zielrichtung dokumentieren: Daten in Modell, Darstellung in Renderer.

Akzeptanzkriterien:

- Es ist klar, welche Funktionen später entfernt werden können.
- Keine neue dauerhafte doppelte Rendering-Logik entsteht.

---

# 4.4 Full Markdown Export migrieren

## Ziel

`full.txt` soll aus `RepositoryExport(mode="full")` gerendert werden, ohne sichtbare Kernstruktur zu brechen.

## 4.4.a Full-Modell aus aktuellem Full-Kontext bauen

Ziel:

`render_full_export(context)` soll intern ein Full-Modell bauen und den MarkdownRenderer nutzen.

Möglicher Ablauf:

~~~text
FullExportContext
  -> RepositoryExport(mode="full")
  -> MarkdownRenderer.render_full(...)
  -> full.txt content
~~~

Akzeptanzkriterien:

- `render_full_export(context)` bleibt aufrufbar.
- Der Rückgabewert ist weiterhin ein String.
- Die Ausgabe enthält die bisherigen Hauptabschnitte.
- Keine Datei wird im Renderer gelesen.

---

## 4.4.b AI Quick Start aus Modelldaten rendern

Ziel:

Der erste Full-Abschnitt bleibt nützlich und stabil.

Zu rendern:

- Projektart
- primäre Sprache
- Package Manager
- Test Framework
- Entrypoints
- Purpose

Anforderung:

Diese Daten müssen vor dem Renderer berechnet oder im Modell abgelegt sein. Der Renderer darf nicht erneut `pyproject.toml` parsen.

Akzeptanzkriterien:

- `# AI Quick Start` bleibt vorhanden.
- Entrypoints erscheinen weiterhin.
- `repodossier` und `repocontext` werden nicht fälschlich entfernt.

---

## 4.4.c Repository Statistics aus ExportSummary rendern

Ziel:

Statistikdaten sollen nicht mehr aus FileInfo-Sequenzen im Renderer berechnet werden.

Zu rendern:

- Total tracked files
- Scanned files
- Exported text files
- Skipped binary files
- Errored files
- Total lines
- Estimated tokens
- File types

Akzeptanzkriterien:

- Zahlen kommen aus `ExportSummary`.
- Formatierung bleibt lesbar.
- Tausendertrennung bleibt konsistent, falls bisher vorhanden.

---

## 4.4.d File Summary und Repository Tree aus Modell rendern

Ziel:

Dateiübersicht und Tree sollen aus `FileEntry` und `FileTreeEntry` kommen.

Anforderungen:

- Gruppierung nach Sprache/Dateityp bleibt erhalten, falls bisher vorhanden.
- Neue Sprachlabels aus Milestone 2 bleiben lesbar.
- Tree-Sortierung ist deterministisch.
- Skipped/truncated/error Dateien werden sichtbar, wenn das bisherige Verhalten sie sichtbar macht.

Akzeptanzkriterien:

- `# File Summary` bleibt vorhanden.
- `# Repository Tree` bleibt vorhanden.
- Tests prüfen Sortierung und Sprachlabels.

---

## 4.4.e Dependencies und Database Schema aus Reports rendern

Ziel:

Dependency- und Schema-Abschnitte sollen aus strukturierten Reportdaten kommen.

Anforderungen Dependencies:

- Runtime dependencies
- Development dependencies
- Optional dependencies
- Unknown dependencies
- Dependency files
- Unsupported lines/Warnungen, falls vorhanden

Anforderungen Database Schema:

- Summary
- Database files
- SQL schema files
- Tables
- Views
- Relationships
- Warnings
- keine Datenbankinhalte

Akzeptanzkriterien:

- Renderer ruft `analyze_dependencies` nicht auf.
- Renderer ruft `analyze_database_schemas` nicht auf.
- Bestehende Abschnittsüberschriften bleiben.
- Leere Reports erzeugen stabile leere Hinweise statt Crash.

---

## 4.4.f Secret Detection Abschnitt aus Modell rendern

Ziel:

Secret Detection bleibt sichtbar und sicher.

Anforderungen:

- Findings enthalten nur Typen, Counts, Pfade oder maskierte Informationen.
- Keine Originalwerte rendern.
- `masked_content` gewinnt vor `content`.
- Der finale Safety-Net-Masker bleibt beim Schreiben aktiv.

Akzeptanzkriterien:

- Tests mit Fake-Secret bleiben grün.
- Kein unmaskierter Wert erscheint in `full.txt`.
- Secret Detection Abschnitt bleibt an stabiler Stelle.

---

## 4.4.g Complete Source Export aus FileEntry rendern

Ziel:

Quelltextausgabe nutzt ausschließlich `FileEntry.rendered_content`.

Anforderungen:

- passende Markdown-Code-Fence-Language verwenden
- Sprache aus zentraler Language Detection nutzen
- Fences sicher wählen, wenn Inhalt selbst Fences enthält
- truncated/skipped Dateien korrekt behandeln
- generated exports nicht self-referentiell aufnehmen

Akzeptanzkriterien:

- `# Complete Source Export` bleibt vorhanden.
- Python, Bash, TypeScript, JavaScript, HTML, CSS, Java, C, C++ und C# bekommen sinnvolle Code-Fence-Labels.
- Inhalte werden nicht im Renderer nachgeladen.

---

## 4.4.h Import Graph und Call Graph aus Reports rendern

Ziel:

Graph-Abschnitte werden aus Reportdaten gerendert, nicht im Renderer berechnet.

Anforderungen:

- Summary-Zahlen bleiben sichtbar.
- Local/internal Beziehungen bleiben prominent.
- External, ambiguous und unresolved bleiben getrennt.
- Display-Limits bleiben deterministisch.
- Truncation-Hinweise bleiben erhalten.

Akzeptanzkriterien:

- Renderer importiert keine Graph-Builder.
- Import Graph Abschnitt bleibt vorhanden.
- Call Graph Abschnitt bleibt vorhanden.
- Tests prüfen mindestens einen internen und einen externen Edge.

---

## 4.4.i Full-Export-Kompatibilitätstest

Ziel:

Der produktive Befehl bleibt stabil.

Tests:

~~~bash
python3 -m pytest --color=yes tests/test_full_exporter.py tests/test_full_exporter_import_graph_section.py tests/test_full_exporter_dependencies.py
~~~

Zusätzlich prüfen:

~~~bash
repodossier full
~~~

Akzeptanzkriterien:

- `full.txt` wird erzeugt.
- `ai.txt` wird weiterhin erzeugt, falls `repodossier full` aktuell beide Dateien erzeugt.
- Split-Optionen bleiben funktionsfähig.
- Keine neuen generierten Dateien werden committed.

---

# 4.5 AI Markdown Export migrieren

## Ziel

`ai.txt` soll aus `RepositoryExport(mode="ai")` gerendert werden und kompakt bleiben.

## 4.5.a AI-Modell aus AIExportContext bauen

Ziel:

AI-spezifische Daten werden vor dem Renderer vorbereitet.

Möglicher Ablauf:

~~~text
FullExportContext
  -> AIExportContext
  -> RepositoryExport(mode="ai")
  -> MarkdownRenderer.render_ai(...)
  -> ai.txt content
~~~

Akzeptanzkriterien:

- `render_ai_export(context)` bleibt aufrufbar.
- AI-Ausgabe enthält keinen vollständigen Source Dump.
- Important Files werden weiterhin begrenzt.

---

## 4.5.b Project und Architecture Summary rendern

Ziel:

Die kompakte AI-Orientierung bleibt erhalten.

Zu rendern:

- Repository-Name
- Tracked/scanned/exported counts
- Project type
- Main entry points
- Top-level directories
- Python package/module roots
- Core areas
- Tests
- Documentation

Akzeptanzkriterien:

- `## Project` bleibt vorhanden.
- `## Architecture Summary` bleibt vorhanden.
- Ausgabe bleibt deutlich kompakter als `full.txt`.

---

## 4.5.c Important Files aus strukturierten Items rendern

Ziel:

Ranking wird nicht im Renderer berechnet.

Anforderungen:

- Pfad
- Reason
- deterministische Reihenfolge
- Limit bleibt erhalten
- generated exports bleiben ausgeschlossen

Akzeptanzkriterien:

- `## Important Files` bleibt vorhanden.
- Jeder Eintrag hat einen Grund.
- Renderer importiert kein Ranking-Modul.

---

## 4.5.d AI Dependencies und Database Schema kompakt rendern

Ziel:

AI-Ausgabe bleibt token-sparend.

Anforderungen:

- keine vollständigen langen Tabellen, wenn kompakte Summary genügt
- klare Hinweise bei leeren Reports
- keine Datenbankinhalte
- keine Secrets

Akzeptanzkriterien:

- `## Dependencies` bleibt vorhanden, wenn Daten vorhanden oder bisher vorgesehen.
- `## Database Schema` bleibt vorhanden.
- Ausgabe bleibt stabil und kompakt.

---

## 4.5.e Symbol Index, Import Graph und Call Graph kompakt rendern

Ziel:

AI behält die wichtigsten statischen Analyseinformationen.

Anforderungen:

- Symbol Index gruppiert nach Datei
- Import Graph Summary und lokale Imports
- Call Graph Summary und wichtigste Edges
- Limits für große Projekte

Akzeptanzkriterien:

- Renderer berechnet keine Symbole.
- Renderer baut keinen Import Graph.
- Renderer baut keinen Call Graph.
- Bestehende AI-Graph-Tests bleiben grün.

---

## 4.5.f Notes und Warnings rendern

Ziel:

AI-Ausgabe enthält weiterhin Kontext zu Limitierungen.

Typische Notes:

- static analysis only
- dynamic behavior may be incomplete
- generated exports excluded
- secret masking best effort
- `repocontext` legacy alias Hinweis nur falls bisher passend

Akzeptanzkriterien:

- `## Notes` bleibt vorhanden.
- Warnings werden nicht verschluckt.
- Keine irreführenden neuen Versprechen.

---

## 4.5.g AI-Export-Kompatibilitätstest

Tests:

~~~bash
python3 -m pytest --color=yes tests/test_ai_exporter.py tests/test_ai_exporter_dependencies.py tests/test_ai_split_export.py
~~~

Zusätzlich prüfen:

~~~bash
repodossier export-ai
repocontext export-ai
~~~

Akzeptanzkriterien:

- `ai.txt` wird erzeugt.
- Inhalt ist kompakt.
- Legacy-Alias funktioniert.
- Split-Export funktioniert.

---

# 4.6 Docs Markdown Export migrieren

## Ziel

`docs.txt` soll docs-only bleiben, aber aus `RepositoryExport(mode="docs")` gerendert werden.

## 4.6.a Docs-Auswahl außerhalb des Renderers halten

Ziel:

Renderer entscheidet nicht, was Dokumentation ist.

Anforderungen:

- `is_documentation_file(...)` bleibt im Docs-Exporter oder einem Builder.
- Dokumentationskategorien werden vor dem Renderer berechnet.
- Source-Code-Dateien werden nicht im Renderer herausgefiltert.

Akzeptanzkriterien:

- Renderer importiert keine Docs-Auswahlfunktion.
- Tests für `is_documentation_file(...)` bleiben erhalten.
- Docs-Ausgabe bleibt docs-only.

---

## 4.6.b Documentation Quick Start rendern

Ziel:

Docs-Ausgabe bleibt direkt verständlich.

Zu rendern:

- Repository-Name
- Anzahl Dokumentationsdateien
- wichtigste Dokumenttypen
- Hinweis auf Zweck von `docs.txt`

Akzeptanzkriterien:

- `# Documentation Quick Start` bleibt vorhanden.
- Ausgabe enthält keine Source-Export-Abschnitte.

---

## 4.6.c Documentation Summary und Files rendern

Ziel:

Übersicht über Dokumentationsdateien bleibt erhalten.

Zu rendern:

- Counts nach Kategorien
- Pfade
- Kategorie
- Lines/Size, falls bisher vorhanden
- Warnings für skipped/generated docs

Akzeptanzkriterien:

- `# Documentation Summary` bleibt vorhanden.
- `# Documentation Files` bleibt vorhanden.
- Sortierung ist deterministisch.

---

## 4.6.d Extracted Documents aus FileEntry rendern

Ziel:

Dokumentinhalte kommen aus `FileEntry.rendered_content`.

Anforderungen:

- Markdown-Dateien werden lesbar eingefügt.
- Code-Fences werden sicher gewählt.
- Große Dokumente respektieren Limits.
- Maskierte Inhalte bleiben maskiert.

Akzeptanzkriterien:

- `# Extracted Documents` bleibt vorhanden.
- Inhalt wird nicht im Renderer nachgeladen.
- Config-Limits bleiben wirksam.

---

## 4.6.e Docs-Export-Kompatibilitätstest

Tests:

~~~bash
python3 -m pytest --color=yes tests/test_docs_exporter.py tests/test_cli_docs_export.py tests/test_docs_split_export.py
~~~

Zusätzlich prüfen:

~~~bash
repodossier export-docs
repocontext export-docs
~~~

Akzeptanzkriterien:

- `docs.txt` wird erzeugt.
- Keine Source-Code-Dateien werden ungewollt aufgenommen.
- Legacy-Alias funktioniert.
- Split-Export funktioniert.

---

# 4.7 Changed Markdown Export migrieren

## Ziel

`changed.txt` soll review-fokussiert bleiben, aber aus modellierten Changed-Daten gerendert werden.

## 4.7.a Changed-Export-Datenmodell festlegen

Ziel:

Changed-spezifische Daten bekommen eine saubere Struktur.

Mindestens modellieren:

- repository path
- compare mode
- target branch, falls vorhanden
- changed files overview
- status pro Datei
- line count / token estimate, falls vorhanden
- git diff text
- changed file contents
- deleted files
- binary/skipped files
- warning/limit notices

Akzeptanzkriterien:

- Git-Diff ist Datenfeld, kein Renderer-Ergebnis.
- Changed-Dateiinhalte sind Datenfelder, keine Renderer-Dateileseoperation.
- Deleted/Binary/Skipped sind strukturiert.

---

## 4.7.b ChangedFileScan zu FileEntry oder Changed Items adaptieren

Ziel:

Vorhandene `ChangedFileScan` Daten sollen wiederverwendet werden.

Anforderungen:

- Status erhalten
- Pfad erhalten
- Sprache aus FileInfo übernehmen
- Content vor Renderer lesen und limitieren
- Binary/skipped korrekt markieren
- Deleted ohne Content markieren

Akzeptanzkriterien:

- Untracked Dateien bleiben unterstützt, sofern bisher unterstützt.
- Deleted Dateien erscheinen weiterhin.
- Binary/skipped Dateien erscheinen weiterhin.
- Renderer kennt keine Scanner-Details.

---

## 4.7.c Compare Mode und Branch-Diff erhalten

Ziel:

`repodossier changed` und `repodossier changed --branch main` bleiben korrekt.

Anforderungen:

- Working-tree mode bleibt erhalten.
- Branch comparison mode bleibt erhalten.
- Git diff wird vor Renderer gesammelt.
- Fehlende Branches erzeugen weiterhin verständliche Fehler.

Akzeptanzkriterien:

- Tests für `--branch` bleiben grün.
- Compare Mode erscheint in `changed.txt`.
- Renderer ruft kein Git auf.

---

## 4.7.d Git Diff Abschnitt rendern

Ziel:

Diff bleibt zentraler Review-Abschnitt.

Anforderungen:

- Diff in `diff` Code-Fence oder bestehendem Format rendern.
- Leerer Diff bekommt klaren Hinweis.
- Diff wird nicht neu erzeugt.
- Secret Masking greift vor oder beim Schreiben weiterhin.

Akzeptanzkriterien:

- `# Git Diff` bleibt vorhanden.
- Diff-Inhalt erscheint bei Änderungen.
- Kein unmaskierter Fake-Secret-Wert erscheint.

---

## 4.7.e Changed File Contents rendern

Ziel:

Geänderte Textdateien bleiben direkt sichtbar.

Anforderungen:

- Sprache für Code-Fence aus `FileEntry.language`
- Content aus `rendered_content`
- Line/file/export limits beachten
- Untracked non-ignored Dateien weiterhin möglich

Akzeptanzkriterien:

- `# Changed File Contents` bleibt vorhanden.
- Inhalte werden nicht im Renderer gelesen.
- Code-Fence-Language bleibt korrekt.

---

## 4.7.f Deleted und Binary / Skipped rendern

Ziel:

Review-relevante Nicht-Content-Fälle bleiben sichtbar.

Anforderungen:

- Deleted files separat listen.
- Binary files separat listen.
- Skipped wegen Limits separat listen.
- Gründe anzeigen, falls vorhanden.

Akzeptanzkriterien:

- `# Deleted Files` bleibt vorhanden, wenn relevant.
- `# Binary / Skipped Files` bleibt vorhanden, wenn relevant.
- Keine Crashes bei gemischten Status.

---

## 4.7.g Bash Call Graph Zusatz im Changed Export erhalten oder bewusst abgrenzen

Ziel:

Falls `changed.txt` aktuell Bash Call Graph Kontext ergänzt, darf dieser nicht versehentlich verschwinden.

Aufgabe:

- Prüfen, ob Changed Export Bash Call Graph Abschnitte aktuell ausgibt.
- Entscheiden, ob dieser Abschnitt in Milestone 4 migriert wird.
- Wenn ja: Daten vor Renderer sammeln und als Report rendern.
- Wenn nein: bewusst dokumentieren und Tests entsprechend anpassen, aber nicht still entfernen.

Akzeptanzkriterien:

- Bestehende Bash-Changed-Tests bleiben grün oder werden mit klarer Migrationsentscheidung angepasst.
- Renderer führt keine Bash-Analyse aus.

---

## 4.7.h Changed-Export-Kompatibilitätstest

Tests:

~~~bash
python3 -m pytest --color=yes tests/test_changed_exporter.py tests/test_changed_cli.py tests/test_changed_cli_acceptance.py tests/test_changed_split_export.py
~~~

Zusätzlich prüfen:

~~~bash
repodossier changed
repocontext changed
~~~

Akzeptanzkriterien:

- `changed.txt` wird erzeugt.
- Working-tree Mode funktioniert.
- Branch Mode funktioniert.
- Split-Export funktioniert.
- Legacy-Alias funktioniert.

---

# 4.8 CLI, Output Writer, Split Export und Secret Safety

## Ziel

Die Renderer-Migration darf keine bestehenden CLI- und Schreibpfade brechen.

## 4.8.a CLI-Kompatibilität sichern

Ziel:

Alle bestehenden Kommandos bleiben nutzbar.

Zu prüfen:

- `repodossier`
- `repodossier full`
- `repodossier export`
- `repodossier export-ai`
- `repodossier export-docs`
- `repodossier changed`
- `repodossier info`
- `repocontext full`
- `repocontext export-ai`
- `repocontext export-docs`
- `repocontext changed`

Akzeptanzkriterien:

- CLI-Parser muss nicht neu erfunden werden.
- Bestehende Hilfeausgaben bleiben plausibel.
- `repocontext` bleibt Alias.

---

## 4.8.b Output Writer unverändert oder minimal nutzen

Ziel:

Schreiblogik bleibt getrennt vom Renderer.

Anforderungen:

- Renderer gibt String zurück.
- Output Writer schreibt String.
- Split Interceptor funktioniert weiter.
- Atomic/temporary output behavior bleibt, falls vorhanden.

Akzeptanzkriterien:

- `write_export_output(...)` bleibt nutzbar.
- Split-Dateien heißen weiterhin stabil.
- Keine Schreiblogik wandert in den Renderer.

---

## 4.8.c Split-Exports für alle Modi testen

Ziel:

Renderer-Migration darf Split-Export nicht brechen.

Zu prüfen:

- `repodossier full --split`
- `repodossier export-ai --split`
- `repodossier export-docs --split`
- `repodossier changed --split`

Akzeptanzkriterien:

- Hauptdatei wird vollständig geschrieben.
- `.partXX.txt` Dateien werden geschrieben.
- Stale part files werden entfernt.
- Split-Header bleibt stabil.

---

## 4.8.d Secret Safety Net erhalten

Ziel:

Sicherheitslogik bleibt auch nach Renderer-Migration aktiv.

Anforderungen:

- Content im Modell ist entweder bereits maskiert oder `masked_content` ist gesetzt.
- Renderer verwendet `rendered_content`.
- Finaler Safety-Net-Masker nach dem Schreiben bleibt aktiv, solange er existiert.
- Secret Detection Sections enthalten keine Originalwerte.

Akzeptanzkriterien:

- Secret-End-to-End-Tests bleiben grün.
- Fake Secrets werden maskiert.
- Keine unmaskierten Werte in generated exports.

---

## 4.8.e Config-Filter und Limits erhalten

Ziel:

Include/Exclude und Limits bleiben vor dem Renderer wirksam.

Zu prüfen:

- include paths
- include globs
- exclude paths
- exclude globs
- max_file_bytes
- max_total_files
- max_export_bytes
- max_line_count
- split settings

Akzeptanzkriterien:

- Renderer entscheidet nicht über Include/Exclude.
- Limit Notices bleiben sichtbar.
- Config Summary bleibt im Export sichtbar.
- Bestehende Config-Tests bleiben grün.

---

# 4.9 Tests für Renderer-Grenzen und Regressionen

## Ziel

Milestone 4 braucht starke Tests, weil er die Rendering-Architektur umstellt.

## 4.9.a Renderer-Unit-Tests mit künstlichem Modell ausbauen

Ziel:

Renderer muss ohne echtes Repository testbar sein.

Tests in oder nahe bei:

- `tests/test_markdown_renderer.py`

Zu ergänzen:

- `render_full_markdown` mit künstlichem Full-Modell
- `render_ai_markdown` mit künstlichem AI-Modell
- `render_docs_markdown` mit künstlichem Docs-Modell
- `render_changed_markdown` mit künstlichem Changed-Modell
- masked content gewinnt vor raw content
- warnings werden gerendert
- reports werden sortiert gerendert
- fehlende optionale Reports crashen nicht

Akzeptanzkriterien:

- Renderer-Tests brauchen kein Git.
- Renderer-Tests brauchen keine echten Dateien.
- Renderer-Tests sind schnell und deterministisch.

---

## 4.9.b Anti-IO-/Anti-Analyzer-Test für Renderer ergänzen

Ziel:

Verhindern, dass später versehentlich Analyse in den Renderer wandert.

Mögliche Teststrategie:

- Quelltext von `src/repodossier/renderers/markdown.py` lesen.
- Verbotene Importnamen prüfen.
- Verbotene Methoden wie `.read_text(` und `.write_text(` prüfen.

Zu verbietende Tokens mindestens:

- `RepositoryScanner`
- `get_repository_info`
- `get_diff(`
- `get_diff_against_branch`
- `analyze_dependencies`
- `analyze_database_schemas`
- `build_import_graph`
- `build_call_graph`
- `mask_export_file`
- `.read_text(`
- `.write_text(`

Akzeptanzkriterien:

- Test schlägt fehl, wenn der Renderer Git/Scanner/Analyzer importiert.
- Test ist nicht zu fragil gegenüber normalen Formatierungsänderungen.

---

## 4.9.c Exporter-Integrationstests für alle Modi erhalten

Ziel:

Nicht nur Renderer isoliert testen, sondern echte Befehle weiterhin prüfen.

Tests:

~~~bash
python3 -m pytest --color=yes \
  tests/test_full_exporter.py \
  tests/test_ai_exporter.py \
  tests/test_docs_exporter.py \
  tests/test_changed_exporter.py
~~~

Akzeptanzkriterien:

- Alle vier Exportmodi erzeugen erwartete Abschnitte.
- Tests zeigen, dass die Produktpfade den Renderer nutzen.
- Keine Snapshot-/Regressionstests werden sinnlos gelöscht.

---

## 4.9.d CLI-Smoke-Tests erhalten

Tests:

~~~bash
python3 -m pytest --color=yes tests/test_cli.py tests/test_release_smoke_cli.py tests/test_repodossier_cli_alias.py
~~~

Akzeptanzkriterien:

- `repodossier --help` funktioniert.
- `repodossier --version` funktioniert.
- `repocontext --help` funktioniert.
- `repocontext --version` funktioniert.
- Hauptcommands bleiben registriert.

---

## 4.9.e Golden-/Snapshot-Tests vorsichtig einsetzen

Ziel:

Regressionen erkennen, aber nicht jeden Whitespace zur Blockade machen.

Empfehlung:

- Keine riesigen Vollsnapshot-Dateien für komplette `full.txt`, wenn sie zu fragil sind.
- Stattdessen Abschnittsreihenfolge, zentrale Überschriften und exemplarische Inhalte testen.
- Für künstliche kleine Modelle kann ein vollständiger Snapshot sinnvoll sein.

Akzeptanzkriterien:

- Tests sind stabil.
- Wichtige Ausgabeänderungen fallen auf.
- Kleine Formatierungsdetails blockieren nicht unnötig.

---

# 4.10 Dokumentation und Architektur aktualisieren

## Ziel

Nach der Migration muss die Dokumentation die neue Realität beschreiben.

## 4.10.a `architecture.md` aktualisieren

Ziel:

Architektur-Doku soll nicht mehr sagen, dass die vollständige Markdown-Migration noch offen ist, sobald sie umgesetzt ist.

Zu aktualisieren:

- Current Pipeline
- Renderer Direction
- Current Export Layer
- Data Flow by Command
- Current Milestone Boundary
- Tests and Regression Coverage

Akzeptanzkriterien:

- `RepositoryExport -> MarkdownRenderer -> Markdown exports` ist beschrieben.
- XML bleibt als nächster Milestone beschrieben.
- Keine falsche Behauptung, dass Markdown noch Legacy-only ist.

---

## 4.10.b README aktualisieren, falls nutzerrelevant

Ziel:

README muss nur angepasst werden, wenn sich sichtbares Verhalten oder Architekturabschnitte ändern.

Mögliche Anpassungen:

- Architecture overview
- Design principles
- Output sections, falls Format leicht geändert wurde
- Roadmap-Status

Akzeptanzkriterien:

- Keine unnötige große README-Umschreibung.
- Nutzerbefehle bleiben korrekt.
- Roadmap-Verweis bleibt aktuell.

---

## 4.10.c Milestone-Datei hinzufügen

Ziel:

Diese Planung wird im Repository abgelegt.

Pfad:

~~~text
planning/1.1.0/milestone4.md
~~~

Akzeptanzkriterien:

- Datei ist versioniert.
- Stil passt zu Milestone 1 bis 3.
- Keine Checkbox-Statuslogik nötig.

---

# 4.11 Abschlussprüfung für Milestone 4

## Ziel

Nach Umsetzung muss klar belegbar sein, dass die Migration vollständig und stabil ist.

## 4.11.a Syntaxprüfung

Befehl:

~~~bash
python3 -m compileall src tests
~~~

Akzeptanzkriterien:

- Keine Syntaxfehler.
- Keine kaputten Imports.

---

## 4.11.b Fokus-Tests für Renderer und Modell

Befehl:

~~~bash
python3 -m pytest --color=yes \
  tests/test_markdown_renderer.py \
  tests/test_export_model.py \
  tests/test_export_model_api.py \
  tests/test_export_model_public_api_e2e.py \
  tests/test_export_model_scanner_integration.py
~~~

Akzeptanzkriterien:

- Renderer-Unit-Tests grün.
- Modelltests grün.
- Public API bleibt kompatibel.

---

## 4.11.c Fokus-Tests für alle Exportmodi

Befehl:

~~~bash
python3 -m pytest --color=yes \
  tests/test_full_exporter.py \
  tests/test_full_exporter_dependencies.py \
  tests/test_full_exporter_import_graph_section.py \
  tests/test_ai_exporter.py \
  tests/test_ai_exporter_dependencies.py \
  tests/test_docs_exporter.py \
  tests/test_changed_exporter.py
~~~

Akzeptanzkriterien:

- Full Export grün.
- AI Export grün.
- Docs Export grün.
- Changed Export grün.

---

## 4.11.d Split-Export-Tests

Befehl:

~~~bash
python3 -m pytest --color=yes \
  tests/test_full_split_export.py \
  tests/test_ai_split_export.py \
  tests/test_docs_split_export.py \
  tests/test_changed_split_export.py \
  tests/test_split_export_acceptance.py \
  tests/test_split_atomic_write_integration.py
~~~

Akzeptanzkriterien:

- Split bleibt für alle Exportmodi funktionsfähig.
- Part-Dateien werden korrekt erzeugt.
- Stale Part-Dateien werden entfernt.

---

## 4.11.e Secret- und Config-Tests

Befehl:

~~~bash
python3 -m pytest --color=yes \
  tests/test_secret_detection_end_to_end.py \
  tests/test_changed_exporter_secret_masking.py \
  tests/test_config.py \
  tests/test_config_full_export_filters.py \
  tests/test_config_ai_export_filters.py \
  tests/test_config_docs_export_filters.py \
  tests/test_config_changed_export_filters.py
~~~

Akzeptanzkriterien:

- Secret Masking bleibt wirksam.
- Config-Filter bleiben wirksam.
- Limits bleiben wirksam.

---

## 4.11.f Vollständige Testsuite

Befehl:

~~~bash
python3 -m pytest --color=yes
~~~

Akzeptanzkriterien:

- Alle Tests grün.
- Keine unerwarteten Skips.
- Keine neuen flaky Tests.

---

## 4.11.g Lokale CLI-Smoke-Prüfung

Befehle:

~~~bash
repodossier full
repodossier export-ai
repodossier export-docs
repodossier changed
repocontext full
repocontext export-ai
repocontext export-docs
repocontext changed
~~~

Akzeptanzkriterien:

- `full.txt` wird erzeugt.
- `ai.txt` wird erzeugt.
- `docs.txt` wird erzeugt.
- `changed.txt` wird erzeugt.
- Legacy-Alias funktioniert.
- Keine Exportdateien werden versehentlich committed.

---

## 4.11.h Pipx-Release-Validierung optional erneut ausführen

Befehl:

~~~bash
scripts/validate_pipx_release.sh
~~~

Akzeptanzkriterien:

- Build funktioniert.
- Twine Check funktioniert.
- Isolierte pipx-Installation funktioniert.
- Beide CLI-Namen funktionieren.
- Full/AI/Docs/Changed Smoke-Exports funktionieren.

---

## 4.11.i Git-Status und Diff prüfen

Befehle:

~~~bash
git status --short
git --no-pager diff -- src tests README.md architecture.md planning/1.1.0/milestone4.md
~~~

Akzeptanzkriterien:

- Nur erwartete Dateien geändert.
- Keine `full.txt`, `ai.txt`, `docs.txt`, `changed.txt` staged.
- Keine `dist/`, `build/`, `*.egg-info` staged.
- Diff ist nachvollziehbar.
- Kein Git-Pager hängt.

---

# 4.12 Empfohlene Patch-Reihenfolge

## Patch 4.1 – Renderer contract and baseline tests

Umfang:

- bestehende Markdown-Abschnitte als Vertrag testen
- Renderer-Grenzen definieren
- Anti-IO-/Anti-Analyzer-Test ergänzen
- Section-Order pro Modus festlegen

Tests:

~~~bash
python3 -m pytest --color=yes tests/test_markdown_renderer.py tests/test_full_exporter.py tests/test_ai_exporter.py tests/test_docs_exporter.py tests/test_changed_exporter.py
~~~

Commit-Vorschlag:

~~~text
Define Markdown renderer migration contract
~~~

---

## Patch 4.2 – Mode-aware MarkdownRenderer API

Umfang:

- `MarkdownRenderer.render_full`
- `MarkdownRenderer.render_ai`
- `MarkdownRenderer.render_docs`
- `MarkdownRenderer.render_changed`
- Convenience-Funktionen in `renderers/__init__.py`
- Unit-Tests mit künstlichen Modellen

Tests:

~~~bash
python3 -m pytest --color=yes tests/test_markdown_renderer.py tests/test_export_model_api.py
~~~

Commit-Vorschlag:

~~~text
Add mode-aware Markdown renderer API
~~~

---

## Patch 4.3 – Full export model-backed rendering

Umfang:

- FullExportContext zu RepositoryExport adaptieren
- Full Markdown aus Renderer rendern
- Legacy-Funktionen als Wrapper behalten
- Full-Export-Tests aktualisieren/erweitern

Tests:

~~~bash
python3 -m pytest --color=yes tests/test_full_exporter.py tests/test_full_exporter_dependencies.py tests/test_full_exporter_import_graph_section.py tests/test_markdown_renderer.py
~~~

Commit-Vorschlag:

~~~text
Render full markdown from export model
~~~

---

## Patch 4.4 – AI export model-backed rendering

Umfang:

- AIExportContext zu RepositoryExport adaptieren
- AI Markdown aus Renderer rendern
- Important Files als strukturierte Daten übergeben
- AI-Tests aktualisieren/erweitern

Tests:

~~~bash
python3 -m pytest --color=yes tests/test_ai_exporter.py tests/test_ai_exporter_dependencies.py tests/test_ai_split_export.py tests/test_markdown_renderer.py
~~~

Commit-Vorschlag:

~~~text
Render AI markdown from export model
~~~

---

## Patch 4.5 – Docs export model-backed rendering

Umfang:

- DocumentationExportContext zu RepositoryExport adaptieren
- Docs Markdown aus Renderer rendern
- Docs-only Auswahl außerhalb des Renderers halten
- Docs-Tests aktualisieren/erweitern

Tests:

~~~bash
python3 -m pytest --color=yes tests/test_docs_exporter.py tests/test_cli_docs_export.py tests/test_docs_split_export.py tests/test_markdown_renderer.py
~~~

Commit-Vorschlag:

~~~text
Render docs markdown from export model
~~~

---

## Patch 4.6 – Changed export model-backed rendering

Umfang:

- Changed-spezifische Modelldaten oder Reportstruktur einführen
- ChangedFileScan adaptieren
- Git Diff und Compare Mode als Daten übergeben
- Changed Markdown aus Renderer rendern
- Changed-Tests aktualisieren/erweitern

Tests:

~~~bash
python3 -m pytest --color=yes tests/test_changed_exporter.py tests/test_changed_cli.py tests/test_changed_cli_acceptance.py tests/test_changed_split_export.py tests/test_markdown_renderer.py
~~~

Commit-Vorschlag:

~~~text
Render changed markdown from export model
~~~

---

## Patch 4.7 – Split, secret, config and CLI hardening

Umfang:

- Split-Exports über neue Renderingpfade prüfen
- Secret Safety Net prüfen
- Config Summary und Limits prüfen
- CLI- und Legacy-Alias-Tests prüfen

Tests:

~~~bash
python3 -m pytest --color=yes \
  tests/test_split_export_acceptance.py \
  tests/test_secret_detection_end_to_end.py \
  tests/test_config_final_acceptance.py \
  tests/test_release_smoke_cli.py \
  tests/test_repodossier_cli_alias.py
~~~

Commit-Vorschlag:

~~~text
Preserve CLI split config and secret safety after renderer migration
~~~

---

## Patch 4.8 – Documentation and final smoke pass

Umfang:

- `architecture.md` aktualisieren
- README nur bei Bedarf aktualisieren
- `planning/1.1.0/milestone4.md` hinzufügen
- vollständige Testsuite
- Selbstexport mit RepoDossier

Tests:

~~~bash
python3 -m compileall src tests
python3 -m pytest --color=yes
scripts/validate_pipx_release.sh
~~~

Commit-Vorschlag:

~~~text
Finalize Markdown renderer migration
~~~

---

# 4.13 Definition of Done

Milestone 4 gilt als fertig, wenn alle folgenden Punkte erfüllt sind:

1. `planning/1.1.0/milestone4.md` existiert.
2. MarkdownRenderer hat eine klare mode-aware API.
3. Full Markdown kann aus `RepositoryExport(mode="full")` gerendert werden.
4. AI Markdown kann aus `RepositoryExport(mode="ai")` gerendert werden.
5. Docs Markdown kann aus `RepositoryExport(mode="docs")` gerendert werden.
6. Changed Markdown kann aus `RepositoryExport(mode="changed")` gerendert werden.
7. `render_markdown(export)` dispatcht korrekt nach Modus.
8. Legacy-Funktion `render_full_export(...)` bleibt aufrufbar.
9. Legacy-Funktion `render_ai_export(...)` bleibt aufrufbar.
10. Legacy-Funktion `render_docs_export(...)` bleibt aufrufbar.
11. Legacy-Funktion `render_changed_export(...)` bleibt aufrufbar.
12. `write_*_export(...)` Funktionen bleiben aufrufbar.
13. `generate_*_export(...)` Funktionen bleiben aufrufbar.
14. Renderer liest keine Dateien.
15. Renderer schreibt keine Dateien.
16. Renderer ruft kein Git auf.
17. Renderer startet keinen Scanner.
18. Renderer startet keine Dependency-Analyse.
19. Renderer startet keine Schema-Analyse.
20. Renderer baut keinen Import Graph.
21. Renderer baut keinen Call Graph.
22. Renderer führt keine Secret Detection aus.
23. Renderer nutzt `FileEntry.rendered_content`.
24. `masked_content` gewinnt vor `content`.
25. Full Export enthält weiterhin `# AI Quick Start`.
26. Full Export enthält weiterhin `# Repository Statistics`.
27. Full Export enthält weiterhin `# File Summary`.
28. Full Export enthält weiterhin `# Repository Tree`.
29. Full Export enthält weiterhin `# Complete Source Export`.
30. Full Export enthält weiterhin Import Graph und Call Graph, wenn Daten vorhanden sind.
31. AI Export enthält weiterhin `# AI CONTEXT`.
32. AI Export enthält weiterhin `## Important Files`.
33. AI Export bleibt kompakt und enthält keinen vollständigen Source Dump.
34. Docs Export enthält weiterhin Documentation-Abschnitte.
35. Docs Export bleibt docs-only.
36. Changed Export enthält weiterhin Summary, Diff und Changed File Contents.
37. Changed Export unterstützt weiterhin working-tree mode.
38. Changed Export unterstützt weiterhin branch comparison mode.
39. Deleted files werden im Changed Export weiterhin sichtbar.
40. Binary/skipped files werden im Changed Export weiterhin sichtbar.
41. Split-Exports funktionieren für Full.
42. Split-Exports funktionieren für AI.
43. Split-Exports funktionieren für Docs.
44. Split-Exports funktionieren für Changed.
45. Config Include/Exclude bleibt wirksam.
46. Config Limits bleiben wirksam.
47. Secret Masking regressiert nicht.
48. `repodossier` CLI bleibt kompatibel.
49. `repocontext` Legacy-Alias bleibt kompatibel.
50. Architektur-Doku beschreibt die neue Modell-zu-Markdown-Pipeline.
51. Renderer-Unit-Tests mit künstlichem Modell existieren.
52. Anti-IO-/Anti-Analyzer-Test für Renderer existiert.
53. Exporter-Integrationstests sind grün.
54. Split-Tests sind grün.
55. Secret-Tests sind grün.
56. Config-Tests sind grün.
57. CLI-Smoke-Tests sind grün.
58. `python3 -m compileall src tests` ist grün.
59. `python3 -m pytest --color=yes` ist grün.
60. Keine generierten Exportdateien werden committed.
61. Keine Build-Artefakte werden committed.

---

# Risiko-Check

## Hauptrisiko 1: Renderer bekommt wieder Analyseverantwortung

Gefahr:

- Der MarkdownRenderer importiert Scanner, Git oder Analyzer, weil Daten noch fehlen.

Gegenmaßnahme:

- Fehlende Daten im Builder/View ergänzen.
- Anti-IO-/Anti-Analyzer-Test einführen.
- Renderer nur mit künstlichen Modellen testen.

---

## Hauptrisiko 2: Ausgabe ändert sich unnötig stark

Gefahr:

- Nutzerworkflows, Tests oder AI-Prompts verlassen sich auf bestehende Überschriften.

Gegenmaßnahme:

- Überschriften und Section-Reihenfolge als Vertrag testen.
- Migration pro Exportmodus getrennt durchführen.
- Keine reine generische Renderer-Ausgabe als Produktformat verwenden.

---

## Hauptrisiko 3: Changed Export passt nicht sauber ins Modell

Gefahr:

- Diff und Compare Mode werden als Markdown-Blob versteckt und blockieren später XML.

Gegenmaßnahme:

- Changed-Daten strukturiert modellieren.
- Diff als Datenfeld speichern.
- File-Status als strukturierte Items speichern.

---

## Hauptrisiko 4: Doppelte Rendering-Logik bleibt dauerhaft

Gefahr:

- Alte Exporter und neuer Renderer rendern parallel dieselben Abschnitte.

Gegenmaßnahme:

- Legacy-Funktionen werden Wrapper.
- Übergangsadapter klar kennzeichnen.
- Neue Features nur in Modell/Renderer einbauen.

---

## Hauptrisiko 5: Secret Masking wird durch Modellschicht umgangen

Gefahr:

- Raw Content im Modell wird direkt gerendert, obwohl masked content vorhanden wäre.

Gegenmaßnahme:

- Renderer nutzt ausschließlich `FileEntry.rendered_content`.
- Secret-E2E-Tests behalten.
- Final Safety Net nicht entfernen.

---

## Hauptrisiko 6: Tests werden durch große Snapshots fragil

Gefahr:

- Jede kleine Formatänderung verursacht massive Snapshot-Diffs.

Gegenmaßnahme:

- Abschnitts- und Strukturtests bevorzugen.
- Vollsnapshots nur für kleine künstliche Modelle.
- Wichtige Inhalte statt kompletten realen Export starr testen.

---

# Kurze Umsetzungsreihenfolge

1. Bestehende Markdown-Abschnitte und öffentliche Funktionen inventarisieren.
2. Section-Verträge und Anti-IO-Regeln testen.
3. Mode-aware MarkdownRenderer API einführen.
4. Full Export aus Modell rendern.
5. AI Export aus Modell rendern.
6. Docs Export aus Modell rendern.
7. Changed Export aus Modell rendern.
8. Split, Config, Secret Safety und CLI prüfen.
9. Architektur-Doku aktualisieren.
10. Vollständige Testsuite und pipx-Validierung ausführen.

---

# Abschlussnotiz

Milestone 4 ist der eigentliche Beweis, dass das interne Export-Modell aus Milestone 3 tragfähig ist. Wenn Markdown sauber aus `RepositoryExport` gerendert wird, kann Milestone 5 XML deutlich sicherer und ohne doppelte Exportlogik umsetzen.
