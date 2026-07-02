# RepoDossier / RepoContext – Milestone 3

## Internes strukturiertes Export-Modell

Stand: 2026-07-02  
Roadmap-Bezug: 1.1.0 / Roadmap Next, Punkt 3  
Projektname: RepoDossier  
Legacy-Kompatibilität: RepoContext bleibt als Alias erhalten

---

## Ziel von Milestone 3

RepoDossier soll intern nicht mehr direkt und verteilt Markdown-Text zusammensetzen. Stattdessen wird ein zentrales, strukturiertes Export-Modell eingeführt.

Dieses Modell wird zur internen Quelle der Wahrheit für spätere Renderer:

- MarkdownRenderer in Milestone 4
- XMLRenderer in Milestone 5
- optionale Zeilennummern in Milestone 6
- Test Map in Milestone 7
- Recent Commit Context in Milestone 8
- tiefere Sprachdaten in Milestone 9

Milestone 3 baut also das Fundament. Die bestehende Ausgabe muss währenddessen funktionsfähig bleiben.

---

## Grundsatzentscheidung

Die Export-Pipeline soll künftig grob so aussehen:

~~~text
Scanner / Git / Config / Analyzer
        ↓
RepositoryExport Modell
        ↓
Renderer
        ↓
Markdown / XML / spätere Formate
~~~

In Milestone 3 wird vor allem der mittlere Teil eingeführt:

~~~text
RepositoryExport Modell
~~~

Die vollständige Markdown-Migration ist erst Milestone 4. XML ist erst Milestone 5.

---

## Nicht-Ziele von Milestone 3

Milestone 3 soll bewusst nicht zu groß werden.

Nicht Teil dieses Meilensteins:

- kein vollständiger MarkdownRenderer-Umbau
- kein XMLRenderer
- kein `--format xml`
- keine optionalen Zeilennummern
- keine Test Map
- kein Recent Commit Context
- keine tiefe JS/TS/Java/C/C++/C# Analyse
- kein Entfernen des RepoContext-Legacy-Alias
- kein Brechen bestehender CLI-Kommandos
- keine neue Ausführungslogik für Projektcode
- kein Compiler-, Build-Tool- oder Parser-Zwang

---

## Erwartetes Ergebnis

Nach Milestone 3 gibt es ein internes strukturiertes Modell, das die wichtigsten Exportdaten enthält.

Mindestens enthalten sein sollen:

- Repository-Metadaten
- Konfigurationszusammenfassung
- Export-Statistiken
- Sprachstatistiken
- File Summary
- Repository Tree
- exportierte Dateien mit Metadaten und Inhalt
- übersprungene Dateien
- gekürzte Dateien
- Warnungen
- vorhandene Analysebereiche als strukturierte Platzhalter oder Reports

Die bestehenden Exporte sollen weiterhin laufen:

- `repodossier full`
- `repodossier export-ai`
- `repodossier export-docs`
- `repodossier changed`
- `repocontext full`
- `repocontext export-ai`
- `repocontext export-docs`
- `repocontext changed`

---

# 3.1 Bestandsaufnahme und Schnittstellen festlegen

## Ziel

Vor dem Umbau muss klar sein, wo aktuell Markdown-Text erzeugt wird und welche Daten dabei entstehen.

## 3.1.a Export-Flüsse identifizieren

Untersuche die bestehenden Exportpfade für:

- Full Export
- AI Export
- Docs Export
- Changed Export

Zu prüfen sind insbesondere Dateien wie:

- `src/repodossier/cli.py`
- `src/repodossier/output_writer.py`
- `src/repodossier/scanner.py`
- `src/repodossier/models.py`
- `src/repodossier/schema.py`
- `src/repodossier/dependencies.py`
- `src/repodossier/secrets.py`
- `src/repodossier/import_graph.py`
- `src/repodossier/ranking.py`
- weitere vorhandene Export- oder Helper-Dateien

Ergebnis:

- Liste der Stellen, an denen aktuell Exportdaten entstehen
- Liste der Stellen, an denen aktuell Markdown/Text formatiert wird
- Entscheidung, wo das neue Modell aufgebaut werden soll

Akzeptanz:

- Es ist nachvollziehbar, welche Funktionen Daten sammeln.
- Es ist nachvollziehbar, welche Funktionen Text rendern.
- Die spätere Trennung zwischen Sammeln und Rendern ist vorbereitet.

---

## 3.1.b Minimalen Umbaupunkt bestimmen

Bestimme einen risikoarmen Einstiegspunkt.

Bevorzugtes Vorgehen:

