# RepoDossier / RepoContext – Roadmap Next

Stand: 2026-07-01

RepoDossier ist der aktuelle Projektname. RepoContext bleibt vorerst als Legacy- und Kompatibilitätsalias erhalten.

Ziel dieser Roadmap ist eine sichere, deterministische und AI-freundliche Weiterentwicklung von RepoDossier. Die Reihenfolge ist bewusst so gewählt, dass zuerst kleine Stabilisierung und schnelle Nutzgewinne kommen, danach das neue Export-Fundament, und erst danach größere Analysefeatures.

---

## Neue empfohlene Umsetzungsreihenfolge

1. Pipx Installation Hardening
2. Content-aware Language Detection für bekannte und neue Sprachen
3. Internes strukturiertes Export-Modell
4. MarkdownRenderer aus internem Modell
5. XMLRenderer mit vollständigem XML + CDATA
6. Optionale Zeilennummern
7. Test Map
8. Recent Commit Context
9. Tieferer Sprachsupport für JavaScript, TypeScript, HTML, CSS, Java, C, C++, C#

---

# 1. Pipx Installation Hardening

## Ziel

RepoDossier soll zuverlässig systemweit bzw. benutzerweit per pipx installierbar sein.

Die README soll den Installationsweg dokumentieren, der lokal zuverlässig funktioniert hat. Die Release- und Smoke-Tests sollen prüfen, dass die CLI nach einer pipx-Installation wirklich verfügbar ist.

## Warum dieser Schritt zuerst kommt

Dieser Schritt ist klein, klar abgegrenzt und risikoarm. Er verbessert sofort die Nutzbarkeit des Projekts, ohne die Export-Architektur umzubauen.

## Offizieller README-Installationsweg

```bash
cd ~/market_research/repo_dossier || {
  echo "Fehler: Projektverzeichnis nicht gefunden."
}

python3 -m pipx uninstall repodossier 2>/dev/null || true
python3 -m pipx install "$PWD"

export PATH="$HOME/.local/bin:$PATH"

repodossier --help
repocontext --help
```

## Nicht mehr als Standard empfehlen

Diese Varianten sollen nicht mehr als Standardweg in der README stehen:

```bash
pipx install -e .
python3 -m pipx install -e .
```

Hintergrund: `pipx install -e .` hat lokal mit der Meldung `Cannot determine package name from spec ...` versagt. `python3 -m pipx install "$PWD"` hat funktioniert.

## Optional nur für Entwickler dokumentieren

Editable Install kann weiterhin als Entwickleroption dokumentiert werden, aber nicht als Standardinstallation:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

## pyproject.toml bereinigen

Aktuell prüfen und bereinigen:

```toml
include = ["repodossier*", "repodossier*"]
```

Ziel:

```toml
include = ["repodossier*"]
```

## Tests und Checks

Ergänzen oder prüfen:

```bash
python3 -m build
python3 -m twine check dist/*
```

pipx-Smoke-Test:

- lokale Installation mit `python3 -m pipx install "$PWD"`
- `repodossier --help` muss funktionieren
- `repocontext --help` muss funktionieren
- `repodossier --version` muss funktionieren
- `repocontext --version` muss funktionieren

## Script-Erweiterung

`scripts/validate_pipx_release.sh` prüfen und ggf. erweitern:

- robuste lokale pipx-Installation nutzen
- temporäre pipx-Umgebung isoliert verwenden
- beide CLI-Kommandos prüfen
- full, ai, docs und changed Smoke-Export prüfen, falls noch nicht vorhanden

## Akzeptanzkriterien

- README dokumentiert den robusten pipx-Weg.
- README empfiehlt nicht mehr primär `pipx install -e .`.
- `pyproject.toml` enthält keine doppelte package-include-Regel.
- pipx-Smoke-Test funktioniert.
- `repodossier` und `repocontext` sind nach Installation verfügbar.
- Vollständige Testsuite bleibt grün.

---

# 2. Content-aware Language Detection für bekannte und neue Sprachen

## Ziel

RepoDossier soll Sprachen nicht nur anhand der Dateiendung erkennen. Dateiendungen bleiben wichtig, aber zusätzlich sollen Shebangs und typische Inhaltsmuster ausgewertet werden.

Dieser Schritt ersetzt die frühere Idee einer reinen Extension-Erkennung für neue Sprachen. Er ist immer noch klein genug für einen frühen Roadmap-Schritt, bringt aber deutlich mehr Nutzen.

## Warum dieser Schritt vor dem Export-Modell kommt

Die Language Detection ist vergleichsweise unabhängig vom späteren XML-/Renderer-Umbau. Gleichzeitig liefert sie bessere Metadaten, die das spätere interne Export-Modell direkt übernehmen kann.

## Neue explizite Sprachen in diesem Schritt

Zusätzlich zu bereits vorhandenen Sprachen sollen mindestens diese Sprachen erkannt werden:

- TypeScript
- JavaScript
- HTML
- CSS
- Java
- C
- C++
- C#

Bestehende Sprachen sollen weiterhin erkannt werden:

- Python
- Bash / Shell
- Markdown
- TOML
- YAML
- JSON
- INI
- Plain text
- wichtige extensionless Dateien wie LICENSE, README, Makefile, Dockerfile

