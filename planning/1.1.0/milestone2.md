# MILESTONE 2 – Content-aware Language Detection für bekannte und neue Sprachen

Release-Linie: 1.1.0  
Empfohlener Zielpfad im Repository: `planning/1.1.0/milestone2.md`  
Roadmap-Punkt: `2. Content-aware Language Detection für bekannte und neue Sprachen`  
Projektname: RepoDossier  
Legacy-Alias: RepoContext / `repocontext`

---

## Ziel

RepoDossier soll Dateisprachen nicht mehr nur über Dateiendungen erkennen.

Dateiendungen bleiben ein wichtiger und stabiler Hinweis, aber die Erkennung soll zusätzlich folgende Signale berücksichtigen:

- Shebangs, z. B. `#!/usr/bin/env python`, `#!/bin/bash`, `#!/bin/sh`
- eindeutige Inhaltsmerkmale, z. B. `def ...:`, `interface`, `<!DOCTYPE html>`, `#include <stdio.h>`
- bekannte extensionless Dateien wie `README`, `LICENSE`, `Makefile`, `Dockerfile`
- konservative Fallbacks für unsichere Fälle
- deterministische Score-Logik bei mehreren möglichen Treffern

Nach diesem Milestone soll RepoDossier mindestens diese Sprachen zuverlässig erkennen:

- Python
- Bash / Shell
- Markdown
- TOML
- YAML
- JSON
- INI
- Plain text
- TypeScript
- JavaScript
- HTML
- CSS
- Java
- C
- C++
- C#


Unsichere Dateien sollen nicht aggressiv falsch klassifiziert werden. Wenn die Erkennung nicht ausreichend sicher ist, soll die Sprache konservativ `text` oder `unknown` bleiben.

---

## Warum dieser Schritt nach Milestone 1 kommt

Milestone 1 stabilisiert Installation, Release-Validierung und pipx-Smoke-Tests.

Milestone 2 verbessert danach direkt die fachliche Qualität der Exporte:

- File Summary wird genauer.
- Codeblock-Languages im Source Export werden besser.
- Neue spätere Analysefeatures bekommen bessere Metadaten.
- Das kommende interne Export-Modell kann die besseren Language Labels übernehmen.
- Die Änderung ist noch klein genug, bevor Export-Modell, Renderer und XML eingeführt werden.

---

## Ergebnis nach Abschluss

Nach Milestone 2 kann RepoDossier:

1. Sprachen anhand von Dateiendungen erkennen.
2. Sprachen anhand von Shebangs erkennen.
3. Sprachen anhand typischer Inhaltsmuster erkennen.
4. Dateiendung, Shebang und Inhalt deterministisch zusammenführen.
5. TypeScript, JavaScript, HTML, CSS, Java, C, C++ und C# explizit erkennen.
6. Bestehende Python-, Bash-, Markdown-, TOML-, YAML-, JSON-, INI- und Text-Erkennung beibehalten.
7. `.h`-Headerdateien konservativ als C oder C++ einordnen, wenn der Inhalt eindeutig ist.
8. JSON nicht unnötig als JavaScript fehlklassifizieren.
9. YAML, Markdown und Text nicht unnötig aggressiv fehlklassifizieren.
10. File Summary und Source-Codeblock-Language mit den neuen Labels ausgeben.
11. Tests für alle neuen und bestehenden Kernfälle bereitstellen.
12. Die vollständige Testsuite grün halten.

---

## Nicht-Ziele für Milestone 2

Folgende Dinge gehören ausdrücklich nicht zu Milestone 2:

- kein vollständiger Parser
- kein tree-sitter
- keine Compiler-Ausführung
- keine Build-Tool-Ausführung
- keine Code-Ausführung aus dem analysierten Projekt
- keine vollständige Typauflösung
- keine semantische JavaScript-/TypeScript-Analyse
- keine Java-/C-/C++-/C#-Symbolanalyse
- kein Import Graph für neue Sprachen
- kein Call Graph für neue Sprachen
- kein XML-Renderer
- kein internes Export-Modell
- keine Zeilennummern
- keine Test Map
- kein Recent Commit Context

Milestone 2 erkennt Sprachen. Tiefere Analyse kommt später.

---

## Sicherheits- und Qualitätsregeln

- RepoDossier darf Projektcode nicht importieren oder ausführen.
- Sprachheuristiken lesen nur Textinhalte.
- Fehlerhafte, binäre oder sehr große Dateien dürfen die Erkennung nicht crashen lassen.
- Die Ausgabe muss deterministisch bleiben.
- Lieber konservativ `text` oder `unknown` als falsch sicher behaupten.
- Existing behavior darf nicht regressieren.
- Exportdateien wie `full.txt`, `ai.txt`, `docs.txt`, `changed.txt` bleiben generierte Artefakte und sollen nicht als neue Sprachfälle missbraucht werden.

---

# 2.0 – Bestandsprüfung nach Milestone 1

## 2.0.a – Frischen Projektstand nach Milestone 1 prüfen

Ziel:
Nach Abschluss von Milestone 1 den echten Stand prüfen, bevor die Umsetzung beginnt.

Zu prüfen:

- `src/repodossier/scanner.py`
- `src/repodossier/models.py`
- `src/repodossier/exporters/full.py`
- `src/repodossier/exporters/ai.py`
- `src/repodossier/exporters/docs.py`
- `src/repodossier/changed_exporter.py`
- `tests/test_scanner.py`
- `tests/test_bash_source_detection.py`
- `tests/test_full_exporter.py`
- `tests/test_ai_exporter.py`
- `tests/test_changed_exporter.py`
- `README.md`

Akzeptanzkriterien:

- Klar ist, wo Language Detection aktuell implementiert ist.
- Klar ist, welche Sprachlabels aktuell genutzt werden.
- Klar ist, ob `FileInfo` oder ein anderes Modell Sprache als String speichert.
- Klar ist, welche Exporter direkt auf Language Labels zugreifen.
- Keine Annahme aus einem alten Dump wird ungeprüft übernommen.

## 2.0.b – Aktuelle Language-Detection-Funktion identifizieren

Ziel:
Die bestehende zentrale Erkennungsstelle finden.

Zu prüfen:

- Gibt es eine Funktion wie `detect_language(...)`?
- Ist die Erkennung direkt in `scan_file(...)` eingebaut?
- Wird nur über Dateiendung erkannt?
- Gibt es bereits Shebang-Erkennung für Bash?
- Gibt es bereits Codeblock-Language-Mapping?

Akzeptanzkriterien:

- Die künftige zentrale API ist bekannt.
- Bestehende Logik wird erweitert statt doppelt implementiert.
- Bash-Erkennung aus früheren Milestones bleibt erhalten.

## 2.0.c – Aktuelle Exportausgaben prüfen

Ziel:
Verstehen, wo neue Language Labels sichtbar werden müssen.

Zu prüfen:

- File Summary im `full.txt`
- Complete Source Export im `full.txt`
- kompakte Dateilisten im `ai.txt`
- Changed File Contents im `changed.txt`
- Documentation Export, falls dort Language Labels genutzt werden

Akzeptanzkriterien:

- Klar ist, welche Exporte neue Labels zeigen sollen.
- Keine unnötige Formatänderung wird geplant.
- Bestehende Überschriften bleiben stabil.

## 2.0.d – Bestehende Tests als Regression-Schutz markieren

Ziel:
Vor der Änderung wissen, welche Tests bestehendes Verhalten absichern.

Relevante Testbereiche:

- Scanner-Tests
- Bash Source Detection Tests
- Full Export Tests
- AI Export Tests
- Changed Export Tests
- README-Dokumentationstests

Akzeptanzkriterien:

- Bestehende Tests bleiben erhalten.
- Neue Tests werden semantisch passend einsortiert.
- Keine Tests werden nur deshalb gelöscht, weil neue Labels eingeführt werden.

---

# 2.1 – Language-Detection-Modell und API festlegen

## 2.1.a – Bestehendes Sprachmodell erfassen

Ziel:
Klären, ob RepoDossier Sprache nur als String oder bereits strukturiert speichert.

Zu prüfen:

- `FileInfo.language`
- mögliche `language`-Felder in Modellen
- Codeblock-Language-Mapping
- Ausgabeformat in File Summary

Akzeptanzkriterien:

- Bestehende Datenstruktur ist dokumentiert.
- Entscheidung ist getroffen, ob Milestone 2 bei einfachem String bleibt oder intern eine kleine Detection-Struktur ergänzt.
- Externe Ausgabe bleibt rückwärtskompatibel.

## 2.1.b – Optionales LanguageDetection-Modell planen

Ziel:
Eine interne Struktur für Score, Confidence und Reason vorbereiten, ohne die Exportausgabe unnötig aufzublähen.

Empfohlene Struktur:

```python
@dataclass(frozen=True)
class LanguageDetection:
    language: str
    confidence: str
    reason: str
    scores: dict[str, int]
```

Mögliche `confidence`-Werte:

- `high`
- `medium`
- `low`

Akzeptanzkriterien:

- Die Scanner-Ausgabe kann weiterhin `language: str` liefern.
- Tests können intern Gründe und Scores prüfen, falls das Modell eingeführt wird.
- Keine Exporter müssen plötzlich komplexe Score-Daten rendern.

## 2.1.c – Zentrale Funktion definieren

Ziel:
Language Detection soll an einer zentralen Stelle testbar sein.

Empfohlene API:

```python
detect_language(path: str | Path, content_sample: str | None = None) -> str
```

Oder bei strukturierter Variante:

```python
detect_language(path: str | Path, content_sample: str | None = None) -> LanguageDetection
```

Wichtig:

- `path` ist repository-relativ oder zumindest dateinamefähig.
- `content_sample` darf `None` sein.
- Die Funktion darf nicht selbst große Dateien lesen, wenn der Scanner bereits Inhalt/Sample hat.

Akzeptanzkriterien:

- Sprachlogik ist separat unit-testbar.
- Scanner kann die Funktion wiederverwenden.
- Exporter enthalten keine eigene Language Detection.

## 2.1.d – Sprachlabels festlegen

Ziel:
Einheitliche Labels für interne Ausgabe und Markdown-Codeblöcke festlegen.

Empfohlene Labels:

| Sprache | Internes Label | Markdown Code Fence |
| --- | --- | --- |
| Python | `python` | `python` |
| Bash/Shell | `bash` oder `shell` | `bash` |
| Markdown | `markdown` | `markdown` |
| TOML | `toml` | `toml` |
| YAML | `yaml` | `yaml` |
| JSON | `json` | `json` |
| INI | `ini` | `ini` |
| TypeScript | `typescript` | `typescript` |
| TSX | `tsx` oder `typescript` | `tsx` |
| JavaScript | `javascript` | `javascript` |
| JSX | `jsx` oder `javascript` | `jsx` |
| HTML | `html` | `html` |
| CSS | `css` | `css` |
| Java | `java` | `java` |
| C | `c` | `c` |
| C++ | `cpp` | `cpp` |
| C# | `csharp` | `csharp` |
| Text | `text` | `text` |
| Unknown | `unknown` | leer oder `text` |

Akzeptanzkriterien:

- Labels sind dokumentiert.
- Codeblock-Languages sind sinnvoll für Markdown-Renderer.
- Bestehende Labels werden nicht unnötig umbenannt.
- `c#` wird nicht als Markdown-Fence genutzt, sondern z. B. `csharp`.

---

# 2.2 – Aktuelle Extension-Erkennung bereinigen und erweitern

## 2.2.a – Bestehende Extension-Mapping-Tabelle finden oder anlegen

Ziel:
Alle Dateiendungen an einer Stelle pflegen.

Umsetzung:

- Falls Mapping bereits existiert: erweitern.
- Falls Mapping verstreut ist: vorsichtig zentralisieren.
- Keine große Architekturverschiebung erzwingen.

Akzeptanzkriterien:

- Extension-Erkennung ist übersichtlich.
- Neue Sprachen können ohne Exporter-Anpassung ergänzt werden.
- Bestehende Sprachen bleiben erhalten.

## 2.2.b – TypeScript-Dateiendungen ergänzen

Zu erkennen:

- `.ts`
- `.tsx`

Erwartete Labels:

- `.ts` -> `typescript`
- `.tsx` -> `tsx` oder `typescript`, je nach gewählter Label-Strategie

Akzeptanzkriterien:

- TypeScript-Dateien erscheinen in File Summary als TypeScript.
- Source Export nutzt sinnvolle Codeblock-Language.

## 2.2.c – JavaScript-Dateiendungen ergänzen

Zu erkennen:

- `.js`
- `.jsx`
- `.mjs`
- `.cjs`

Erwartete Labels:

- `.js` -> `javascript`
- `.jsx` -> `jsx` oder `javascript`
- `.mjs` -> `javascript`
- `.cjs` -> `javascript`

Akzeptanzkriterien:

- JavaScript-Dateien erscheinen in File Summary als JavaScript.
- CommonJS und ESM werden nicht als unknown behandelt.

