# RepoDossier / RepoContext – Roadmap Next

Stand: 2026-07-01

Diese Roadmap beschreibt die nächsten sinnvollen Erweiterungen für RepoDossier in der aktuell bevorzugten Umsetzungsreihenfolge.

RepoDossier ist der aktuelle Projektname. RepoContext bleibt vorerst als Legacy-/Kompatibilitätsalias erhalten. Ziel bleibt ein sicheres, deterministisches und AI-freundliches CLI-Werkzeug für Repository-Exporte.

## Grundentscheidungen

- XML mit CDATA wird das primäre AI-/Maschinenformat.
- Markdown bleibt zunächst als Human-/Legacy-Ausgabe erhalten.
- Intern soll ein strukturiertes Export-Modell entstehen.
- XML und Markdown sollen aus demselben internen Modell gerendert werden.
- JSON/YAML sind nicht das primäre Maschinenformat.
- Analyse bleibt statisch und sicher: Projektcode wird nicht ausgeführt.
- Bestehende Kommandos und Workflows sollen möglichst kompatibel bleiben.

---

# 1. Pipx Installation Hardening

## Ziel

RepoDossier soll zuverlässig systemweit beziehungsweise benutzerweit per `pipx` installierbar sein. Die README soll den Installationsweg dokumentieren, der lokal funktioniert hat, und die Release-/Smoke-Tests sollen prüfen, dass die CLI nach pipx-Installation wirklich verfügbar ist.

## Hintergrund

Der folgende Befehl hat funktioniert:

```bash
cd ~/market_research/repo_dossier || {
  echo "Fehler: Projektverzeichnis nicht gefunden."
}

python3 -m pipx uninstall repodossier 2>/dev/null || true
python3 -m pipx install "$PWD"

export PATH="$HOME/.local/bin:$PATH"

which repodossier || true
which repocontext || true

repodossier --help
repocontext --help
```

Der folgende Ansatz soll nicht mehr als Standard empfohlen werden:

```bash
pipx install -e .
python3 -m pipx install -e .
```

Dieser hatte lokal mit folgender Meldung versagt:

```text
Cannot determine package name from spec ...
```

## Anforderungen

### 1.1 README-Installationsweg aktualisieren

Die README soll für lokale Installation aus einem Checkout den robusten Weg dokumentieren:

```bash
python3 -m pipx install "$PWD"
```

Die Anleitung soll klar zeigen:

- Projektverzeichnis betreten.
- Vorherige Installation entfernen, falls vorhanden.
- Lokal per pipx installieren.
- PATH für aktuelles Terminal setzen.
- `repodossier --help` prüfen.
- `repocontext --help` prüfen.

### 1.2 Editable-Install nur als Development-Option dokumentieren

Editable pipx-Installationen sollen höchstens als Entwickleroption genannt werden, nicht als Hauptweg.

Für eigentliche Entwicklung bleibt weiterhin möglich:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

### 1.3 pyproject.toml bereinigen

Aktuell ist der Include-Eintrag doppelt:

```toml
include = ["repodossier*", "repodossier*"]
```

Er soll bereinigt werden zu:

```toml
include = ["repodossier*"]
```

### 1.4 Packaging-Checks ergänzen

Es sollen Checks ergänzt oder dokumentiert werden:

```bash
python3 -m build
python3 -m twine check dist/*
```

Diese Checks stellen sicher, dass das Paket sauber gebaut und geprüft werden kann.

### 1.5 pipx-Smoke-Test ergänzen

Ein Smoke-Test oder Validierungsskript soll prüfen:

- lokale Installation mit `python3 -m pipx install "$PWD"`
- `repodossier --help` funktioniert
- `repocontext --help` funktioniert
- `repodossier --version` funktioniert
- `repocontext --version` funktioniert

### 1.6 validate_pipx_release.sh prüfen/erweitern

Falls `scripts/validate_pipx_release.sh` bereits existiert, soll es den robusten Installationsweg nutzen oder mindestens abdecken.

Das Skript soll nach Möglichkeit:

- temporäre pipx-Umgebung nutzen
- Paket aus lokalem Checkout installieren
- beide CLI-Kommandos prüfen
- Export-Kommandos in einem temporären Git-Repo prüfen
- Reinstallationsfall prüfen

## Tests

- README enthält `python3 -m pipx install "$PWD"`.
- README empfiehlt nicht primär `pipx install -e .`.
- `pyproject.toml` enthält keinen doppelten Include-Eintrag.
- `scripts/validate_pipx_release.sh` prüft `repodossier` und `repocontext`.
- Packaging-Build läuft erfolgreich.
- `twine check` läuft erfolgreich.

## Definition of Done

- RepoDossier kann lokal per `python3 -m pipx install "$PWD"` installiert werden.
- `repodossier --help` funktioniert.
- `repocontext --help` funktioniert.
- README ist konsistent.
- Packaging-Checks sind dokumentiert oder getestet.
- Tests sind grün.

---