## Erkennungsstrategie

Priorität:

1. Shebang gewinnt, wenn eindeutig.
2. Eindeutige Inhaltsmerkmale bekommen hohe Priorität.
3. Dateiendung bleibt starker Hinweis.
4. Score-basiertes System entscheidet bei mehreren möglichen Treffern.
5. Bei Unsicherheit bleibt die Sprache `text` oder `unknown`.

## Score-basiertes System

Jede Sprache bekommt positive und ggf. negative Signale.

Beispiele:

Python:

- `#!/usr/bin/env python` oder `#!/usr/bin/python` sehr stark
- `def ...:`
- `class ...:`
- `import ...`
- `from ... import ...`
- `if __name__ == "__main__"`

Bash / Shell:

- `#!/usr/bin/env bash`
- `#!/bin/bash`
- `#!/bin/sh`
- `set -euo pipefail`
- `function name { ... }`
- `name() { ... }`

JavaScript / TypeScript:

- `import ... from ...`
- `export default`
- `require(...)`
- `function name(...)`
- `const name = (...) => ...`
- TypeScript-spezifisch: `interface`, `type`, `enum`, Typannotationen wie `name: string`

HTML:

- `<!DOCTYPE html>`
- `<html>`
- `<head>`
- `<body>`
- `<script>`
- `<link rel="stylesheet">`

CSS:

- `selector { property: value; }`
- `@media`
- `@import`
- `@keyframes`

Java:

- `package com.example;`
- `import java...;`
- `public class`
- `interface`
- `enum`
- `record`
- `public static void main`

C:

- `#include <stdio.h>`
- `#include "..."`
- `int main(`
- `typedef struct`
- `struct name`
- viele Semikolons und C-ähnliche Funktionsdefinitionen

C++:

- `#include <iostream>`
- `#include <vector>`
- `namespace ...`
- `class ...`
- `template <...>`
- `std::`
- `using namespace`

C#:

- `using System;`
- `namespace ...`
- `public class`
- `interface`
- `enum`
- `record`
- `async Task`
- Attribute wie `[Serializable]`, `[Test]`, `[Fact]`

## Dateiendungen

TypeScript:

- `.ts`
- `.tsx`

JavaScript:

- `.js`
- `.jsx`
- `.mjs`
- `.cjs`

HTML:

- `.html`
- `.htm`

CSS:

- `.css`

Java:

- `.java`

C:

- `.c`
- `.h`, wenn Inhalt eher C ist

C++:

- `.cpp`
- `.cc`
- `.cxx`
- `.hpp`
- `.hh`
- `.hxx`
- `.h`, wenn Inhalt eher C++ ist

C#:

- `.cs`

## Besonderheit Header-Dateien

`.h` ist mehrdeutig. Es kann C oder C++ sein.

Erkennungslogik:

- Wenn `namespace`, `class`, `template`, `std::` vorkommt, eher C++.
- Wenn `typedef struct`, `#include <stdio.h>`, C-Funktionssignaturen ohne C++-Merkmale vorkommen, eher C.
- Wenn nicht eindeutig, kann `c-header`, `cpp-header`, `c/c++` oder `unknown` verwendet werden.

Für die erste Version reicht eine konservative Entscheidung.

## Nicht-Ziele der ersten Version

- kein vollständiger Parser
- kein tree-sitter
- kein Compiler
- keine Code-Ausführung
- keine perfekte Typauflösung
- keine perfekte Unterscheidung aller Dialekte
- keine Ausführung von Build-Tools

Parser- oder tree-sitter-basierte Erkennung bleibt eine spätere optionale Erweiterung.

## Mögliche interne Struktur

Neue oder erweiterte Datei:

- `src/repodossier/scanner.py`
- optional neues Modul: `src/repodossier/languages.py`

Mögliche API:

```python
detect_language(path: str, content_sample: str | None = None) -> LanguageDetection
```

Mögliche Datenstruktur:

```python
@dataclass(frozen=True)
class LanguageDetection:
    language: str
    confidence: str
    reason: str
    scores: dict[str, int]
```

## Tests

Language Detection Tests:

- Python per `.py`
- Python per Shebang ohne Extension
- Bash per `.sh`
- Bash per Shebang ohne Extension
- TypeScript per `.ts`
- TypeScript per Inhalt
- JavaScript per `.js`
- JavaScript per Inhalt
- HTML per `.html`
- HTML per Inhalt
- CSS per `.css`
- CSS per Inhalt
- Java per `.java`
- Java per Inhalt
- C per `.c`
- C per Inhalt
- C++ per `.cpp`
- C++ Header per Inhalt
- C# per `.cs`
- C# per Inhalt
- JSON vs JavaScript unterscheiden
- YAML vs Markdown/Text nicht unnötig falsch erkennen
- Unklare Datei bleibt `text` oder `unknown`

Export Tests:

- File Summary zeigt neue Sprachen.
- Source Export nutzt passende Codeblock-Language.
- MarkdownRenderer übernimmt Language Labels.
- später XMLRenderer übernimmt Language Labels.

## Akzeptanzkriterien