## 2.2.d – HTML-Dateiendungen ergänzen

Zu erkennen:

- `.html`
- `.htm`

Akzeptanzkriterien:

- HTML-Dateien erscheinen als HTML.
- HTML-Codeblöcke nutzen `html`.

## 2.2.e – CSS-Dateiendungen ergänzen

Zu erkennen:

- `.css`

Akzeptanzkriterien:

- CSS-Dateien erscheinen als CSS.
- CSS-Codeblöcke nutzen `css`.

## 2.2.f – Java-Dateiendung ergänzen

Zu erkennen:

- `.java`

Akzeptanzkriterien:

- Java-Dateien erscheinen als Java.
- Java-Codeblöcke nutzen `java`.

## 2.2.g – C-Dateiendungen ergänzen

Zu erkennen:

- `.c`
- `.h`, falls Inhalt klar C ist

Akzeptanzkriterien:

- `.c` wird als C erkannt.
- `.h` wird nicht blind immer als C klassifiziert, wenn C++-Hinweise vorliegen.

## 2.2.h – C++-Dateiendungen ergänzen

Zu erkennen:

- `.cpp`
- `.cc`
- `.cxx`
- `.hpp`
- `.hh`
- `.hxx`
- `.h`, falls Inhalt klar C++ ist

Akzeptanzkriterien:

- C++-Dateien erscheinen als C++.
- C++-Codeblöcke nutzen `cpp`.
- Header-Erkennung bleibt konservativ.

## 2.2.i – C#-Dateiendung ergänzen

Zu erkennen:

- `.cs`

Akzeptanzkriterien:

- C#-Dateien erscheinen als C# oder CSharp.
- Markdown-Codeblock nutzt `csharp`.

## 2.2.j – Extensionless bekannte Dateien absichern

Zu erkennen wie bisher:

- `README`
- `LICENSE`
- `COPYING`
- `NOTICE`
- `CHANGELOG`
- `Makefile`
- `Dockerfile`

Akzeptanzkriterien:

- Bestehende extensionless Erkennung regressiert nicht.
- `Makefile` wird nicht durch generische Inhaltsheuristik falsch überschrieben.

---

# 2.3 – Shebang-Erkennung einführen oder erweitern

## 2.3.a – Shebang-Zeile robust extrahieren

Ziel:
Die erste Zeile einer Textdatei auswerten, ohne große Dateien vollständig neu zu lesen.

Regeln:

- Nur erste Zeile prüfen.
- UTF-8 mit Fehlerbehandlung verwenden, falls nötig.
- Binary-Dateien nicht analysieren.
- Whitespace vor Shebang normalerweise nicht als gültiger Shebang werten.

Akzeptanzkriterien:

- `#!/usr/bin/env python3` wird erkannt.
- `#!/bin/bash` wird erkannt.
- Datei ohne Shebang crasht nicht.
- Leere Datei crasht nicht.

## 2.3.b – Python-Shebang erkennen

Zu erkennen:

- `#!/usr/bin/env python`
- `#!/usr/bin/env python3`
- `#!/usr/bin/python`
- `#!/usr/bin/python3`

Akzeptanzkriterien:

- Extensionless Python-Skripte werden als Python erkannt.
- Shebang gewinnt gegenüber fehlender oder unklarer Extension.

## 2.3.c – Bash-/Shell-Shebang erkennen

Zu erkennen:

- `#!/usr/bin/env bash`
- `#!/bin/bash`
- `#!/usr/bin/bash`
- `#!/bin/sh`
- `#!/usr/bin/env sh`

Akzeptanzkriterien:

- Extensionless Shell-Skripte werden erkannt.
- Bestehende Bash-Support-Tests bleiben grün.

## 2.3.d – Node-/JavaScript-Shebang erkennen

Zu erkennen:

- `#!/usr/bin/env node`
- `#!/usr/bin/node`

Akzeptanzkriterien:

- Extensionless Node-Skripte werden als JavaScript erkannt.
- Shebang wird höher gewichtet als generischer Text.

## 2.3.e – Shebang vor Extension priorisieren, wenn eindeutig

Ziel:
Wenn ein Shebang eindeutig ist, soll er stärker zählen als die Dateiendung.

Beispiele:

- Datei `script` mit Python-Shebang -> Python.
- Datei `deploy` mit Bash-Shebang -> Bash.
- Datei `tool.txt` mit Python-Shebang -> Python oder mindestens high-confidence Python, falls Projektstil das erlaubt.

Akzeptanzkriterien:

- Eindeutiger Shebang gewinnt.
- Unbekannter Shebang führt nicht zu falscher Sprache.

---

# 2.4 – Content-Heuristiken und Score-System

## 2.4.a – Score-basiertes Grundsystem einführen

Ziel:
Dateiendung, Shebang und Inhaltsmerkmale deterministisch zusammenführen.

Prinzip:

- Jede Sprache bekommt Punkte.
- Shebang gibt sehr viele Punkte.
- Extension gibt viele Punkte.
- eindeutige Inhaltsmerkmale geben mittlere bis hohe Punkte.
- schwache Inhaltsmerkmale geben wenige Punkte.
- Negative Signale können Fehlklassifikationen verhindern.

Beispiel-Gewichtung:

- eindeutiger Shebang: +100
- eindeutige Extension: +50
- eindeutiges Inhaltsmerkmal: +20
- schwaches Inhaltsmerkmal: +5
- Konfliktsignal: -20

Akzeptanzkriterien:

- Scores sind deterministisch.
- Tests können typische Fälle reproduzierbar prüfen.
- Bei Gleichstand wird konservativ entschieden.

## 2.4.b – Confidence aus Scores ableiten

Ziel:
Optional intern sichtbar machen, wie sicher die Erkennung ist.

Mögliche Regeln:

- `high`: eindeutiger Shebang oder Extension plus passende Inhalte
- `medium`: Extension oder mehrere passende Inhaltssignale
- `low`: nur schwache Inhaltssignale
- unsicher: `text` oder `unknown`

Akzeptanzkriterien:

- Confidence wird nicht zwingend exportiert.
- Tests können konservative Entscheidungen prüfen.
- Kein Nutzer bekommt falsche Sicherheit angezeigt.

## 2.4.c – Tie-Breaking-Regeln definieren

Ziel:
Bei mehreren ähnlichen Scores keine zufällige Ausgabe erzeugen.

Regeln:

1. Eindeutiger Shebang gewinnt.
2. Eindeutige Extension gewinnt bei schwachem Inhalt.
3. Eindeutiger Inhalt kann mehrdeutige Extension korrigieren.
4. Bei knappem Abstand: `text` oder `unknown`.
5. Bei `.h`: spezieller C/C++-Headerpfad.

Akzeptanzkriterien:

- Sortierung und Ergebnis sind stabil.
- Tests hängen nicht von Dictionary-Reihenfolge ab.

## 2.4.d – Content-Sample begrenzen

Ziel:
Language Detection soll auch bei großen Dateien schnell bleiben.

Regeln:

- Nur Anfang der Datei analysieren, z. B. erste 8 KB oder erste 200 Zeilen.
- Scanner darf bereits gelesenen Inhalt wiederverwenden.
- Keine zweite vollständige Datei-Lesung erzwingen.

Akzeptanzkriterien:

- Große Dateien führen nicht zu unnötiger Last.
- Truncation-/Limit-Logik bleibt unverändert.

---

# 2.5 – Heuristiken für bestehende Sprachen absichern

## 2.5.a – Python-Heuristiken ergänzen

Signale:

- `def name(...):`
- `async def name(...):`
- `class Name:`
- `import ...`
- `from ... import ...`
- `if __name__ == "__main__":`
- Python-Shebang

Akzeptanzkriterien:

- Python per Extension bleibt erkannt.
- Python per Shebang ohne Extension wird erkannt.
- Python per typischem Inhalt kann erkannt werden, wenn keine Extension vorhanden ist.

## 2.5.b – Bash-/Shell-Heuristiken ergänzen

Signale:

- Bash-/Shell-Shebang
- `set -euo pipefail`
- `set -eu`
- `function name { ... }`
- `name() { ... }`
- häufige Shell-Kommandostrukturen, aber konservativ

Akzeptanzkriterien:

- Bestehende Bash-Support-Erkennung regressiert nicht.
- Shell-Skripte ohne `.sh` werden erkannt, wenn Shebang vorhanden ist.

## 2.5.c – Markdown-Heuristiken absichern

Signale:

- `.md` / `.markdown`
- viele Markdown-Überschriften `#`, `##`
- Markdown-Listen
- fenced code blocks

Akzeptanzkriterien:

- README-Dateien bleiben Markdown.
- Markdown wird nicht wegen Codeblock-Inhalten als Python/JS fehlklassifiziert.

## 2.5.d – JSON-Heuristik absichern

Signale:

- `.json`
- Inhalt beginnt mit `{` oder `[` und ist JSON-typisch
- doppelte Quotes bei Keys

Wichtig:

- JSON darf nicht als JavaScript klassifiziert werden, nur weil `{}` und `:` vorkommen.

Akzeptanzkriterien:

- `package.json` wird als JSON erkannt.
- JSON mit Objekt/Array wird nicht JavaScript.
- Ungültiges JSON muss nicht vollständig geparst werden, aber darf nicht crashen.

## 2.5.e – YAML-Heuristik absichern

Signale:

- `.yml` / `.yaml`
- `key: value`
- Listen mit `- item`
- GitHub Actions YAML

Wichtig:

- YAML darf nicht wegen Doppelpunkten als TypeScript fehlklassifiziert werden.

Akzeptanzkriterien:

- `.github/workflows/*.yml` bleibt YAML.
- YAML/Text-Grenzfälle bleiben konservativ.

## 2.5.f – TOML- und INI-Heuristiken absichern

TOML-Signale:

- `.toml`
- `[project]`
- `[tool.*]`
- `key = "value"`

INI-Signale:

- `.ini`
- `.cfg`
- `[section]`
- `key=value`

Akzeptanzkriterien:

- `pyproject.toml` bleibt TOML.
- INI/CFG-Dateien bleiben INI oder Text je nach bestehendem Verhalten.

---

# 2.6 – Heuristiken für neue Web-Sprachen

## 2.6.a – TypeScript-Heuristiken einführen

Starke Signale:

- `.ts`
- `.tsx`
- `interface Name`
- `type Name = ...`
- `enum Name`
- Typannotationen wie `name: string`
- `public`, `private`, `readonly` in TypeScript-Kontext
- `import ... from "..."` plus TypeScript-spezifische Signale

Abgrenzung zu JavaScript:

- Wenn `.ts` oder `.tsx`, TypeScript bevorzugen.
- Wenn nur JS-Signale ohne Typ-Signale, JavaScript bevorzugen.

Akzeptanzkriterien:

- `.ts` wird TypeScript.
- Inhalt mit `interface` und Typannotationen wird TypeScript.
- YAML mit `key: value` wird nicht TypeScript.

## 2.6.b – JavaScript-Heuristiken einführen

Signale:

- `.js`, `.jsx`, `.mjs`, `.cjs`
- `import ... from "..."`
- `export default`
- `module.exports`
- `require("...")`
- `function name(...)`
- `const name = (...) => ...`
- Node-Shebang

Akzeptanzkriterien:

- `.js` wird JavaScript.
- `.mjs` und `.cjs` werden JavaScript.
- Extensionless Node-Skript mit Shebang wird JavaScript.
- JSON wird nicht JavaScript.

## 2.6.c – HTML-Heuristiken einführen

Signale:

- `.html`, `.htm`
- `<!DOCTYPE html>`
- `<html>`
- `<head>`
- `<body>`
- `<script>`
- `<link rel="stylesheet">`

Akzeptanzkriterien:

- HTML-Dateien werden erkannt.
- HTML-Fragmente können erkannt werden, wenn genügend eindeutige Tags vorhanden sind.
- XML oder Markdown mit HTML-Beispiel wird nicht aggressiv falsch erkannt.

## 2.6.d – CSS-Heuristiken einführen

Signale:

- `.css`
- `selector { property: value; }`
- `@media`
- `@import`
- `@keyframes`
- CSS-Eigenschaften wie `display:`, `margin:`, `color:`, `font-size:` innerhalb von `{}`

Akzeptanzkriterien:

- `.css` wird CSS.
- Inhalt mit typischer CSS-Struktur wird CSS.
- JSON/YAML mit `{}` oder `:` wird nicht CSS.

---

# 2.7 – Heuristiken für Java, C, C++ und C#

## 2.7.a – Java-Heuristiken einführen

Signale:

- `.java`
- `package com.example;`
- `import java...;`
- `public class Name`
- `interface Name`
- `enum Name`
- `record Name`
- `public static void main`

Akzeptanzkriterien:

- `.java` wird Java.
- Java-Inhalt ohne Extension kann bei eindeutigen Signalen Java werden.
- C# mit `namespace` wird nicht Java, wenn C#-Signale stärker sind.