# 2. Reine Language Detection für TypeScript, JavaScript, HTML, CSS und Java

## Ziel

RepoDossier soll zusätzliche Dateitypen explizit erkennen, korrekt benennen und in File Summary, Source Export, Markdown-Ausgabe und später XML-Metadaten sauber darstellen.

Dieser Schritt umfasst bewusst nur reine Erkennung und Export-Metadaten. Tiefergehende Analyse wie Symbol Extraction, Import Graph oder Call Graph folgt später.

## Warum dieser Schritt früh kommt

- Relativ klein und risikoarm.
- Verbessert sofort bestehende Dumps.
- Unabhängig vom großen Export-Modell-Umbau umsetzbar.
- Spätere Analyse kann auf korrekten Language Labels aufbauen.

## Neue Sprachen und Dateiendungen

### TypeScript

Erkennen:

- `.ts`
- `.tsx`

Mögliche Labels:

- `typescript`
- `tsx` oder `typescriptreact`

### JavaScript

Erkennen:

- `.js`
- `.jsx`
- `.mjs`
- `.cjs`

Mögliche Labels:

- `javascript`
- `jsx` oder `javascriptreact`

### HTML

Erkennen:

- `.html`
- `.htm`

Label:

- `html`

### CSS

Erkennen:

- `.css`

Label:

- `css`

### Java

Erkennen:

- `.java`

Label:

- `java`

## Anforderungen

### 2.1 Scanner erweitern

Die bestehende Language Detection soll diese Dateiendungen explizit erkennen.

Aktuell unterstützte beziehungsweise dokumentierte Typen sind unter anderem:

- Python
- Bash
- Markdown
- TOML
- YAML
- JSON
- INI
- plain text

Diese Liste soll um TypeScript, JavaScript, HTML, CSS und Java ergänzt werden.

### 2.2 File Summary erweitern

Die File Summary soll Dateien dieser Typen gruppiert und korrekt benannt anzeigen.

Beispiel:

```text
## TypeScript (3 files)
- `src/content.ts` — 120 lines, ~800 tokens

## JavaScript (2 files)
- `extension/background.js` — 90 lines, ~600 tokens

## HTML (1 file)
- `extension/popup.html` — 40 lines, ~200 tokens

## CSS (1 file)
- `extension/styles.css` — 80 lines, ~300 tokens

## Java (2 files)
- `src/main/java/com/example/App.java` — 150 lines, ~900 tokens
```

### 2.3 Source Export Code Fence Labels

Markdown Source Export soll passende Code-Fence-Labels verwenden:

```markdown
```typescript
```

```markdown
```javascript
```

```markdown
```html
```

```markdown
```css
```

```markdown
```java
```

### 2.4 AI Export berücksichtigen

Der AI Export soll diese Dateitypen mindestens als Dateien erkennen und in relevanten Übersichten korrekt benennen.

Noch nicht erforderlich:

- TypeScript-Symbolanalyse
- JavaScript-Importgraph
- Java-Callgraph
- HTML-Referenzanalyse
- CSS-Selektoranalyse

### 2.5 Config Include/Exclude respektieren

Alle neuen Dateitypen müssen bestehende Include-/Exclude-Regeln respektieren.

Beispiele:

```yaml
include:
  paths:
    - extension

exclude:
  paths:
    - extension/dist