- Neue Sprachen werden explizit erkannt.
- Bestehende Sprachen regressieren nicht.
- Shebang-Erkennung funktioniert.
- Inhaltsheuristiken funktionieren für typische Dateien.
- Extension bleibt Fallback.
- Unsichere Fälle werden konservativ behandelt.
- Tests sind deterministisch.
- Vollständige Testsuite bleibt grün.

---

# 3. Internes strukturiertes Export-Modell

## Ziel

RepoDossier soll intern nicht mehr direkt Markdown-Text zusammensetzen. Stattdessen soll zuerst ein strukturiertes internes Export-Modell aufgebaut werden. Dieses Modell wird anschließend von verschiedenen Renderern ausgegeben.

## Warum dieser Schritt zentral ist

Ohne internes Modell würde XML nur ein zweiter hart verdrahteter Exporter werden. Das würde doppelte Logik erzeugen und spätere Features erschweren.

Das interne Modell wird die Quelle der Wahrheit. Markdown und XML sind nur noch Renderziele.

## Modell soll mindestens enthalten

Repository und Umgebung:

- repository metadata
- root path / root name
- git branch
- git commit
- git dirty status optional
- command/mode
- generated timestamp optional, falls deterministisch handhabbar

Konfiguration:

- config active yes/no
- config path
- include paths
- include globs
- exclude paths
- exclude globs
- limits
- split settings

Statistik:

- total tracked files
- scanned files
- exported text files
- skipped binary files
- errored files
- total lines
- estimated tokens
- file type statistics
- language statistics

Struktur:

- repository tree
- file summary
- omitted files
- truncated files
- warnings

Analysebereiche:

- dependencies
- database schema
- secret detection summary
- symbol index
- import graph
- call graph
- test map
- recent commits

Dateien:

- path
- language
- size bytes
- line count
- token estimate
- binary/text status
- skipped/truncated status
- content if included
- masked content if secret detection applies

## Mögliche neue Dateien

- `src/repodossier/export_model.py`
- `src/repodossier/renderers/__init__.py`
- `src/repodossier/renderers/markdown.py`
- `src/repodossier/renderers/xml.py`

## Mögliche zentrale Datenmodelle

- `RepositoryExport`
- `RepositoryMetadata`
- `ExportConfigurationSummary`
- `ExportSummary`
- `LanguageStatistics`
- `FileEntry`
- `FileTreeEntry`
- `DependencyReport`
- `DatabaseSchemaReport`
- `SecretDetectionSummary`
- `SymbolIndex`
- `ImportGraphReport`
- `CallGraphReport`
- `TestMapReport`
- `RecentCommitReport`
- `ExportWarning`

## Anforderungen

- Exporter sammeln Daten und bauen das Modell.
- Renderer rendern nur.
- Keine Git-/Scanner-/Analyzer-Logik in Renderern.
- Keine doppelte Exportlogik für Markdown und XML.
- Bestehende Markdown-Ausgabe soll möglichst stabil bleiben.
- Bestehende CLI-Kommandos bleiben kompatibel.

## Tests

- Unit-Tests für Export-Modell.
- Tests für leeres/minimales Modell.
- Tests für Full-Export-Modell.
- Tests für AI-Export-Modell.
- Tests für Docs-Export-Modell.
- Tests für Changed-Export-Modell, falls in diesem Schritt migriert.
- Regressionstests, dass bestehende Exporte weiterhin erzeugt werden.
- Tests, dass Include/Exclude/Limits im Modell sichtbar sind.
- Tests, dass Language Detection aus Schritt 2 im Modell landet.

## Akzeptanzkriterien

- Es gibt ein zentrales strukturiertes Export-Modell.
- Full/AI/Docs/Changed können zumindest teilweise daraus gespeist werden.
- Bestehende Exportausgaben bleiben funktionsfähig.
- Renderer können auf dasselbe Modell zugreifen.
- Tests sind grün.

---

# 4. MarkdownRenderer aus internem Modell

## Ziel

Der bisherige Markdown-/Text-Export bleibt erhalten, wird aber aus dem neuen internen Export-Modell gerendert.

## Warum MarkdownRenderer vor XML kommt

Damit wird bewiesen, dass das neue Modell die bestehende Ausgabe abbilden kann. Dadurch sinkt das Risiko, dass der XML-Umbau bestehende Workflows zerstört.

## Betroffene Ausgaben

- `full.txt`
- `ai.txt`
- `docs.txt`
- `changed.txt`

## Anforderungen

- Bestehende Überschriften möglichst stabil halten.
- Bestehende Reihenfolge möglichst stabil halten.
- MarkdownRenderer führt keine Analyse aus.
- MarkdownRenderer liest keine Dateien.
- MarkdownRenderer ruft kein Git auf.
- MarkdownRenderer rendert nur das Modell.

## Full Markdown Export

Soll weiterhin enthalten:

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

Später zusätzlich:

- Test Map
- Recent Commits
- optional Zeilennummern

## AI Markdown Export

Soll weiterhin kompakt sein und enthalten:

- Project summary
- Architecture Summary
- Important Files
- Dependencies
- Database Schema
- Symbol Index
- Import Graph
- Call Graph
- Notes