## 2.7.b – C-Heuristiken einführen

Signale:

- `.c`
- `#include <stdio.h>`
- `#include "..."`
- `int main(`
- `typedef struct`
- `struct Name`
- C-ähnliche Funktionsdefinitionen

Akzeptanzkriterien:

- `.c` wird C.
- Typische C-Dateien werden C.
- C++-Dateien mit `std::`, `namespace`, `template` werden nicht C.

## 2.7.c – C++-Heuristiken einführen

Signale:

- `.cpp`, `.cc`, `.cxx`, `.hpp`, `.hh`, `.hxx`
- `#include <iostream>`
- `#include <vector>`
- `namespace Name`
- `class Name`
- `template <...>`
- `std::`
- `using namespace`

Akzeptanzkriterien:

- C++-Dateiendungen werden C++.
- Typische C++-Inhalte werden C++.
- Header mit C++-Merkmalen werden C++.

## 2.7.d – C#-Heuristiken einführen

Signale:

- `.cs`
- `using System;`
- `namespace Name`
- `public class Name`
- `interface Name`
- `enum Name`
- `record Name`
- `async Task`
- Attribute wie `[Serializable]`, `[Test]`, `[Fact]`

Akzeptanzkriterien:

- `.cs` wird C# / CSharp.
- C#-Codeblock nutzt `csharp`.
- Java und C# werden bei typischem Inhalt nicht verwechselt.

## 2.7.e – `.h` Header-Dateien konservativ behandeln

Ziel:
`.h` kann C oder C++ sein.

Regeln:

- Wenn `namespace`, `class`, `template`, `std::`, `using namespace` vorkommt: eher C++.
- Wenn `typedef struct`, `#include <stdio.h>`, C-Funktionssignaturen ohne C++-Merkmale vorkommen: eher C.
- Wenn beide ähnlich stark oder kaum Signale vorhanden sind: `text`, `unknown`, `c-header`, `cpp-header` oder konservativer bestehender Fallback.

Empfehlung für erste Version:

- Intern nur `c` oder `cpp` nutzen, wenn der Inhalt klar genug ist.
- Bei Unsicherheit nicht hart behaupten.

Akzeptanzkriterien:

- C-Header mit `typedef struct` wird C.
- C++-Header mit `namespace`/`class`/`template` wird C++.
- Leerer Header bleibt konservativ.

---

# 2.8 – Konfliktfälle und False-Positive-Schutz

## 2.8.a – JSON vs JavaScript absichern

Problem:
JSON sieht syntaktisch teilweise wie JavaScript aus.

Regeln:

- `.json` hat starken JSON-Score.
- JSON-ähnlicher Inhalt mit quoted keys bleibt JSON oder Text.
- JavaScript braucht JS-spezifische Signale wie `import`, `export`, `function`, `const`, `require`, `module.exports`.

Tests:

- `package.json` -> JSON
- `{ "scripts": { "build": "vite" } }` -> JSON
- `const config = {}` -> JavaScript

Akzeptanzkriterien:

- JSON wird nicht fälschlich als JavaScript klassifiziert.

## 2.8.b – YAML vs TypeScript absichern

Problem:
Doppelpunkte kommen in YAML und TypeScript vor.

Regeln:

- `.yml` / `.yaml` bleibt YAML.
- TypeScript-Typannotationen zählen nur in passendem Kontext, z. B. `const name: string` oder Funktionsparameter.
- Einfache `key: value`-Zeilen reichen nicht für TypeScript.

Tests:

- GitHub Actions YAML bleibt YAML.
- `const name: string = "x";` wird TypeScript.

Akzeptanzkriterien:

- YAML wird nicht fälschlich als TypeScript klassifiziert.

## 2.8.c – Markdown mit Codeblöcken absichern

Problem:
Markdown-Dateien enthalten oft Code aus anderen Sprachen.

Regeln:

- `.md` bleibt Markdown.
- README bleibt Markdown.
- Inhalte innerhalb fenced code blocks sollen nicht die gesamte Datei umklassifizieren.

Tests:

- README mit Python-Codeblock bleibt Markdown.
- Markdown mit HTML-Beispiel bleibt Markdown.

Akzeptanzkriterien:

- Dokumentation wird nicht wegen Beispielen falsch klassifiziert.

## 2.8.d – HTML vs XML/Text konservativ behandeln

Problem:
XML oder Template-Dateien können HTML-ähnlich sein.

Regeln:

- `.html` / `.htm` klar HTML.
- Inhalt mit `<!DOCTYPE html>` oder `<html>` stark HTML.
- Einzelne Tags ohne HTML-Kontext reichen nicht zwingend.

Akzeptanzkriterien:

- HTML wird erkannt.
- Beliebige XML-/Textdatei mit einem Tag wird nicht automatisch HTML.

## 2.8.e – CSS vs JSON/YAML konservativ behandeln

Problem:
CSS nutzt `{}` und `:`.

Regeln:

- CSS braucht Selektor plus Blockstruktur oder CSS-At-Rules.
- JSON/YAML-Strukturen bleiben JSON/YAML.

Akzeptanzkriterien:

- CSS wird erkannt.
- JSON/YAML wird nicht CSS.

## 2.8.f – Unsichere Fälle bewusst als text/unknown lassen

Ziel:
Keine Scheingenauigkeit.

Regeln:

- Wenn Score-Abstand zu klein ist: `text` oder `unknown`.
- Wenn Inhalt sehr kurz ist und Extension unbekannt: `text`.
- Wenn Datei leer ist: `text` oder `unknown`, je nach bestehendem Verhalten.

Akzeptanzkriterien:

- Unklare Datei bleibt konservativ.
- Tests prüfen mindestens einen unklaren Fall.

---

# 2.9 – Scanner-Integration

## 2.9.a – Scanner nutzt zentrale Detection-Funktion

Ziel:
FileInfo oder vergleichbare Scanner-Ausgabe soll neue Language Detection verwenden.

Umsetzung:

- In `scan_file(...)` oder passender Funktion Content-Sample an Detection übergeben.
- Shebang und Heuristiken nur für Textdateien ausführen.
- Binary-Dateien bleiben binary/skipped.

Akzeptanzkriterien:

- FileInfo enthält neues Sprachlabel.
- Scanner liest Dateien nicht unnötig doppelt.
- Binary-Erkennung bleibt unverändert sicher.

## 2.9.b – Bestehende FileInfo-Felder stabil halten

Ziel:
Keine unnötigen Modellbrüche.