```

## Tests

### 2.6 Language Detection Tests

Testfälle:

- `.ts` wird TypeScript.
- `.tsx` wird TypeScript/TSX.
- `.js` wird JavaScript.
- `.jsx` wird JavaScript/JSX.
- `.mjs` wird JavaScript.
- `.cjs` wird JavaScript.
- `.html` wird HTML.
- `.htm` wird HTML.
- `.css` wird CSS.
- `.java` wird Java.

### 2.7 File Summary Tests

- File Summary gruppiert neue Sprachen korrekt.
- Anzahl der Dateien stimmt.
- Sortierung bleibt deterministisch.

### 2.8 Source Export Tests

- Full Export enthält passende Code-Fence-Labels.
- Inhalte werden korrekt exportiert.
- Secret Detection bleibt aktiv.

### 2.9 Config Tests

- Include-Regeln funktionieren mit neuen Dateitypen.
- Exclude-Regeln funktionieren mit neuen Dateitypen.
- Exclude gewinnt über Include.

## Definition of Done

- Alle fünf Sprachen werden explizit erkannt.
- File Summary zeigt sie korrekt.
- Source Export nutzt passende Codeblock-Sprachen.
- AI Export behandelt sie nicht mehr als unknown, sofern passend.
- Tests sind grün.

---

# 3. Internes strukturiertes Export-Modell

## Ziel

RepoDossier soll intern nicht mehr primär Markdown-Text zusammensetzen, sondern zuerst ein strukturiertes Export-Modell aufbauen. Dieses Modell wird anschließend von MarkdownRenderer und XMLRenderer ausgegeben.

## Warum

- XML soll vollständig strukturiert sein.
- Markdown und XML sollen nicht zwei separate Exportlogiken haben.
- Neue Features wie Test Map, Recent Commit Context und weitere Sprachdaten sollen sauber modelliert werden.
- Tests können interne Daten unabhängig vom Ausgabeformat prüfen.

## Grundidee

Statt:

```text
Exporter sammelt Daten und schreibt direkt Markdown-Text.
```

soll gelten:

```text
Exporter/Analyzer sammeln Daten -> internes Export-Modell -> Renderer erzeugt Markdown oder XML.
```

## Mögliche neue Module

```text
src/repodossier/export_model.py
src/repodossier/renderers/__init__.py
src/repodossier/renderers/markdown.py
src/repodossier/renderers/xml.py
```

## Mögliche Kernmodelle

### RepositoryExport

Enthält den gesamten Export.

Felder:

- `mode`
- `repository`
- `configuration`
- `summary`
- `file_types`
- `tree`
- `dependencies`
- `database_schema`
- `symbols`
- `import_graph`
- `call_graph`
- `test_map`
- `recent_commits`
- `files`
- `omitted_files`
- `truncated_files`
- `warnings`
- `secret_detection`

### RepositoryMetadata

Felder:

- Repository root
- Root name
- Git branch
- Git commit
- Git status summary optional

### ExportConfigurationStatus

Felder:

- Config active yes/no
- Config path optional
- Include paths
- Include globs
- Exclude paths
- Exclude globs
- Limits

### ExportSummary

Felder:

- Total tracked files
- Scanned files
- Exported text files
- Skipped binary files
- Errored files
- Total lines
- Estimated tokens

### FileEntry

Felder:

- path
- language
- size_bytes
- line_count
- estimated_tokens
- content
- is_binary
- is_text
- is_truncated
- omitted_reason
- warnings

### OmittedFileEntry

Felder:

- path
- reason
- size_bytes optional
- language optional

### WarningEntry

Felder:

- code
- message
- path optional
- severity optional

## Anforderungen

### 3.1 Bestehende Daten modellieren

Zuerst sollen bestehende Daten modelliert werden, nicht sofort große neue Features.

Bestehende Daten:

- Config Status
- AI Quick Start / Repository Summary
- Repository Statistics
- File Summary
- Repository Tree
- Dependencies
- Database Schema
- Secret Detection
- Complete Source Export
- Symbol Index
- Import Graph
- Call Graph
- Warnings

### 3.2 Full Export Modell

Full Export soll ein vollständiges RepositoryExport-Modell erzeugen.

### 3.3 AI Export Modell

AI Export soll ein kompaktes RepositoryExport-Modell erzeugen, ohne vollständigen Source Dump, aber mit Architektur-, Ranking-, Symbol-, Import- und Callgraph-Daten.

### 3.4 Docs Export Modell

Docs Export soll ein Dokumentationsmodell erzeugen, das mit dem allgemeinen Modell kompatibel ist.

### 3.5 Changed Export Modell

Changed Export soll ein Änderungsmodell erzeugen, das später ebenfalls von Markdown/XML gerendert werden kann.

### 3.6 Keine doppelten Analysepfade

Analyzer wie Dependencies, Schema, Symbols, Import Graph, Call Graph und Secret Detection sollen nicht mehrfach für verschiedene Renderer laufen müssen.

## Tests

- Export-Modell kann für ein minimales Repo erzeugt werden.
- Full Export Modell enthält erwartete Sektionen.
- AI Export Modell enthält erwartete Sektionen.
- Docs Export Modell bleibt docs-only.
- Changed Export Modell enthält geänderte Dateien und Diff-Informationen.
- Config Summary ist im Modell vorhanden.
- File Entries sind stabil sortiert.
- Warnings sind modelliert.
- Secret Detection Summary ist modelliert.

## Definition of Done

- Es gibt ein internes Export-Modell.
- Bestehende Exportdaten können in dieses Modell überführt werden.
- Renderer können auf dieses Modell zugreifen.
- Bestehende Tests sind grün oder bewusst angepasst.

---

# 4. MarkdownRenderer aus internem Modell

## Ziel

Die bisherige Markdown-/Text-Ausgabe soll aus dem neuen internen Export-Modell gerendert werden. Markdown bleibt Human-/Legacy-Ausgabe.

## Warum vor XML

- Beweist, dass das neue interne Modell die bestehende Ausgabe abbilden kann.
- Reduziert Regressionen.
- Bestehende Workflows bleiben stabil.
- Danach kann XML denselben Datenbaum nutzen.

## Anforderungen

### 4.1 MarkdownRenderer einführen

Ein MarkdownRenderer soll aus RepositoryExport Markdown erzeugen.

Mögliche API:

```python
render_markdown(export: RepositoryExport) -> str
```

Oder:

```python
MarkdownRenderer().render(export)
```

### 4.2 Full Markdown Export

`repodossier full` soll weiterhin `full.txt` erzeugen.

Inhalt bleibt möglichst stabil:

- RepoDossier Configuration
- AI Quick Start
- Repository Statistics
- File Summary
- Repository Tree
- Dependencies
- Database Schema
- Secret Detection
- Complete Source Export
- Warnings
- Import Graph
- Call Graph

### 4.3 AI Markdown Export

`repodossier export-ai` soll weiterhin `ai.txt` erzeugen.

Inhalt bleibt kompakt und AI-orientiert.

### 4.4 Docs Markdown Export

`repodossier export-docs` soll weiterhin `docs.txt` erzeugen.

Docs Export bleibt documentation-only.

### 4.5 Changed Markdown Export

`repodossier changed` soll weiterhin `changed.txt` erzeugen.

Changed Export bleibt review-fokussiert:

- Changed Export header
- Repository path
- Compare Mode
- Changed Files Summary
- Changed Files overview
- Git Diff
- Changed File Contents
- Deleted Files
- Binary / Skipped Files

### 4.6 Keine Analyse im Renderer

MarkdownRenderer darf nicht scannen, Git lesen oder Analyzer ausführen.

Er rendert nur das Modell.

## Tests

- Full Markdown Export bleibt lesbar.
- AI Markdown Export bleibt kompakt.
- Docs Markdown Export bleibt docs-only.
- Changed Markdown Export bleibt korrekt.
- Bestehende README-Tests bleiben grün oder werden bewusst aktualisiert.
- MarkdownRenderer nutzt Modellwerte.
- Keine doppelte Exportlogik.

## Definition of Done

- Markdown-Ausgaben werden aus dem internen Modell erzeugt.
- Bestehende CLI-Kommandos funktionieren.
- Bestehende Workflows bleiben kompatibel.
- Tests sind grün.

---

# 5. XMLRenderer mit vollständigem XML + CDATA

## Ziel

RepoDossier soll aus dem internen Export-Modell einen vollständig strukturierten XML-Dump erzeugen können. XML ist das primäre AI-/Maschinenformat.

## Grundentscheidung

- Der gesamte Dump ist XML.
- Keine losen Markdown-Blöcke im XML.
- Dateiinhalte werden in CDATA gekapselt.
- Sonderfall `]]>` wird korrekt behandelt.

## Mögliche CLI

```bash
repodossier full --format xml
repodossier export-ai --format xml
repodossier export-docs --format xml
repodossier changed --format xml
```

Kompatibilitätsalias optional:

```bash
repocontext full --format xml
repocontext export-ai --format xml
```

## XML-Struktur

Root:

```xml
<repodossier version="1" mode="full">
  ...