Später zusätzlich:

- Test Map kompakt
- Recent Commits kompakt

## Docs Markdown Export

Soll docs-only bleiben:

- Documentation Quick Start
- Documentation Summary
- Documentation Files
- Extracted Documents
- Warnings

## Changed Markdown Export

Soll review-fokussiert bleiben:

- Changed Export Header
- Repository path
- Compare Mode
- Changed Files Summary
- Changed Files overview
- Git Diff
- Changed File Contents
- Deleted Files
- Binary / Skipped Files

## Tests

- Full Markdown Export Snapshot-/Regressionstest.
- AI Markdown Export Regressionstest.
- Docs Markdown Export Regressionstest.
- Changed Markdown Export Regressionstest.
- Renderer-Unit-Tests mit künstlichem Modell.
- Tests, dass Renderer keine Analysefunktionen aufruft.

## Akzeptanzkriterien

- Markdown-Ausgaben funktionieren weiterhin.
- Markdown wird aus dem Modell gerendert.
- Alte Workflows bleiben nutzbar.
- Tests sind grün.

---

# 5. XMLRenderer mit vollständigem XML + CDATA

## Ziel

RepoDossier soll einen vollständig maschinenlesbaren XML-Export erzeugen können. Der gesamte Dump soll XML-strukturiert sein.

Nicht nur Datei-Inhalte, sondern alle Bereiche des Dumps sollen XML-Elemente sein.

## Grundentscheidung

- XML ist das primäre zukünftige AI-/Maschinenformat.
- Dateiinhalte werden mit CDATA gekapselt.
- Markdown bleibt Human-/Legacy-Ausgabe.
- JSON/YAML sind nicht primäres Maschinenformat.

## Mögliche CLI

```bash
repodossier full --format xml
repodossier export-ai --format xml
repodossier export-docs --format xml
repodossier changed --format xml
```

Legacy-Alias optional:

```bash
repocontext full --format xml
repocontext export-ai --format xml
repocontext export-docs --format xml
repocontext changed --format xml
```

## XML soll strukturieren

- Repository-Metadaten
- Config-Status
- Summary
- Repository Statistics
- File Summary
- Dateibaum
- Dependencies
- Database Schema
- Secret Detection
- Symbol Map / Symbol Index
- Import Graph
- Call Graph
- Test Map
- Recent Commits
- ausgelassene Dateien
- gekürzte Dateien
- Warnings
- eigentliche Dateiinhalte

## CDATA-Anforderung

Dateiinhalte sollen mit CDATA gekapselt werden:

```xml
<content><![CDATA[
...
]]></content>
```

Sonderfall `]]>` muss korrekt behandelt werden.

Sichere Strategie:

```text
]]> wird intern gesplittet in ]]]]><![CDATA[>
```

## Beispielstruktur

```xml
<repodossier version="1" mode="full">
  <repository>
    <root_name>repo_dossier</root_name>
    <git_branch>main</git_branch>
    <git_commit>...</git_commit>
  </repository>

  <configuration active="false">
    <include>
      <paths />
      <globs />
    </include>
    <exclude>
      <paths />
      <globs />
    </exclude>
    <limits />
  </configuration>

  <summary>
    <tracked_files>154</tracked_files>
    <exported_text_files>154</exported_text_files>
    <total_lines>50557</total_lines>
    <estimated_tokens>362113</estimated_tokens>
  </summary>

  <files>
    <file path="src/repodossier/cli.py" language="python" lines="500">
      <content><![CDATA[
...
      ]]></content>
    </file>
  </files>
</repodossier>
```

## Tests

- XML ist parsebar mit Python stdlib XML parser.
- Full XML Export funktioniert.
- AI XML Export funktioniert.
- Docs XML Export funktioniert, falls im Scope.
- Changed XML Export funktioniert, falls im Scope.
- Alle Hauptbereiche sind XML-Elemente.
- Kein loser Markdown-Header im XML.
- Dateiinhalte bleiben erhalten.
- CDATA-Sonderfall ist abgesichert.
- Secret Masking bleibt aktiv.
- Include/Exclude/Limits werden sichtbar.
- Language Labels aus Schritt 2 erscheinen im XML.

## Akzeptanzkriterien

- XMLRenderer rendert aus dem internen Modell.
- XML ist vollständig strukturiert.
- XML ist parsebar.
- CDATA ist sicher.
- Full und AI unterstützen mindestens XML.
- Tests sind grün.

---

# 6. Optionale Zeilennummern

## Ziel

Dateien können optional mit Zeilennummern exportiert werden. Das hilft AI-Assistenten bei präzisen Verweisen und Patch-Anweisungen.

## Warum nach Renderern