Akzeptanzkriterien:

- Tests, die `FileInfo.language` prüfen, bleiben sinnvoll.
- Exporter müssen nicht groß umgebaut werden.
- Neue interne Detection-Metadaten sind optional.

## 2.9.c – Codeblock-Language-Mapping prüfen

Ziel:
Source Export soll sinnvolle Markdown-Codeblock-Languages nutzen.

Beispiele:

- `typescript` -> ```typescript
- `javascript` -> ```javascript
- `html` -> ```html
- `css` -> ```css
- `java` -> ```java
- `c` -> ```c
- `cpp` -> ```cpp
- `csharp` -> ```csharp

Akzeptanzkriterien:

- Markdown-Codefences sind gültig und nützlich.
- Unknown/Text erzeugt keine kaputte Fence-Language.

---

# 2.10 – Full Export Integration

## 2.10.a – File Summary mit neuen Sprachen prüfen

Ziel:
`full.txt` soll neue Sprachen in der File Summary gruppieren.

Beispiele:

```text
## TypeScript (2 files)
- `src/app.ts` — ...

## JavaScript (1 file)
- `scripts/build.js` — ...

## C++ (1 file)
- `src/main.cpp` — ...
```

Akzeptanzkriterien:

- Neue Sprachen erscheinen lesbar.
- Sortierung bleibt deterministisch.
- Bestehende File Summary regressiert nicht.

## 2.10.b – Complete Source Export nutzt neue Codefences

Ziel:
Quellcodeblöcke im `full.txt` sollen passende Language-Fences haben.

Akzeptanzkriterien:

- `.ts` nutzt TypeScript-Fence.
- `.js` nutzt JavaScript-Fence.
- `.html` nutzt HTML-Fence.
- `.css` nutzt CSS-Fence.
- `.java`, `.c`, `.cpp`, `.cs` nutzen passende Fences.

## 2.10.c – Warnings unverändert lassen

Ziel:
Language Detection darf nicht unnötig Warnings erzeugen.

Akzeptanzkriterien:

- Unsichere Sprache ist kein Fehler.
- Keine neuen lauten Warnings bei normalen Repositories.

---

# 2.11 – AI Export, Docs Export und Changed Export Integration

## 2.11.a – AI Export prüft neue Labels

Ziel:
`ai.txt` soll neue Sprachlabels dort korrekt übernehmen, wo Dateien, wichtige Dateien oder kompakte Source-Kontexte angezeigt werden.

Akzeptanzkriterien:

- Important Files oder andere AI-Dateilisten zeigen sinnvolle Sprache, falls dort Sprache ausgegeben wird.
- Keine unnötige Vergrößerung des AI Exports.
- AI Export bleibt kompakt.

## 2.11.b – Docs Export bleibt documentation-only

Ziel:
Docs Export soll durch neue Language Detection nicht plötzlich Quellcode aufnehmen.

Akzeptanzkriterien:

- `docs.txt` bleibt auf Dokumentationsdateien fokussiert.
- Markdown-Erkennung bleibt stabil.
- README/SPEC/architecture bleiben Dokumentation.

## 2.11.c – Changed Export nutzt neue Labels

Ziel:
`changed.txt` soll bei geänderten neuen Dateitypen passende Labels und Codefences nutzen.

Akzeptanzkriterien:

- Geänderte `.ts`, `.js`, `.html`, `.css`, `.java`, `.c`, `.cpp`, `.cs` Dateien werden sinnvoll markiert.
- Diff- und Changed-Content-Abschnitte bleiben kompatibel.

---

# 2.12 – Unit Tests für Language Detection

## 2.12.a – Neue Testdatei oder bestehende Scanner-Tests erweitern

Empfehlung:

- Neue Datei: `tests/test_language_detection.py`

Alternative:

- Semantisch passende Erweiterung von `tests/test_scanner.py`

Akzeptanzkriterien:

- Tests sind übersichtlich gruppiert.
- Keine unzusammenhängenden Tests blind ans Ende großer Dateien anhängen.

## 2.12.b – Regression-Tests für bestehende Sprachen

Testfälle:

- Python per `.py`
- Python per Shebang ohne Extension
- Bash per `.sh`
- Bash per Shebang ohne Extension
- Markdown per `.md`
- README ohne Extension
- TOML per `pyproject.toml`
- YAML per `.yml`
- JSON per `.json`
- INI per `.ini` oder `.cfg`, falls bisher unterstützt
- Plain text per `.txt`

Akzeptanzkriterien:

- Bestehende Sprachen bleiben erkannt.
- Bash- und Python-Shebangs funktionieren.

## 2.12.c – Tests für TypeScript

Testfälle:

- `.ts` Datei wird TypeScript.
- `.tsx` Datei wird TypeScript/TSX.
- Extensionless Inhalt mit `interface User { id: string }` wird TypeScript oder konservativ korrekt.
- YAML-ähnlicher Inhalt wird nicht TypeScript.

Akzeptanzkriterien:

- TypeScript wird explizit erkannt.
- False Positives bleiben begrenzt.

## 2.12.d – Tests für JavaScript

Testfälle:

- `.js` wird JavaScript.
- `.jsx` wird JavaScript/JSX.
- `.mjs` wird JavaScript.
- `.cjs` wird JavaScript.
- Node-Shebang ohne Extension wird JavaScript.
- JSON wird nicht JavaScript.

Akzeptanzkriterien:

- JavaScript wird explizit erkannt.
- JSON-Abgrenzung ist getestet.

## 2.12.e – Tests für HTML

Testfälle:

- `.html` wird HTML.
- `.htm` wird HTML.
- Inhalt mit `<!DOCTYPE html>` wird HTML.
- Inhalt mit `<html><head><body>` wird HTML.

Akzeptanzkriterien:

- HTML wird explizit erkannt.
- Kaputter/kurzer HTML-ähnlicher Text crasht nicht.

## 2.12.f – Tests für CSS

Testfälle:

- `.css` wird CSS.
- Inhalt mit `body { margin: 0; }` wird CSS.
- Inhalt mit `@media` wird CSS.
- JSON/YAML wird nicht CSS.

Akzeptanzkriterien:

- CSS wird explizit erkannt.
- False Positives bleiben begrenzt.

## 2.12.g – Tests für Java

Testfälle:

- `.java` wird Java.
- Inhalt mit `package`, `import java`, `public class` wird Java.
- Inhalt mit `public static void main` wird Java.

Akzeptanzkriterien:

- Java wird explizit erkannt.

## 2.12.h – Tests für C

Testfälle:

- `.c` wird C.
- Inhalt mit `#include <stdio.h>` und `int main(` wird C.
- Header mit `typedef struct` wird C, falls Header-Logik implementiert.

Akzeptanzkriterien:

- C wird explizit erkannt.

## 2.12.i – Tests für C++

Testfälle:

- `.cpp` wird C++.
- `.cc` wird C++.
- `.cxx` wird C++.
- `.hpp` wird C++.
- Header mit `namespace`, `class`, `template` oder `std::` wird C++.

Akzeptanzkriterien:

- C++ wird explizit erkannt.
- C/C++ Header-Abgrenzung funktioniert konservativ.

## 2.12.j – Tests für C#

Testfälle:

- `.cs` wird C# / CSharp.
- Inhalt mit `using System;`, `namespace`, `public class` wird C#.
- Inhalt mit `[Fact]` oder `async Task` wird C#.

Akzeptanzkriterien:

- C# wird explizit erkannt.
- Codeblock-Language ist `csharp`.

## 2.12.k – Tests für unklare Dateien

Testfälle:

- kurze Datei ohne Extension und ohne eindeutige Merkmale
- leerer Text
- `.h` ohne klare C/C++-Merkmale
- gemischter Inhalt mit knappem Score

Akzeptanzkriterien:

- Unsichere Fälle bleiben `text` oder `unknown`.
- Keine aggressive Fehlklassifikation.

---

# 2.13 – Export-Regressionstests

## 2.13.a – Full Export File Summary Test ergänzen

Ziel:
Full Export muss neue Sprachen sichtbar gruppieren.

Setup:

- Testrepository mit Dateien:
  - `src/app.ts`
  - `src/main.js`
  - `web/index.html`
  - `web/style.css`
  - `src/App.java`
  - `src/main.c`
  - `src/main.cpp`
  - `src/App.cs`

Akzeptanzkriterien:

- File Summary enthält neue Sprachgruppen.
- Pfade werden korrekt angezeigt.
- Bestehende Gruppen bleiben erhalten.

## 2.13.b – Full Export Code Fence Test ergänzen

Ziel:
Complete Source Export nutzt passende Codeblock-Languages.

Akzeptanzkriterien:

- TypeScript-Datei steht in TypeScript-Fence.
- JavaScript-Datei steht in JavaScript-Fence.
- HTML-Datei steht in HTML-Fence.
- CSS-Datei steht in CSS-Fence.
- Java/C/C++/C# nutzen passende Fences.

## 2.13.c – Changed Export Test ergänzen

Ziel:
Changed Export übernimmt neue Language Labels für geänderte Dateien.

Akzeptanzkriterien:

- `changed.txt` enthält geänderte neue Dateitypen.
- Codefences sind sinnvoll.
- Deleted/Binary-Verhalten bleibt unverändert.

## 2.13.d – AI Export Regression prüfen

Ziel:
AI Export darf durch neue Language Detection nicht kaputtgehen.

Akzeptanzkriterien:

- `export-ai` läuft mit neuen Dateitypen.
- Ausgabe bleibt kompakt.
- Keine neuen Sprachen führen zu Exceptions.

## 2.13.e – Docs Export Regression prüfen

Ziel:
Docs Export bleibt unverändert fokussiert.

Akzeptanzkriterien:

- README bleibt Dokumentation.
- Source-Dateien werden nicht wegen neuer Sprachlabels in docs exportiert.

---

# 2.14 – README und Dokumentation aktualisieren

## 2.14.a – README Supported files aktualisieren

Ziel:
README soll neue unterstützte Sprachen nennen.

Ergänzen:

- TypeScript
- JavaScript
- HTML
- CSS
- Java
- C
- C++
- C#

Akzeptanzkriterien:

- README widerspricht nicht mehr dem neuen Stand.
- Bestehende Supported-files-Liste bleibt verständlich.

## 2.14.b – README Language Detection beschreiben

Ziel:
Nutzer sollen verstehen, dass RepoDossier content-aware erkennt.

Zu dokumentieren:

- Dateiendungen bleiben wichtig.
- Shebangs werden erkannt.
- Inhaltsheuristiken werden genutzt.
- Unsichere Fälle werden konservativ behandelt.
- Keine Parser/Compiler/Build-Tools werden ausgeführt.

Akzeptanzkriterien:

- README beschreibt das Verhalten ohne Überversprechen.
- Sicherheitsgrenze „keine Code-Ausführung“ bleibt sichtbar.

## 2.14.c – Roadmap/Planning-Hinweis aktualisieren, falls nötig

Ziel:
Milestone 2 soll in `planning/1.1.0/` liegen und zur Roadmap passen.

Akzeptanzkriterien:

- `planning/1.1.0/milestone2.md` existiert.
- `planning/README.md` muss nur geändert werden, wenn die aktive 1.1.0-Struktur dort ergänzt werden soll.
- `planning/roadmap_next.md` muss nicht umgeschrieben werden, wenn er weiter korrekt ist.

## 2.14.d – README Tests aktualisieren

Ziel:
Dokumentationsregressionen vermeiden.

Tests:

- README erwähnt Content-aware Language Detection.
- README erwähnt neue Sprachen.
- README erwähnt Shebangs oder Inhaltsheuristiken.
- README behauptet keine vollständige Parser-Analyse.

Akzeptanzkriterien:

- Dokumentationstests bleiben grün.

---

# 2.15 – Abschlussprüfung

## 2.15.a – Syntaxprüfung ausführen

Befehl:

```bash
python3 -m compileall src tests
```

Akzeptanzkriterien:

- Keine Syntaxfehler.

## 2.15.b – Vollständige Testsuite ausführen

Befehl:

```bash
python3 -m pytest --color=yes
```

Akzeptanzkriterien:

- Alle Tests grün.
- Neue Language-Detection-Tests grün.
- Export-Regressionstests grün.

## 2.15.c – RepoDossier CLI Smoke Checks ausführen

Befehle:

```bash
repodossier --version
repodossier --help
repodossier full
repodossier export-ai
repodossier export-docs
repodossier changed
```

Legacy-Alias prüfen:

```bash
repocontext --version
repocontext --help
```

Akzeptanzkriterien:

- CLI funktioniert weiterhin.
- Exporte werden erzeugt.
- Kein Befehl crasht wegen neuer Language Detection.

## 2.15.d – Exporte kurz prüfen

Zu prüfen:

- `full.txt` enthält neue Sprachgruppen, sofern Testdateien oder Projektdateien vorhanden sind.
- Codefences wirken korrekt.
- `ai.txt` bleibt kompakt.
- `docs.txt` bleibt docs-only.
- `changed.txt` funktioniert weiterhin.