</repodossier>
```

Hauptbereiche:

- `<repository>`
- `<configuration>`
- `<summary>`
- `<file_types>`
- `<tree>`
- `<dependencies>`
- `<database_schema>`
- `<secret_detection>`
- `<symbols>`
- `<import_graph>`
- `<call_graph>`
- `<test_map>`
- `<recent_commits>`
- `<files>`
- `<omitted_files>`
- `<truncated_files>`
- `<warnings>`

## CDATA Handling

Dateiinhalte:

```xml
<content><![CDATA[
...
]]></content>
```

Sonderfall:

Wenn Inhalt `]]>` enthält, muss CDATA sicher gesplittet werden.

Beispielstrategie:

```text
]]> -> ]]]]><![CDATA[>
```

## XML für Dateien

Beispiel:

```xml
<file path="src/repodossier/cli.py" language="python" lines="500" size_bytes="12345" truncated="false">
  <content><![CDATA[
...
  ]]></content>
</file>
```

Bei gekürzten Dateien:

```xml
<file path="large.txt" language="text" truncated="true" omitted_reason="max_line_count">
  <content><![CDATA[
...
  ]]></content>
</file>
```

Bei ausgelassenen Dateien:

```xml
<omitted_file path="data.sqlite" reason="binary" size_bytes="123456" />
```

## Anforderungen

### 5.1 XMLRenderer einführen

Mögliche API:

```python
render_xml(export: RepositoryExport) -> str
```

Oder:

```python
XMLRenderer().render(export)
```

### 5.2 XML muss parsebar sein

Ausgabe muss mit Python stdlib parsebar sein:

```python
xml.etree.ElementTree.fromstring(xml_text)
```

### 5.3 XML muss deterministisch sein

Sortierung stabil halten:

- Dateien nach Pfad
- Warnings nach Pfad/Code
- Dependencies nach Typ/Name
- Graphen deterministisch

### 5.4 Full XML Export

`full --format xml` soll vollständigen Kontext strukturiert ausgeben.

### 5.5 AI XML Export

`export-ai --format xml` soll kompakten AI-Kontext strukturiert ausgeben.

### 5.6 Docs/Changed XML optional in erster Phase

Falls zu groß, zuerst full und ai. Danach docs und changed.

## Tests

- XMLRenderer erzeugt parsebares XML.
- Root-Element enthält Version und Mode.
- Repository-Metadaten erscheinen.
- Config erscheint.
- Summary erscheint.
- Tree erscheint strukturiert.
- Files erscheinen mit Attributen.
- Inhalte stehen in CDATA.
- `]]>` wird korrekt behandelt.
- Secret Masking bleibt aktiv.
- Full XML Export funktioniert.
- AI XML Export funktioniert.
- Markdown-Ausgabe bleibt unverändert verfügbar.

## Definition of Done

- `repodossier full --format xml` funktioniert.
- `repodossier export-ai --format xml` funktioniert.
- XML ist vollständig strukturiert.
- Dateiinhalte sind CDATA.
- XML ist parsebar.
- Tests sind grün.

---

# 6. Optionale Zeilennummern

## Ziel

Dateiinhalte können optional mit Zeilennummern exportiert werden. Das hilft der AI bei präzisen Verweisen, Patch-Anweisungen und Fehlersuche.

## Mögliche CLI

```bash
repodossier full --line-numbers
repodossier export-ai --line-numbers
repodossier export-docs --line-numbers
repodossier changed --line-numbers
```

Legacy-Alias optional:

```bash
repocontext full --line-numbers
repocontext export-ai --line-numbers
```

## Warum nach den Renderern

Zeilennummern sind ein Ausgabe-/Rendering-Thema. Sie müssen sowohl Markdown als auch XML betreffen. Nach dem Renderer-Umbau ist das sauberer.

## Anforderungen

### 6.1 Standard bleibt ohne Zeilennummern

Ohne Flag bleibt der Inhalt wie bisher.

### 6.2 Markdown-Ausgabe

Mögliche Form:

```text
001 | import argparse
002 |
003 | def main():
004 |     ...
```

### 6.3 XML-Ausgabe

Einfache erste Variante:

```xml
<content line_numbers="true"><![CDATA[
001 | import argparse
002 |
003 | def main():
]]></content>
```

Spätere mögliche Variante:

```xml
<lines>
  <line number="1"><![CDATA[import argparse]]></line>
  <line number="2"><![CDATA[]]></line>