Zeilennummern sind ein Ausgabe- und Rendering-Thema. Sie müssen für Markdown und XML sauber definiert werden.

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
repocontext export-docs --line-numbers
repocontext changed --line-numbers
```

## Nutzen

- AI kann genauer auf Dateien und Zeilen verweisen.
- Fehlermeldungen lassen sich leichter zuordnen.
- Patch-Anweisungen werden präziser.
- Reviews werden besser nachvollziehbar.

## Wichtig

- Zeilennummern erhöhen Tokenverbrauch.
- Deshalb optional, nicht Standard.
- Truncation und Secret Masking müssen weiterhin funktionieren.

## Markdown-Variante

```text
001 | import argparse
002 |
003 | def main():
004 |     ...
```

## XML-Variante A

```xml
<content line_numbers="true"><![CDATA[
001 | import argparse
002 |
003 | def main():
]]></content>
```

## XML-Variante B für später

```xml
<lines>
  <line number="1"><![CDATA[import argparse]]></line>
  <line number="2"><![CDATA[]]></line>
</lines>
```

Empfehlung für erste Version: einfache Content-Variante mit `001 |`. Echte `<line>`-Elemente können später kommen.

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

## Akzeptanzkriterien

- Zeilennummern sind optional.
- full/ai/changed unterstützen sie mindestens.
- Markdown und XML verhalten sich konsistent.
- Tests sind grün.

---

# 7. Test Map

## Ziel

RepoDossier soll sichtbar machen, welche Tests vermutlich zu welchen Source-Dateien gehören.

Die Test Map soll AI-Code-Reviews, Debugging und Milestone-Prüfungen verbessern.

## Beispiel

```text
src/repodossier/config.py
- tests/test_config.py
- tests/test_config_full_export_limits.py
- tests/test_config_ai_export_filters.py
```

## Nutzen

- AI erkennt schneller, welche Tests nach einer Änderung relevant sind.
- Bei Patches kann gezielter geprüft werden.
- Bei Fehlermeldungen kann Source-Datei und Testdatei besser verbunden werden.
- Große Repositories werden für Reviews übersichtlicher.

## Scope erste Version

- heuristisch und statisch
- keine Tests ausführen
- keine Coverage messen
- keine perfekte Zuordnung versprechen
- keine dynamische Analyse

## Mögliche Heuristiken

- `tests/test_config.py` passt zu `src/repodossier/config.py`
- `tests/test_cli.py` passt zu `src/repodossier/cli.py`
- `tests/test_full_exporter.py` passt zu `src/repodossier/exporters/full.py`
- Testdateinamen nach `test_<module>.py`
- Import-Statements in Testdateien auswerten
- direkte Erwähnung von Modulnamen im Test

## XML-Struktur

```xml
<test_map>
  <mapping source="src/repodossier/config.py">
    <test_file path="tests/test_config.py" reason="name_match" />
    <test_file path="tests/test_config_full_export_limits.py" reason="name_prefix_match" />
  </mapping>
</test_map>
```

## Markdown-Struktur

```text
# Test Map

src/repodossier/config.py
- tests/test_config.py
- tests/test_config_full_export_limits.py
```

## Tests

- Einfache Modul/Test-Namenszuordnung funktioniert.
- Exporter-Testdateien werden passenden Exporter-Modulen zugeordnet.
- Unpassende Tests werden nicht wild zugeordnet.
- Ergebnis ist deterministisch sortiert.
- XMLRenderer rendert Test Map.
- MarkdownRenderer rendert Test Map.
- Kein Crash bei Repos ohne tests-Ordner.
- Exclude-Regeln werden respektiert, z. B. wenn tests ausgeschlossen sind.

## Akzeptanzkriterien

- Test Map existiert als eigener Modellteil.
- Full/AI können Test Map ausgeben.
- XML und Markdown können Test Map rendern.
- Tests sind grün.

---

# 8. Recent Commit Context

## Ziel

Die letzten Commits sollen im Export als Übersicht enthalten sein. Dadurch versteht die AI besser, was zuletzt geändert wurde und warum.

Besonders nützlich für Milestone-, Patch- und Review-Workflows.

## Warum nach Test Map

Recent Commit Context profitiert stark vom strukturierten Modell. Patches und Diffs müssen in XML sauber mit CDATA behandelt werden. Deshalb sollte XML/CDATA vorher stabil sein.

## Modus full

Full soll maximale Nachvollziehbarkeit liefern:

- Recent Commits Übersicht
- Commit Hash
- Commit Message
- Author/Date optional
- betroffene Dateien
- kompletter Patch/Diff pro Commit

## Modus ai

AI soll Token sparen:

- Recent Commits Übersicht
- Commit Hash kurz
- Commit Message
- Kurzbeschreibung / Summary
- betroffene Dateien
- keine vollständigen Patches

## Mögliche CLI

```bash
repodossier full --recent-commits 5
repodossier export-ai --recent-commits 10
repodossier full --no-recent-commits
repodossier export-ai --no-recent-commits
```

## Mögliche Config

```yaml
git:
  recent_commits_full: 5
  recent_commits_ai: 10
  include_patches_in_full: true
  include_patches_in_ai: false
```

## XML-Struktur

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

## Markdown-Struktur full

```text
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

## Markdown-Struktur ai