Akzeptanzkriterien:

- Exportausgaben sind plausibel.
- Keine self-reference durch generierte Dateien.

## 2.15.e – Git Status und Diff prüfen

Befehle:

```bash
git status --short
git --no-pager diff --stat
git --no-pager diff -- README.md pyproject.toml src tests planning
```

Akzeptanzkriterien:

- Nur erwartete Dateien geändert.
- Keine generierten Exportdateien versehentlich committet.
- Keine TASKS.md-Änderung, sofern nicht ausdrücklich gewünscht.

## 2.15.f – Commit erstellen

Empfohlene Commit-Nachricht:

```text
Add content-aware language detection
```

Akzeptanzkriterien:

- Commit enthält Code, Tests und Dokumentation.
- Arbeitsbaum ist danach sauber oder enthält nur bewusst uncommitted lokale Artefakte.

---

# 2.16 – Empfohlene Patch-Reihenfolge

## Patch 2.1 – Detection-Grundstruktur und bestehende Regressionen

Umfang:

- zentrale Detection-Funktion identifizieren oder einführen
- bestehende Sprachlabels absichern
- Regressionstests für Python, Bash, Markdown, TOML, YAML, JSON, INI, Text
- keine neuen Sprachen außer vielleicht vorbereitende Mapping-Struktur

Ziel:

- Sichere Basis, bevor neue Sprachen ergänzt werden.

## Patch 2.2 – Shebang-Erkennung

Umfang:

- Python-Shebang
- Bash-/Shell-Shebang
- Node-/JavaScript-Shebang
- Tests für extensionless Skripte

Ziel:

- Eindeutige Skripte ohne Dateiendung werden korrekt erkannt.

## Patch 2.3 – Extension-Mapping für neue Sprachen

Umfang:

- TypeScript Extensions
- JavaScript Extensions
- HTML/CSS Extensions
- Java/C/C++/C# Extensions
- Codeblock-Language-Mapping
- Unit Tests

Ziel:

- Die neuen Sprachen funktionieren bereits dateiendungsbasiert.

## Patch 2.4 – Content-Heuristiken und Score-System

Umfang:

- Score-System
- Content-Heuristiken für bestehende und neue Sprachen
- Confidence/Reason optional
- deterministisches Tie-Breaking

Ziel:

- Content-aware Erkennung funktioniert ohne vollständige Parser.

## Patch 2.5 – Konfliktfälle und konservative Fallbacks

Umfang:

- JSON vs JavaScript
- YAML vs TypeScript
- Markdown mit Codeblöcken
- HTML/XML/Text-Konflikte
- CSS/JSON/YAML-Konflikte
- unklare Dateien bleiben text/unknown

Ziel:

- Qualität statt aggressiver Fehlklassifikation.

## Patch 2.6 – Exportintegration

Umfang:

- Full Export File Summary
- Complete Source Export Codefences
- Changed Export Labels
- AI Export Regression
- Docs Export Regression

Ziel:

- Neue Language Detection ist in den Nutzeroutputs sichtbar.

## Patch 2.7 – README, Doku und Abschlussprüfung

Umfang:

- README Supported Files aktualisieren
- Content-aware Language Detection dokumentieren
- README Tests aktualisieren
- vollständige Testsuite
- CLI Smoke Checks
- Commit

Ziel:

- Milestone 2 ist abschließbar.

---

# 2.17 – Definition of Done

Milestone 2 ist fertig, wenn alle folgenden Punkte erfüllt sind:

1. Es gibt eine zentrale, testbare Language-Detection-Logik.
2. Dateiendungen werden weiterhin erkannt.
3. Shebangs werden erkannt.
4. Inhaltsheuristiken werden ausgewertet.
5. Die Erkennung ist deterministisch.
6. Unsichere Fälle werden konservativ behandelt.
7. Python-Erkennung regressiert nicht.
8. Bash-/Shell-Erkennung regressiert nicht.
9. Markdown-Erkennung regressiert nicht.
10. TOML-Erkennung regressiert nicht.
11. YAML-Erkennung regressiert nicht.
12. JSON-Erkennung regressiert nicht.
13. INI/Text-Erkennung regressiert nicht.
14. TypeScript wird explizit erkannt.
15. JavaScript wird explizit erkannt.
16. HTML wird explizit erkannt.
17. CSS wird explizit erkannt.
18. Java wird explizit erkannt.
19. C wird explizit erkannt.
20. C++ wird explizit erkannt.
21. C# wird explizit erkannt.
22. `.h` Header werden konservativ als C oder C++ erkannt, wenn eindeutig.
23. JSON wird nicht unnötig als JavaScript fehlklassifiziert.
24. YAML wird nicht unnötig als TypeScript fehlklassifiziert.
25. Markdown mit Codeblöcken bleibt Markdown.
26. Leere oder unklare Dateien crashen nicht.
27. File Summary zeigt neue Sprachen korrekt.
28. Source Export nutzt passende Codeblock-Languages.
29. Changed Export nutzt passende Language Labels.
30. AI Export läuft weiterhin stabil und kompakt.
31. Docs Export bleibt documentation-only.
32. README dokumentiert die neuen Sprachsupports.
33. README dokumentiert Shebangs und Inhaltsheuristiken.
34. README überverspricht keine vollständige Parser-/Compiler-Analyse.
35. Unit Tests für neue Language Detection sind vorhanden.
36. Export-Regressionstests sind vorhanden.
37. Die vollständige Testsuite ist grün.
38. CLI Smoke Checks funktionieren.
39. Es gibt einen Commit für die Umsetzung.

---

# 2.18 – Hinweise für spätere Milestones

Milestone 2 liefert nur bessere Sprachmetadaten.

Spätere Milestones können darauf aufbauen:

- Milestone 3: Internes strukturiertes Export-Modell übernimmt Language Labels.
- Milestone 4: MarkdownRenderer rendert Language Labels aus dem Modell.
- Milestone 5: XMLRenderer gibt Language Labels strukturiert aus.
- Milestone 6: Optionale Zeilennummern nutzen korrekte Codeblock-Languages.
- Milestone 9: Tieferer Sprachsupport nutzt die Erkennung als Einstieg für Symbol-, Import- und Call-Analyse.

Wichtig:

- In Milestone 2 keine tiefe Analyse vorziehen.
- Keine Parser-/Compiler-Integration erzwingen.
- Die Erkennung soll bewusst klein, robust und deterministisch bleiben.