</lines>
```

Empfehlung für erste Umsetzung:

- einfache Content-Variante mit Attribut `line_numbers="true"`
- keine zu große XML-Komplexität in der ersten Version

### 6.4 Changed Export

Zeilennummern sind besonders nützlich für Changed File Contents.

### 6.5 AI Export

Optional, aber nicht Standard, weil Tokenverbrauch steigt.

## Tests

- Ohne Flag keine Zeilennummern.
- Mit Flag Zeilennummern vorhanden.
- Nummerierung beginnt bei 1.
- Leere Zeilen bleiben erhalten.
- MarkdownRenderer funktioniert.
- XMLRenderer kennzeichnet line_numbers korrekt.
- Secret Masking funktioniert weiterhin.
- Truncation/Limits funktionieren weiterhin.
- Split-Exports funktionieren weiterhin.

## Definition of Done

- `--line-numbers` funktioniert für relevante Exporte.
- Default bleibt unverändert.
- Markdown und XML verhalten sich konsistent.
- Tests sind grün.

---

# 7. Test Map

## Ziel

RepoDossier soll sichtbar machen, welche Tests vermutlich zu welchen Source-Dateien gehören. Die Test Map soll AI-Code-Reviews, Debugging und Milestone-Prüfungen verbessern.

## Nutzen

- AI erkennt schneller, welche Tests nach einer Änderung relevant sind.
- Bei Patches kann gezielter geprüft werden.
- Bei Fehlermeldungen kann Source-Datei und Testdatei besser verbunden werden.
- Hilft besonders bei großen Repositories mit vielen Tests.

## Beispiel

```text
src/repodossier/config.py
- tests/test_config.py
- tests/test_config_full_export_limits.py
- tests/test_config_ai_export_filters.py
```

## Warum nach Export-Modell und XML

Test Map ist ein neues Analyse-/Modellfeature. Es soll direkt strukturiert im internen Modell landen und dann sowohl in XML als auch Markdown gerendert werden.

## Anforderungen

### 7.1 Heuristische Zuordnung

Mögliche Heuristiken:

- `tests/test_config.py` passt zu `src/repodossier/config.py`
- `tests/test_cli.py` passt zu `src/repodossier/cli.py`
- `tests/test_full_exporter.py` passt zu `src/repodossier/exporters/full.py`
- Testdateien nach Muster `test_<module>.py`
- Testdateien mit Präfix `test_<module>_...py`
- Imports in Testdateien auswerten
- Direkte Erwähnung von Modulnamen im Test optional auswerten

### 7.2 Keine Tests ausführen

Die erste Version bleibt statisch.

Nicht-Ziele:

- keine Coverage-Messung
- keine Testausführung
- keine dynamische Analyse
- keine perfekte Zuordnung versprechen

### 7.3 Exclude-Regeln respektieren

Wenn Tests ausgeschlossen sind, soll die Test Map das respektieren.

Beispiel:

```yaml
exclude:
  paths:
    - tests