```text
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

## Akzeptanzkriterien

- Recent Commits existieren im Modell.
- Full kann Patches enthalten.
- AI bleibt kompakt.
- XML und Markdown rendern korrekt.
- Tests sind grün.

---

# 9. Tieferer Sprachsupport für JavaScript, TypeScript, HTML, CSS, Java, C, C++, C#

## Ziel

RepoDossier soll zusätzliche Sprachen nicht nur erkennen, sondern sinnvoll statisch analysieren, soweit das für AI-Exporte nützlich ist.

Analyse bleibt statisch und sicher. Es wird kein Projektcode ausgeführt. Es werden keine Compiler, Build-Tools oder Frameworks ausgeführt.

## Warum zuletzt

Dieser Block ist groß und potenziell komplex. Symbol Extraction, Import Graph und Call Graph für mehrere Sprachen sind deutlich aufwändiger als reine Language Detection. Nach Export-Modell, MarkdownRenderer und XMLRenderer können neue Analyseergebnisse sauber modelliert und in beiden Ausgabeformaten gerendert werden.

## Allgemeine Anforderungen

- Analyse bleibt statisch.
- Keine Code-Ausführung.
- Keine Compiler-Ausführung.
- Keine Build-Tool-Ausführung.
- Keine vollständige Type-Inference versprechen.
- Konservativ bleiben.
- Lieber weniger erkennen als falsche Beziehungen behaupten.
- Include/Exclude-Regeln respektieren.
- Secret Detection weiterhin anwenden.
- Ergebnisse ins interne Export-Modell schreiben.
- XMLRenderer und MarkdownRenderer unterstützen die neuen Analysebereiche.

---

## 9.1 JavaScript / TypeScript Symbol Extraction

### Dateien

JavaScript:

- `.js`
- `.jsx`
- `.mjs`
- `.cjs`

TypeScript:

- `.ts`
- `.tsx`

### Zu erkennen

- functions
- async functions
- arrow functions mit Namen
- classes
- methods
- exported symbols
- default exports
- constants optional
- TypeScript interfaces optional
- TypeScript type aliases optional
- TypeScript enums optional

### Beispiele

```typescript
function run() {}
async function load() {}
const handler = () => {}
export function main() {}
export default class App {}
class Service { start() {} }
interface User { id: string }
type Mode = "dev" | "prod"
```

### Nicht-Ziele

- vollständiger TypeScript Compiler
- komplette Typauflösung
- JSX/TSX vollständig semantisch verstehen
- Framework-Magie erkennen

### Tests

- functions werden erkannt
- async functions werden erkannt
- arrow functions mit Namen werden erkannt
- classes und methods werden erkannt
- named exports werden erkannt
- default exports werden erkannt
- TypeScript interface/type optional erkannt

---

## 9.2 JavaScript / TypeScript Import Graph

### Zu erkennen

- `import ... from "..."`
- `import "..."`
- `export ... from "..."`
- `require("...")`
- dynamic `import("...")` optional/konservativ
- lokale Modulbeziehungen
- externe Module separat

### Tests

- ES imports werden erkannt
- re-exports werden erkannt
- require wird erkannt
- lokale relative Imports werden auf Dateien gemappt
- externe Packages werden separat geführt
- dynamische Imports crashen nicht

---

## 9.3 JavaScript / TypeScript konservativer Call Graph

### Zu erkennen

- direkte Funktionsaufrufe
- einfache Methodenaufrufe
- Aufrufe bekannter lokaler Funktionen
- Klassenmethoden, soweit statisch naheliegend

### Nicht-Ziele

- vollständige Type-Inference
- Runtime-Bindings
- Monkeypatching
- Framework Injection
- React/Vue/Angular-Semantik vollständig verstehen

### Tests

- direkte lokale Funktionsaufrufe werden erkannt
- importierte Funktionen werden konservativ erkannt
- externe Calls werden separat geführt
- unresolved Calls werden nicht als sicher intern behauptet
- kein Crash bei komplexer Syntax

---

## 9.4 HTML Referenzanalyse

### Dateien

- `.html`
- `.htm`

### Zu erkennen

- `title`
- `script src`
- inline script als Hinweis, aber nicht ausführen
- `link rel="stylesheet"`
- `form action`
- wichtige IDs/classes optional
- lokale Referenzen zu JS/CSS-Dateien

### Beziehungen

- HTML -> JavaScript über `<script src="...">`
- HTML -> CSS über `<link rel="stylesheet" href="...">`
- HTML -> Assets optional, aber nicht übertreiben

### Call Graph

Für HTML selbst normalerweise kein Call Graph. Inline-JavaScript könnte später optional an JS-Analyse übergeben werden, aber nicht in der ersten Version.

### Nicht-Ziele

- Browser ausführen
- DOM simulieren
- JavaScript ausführen
- vollständiger HTML5 Parser, wenn einfache statische Analyse reicht

### Tests

- title wird erkannt
- script src wird erkannt
- stylesheet link wird erkannt
- form action wird erkannt
- lokale JS/CSS-Referenzen erscheinen
- kein Crash bei kaputtem HTML

---

## 9.5 CSS Struktur- und Importanalyse

### Dateien

- `.css`

### Zu erkennen

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
- url(...) optional erkannt
- kein Crash bei ungewöhnlichem CSS

---

## 9.6 Java Symbol Extraction

### Dateien

- `.java`

### Zu erkennen

- classes
- interfaces
- enums
- records
- methods
- constructors
- fields optional
- nested classes optional

### Beispiele

```java
package com.example;

import java.util.List;