- keine große Komplettmigration in einem Schritt
- erst Modell parallel aufbauen
- bestehende Ausgabe weiterverwenden
- danach schrittweise Daten aus dem Modell beziehen

Akzeptanz:

- Bestehende CLI-Ausgabe bleibt während des Umbaus funktionsfähig.
- Der erste Modellaufbau kann getestet werden, ohne alle Renderer umzuschreiben.
- Es gibt keine unnötige große Änderung an CLI oder Nutzeroberfläche.

---

## 3.1.c Kompatibilitätsgrenzen dokumentieren

Festlegen, was in Milestone 3 stabil bleiben muss:

- CLI-Kommandos
- Dateinamen der Exporte
- Exit Codes
- Standardausgabe
- bisherige Markdown-Struktur, soweit möglich
- RepoContext-Alias
- Tests aus Milestone 1 und 2

Akzeptanz:

- Keine bestehende öffentliche Funktion wird ohne Not entfernt.
- Alte Tests bleiben gültig oder werden nur angepasst, wenn die Änderung sachlich nötig ist.
- Neue Modelltests kommen zusätzlich hinzu.

---

# 3.2 Neues Modul `export_model.py` einführen

## Ziel

Ein zentrales Modul enthält die Datenklassen für den strukturierten Export.

## 3.2.a Datei `src/repodossier/export_model.py` anlegen

Neue Datei:

- `src/repodossier/export_model.py`

Dieses Modul soll reine Datenstrukturen enthalten.

Erlaubt:

- `dataclasses`
- einfache Helper für sichere Defaults
- Typdefinitionen
- kleine Normalisierungsfunktionen, falls nötig

Nicht erlaubt:

- Datei-Scanning
- Git-Aufrufe
- Rendering
- Markdown-Erzeugung
- XML-Erzeugung
- CLI-Parsing
- Analyzer-Ausführung

Akzeptanz:

- Das Modul kann isoliert importiert werden.
- Das Modul hat keine schweren Seiteneffekte.
- Es ist testbar ohne Repository auf der Festplatte.

---

## 3.2.b Basismodell `RepositoryExport` definieren

Einführen einer zentralen Datenklasse:

~~~python
@dataclass
class RepositoryExport:
    metadata: RepositoryMetadata
    configuration: ExportConfigurationSummary
    summary: ExportSummary
    files: list[FileEntry]
    tree: list[FileTreeEntry]
    omitted_files: list[OmittedFile]
    truncated_files: list[TruncatedFile]
    warnings: list[ExportWarning]
    reports: ExportReports
~~~

Die genaue Implementierung darf abweichen, aber die Verantwortlichkeiten sollen erhalten bleiben.

Akzeptanz:

- Ein vollständiger Export kann als ein Objekt repräsentiert werden.
- Renderer können später nur dieses Objekt erhalten.
- Kein Renderer muss später Scanner-, Git- oder Analyzer-Details kennen.

---

## 3.2.c `RepositoryMetadata` definieren

Das Modell soll Repository-Metadaten enthalten:

- root path
- root name
- git branch
- git commit
- git dirty status, falls verfügbar
- command/mode
- RepoDossier-Version, falls verfügbar
- generated timestamp optional und deterministisch handhabbar

Wichtig:

- Timestamp nur aufnehmen, wenn Tests dadurch nicht instabil werden.
- Falls Timestamp genutzt wird, muss er injizierbar oder normalisierbar sein.

Akzeptanz:

- Full/AI/Docs/Changed können ihren Modus im Modell abbilden.
- Git-Informationen fehlen sauber, wenn kein Git-Repo vorhanden ist.
- Tests bleiben deterministisch.

---

## 3.2.d `ExportConfigurationSummary` definieren

Das Modell soll die wirksame Konfiguration beschreiben:

- config active yes/no
- config path
- include paths
- include globs
- exclude paths
- exclude globs
- limits
- split settings
- relevante Export-Flags
- optional: line number setting vorbereitet, aber noch nicht aktiv

Akzeptanz:

- Konfigurationsdaten sind strukturiert verfügbar.
- Include/Exclude/Limits sind nicht nur als Textabschnitt vorhanden.
- Spätere XML-Ausgabe kann daraus direkt Elemente erzeugen.

---

## 3.2.e `ExportSummary` definieren

Statistikmodell für den Export:

- total tracked files
- scanned files
- exported text files
- skipped binary files
- errored files
- total lines
- estimated tokens
- file type statistics
- language statistics
- total bytes optional
- truncated count
- warning count

Akzeptanz:

- Bisherige Repository Statistics lassen sich aus dem Modell erzeugen.
- Sprachstatistiken aus Milestone 2 können übernommen werden.
- Fehlende Werte haben sichere Defaults.

---

# 3.3 Dateimodelle einführen

## Ziel

Dateien sollen einheitlich und strukturiert beschrieben werden.

## 3.3.a `FileEntry` definieren

Jede exportierte Datei soll mindestens enthalten:

- path
- language
- size bytes
- line count
- token estimate
- binary/text status
- skipped status
- truncated status
- content included yes/no
- content
- masked content, falls Secret Detection aktiv war
- reason, falls Datei nicht vollständig exportiert wurde

Akzeptanz:

- Source Export kann später aus `FileEntry` gerendert werden.
- XML kann später Inhalte und Metadaten sauber trennen.
- Secret Masking bleibt modellierbar.

---

## 3.3.b `OmittedFile` definieren

Übersprungene Dateien sollen strukturiert erfasst werden:

- path
- reason
- detected type, falls bekannt
- size bytes optional
- matched rule optional
- binary yes/no optional

Mögliche Gründe:

- binary
- excluded
- too large
- unreadable
- ignored
- unsupported
- outside limits

Akzeptanz:

- Omitted Files können später in Markdown und XML identisch aus dem Modell gerendert werden.
- Es gibt keine reine Freitext-Sammlung ohne strukturierte Gründe.

---

## 3.3.c `TruncatedFile` definieren

Gekürzte Dateien sollen strukturiert erfasst werden:

- path
- original line count optional
- exported line count optional
- original bytes optional
- exported bytes optional
- reason
- limit name optional

Akzeptanz:

- Truncation wird sichtbar.
- Spätere Renderer können Truncation deutlich markieren.
- Tests können gezielt prüfen, ob Limits im Modell auftauchen.

---

## 3.3.d `FileTreeEntry` definieren

Repository Tree soll modellierbar sein:

- path
- name
- type: file/directory
- depth
- children optional oder flache sortierte Liste
- language optional
- omitted/skipped optional

Empfehlung:

- Für Milestone 3 reicht eine deterministische flache Liste mit `depth`.
- Eine verschachtelte Baumstruktur kann später ergänzt werden.

Akzeptanz:

- Repository Tree kann aus dem Modell gerendert werden.
- Sortierung ist deterministisch.
- Exclude-Regeln werden respektiert.

---

# 3.4 Report-Modelle für Analysebereiche vorbereiten

## Ziel

Vorhandene Analysebereiche sollen im Modell einen festen Platz bekommen, ohne dass Milestone 3 alle Analyzer neu schreiben muss.

## 3.4.a `ExportReports` definieren

Zentrale Sammelstruktur:

- dependencies
- database_schema
- secret_detection
- symbol_index
- import_graph
- call_graph
- test_map, optional leer für später
- recent_commits, optional leer für später

Akzeptanz:

- Alle Analysebereiche haben einen festen Platz.
- Spätere Milestones müssen das Modell nicht erneut grundsätzlich umbauen.
- Leere Reports sind erlaubt und sicher renderbar.

---

## 3.4.b `DependencyReport` modellieren

Struktur für Abhängigkeiten:

- detected manifests
- dependency entries
- package/ecosystem optional
- version optional
- source file/path
- warnings optional

Akzeptanz:

- Bestehender Dependencies-Abschnitt kann später aus dem Modell entstehen.
- Fehlende Dependency-Daten führen nicht zu Crashes.

---

## 3.4.c `DatabaseSchemaReport` modellieren

Struktur für Datenbankschema:

- schema files
- tables
- columns
- indexes optional
- relationships optional
- warnings optional

Akzeptanz:

- Bestehender Database-Schema-Abschnitt kann später aus dem Modell entstehen.
- Kein Zwang zu perfekter DB-Analyse in diesem Milestone.

---

## 3.4.d `SecretDetectionSummary` modellieren

Struktur für Secret Detection:

- scanned files count
- findings count
- masked files count
- findings summary
- path
- finding type
- severity optional
- line optional
- masked yes/no

Wichtig:

- Keine echten Secrets im Modell speichern, wenn sie bereits maskiert werden müssen.
- Renderer dürfen später keine unmaskierten Secrets ausgeben.

Akzeptanz:

- Secret-Masking bleibt sicher.
- Tests prüfen, dass keine offensichtlichen Secrets über das Modell leaken.
- Findings sind strukturiert, nicht nur Freitext.

---

## 3.4.e `SymbolIndexReport` vorbereiten

Struktur für Symbole:

- symbol name
- kind
- path
- language
- line optional
- parent optional
- signature optional
- export/public optional

Akzeptanz:

- Bestehende Symbolinformationen können übernommen werden.
- Neue Sprachen aus späteren Milestones können ohne Modellbruch ergänzt werden.

---

## 3.4.f `ImportGraphReport` vorbereiten

Struktur für Import-/Include-Beziehungen:

- source path
- target path optional
- imported name/module
- relationship type
- local/external/unresolved
- language
- reason optional

Akzeptanz:

- Bestehender Import Graph kann später aus dem Modell gerendert werden.
- C/C++ Includes und JS/TS Imports passen später in dieselbe Struktur.

---

## 3.4.g `CallGraphReport` vorbereiten

Struktur für Call-Graph-Beziehungen:

- caller
- callee
- source path
- target path optional
- line optional
- confidence
- internal/external/unresolved/ambiguous
- language

Akzeptanz:

- Bestehender Call Graph kann später modelliert werden.
- Konservative spätere Analysen können Unsicherheit ausdrücken.

---

## 3.4.h Platzhalter für `TestMapReport` und `RecentCommitReport`

Auch wenn diese Features erst später kommen, soll das Modell vorbereitet werden.

`TestMapReport`:

- mappings
- source file
- test file
- reason
- confidence optional

`RecentCommitReport`:

- commits
- hash
- short hash
- message
- author/date optional
- changed files
- summary optional
- patch optional

Akzeptanz:

- Milestone 7 und 8 können auf vorhandene Modellplätze aufbauen.
- In Milestone 3 bleiben diese Reports standardmäßig leer.
- Renderer können leere Reports später einfach auslassen.

---

# 3.5 Modell-Builder einführen

## Ziel

Daten sollen gesammelt und in `RepositoryExport` überführt werden.

## 3.5.a Datei für Builder festlegen

Mögliche neue Datei:

- `src/repodossier/export_builder.py`

Alternativ kann der Builder zunächst in einem bestehenden Modul entstehen, falls das weniger invasiv ist. Langfristig ist ein eigenes Modul vorzuziehen.

Akzeptanz:

- Es gibt eine zentrale Funktion oder Klasse, die das Export-Modell baut.
- Die Sammellogik liegt nicht in Renderern.
- Das Modell lässt sich in Tests künstlich oder über Fixture-Repos erzeugen.

---

## 3.5.b Zentrale Builder-API definieren

Mögliche API:

~~~python
def build_repository_export(
    root: Path,
    *,
    mode: str,
    config: Config,
    scan_result: ScanResult | None = None,
    include_content: bool = True,
) -> RepositoryExport:
    ...
~~~

Die echte Signatur darf abweichen, aber sie soll klar trennen:

- Eingaben
- Sammeln von Daten
- Ausgabe als Modell

Akzeptanz:

- CLI oder bestehende Exportfunktionen können den Builder aufrufen.
- Der Builder gibt ein `RepositoryExport` zurück.
- Der Builder rendert keinen Markdown-Text.

---

## 3.5.c Minimalen Full-Export-Builder implementieren

Für den ersten Schritt soll mindestens der Full-Modus modelliert werden:

- Metadata
- Configuration
- Summary
- File Summary
- Repository Tree
- FileEntry-Liste
- Warnings

Akzeptanz:

- Ein Full-Export-Modell kann aus einem Testrepository gebaut werden.
- Die wichtigsten Zahlen stimmen mit bestehenden Exportwerten überein.
- Existing Full Export bleibt weiterhin nutzbar.

---

## 3.5.d AI-/Docs-/Changed-Modus vorbereiten

In Milestone 3 müssen nicht alle Modi vollständig neu gerendert werden. Aber das Modell soll ihren Modus kennen.

Zu modellieren:

- mode = `full`
- mode = `ai`
- mode = `docs`
- mode = `changed`

Akzeptanz:

- `RepositoryExport.metadata.mode` oder vergleichbares Feld unterscheidet die Modi.
- Tests können Modelle für alle Modi erzeugen.
- Noch nicht migrierte Details dürfen als leerer Report oder strukturierte Warnung erscheinen.

---

## 3.5.e Content-Inclusion-Regeln modellieren

Unterschiedliche Modi exportieren unterschiedliche Inhalte.

Beispiele:

- Full: vollständiger Source Export, soweit Limits es erlauben
- AI: kompakter, ggf. nur wichtige Dateien
- Docs: nur Dokumentation
- Changed: geänderte Dateien und Diff-Kontext

In Milestone 3 soll mindestens vorbereitet werden:

- `FileEntry.content_included`
- `FileEntry.content`
- `FileEntry.omitted_reason`
- `FileEntry.truncated`

Akzeptanz:

- Renderer können später erkennen, ob Inhalt ausgegeben werden darf.
- Keine Logik versteckt sich ausschließlich in Markdown-Strings.

---

# 3.6 Bestehende Daten in das Modell übernehmen

## Ziel

Das Modell soll nicht leer bleiben, sondern reale bestehende Exportdaten aufnehmen.

## 3.6.a Repository-Metadaten übernehmen

Übernehmen aus bestehender Git-/Projektlogik:

- root name
- root path
- branch
- commit
- dirty status, falls vorhanden

Akzeptanz:

- In einem Git-Repo werden Branch und Commit erkannt.
- Außerhalb von Git gibt es keinen Crash.
- Fehlende Git-Daten werden sauber als `None`, leer oder `unknown` modelliert.

---

## 3.6.b Konfigurationsdaten übernehmen

Übernehmen:

- aktive Config ja/nein
- Config-Pfad
- Include/Exclude-Regeln
- Limits
- Split-Konfiguration, falls vorhanden

Akzeptanz:

- Tests prüfen Config aktiv und Config nicht aktiv.
- Include/Exclude/Limits erscheinen im Modell.
- Keine Config-Information wird nur als gerenderter Text gespeichert.

---

## 3.6.c Datei- und Sprachdaten übernehmen

Übernehmen:

- Pfad
- erkannte Sprache aus Milestone 2
- Größe
- Zeilenanzahl
- Token-Schätzung
- Text/Binary
- skipped/truncated

Akzeptanz:

- Neue Sprachen aus Milestone 2 erscheinen im Modell.
- Existing language wrappers bleiben kompatibel.
- File Summary kann vollständig aus Modellfeldern erzeugt werden.

---

## 3.6.d Repository Tree übernehmen

Bestehende Tree-Logik soll strukturierte Einträge liefern.

Akzeptanz:

- Sortierung stabil.
- Verzeichnistiefe korrekt.
- Ausgeschlossene Dateien tauchen nicht unerwartet auf.
- Tests mit kleinem Fixture-Repo sind deterministisch.

---

## 3.6.e Warnings übernehmen

Warnungen sollen nicht mehr nur als Textliste existieren.

Struktur:

- code optional
- message
- path optional
- severity optional
- source optional

Akzeptanz:

- Bestehende Warnungen sind im Modell sichtbar.
- Renderer können später Warnungen einheitlich ausgeben.
- Tests können gezielt nach Warning-Codes oder Messages suchen.

---

# 3.7 Kompatibilitätsbrücke zur bestehenden Markdown-Ausgabe

## Ziel

Milestone 3 soll das Modell einführen, ohne die komplette Markdown-Ausgabe schon umzubauen.

## 3.7.a Bestehenden Export nicht hart ersetzen

Die vorhandene Ausgabe soll zunächst stabil bleiben.

Erlaubte Strategie:

- Modell parallel bauen
- bestehende Rendering-Funktionen weiterverwenden
- punktuell Daten aus Modell übernehmen, wo risikoarm
- keine komplette MarkdownRenderer-Migration in Milestone 3

Akzeptanz:

- Bisherige Snapshot- oder Regressionstests bleiben grün.
- Nutzer sieht keine unnötigen Ausgabeabbrüche.
- Die eigentliche Renderer-Migration bleibt sauber Milestone 4.

---

## 3.7.b Optionalen internen Debug-Zugang vermeiden oder testintern halten

Kein öffentliches CLI-Flag für unfertige Modell-Dumps einführen, wenn nicht nötig.

Falls für Tests hilfreich:

- interne Testfunktion
- kein dokumentiertes Nutzerfeature
- kein instabiles Ausgabeformat als öffentliche API

Akzeptanz:

- Kein versehentliches neues öffentliches Format.
- Tests können das Modell trotzdem prüfen.
- CLI bleibt übersichtlich.

---

## 3.7.c Modell-zu-Legacy-Helfer nur bei Bedarf

Falls bestehende Funktionen bestimmte Datenstrukturen erwarten, darf es Adapter geben.

Regeln:

- Adapter sind klein.
- Adapter sind klar benannt.
- Adapter enthalten keine neue Analyse.
- Adapter sollen später in Milestone 4 entfernt oder reduziert werden können.

Akzeptanz:

- Es entsteht keine zweite dauerhafte Exportlogik.
- Der Übergang bleibt nachvollziehbar.

---

# 3.8 Tests für das Export-Modell

## Ziel