```

Dann soll die Test Map leer sein oder klar anzeigen, dass keine Tests im gefilterten Export vorhanden sind.

### 7.4 XML-Ausgabe

```xml
<test_map>
  <mapping source="src/repodossier/config.py">
    <test_file path="tests/test_config.py" reason="name_match" />
    <test_file path="tests/test_config_full_export_limits.py" reason="name_prefix_match" />
  </mapping>
</test_map>
```

### 7.5 Markdown-Ausgabe

```markdown
# Test Map

src/repodossier/config.py
- tests/test_config.py
- tests/test_config_full_export_limits.py
```

## Tests

- Einfache Modul/Test-Namenszuordnung funktioniert.
- Prefix-Matches funktionieren.
- Exporter-Testdateien werden passenden Exporter-Modulen zugeordnet.
- Unpassende Tests werden nicht wild zugeordnet.
- Ergebnis ist deterministisch sortiert.
- XMLRenderer rendert Test Map.
- MarkdownRenderer rendert Test Map.
- Kein Crash bei Repos ohne tests-Ordner.
- Exclude-Regeln werden respektiert.

## Definition of Done

- Test Map existiert als eigener Modellteil.
- Test Map wird in Markdown gerendert.
- Test Map wird in XML gerendert.
- Tests sind grün.

---

# 8. Recent Commit Context

## Ziel

Die letzten Commits sollen im Export als Übersicht enthalten sein. Dadurch versteht die AI besser, was zuletzt geändert wurde und warum.

## Nutzen

Besonders hilfreich für:

- Milestone-Prüfungen
- Patch-Reviews
- Abschlussprüfungen
- Verstehen der jüngsten Entwicklungslinie
- Zusammenhang zwischen Codeänderungen und Absicht

## Warum nach Test Map

Recent Commits ist sehr nützlich, aber Git-/Diff-Handling kann größer werden. Es profitiert stark vom strukturierten Modell. Patches brauchen außerdem saubere CDATA-Behandlung in XML.

## Anforderungen

### 8.1 Full Export

Full soll enthalten:

- Recent Commits Übersicht
- Commit Hash
- Commit Message
- Author/Date optional
- betroffene Dateien
- kompletter Patch/Diff pro Commit

### 8.2 AI Export

AI soll enthalten:

- Recent Commits Übersicht
- Commit Hash kurz
- Commit Message
- Kurzbeschreibung / Summary
- betroffene Dateien
- keine vollständigen Patches

### 8.3 Warum diese Trennung

- full soll maximale Nachvollziehbarkeit liefern.
- ai soll Token sparen.
- Patches können im ai-Export sehr groß werden.
- Commit-Messages und betroffene Dateien reichen im AI Export meistens als Kontext.

### 8.4 Mögliche CLI

```bash
repodossier full --recent-commits 5
repodossier export-ai --recent-commits 10
repodossier full --no-recent-commits
repodossier export-ai --no-recent-commits
```

### 8.5 Mögliche Config

```yaml
git:
  recent_commits_full: 5
  recent_commits_ai: 10
  include_patches_in_full: true
  include_patches_in_ai: false
```

### 8.6 XML-Struktur

```xml
<recent_commits>
  <commit hash="..." short_hash="...">
    <message>...</message>
    <author>...</author>
    <date>...</date>
    <changed_files>
      <file path="..." />
    </changed_files>
    <summary>...</summary>
    <patch><![CDATA[
diff --git ...
    ]]></patch>
  </commit>
</recent_commits>
```

Im AI XML Export wird `<patch>` weggelassen.

### 8.7 Markdown Full

```markdown
# Recent Commits

## abc1234 Add XML renderer
Author: ...
Date: ...
Changed files:
- src/...
- tests/...

Patch:
```diff
...
```
```

### 8.8 Markdown AI

```markdown
## Recent Commits

- abc1234 Add XML renderer
  - Files: src/..., tests/...
  - Summary: Introduces XML renderer for structured exports.