public class App {
    public static void main(String[] args) {}
    private void run() {}
}
```

### Tests

- class wird erkannt
- interface wird erkannt
- enum wird erkannt
- record wird erkannt
- method wird erkannt
- constructor wird erkannt
- package wird im Symbolkontext sichtbar

---

## 9.7 Java Package- und Importanalyse

### Zu erkennen

- package-Deklarationen
- import statements
- static imports
- lokale Klassenbeziehungen, soweit statisch ableitbar
- externe Packages separat

### Tests

- package wird erkannt
- normale imports werden erkannt
- static imports werden erkannt
- lokale Projektklassen werden auf Dateien gemappt
- externe Imports werden separat geführt

---

## 9.8 Java konservativer Call Graph

### Zu erkennen

- direkte Methodenaufrufe, soweit praktikabel
- Konstruktoraufrufe optional
- static method calls optional
- `this.method()` optional
- einfache same-class calls optional

### Nicht-Ziele

- vollständige Type-Inference
- JVM-Ausführung
- Maven/Gradle-Ausführung
- Annotation Processing
- Spring-/Framework-Magie

### Tests

- direkte Methodenaufrufe werden erkannt
- Konstruktoraufrufe optional erkannt
- static calls optional erkannt
- externe Calls werden getrennt
- unresolved Calls werden nicht falsch als intern behauptet

---

## 9.9 C Symbol Extraction

### Dateien

- `.c`
- `.h`, wenn Inhalt eher C ist

### Zu erkennen

- functions
- function declarations/prototypes optional
- structs
- typedefs
- enums
- macros optional
- global variables optional

### Beispiele

```c
#include <stdio.h>

typedef struct User {
    int id;
} User;

int main(int argc, char **argv) {
    return 0;
}
```

### Nicht-Ziele

- vollständiger C-Parser
- Präprozessor vollständig ausführen
- Makros expandieren
- Build-System ausführen

### Tests

- function wird erkannt
- prototype wird optional erkannt
- struct wird erkannt
- typedef wird erkannt
- enum wird erkannt
- include wird erkannt

---

## 9.10 C Include Graph und konservativer Call Graph

### Include Graph

Zu erkennen:

- `#include <...>` als externe/system includes
- `#include "..."` als lokale includes
- lokale Header-Beziehungen

### Call Graph

Zu erkennen:

- direkte Funktionsaufrufe
- Aufrufe bekannter lokaler Funktionen
- externe Calls separat

### Nicht-Ziele

- Makroauflösung
- Funktionszeiger vollständig auflösen
- Präprozessorbedingungen auswerten
- Linker-/Compilerverhalten simulieren

### Tests

- lokale includes werden erkannt
- System-includes werden separat geführt
- direkte lokale Calls werden erkannt
- externe Calls werden getrennt
- Funktionszeiger crashen nicht

---

## 9.11 C++ Symbol Extraction

### Dateien

- `.cpp`
- `.cc`
- `.cxx`
- `.hpp`
- `.hh`
- `.hxx`
- `.h`, wenn Inhalt eher C++ ist

### Zu erkennen

- namespaces
- classes
- structs
- methods
- constructors
- destructors optional
- free functions
- enums
- templates optional/konservativ

### Beispiele

```cpp
#include <iostream>
#include <vector>

namespace demo {
class App {
public:
    void run();
};
}
```

### Nicht-Ziele

- vollständiger C++ Parser
- Templates vollständig interpretieren
- Overload Resolution
- Makros expandieren
- Compiler ausführen

### Tests

- namespace wird erkannt
- class wird erkannt
- method wird erkannt
- constructor wird erkannt
- free function wird erkannt
- template syntax crasht nicht

---

## 9.12 C++ Include Graph und konservativer Call Graph

### Include Graph

Zu erkennen:

- lokale includes
- system includes
- Header-/Source-Beziehungen, soweit statisch ableitbar

### Call Graph

Zu erkennen:

- direkte Funktionsaufrufe
- einfache Methodenaufrufe
- Konstruktoraufrufe optional
- bekannte lokale Funktionen/Methoden konservativ

### Nicht-Ziele

- vollständige Type-Inference
- Overload Resolution
- virtuelle Dispatch-Auflösung
- Templates vollständig auflösen
- Build-System ausführen

### Tests

- lokale includes werden erkannt
- system includes werden getrennt
- direkte Calls werden erkannt
- Methodenaufrufe werden konservativ erkannt
- unresolved Calls bleiben unresolved

---

## 9.13 C# Symbol Extraction

### Dateien

- `.cs`

### Zu erkennen

- namespaces
- using directives
- classes
- interfaces
- enums
- records
- structs
- methods
- constructors
- properties optional
- fields optional
- attributes optional als Metadaten

### Beispiele

```csharp
using System;

namespace Demo;

public class App
{
    public static void Main(string[] args) {}
    private void Run() {}
}
```

### Nicht-Ziele

- vollständiger Roslyn-Ersatz
- MSBuild ausführen
- NuGet Restore
- Source Generators
- Reflection verstehen

### Tests

- namespace wird erkannt
- using wird erkannt
- class wird erkannt
- interface wird erkannt
- enum wird erkannt
- record wird erkannt
- method wird erkannt
- property optional erkannt