Das neue Modell muss unabhängig von Markdown-Formatierung testbar sein.

## 3.8.a Unit-Tests für Datenklassen

Neue Tests, z. B.:

- `tests/test_export_model.py`

Testfälle:

- leeres minimales Modell
- Modell mit einer Datei
- Modell mit übersprungener Datei
- Modell mit gekürzter Datei
- Modell mit Warnung
- Modell mit leeren Reports

Akzeptanz:

- Defaults funktionieren.
- Listen teilen keine mutable Defaults.
- Modell ist einfach instanziierbar.
- `dataclasses.asdict` oder vergleichbare Serialisierung funktioniert, falls genutzt.

---

## 3.8.b Builder-Tests mit minimalem Fixture-Repo

Neue Tests, z. B.:

- `tests/test_export_builder.py`

Fixture enthält:

- eine Python-Datei
- eine Markdown-Datei
- eine JSON-Datei
- optional eine Datei aus Milestone 2, z. B. TypeScript oder C#
- optional eine ignorierte/binäre Datei

Akzeptanz:

- Builder erzeugt `RepositoryExport`.
- Dateien erscheinen mit korrektem Pfad.
- Sprache wird korrekt übernommen.
- Zeilenanzahl und Größe sind plausibel.
- Summary stimmt.

---

## 3.8.c Config-Tests

Testfälle:

- ohne Config
- mit Include-Regel
- mit Exclude-Regel
- mit Limit
- mit Split-Einstellung, falls vorhanden

Akzeptanz:

- Config Summary im Modell enthält die erwarteten Werte.
- Excluded Files werden nicht falsch als exportiert gezählt.
- Limits sind sichtbar.

---

## 3.8.d Git-Metadaten-Tests

Testfälle:

- Fixture-Git-Repo mit Commit
- Repo ohne Commit oder außerhalb Git, falls einfach testbar
- dirty status optional

Akzeptanz:

- Git-Daten werden korrekt modelliert, wenn vorhanden.
- Kein Crash ohne Git.
- Tests sind robust und nicht abhängig vom echten Arbeitsverzeichnis.

---

## 3.8.e Secret-Masking-Tests

Testfälle:

- Datei mit erkennbarem Secret
- Secret wird maskiert
- Modell enthält keine unmaskierte sensible Zeichenfolge, wenn Masking greifen soll
- Summary zeigt Finding

Akzeptanz:

- Sicherheitsverhalten regressiert nicht.
- Modell wird nicht zum Secret-Leak.

---

## 3.8.f Regressionstests für bestehende Exporte

Bestehende Exporttests müssen grün bleiben.

Prüfen:

- Full Export wird erzeugt.
- AI Export wird erzeugt.
- Docs Export wird erzeugt.
- Changed Export wird erzeugt.
- Beide CLIs funktionieren weiterhin:
  - `repodossier`
  - `repocontext`

Akzeptanz:

- Keine bestehende Hauptfunktion bricht.
- Neue Tests ergänzen bestehende Tests statt sie unnötig zu ersetzen.

---

# 3.9 Determinismus und Sortierung

## Ziel

Das Export-Modell soll stabile Ausgaben ermöglichen.

## 3.9.a Stabile Sortierung für Dateien

Festlegen:

- Pfade sortiert nach normalisierter POSIX-Darstellung
- Verzeichnisse und Dateien konsistent sortiert
- keine zufällige Set-Reihenfolge

Akzeptanz:

- Wiederholte Builds desselben Fixture-Repos ergeben gleiche Reihenfolge.
- Tests prüfen mindestens eine stabile Reihenfolge.

---

## 3.9.b Stabile Sortierung für Reports

Für alle Listen im Modell:

- dependencies
- symbols
- imports
- calls
- warnings
- omitted files
- truncated files

Akzeptanz:

- Keine nondeterministischen Testfehler.
- Spätere Renderer erhalten stabile Daten.

---

## 3.9.c Zeitabhängige Werte kontrollieren

Falls ein Timestamp im Modell existiert:

- injizierbar machen
- in Tests fixieren
- oder in Milestone 3 weglassen

Akzeptanz:

- Snapshot-Tests werden nicht durch aktuelle Uhrzeit instabil.
- Export-Modell bleibt reproduzierbar.

---

# 3.10 Dokumentation aktualisieren

## Ziel

Die Architekturänderung soll nachvollziehbar sein.

## 3.10.a Architektur-Doku ergänzen

Geeignete Datei aktualisieren, z. B.:

- `architecture.md`
- `planning/spec.md`
- README nur kurz, falls relevant

Beschreiben:

- Scanner/Analyzer sammeln Daten.
- `RepositoryExport` ist internes Modell.
- Renderer sollen nur rendern.
- MarkdownRenderer folgt in Milestone 4.
- XMLRenderer folgt in Milestone 5.

Akzeptanz:

- Neue Architektur ist für spätere Arbeit verständlich.
- Doku verspricht kein fertiges XML in Milestone 3.
- RepoContext Legacy-Alias wird nicht falsch entfernt.

---

## 3.10.b Entwicklerhinweise ergänzen

Kurz dokumentieren:

- Wo liegen die Modellklassen?
- Wo liegt der Builder?
- Welche Regeln gelten für Renderer?
- Welche neuen Tests prüfen das Modell?

Akzeptanz:

- Ein späterer Entwickler weiß, wo Milestone 4 ansetzen muss.
- Keine überlange Nutzer-README, wenn es nur interne Architektur betrifft.

---

# 3.11 Abschlussprüfung

## Ziel

Am Ende muss nachweisbar sein, dass Milestone 3 wirklich umgesetzt ist.

## 3.11.a Relevante Tests ausführen

Mindestens:

~~~bash
python3 -m pytest --color=yes
~~~

Zusätzlich, falls im Projekt vorhanden und sinnvoll:

~~~bash
python3 -m build
python3 -m twine check dist/*
~~~

Akzeptanz:

- Testsuite ist grün.
- Build bleibt funktionsfähig, falls Build-Check Teil des aktuellen Release-Prozesses ist.

---

## 3.11.b CLI-Smoke-Checks ausführen

Mindestens prüfen:

~~~bash
repodossier --help
repocontext --help
repodossier full --help
repodossier export-ai --help
repodossier export-docs --help
repodossier changed --help
~~~

Falls sinnvoll mit kleinem Fixture oder Projektlauf:

~~~bash
repodossier full
repodossier export-ai
repodossier export-docs
repodossier changed
~~~

Akzeptanz:

- CLI startet.
- Hauptkommandos existieren.
- Keine neuen Importfehler.
- Legacy-Alias funktioniert.

---

## 3.11.c Modell-spezifische Abschlussprüfung

Prüfen:

- `RepositoryExport` existiert.
- `RepositoryMetadata` existiert.
- `ExportConfigurationSummary` existiert.
- `ExportSummary` existiert.
- `FileEntry` existiert.
- `FileTreeEntry` existiert.
- `ExportReports` existiert.
- Builder erzeugt ein Modell.
- Bestehende Exporte bleiben nutzbar.

Akzeptanz:

- Milestone 3 ist nicht nur eine leere Datei mit Dataclasses.
- Reale Exportdaten landen im Modell.
- Es gibt Tests, die genau das absichern.

---

# Definition of Done für Milestone 3

Milestone 3 gilt als abgeschlossen, wenn alle folgenden Punkte erfüllt sind:

1. `src/repodossier/export_model.py` existiert oder eine gleichwertige zentrale Modellstruktur wurde eingeführt.
2. Es gibt ein zentrales Modell für Repository-Exporte.
3. Das Modell enthält Repository-Metadaten.
4. Das Modell enthält Konfigurationsinformationen.
5. Das Modell enthält Export-Statistiken.
6. Das Modell enthält Sprachstatistiken.
7. Das Modell enthält File Summary Daten.
8. Das Modell enthält Repository Tree Daten.
9. Das Modell enthält exportierte Dateien als strukturierte `FileEntry`-ähnliche Objekte.
10. Das Modell enthält übersprungene Dateien strukturiert.
11. Das Modell enthält gekürzte Dateien strukturiert.
12. Das Modell enthält Warnungen strukturiert.
13. Das Modell hat vorbereitete Report-Bereiche für Dependencies.
14. Das Modell hat vorbereitete Report-Bereiche für Database Schema.
15. Das Modell hat vorbereitete Report-Bereiche für Secret Detection.
16. Das Modell hat vorbereitete Report-Bereiche für Symbol Index.
17. Das Modell hat vorbereitete Report-Bereiche für Import Graph.
18. Das Modell hat vorbereitete Report-Bereiche für Call Graph.
19. Das Modell hat vorbereitete leere Bereiche für Test Map und Recent Commits.
20. Ein Builder oder eine zentrale Builder-Funktion erzeugt ein Modell aus realen Projektdaten.
21. Renderer enthalten keine neue Scanner-, Git- oder Analyzer-Logik.
22. Bestehende Markdown-Ausgaben bleiben funktionsfähig.
23. `repodossier` CLI bleibt kompatibel.
24. `repocontext` Legacy-Alias bleibt kompatibel.
25. Neue Unit-Tests für Modellklassen existieren.
26. Neue Builder-Tests existieren.
27. Config-Daten werden im Modell getestet.
28. Language Detection aus Milestone 2 landet im Modell.
29. Secret-Masking regressiert nicht.
30. Sortierung ist deterministisch.
31. Zeitabhängige Werte machen Tests nicht instabil.
32. Architektur-/Entwicklerdoku ist aktualisiert.
33. Die komplette Testsuite ist grün.

---

# Empfohlene Commit-Aufteilung

Falls der Meilenstein in mehreren Commits umgesetzt wird:

## Commit 1

Thema:

- Export-Modell-Datenklassen

Inhalt:

- `export_model.py`
- Unit-Tests für Defaults und einfache Modelle

## Commit 2

Thema:

- Export Builder Grundstruktur

Inhalt:

- `export_builder.py`
- RepositoryMetadata
- ExportConfigurationSummary
- ExportSummary
- Builder-Tests mit Fixture-Repo

## Commit 3

Thema:

- FileEntry, Tree, Omitted/Truncated/Warnungen

Inhalt:

- strukturierte Dateidaten
- Tree-Daten
- Warning-Daten
- Tests für Dateien, Tree, Limits

## Commit 4

Thema:

- Reports und bestehende Analyseintegration

Inhalt:

- ExportReports
- DependencyReport
- DatabaseSchemaReport
- SecretDetectionSummary
- Symbol/Import/Call Reports
- Tests für leere und einfache Reports

## Commit 5

Thema:

- Kompatibilität und Doku

Inhalt:

- bestehende Exporte bleiben grün
- Doku zur neuen Architektur
- Abschlussprüfung

---

# Risiko-Check

## Hauptrisiko 1: Zu großer Umbau

Gefahr:

- Full/AI/Docs/Changed werden gleichzeitig komplett neu geschrieben.

Gegenmaßnahme:

- Milestone 3 baut das Modell.
- Vollständige MarkdownRenderer-Migration bleibt Milestone 4.

---

## Hauptrisiko 2: Doppelte dauerhafte Exportlogik

Gefahr:

- Alte Markdown-Logik und neues Modell entwickeln sich auseinander.

Gegenmaßnahme:

- Adapter nur übergangsweise nutzen.
- In Doku klar festhalten: Modell ist Zielarchitektur.
- Milestone 4 muss Markdown aus Modell rendern.

---

## Hauptrisiko 3: Modell speichert zu viel Freitext

Gefahr:

- XMLRenderer kann später keine echten XML-Elemente erzeugen.

Gegenmaßnahme:

- Daten strukturiert modellieren.
- Freitext nur für Messages, Reasons und Content nutzen.
- Pfade, Zahlen, Typen und Beziehungen als Felder speichern.

---

## Hauptrisiko 4: Secrets landen unmaskiert im Modell

Gefahr:

- Renderer geben später versehentlich Secrets aus.

Gegenmaßnahme:

- Secret Masking vor oder beim Befüllen von `FileEntry.content`.
- Tests mit Beispielsecret.
- Keine unmaskierten Findings speichern.

---

## Hauptrisiko 5: Tests werden nondeterministisch

Gefahr:

- Timestamps, Git-Daten oder Set-Reihenfolgen erzeugen flaky Tests.

Gegenmaßnahme:

- Sortierung erzwingen.
- Zeitwerte injizierbar machen oder weglassen.
- Git-Fixtures isolieren.

---

# Kurze Umsetzungsreihenfolge

1. Bestandsaufnahme der bestehenden Exportfunktionen.
2. `export_model.py` mit zentralen Datenklassen anlegen.
3. Unit-Tests für Modellklassen schreiben.
4. `export_builder.py` oder zentrale Builder-Funktion einführen.
5. Metadata, Config und Summary befüllen.
6. FileEntry, Tree, Omitted, Truncated und Warnings befüllen.
7. Report-Platzhalter und vorhandene Analysebereiche anbinden.
8. Bestehende Exporte kompatibel halten.
9. Deterministische Sortierung absichern.
10. Tests und Doku ergänzen.
11. Abschlussprüfung durchführen.

---

# Abschlussnotiz

Milestone 3 ist ein Architektur-Fundament. Der sichtbare Nutzen für Nutzer ist kleiner als bei Milestone 2, aber dieser Schritt entscheidet, ob XML, MarkdownRenderer, Zeilennummern, Test Map und Recent Commit Context später sauber und ohne doppelte Logik umgesetzt werden können.