```

## Tests

- Git-Commit-Liste wird korrekt gelesen.
- Limit wird beachtet.
- Full enthält Patch/Diff.
- AI enthält keinen vollständigen Patch.
- Betroffene Dateien werden gelistet.
- Kein Crash in Repos ohne Commits.
- Kein Crash außerhalb von Git mit sinnvoller Fehlermeldung oder leerem Abschnitt.
- XMLRenderer rendert Recent Commits strukturiert.
- MarkdownRenderer rendert Recent Commits lesbar.
- Secret Detection maskiert Secrets in Patches.
- CDATA behandelt Diff-Inhalte korrekt.

## Definition of Done

- Recent Commit Context existiert im Modell.
- Full Export enthält Patches.
- AI Export enthält nur Kurzinfos.
- Markdown und XML rendern korrekt.
- Tests sind grün.

---

# 9. Tieferer Sprachsupport: JS/TS/HTML/CSS/Java Analyse

## Ziel

RepoDossier soll die bereits erkannten zusätzlichen Sprachen tiefer analysieren, soweit das für AI-Codeverständnis sinnvoll ist.

## Warum zuletzt

- Größter und riskantester Block.
- Mehrsprachige statische Analyse ist komplex.
- Nach Export-Modell und XML können Analyseergebnisse sauber abgelegt werden.
- Reine Language Detection ist bereits vorher erledigt.

## Allgemeine Anforderungen

- Analyse bleibt statisch.
- Kein Code wird ausgeführt.
- Keine Browser-Ausführung.
- Keine JVM-Ausführung.
- Keine Node-Ausführung.
- Keine vollständige Compiler-/Typechecker-Genauigkeit versprechen.
- Ergebnisse sollen konservativ und nützlich sein.

---

## 9.1 JavaScript/TypeScript Symbol Extraction

### Ziel

JS/TS-Dateien sollen wichtige Symbole sichtbar machen.

### Erkennen

- functions
- async functions
- arrow functions mit Namen
- classes
- methods
- exported symbols
- default exports
- constants optional
- TypeScript interfaces optional
- TypeScript types optional

### Beispiele

```typescript
function run() {}
async function load() {}
const handler = () => {}
export function main() {}
export default class App {}
class Service { start() {} }
interface Config {}
type Mode = "full" | "ai";
```

### Tests

- function erkannt
- async function erkannt
- arrow function erkannt
- class erkannt
- method erkannt
- export erkannt
- default export erkannt
- interface/type optional erkannt oder bewusst ignoriert

---

## 9.2 JavaScript/TypeScript Import Graph

### Ziel

Lokale Modulbeziehungen und externe Abhängigkeiten in JS/TS sichtbar machen.

### Erkennen

- `import ... from "..."`
- `import "..."`
- `export ... from "..."`
- `require("...")`
- dynamic `import("...")` optional/konservativ

### Klassifikation

- lokale Imports
- externe Imports
- unresolved Imports

### Tests

- ES import erkannt
- side-effect import erkannt
- export-from erkannt
- require erkannt
- lokaler Import auf Datei gemappt
- externer Import separat gelistet
- unresolved Import erzeugt keinen Crash

---

## 9.3 JavaScript/TypeScript konservativer Call Graph

### Ziel

Einfache direkte Aufrufe sollen sichtbar werden, ohne vollständige Type-Inference zu behaupten.

### Erkennen

- direkte Funktionsaufrufe
- einfache Methodenaufrufe
- Aufrufe bekannter lokaler Funktionen
- Aufrufe importierter lokaler Funktionen, soweit auflösbar

### Nicht-Ziele

- vollständige TypeScript-Typauflösung
- Framework-Magie
- React Lifecycle vollständig verstehen
- dynamische Funktionsaufrufe perfekt auflösen
- Runtime-Auswertung

### Tests

- Funktion A ruft Funktion B
- importierte lokale Funktion wird erkannt
- unbekannte Aufrufe werden als unresolved/ambiguous behandelt
- kein Crash bei komplexem JS/TS

---

## 9.4 HTML Referenzanalyse

### Ziel

HTML-Dateien sollen wichtige Struktur- und Referenzinformationen liefern.

### Erkennen

- `<title>`
- `<script src="...">`
- inline script als Hinweis, aber nicht ausführen
- `<link rel="stylesheet" href="...">`
- `<form action="...">`
- wichtige IDs/classes optional
- lokale Referenzen zu JS/CSS-Dateien

### Beziehungen

- HTML -> JavaScript über script src
- HTML -> CSS über stylesheet link
- HTML -> Assets optional

### Nicht-Ziele

- Browser ausführen
- DOM simulieren
- JavaScript aus HTML ausführen
- vollständiger HTML5 Parser, wenn einfache statische Analyse reicht

### Tests

- title wird extrahiert
- script src wird erkannt
- stylesheet link wird erkannt
- form action wird erkannt
- lokale JS/CSS-Referenzen werden abgebildet
- kaputtes HTML crasht nicht

---

## 9.5 CSS Struktur-/Importanalyse

### Ziel

CSS-Dateien sollen wichtige Strukturinformationen liefern.

### Erkennen

- `@import`
- selectors
- media queries
- keyframes
- `url(...)` optional als Asset-Hinweis

### Call Graph

Für CSS nicht sinnvoll. Kein Call Graph für CSS.

### Nicht-Ziele

- CSS ausführen
- Layout berechnen
- Browser Rendering simulieren
- vollständige CSS-Spezifikation implementieren

### Tests

- @import wird erkannt
- einfache Selektoren werden erkannt
- media queries werden erkannt
- keyframes werden erkannt
- ungewöhnliches CSS crasht nicht

---

## 9.6 Java Symbol Extraction

### Ziel

Java-Dateien sollen wichtige Symbole sichtbar machen.

### Erkennen

- classes
- interfaces
- enums
- records
- methods
- constructors
- fields optional
- nested classes optional

### Beispiel

```java
package com.example;

import java.util.List;