---

## 9.14 C# Import-/Dependency-Analyse und konservativer Call Graph

### Import-/Dependency-Analyse

Zu erkennen:

- using directives
- namespace relationships
- lokale Klassenbeziehungen, soweit statisch ableitbar
- externe namespaces separat

### Call Graph

Zu erkennen:

- direkte Methodenaufrufe
- static method calls optional
- constructor calls optional
- same-class calls optional

### Nicht-Ziele

- vollständige Type-Inference
- Roslyn-Integration in erster Version
- MSBuild-Ausführung
- Dependency Injection vollständig verstehen

### Tests

- using directives werden erkannt
- lokale Typreferenzen werden konservativ erkannt
- direkte Methodenaufrufe werden erkannt
- externe Calls werden getrennt
- unresolved Calls bleiben unresolved

---

## 9.15 Gemeinsame Exportintegration für tiefere Sprachdaten

### Ziel

Neue Sprachdaten sollen nicht in Sonderformaten versteckt werden, sondern in die bestehenden Modellbereiche integriert werden:

- Symbol Index
- Import Graph
- Call Graph
- File Summary
- XML Export
- Markdown Export

### Anforderungen

- Jede Sprache bekommt ein klares language label.
- Symbole enthalten Sprache und Datei.
- Import-/Include-Beziehungen unterscheiden lokal/extern/unresolved.
- Call Graph unterscheidet intern/extern/unresolved/ambiguous.
- Ausgabe bleibt deterministisch.
- Große Gruppen werden begrenzt.

### Tests

- Symbol Index zeigt JS/TS/Java/C/C++/C# Symbole.
- Import Graph zeigt JS/TS/Java/C/C++/C# Beziehungen.
- Call Graph zeigt konservative Calls.
- XML enthält strukturierte Sprachdaten.
- Markdown bleibt lesbar.
- AI Export bleibt kompakt.

---

# Aktuell bewusst gestrichen oder zurückgestellt

Diese Punkte wurden besprochen, sind aber aktuell nicht Teil der aktiven Roadmap:

- Code Compression / Token Saving Mode
- Project Rename / Unique Naming
- Token-Schätzung / Token-Budget
- Task-focused Context Selection
- Remote Git URL Export
- Kurzbeschreibung pro Datei
- vollständige parser-/tree-sitter-basierte Spracherkennung als erster Schritt

Diese Punkte können später wieder aufgenommen werden.

---

# Finale kompakte Reihenfolge

1. Pipx Installation Hardening
2. Content-aware Language Detection für bekannte und neue Sprachen
3. Internes strukturiertes Export-Modell
4. MarkdownRenderer aus internem Modell
5. XMLRenderer mit vollständigem XML + CDATA
6. Optionale Zeilennummern
7. Test Map
8. Recent Commit Context
9. Tieferer Sprachsupport für JavaScript, TypeScript, HTML, CSS, Java, C, C++, C#

---

# Definition of Done für die aktuelle Roadmap

Die Roadmap gilt als umgesetzt, wenn:

1. RepoDossier per pipx robust installierbar ist.
2. README den funktionierenden pipx-Installationsweg dokumentiert.
3. TypeScript, JavaScript, HTML, CSS, Java, C, C++ und C# explizit erkannt werden.
4. Language Detection nicht nur Dateiendungen, sondern auch Shebangs und Inhaltsheuristiken nutzt.
5. Unsichere Sprachfälle konservativ als text/unknown behandelt werden.
6. RepoDossier intern ein strukturiertes Export-Modell verwendet.
7. Markdown aus diesem Modell gerendert wird.
8. XML aus diesem Modell gerendert wird.
9. XML vollständig strukturiert ist.
10. Dateiinhalte in XML per CDATA gekapselt sind.
11. Der CDATA-Sonderfall `]]>` sicher behandelt wird.
12. full und ai mindestens XML-Ausgabe unterstützen.
13. Markdown-/Legacy-Ausgabe weiterhin funktioniert.
14. Optionale Zeilennummern verfügbar sind.
15. Test Map als eigener Abschnitt/Modellteil existiert.
16. Recent Commit Context im full-Export Patches enthalten kann.
17. Recent Commit Context im ai-Export kompakt bleibt und keine vollständigen Patches enthält.
18. Für JS/TS sinnvolle statische Symbol-, Import- und Call-Analyse vorhanden ist, soweit praktikabel.
19. Für HTML/CSS sinnvolle Struktur- und Referenzanalyse vorhanden ist.
20. Für Java sinnvolle statische Symbol-, Import- und Call-Analyse vorhanden ist, soweit praktikabel.
21. Für C/C++ sinnvolle statische Symbol-, Include- und Call-Analyse vorhanden ist, soweit praktikabel.
22. Für C# sinnvolle statische Symbol-, using-/namespace- und Call-Analyse vorhanden ist, soweit praktikabel.
23. Keine neue Analyse führt Projektcode aus.
24. Keine neue Analyse führt Compiler oder Build-Tools aus.
25. Alle neuen Features sind getestet.
26. Die komplette Testsuite ist grün.
27. README und relevante Doku sind aktualisiert.