public class App {
    public static void main(String[] args) {}
    private void run() {}
}
```

### Tests

- class erkannt
- interface erkannt
- enum erkannt
- record erkannt
- method erkannt
- constructor erkannt
- package erkannt
- nested class optional erkannt oder bewusst ignoriert

---

## 9.7 Java Package-/Importanalyse

### Ziel

Java package/import-Beziehungen sollen sichtbar werden.

### Erkennen

- package-Deklarationen
- import statements
- static imports
- lokale Klassenbeziehungen, soweit statisch ableitbar
- externe Packages separat

### Tests

- package wird erkannt
- import wird erkannt
- static import wird erkannt
- lokaler Import wird auf Datei gemappt, soweit möglich
- externer Import wird separat angezeigt
- unresolved Imports crashen nicht

---

## 9.8 Java konservativer Call Graph

### Ziel

Einfache direkte Methodenaufrufe sollen sichtbar werden, ohne vollständige Java-Typauflösung zu behaupten.

### Erkennen

- direkte Methodenaufrufe, soweit praktikabel
- Konstruktoraufrufe optional
- static method calls optional
- self/this calls optional

### Nicht-Ziele

- kein vollständiger Java-Compiler
- keine vollständige Typauflösung
- keine Maven/Gradle-Ausführung
- keine Annotation-Processing-Auswertung
- keine Spring-/Framework-Magie
- keine JVM-Ausführung

### Tests

- Methode A ruft Methode B
- this.method wird erkannt
- static call optional erkannt
- Konstruktoraufruf optional erkannt
- unbekannte Aufrufe werden konservativ behandelt
- kein Crash bei komplexem Java

---

# Aktuell bewusst gestrichen oder zurückgestellt

Diese Punkte wurden besprochen, sind aber aktuell nicht Teil dieser aktiven Roadmap:

- Code Compression / Token Saving Mode
- Project Rename / Unique Naming
- Token-Schätzung / Token-Budget
- Task-focused Context Selection
- Remote Git URL Export
- Kurzbeschreibung pro Datei

Hinweis:

Diese Punkte können später wieder aufgenommen werden, sind aber aktuell nicht Teil der geplanten nächsten Umsetzungsreihenfolge.

---

# Finale empfohlene Umsetzungsreihenfolge

1. Pipx Installation Hardening
2. Reine Language Detection für TypeScript, JavaScript, HTML, CSS und Java
3. Internes strukturiertes Export-Modell
4. MarkdownRenderer aus internem Modell
5. XMLRenderer mit vollständigem XML + CDATA
6. Optionale Zeilennummern
7. Test Map
8. Recent Commit Context
9. Tieferer Sprachsupport: JS/TS/HTML/CSS/Java Analyse

---

# Warum diese Reihenfolge

1. Pipx Installation Hardening ist klein, klar und verbessert sofort Installation und Release-Qualität.
2. Reine Language Detection bringt schnellen Nutzen ohne großen Architekturumbau.
3. Das interne Export-Modell ist die Grundlage für alle größeren Änderungen.
4. MarkdownRenderer aus dem Modell sichert bestehende Workflows ab.
5. XMLRenderer kann danach sauber aus demselben Modell entstehen.
6. Zeilennummern sind nach dem Renderer-Umbau einfacher und sauberer.
7. Test Map ist ein neues Modell-/Analysefeature und passt gut nach XML/Renderer.
8. Recent Commit Context profitiert vom Modell und braucht saubere XML-/CDATA-Behandlung für Patches.
9. Tieferer Sprachsupport ist groß und sollte erst kommen, wenn Modell und Renderer stabil sind.

---

# Definition of Done für diese Roadmap

Die Roadmap gilt als umgesetzt, wenn:

1. RepoDossier per pipx robust installierbar ist.
2. README den funktionierenden pipx-Weg dokumentiert.
3. Packaging-/pipx-Smoke-Tests vorhanden sind.
4. TypeScript, JavaScript, HTML, CSS und Java explizit erkannt werden.
5. RepoDossier intern ein strukturiertes Export-Modell verwendet.
6. Markdown aus diesem Modell gerendert wird.
7. XML aus diesem Modell gerendert wird.
8. XML vollständig strukturiert ist.
9. Dateiinhalte in XML per CDATA gekapselt sind.
10. Der CDATA-Sonderfall `]]>` sicher behandelt wird.
11. full und ai mindestens XML-Ausgabe unterstützen.
12. Markdown-/Legacy-Ausgabe weiterhin funktioniert.
13. Optionale Zeilennummern verfügbar sind.
14. Test Map als eigener Abschnitt/Modellteil existiert.
15. Recent Commit Context im full-Export Patches enthält.
16. Recent Commit Context im ai-Export nur Kurzinfos enthält.
17. Für JS/TS und Java sinnvolle statische Analyse vorhanden ist, soweit praktikabel.
18. Für HTML/CSS sinnvolle Struktur-/Referenzanalyse vorhanden ist.
19. Alle neuen Features sind getestet.
20. Die komplette Testsuite ist grün.
21. README und relevante Doku sind aktualisiert.
