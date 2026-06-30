# MILESTONE10 – Dependency Detection

## Ziel

RepoContext soll Projektabhängigkeiten automatisch erkennen und strukturiert im Export sichtbar machen.

Milestone 10 erweitert die Analyse um Dependency Detection für typische Python-Projekte.

Erkannt werden sollen insbesondere:

- Abhängigkeiten aus pyproject.toml
- Abhängigkeiten aus requirements.txt
- Runtime Dependencies
- Development Dependencies
- optionale / extra Dependencies, soweit sinnvoll
- eine kompakte Dependency-Zusammenfassung im Export

Der Fokus liegt auf robuster, statischer Analyse ohne Installation der Pakete.

---

## Ergebnis nach Abschluss

Nach Milestone 10 kann RepoContext:

1. Dependency-Dateien im Repository erkennen.
2. pyproject.toml analysieren.
3. requirements.txt analysieren.
4. Dependencies nach Typ klassifizieren.
5. Eine interne Dependency-Struktur erzeugen.
6. Dependency-Informationen in full.txt ausgeben.
7. Dependency-Informationen in ai.txt sinnvoll zusammenfassen.
8. Tests für die Dependency Detection bereitstellen.

---

# 10.1 Dependency-Modell einführen

## Ziel

Eine stabile interne Datenstruktur schaffen, mit der erkannte Dependencies unabhängig von ihrer Quelle weiterverarbeitet werden können.

## Aufgaben

### 10.1.a Dependency-Dataclasses oder Typed Structures erstellen

Neue Struktur für einzelne Dependencies einführen.

Eine Dependency sollte mindestens enthalten:

- Name
- Normalized Name
- Version Constraint
- Dependency Type
- Source File
- Source Section
- Raw Value

Beispiele:

- click >=8.0
- pytest >=8
- ruff ==0.6.0
- requests[security] >=2.31

Mögliche Typen:

- runtime
- development
- optional
- unknown

### 10.1.b Dependency-Collection einführen

Eine übergeordnete Struktur einführen, die alle gefundenen Dependencies enthält.

Sie sollte enthalten:

- Liste aller Dependencies
- Liste gefundener Dependency-Dateien
- Parsing-Warnings
- unsupported requirement lines
- eventuell nicht unterstützte Sections

### 10.1.c Stabile Sortierung definieren

Dependencies sollen deterministisch sortiert werden.

Sortierung:

1. Dependency Type
2. Normalized Name
3. Source File
4. Raw Value

Das ist wichtig für stabile Tests und stabile Exporte.

---

# 10.2 pyproject.toml erkennen und analysieren

## Ziel

RepoContext soll pyproject.toml erkennen und relevante Dependency-Sections auslesen.

## Aufgaben

### 10.2.a pyproject.toml Discovery

Beim Scannen des Repositories soll geprüft werden, ob eine pyproject.toml vorhanden ist.

Die Datei soll nur analysiert werden, wenn sie als Textdatei lesbar ist.

### 10.2.b PEP-621 Dependencies lesen

Folgende Standardbereiche analysieren:

```toml
[project]
dependencies = []
optional-dependencies = {}
```

Zuordnung:

- project.dependencies -> runtime
- project.optional-dependencies.* -> optional

### 10.2.c Poetry Dependencies lesen

Falls vorhanden, folgende Poetry-Bereiche analysieren:

```toml
[tool.poetry.dependencies]
[tool.poetry.group.dev.dependencies]
[tool.poetry.dev-dependencies]
```

Zuordnung:

- tool.poetry.dependencies -> runtime
- tool.poetry.group.dev.dependencies -> development
- tool.poetry.dev-dependencies -> development

Hinweis:

- Python selbst soll nicht als normale Dependency behandelt werden.
- Beispiel: python = "^3.12" ignorieren oder separat als Python Requirement behandeln.

### 10.2.d Optional weitere Poetry Groups unterstützen

Poetry-Gruppen wie diese erkennen:

```toml
[tool.poetry.group.test.dependencies]
[tool.poetry.group.docs.dependencies]
[tool.poetry.group.lint.dependencies]
```

Zuordnung:

- dev, test, docs, lint -> development
- andere Gruppen -> optional

### 10.2.e Parsing robust machen

Ungültige oder nicht lesbare TOML-Dateien dürfen RepoContext nicht abbrechen lassen.

Stattdessen:

- Warning erfassen
- Export weiterlaufen lassen
- Dependency-Liste leer oder teilweise gefüllt ausgeben

---

# 10.3 requirements.txt analysieren

## Ziel

RepoContext soll klassische requirements.txt-Dateien erkennen und auswerten.

## Aufgaben

### 10.3.a requirements.txt Discovery

Mindestens folgende Dateien erkennen:

- requirements.txt
- requirements-dev.txt
- dev-requirements.txt
- requirements_test.txt
- requirements-test.txt
- requirements-docs.txt
- docs-requirements.txt
- requirements-lint.txt
- lint-requirements.txt
- Dateien unter requirements/*.txt

### 10.3.b Dependency-Typ aus Dateiname ableiten

Zuordnung:

- requirements.txt -> runtime
- Dateien mit dev, test, lint, docs im Namen -> development
- sonstige requirements-Dateien -> unknown

### 10.3.c Einfache Requirements parsen

Folgende Formen unterstützen:

```txt
requests
requests>=2.31
click==8.1.7
pytest ~=8.0
```

Zu erfassen:

- Name
- Constraint
- Raw Value
- Source File

### 10.3.d Kommentare und Leerzeilen ignorieren

Ignorieren:

```txt
# comment

requests>=2
```

Inline-Kommentare nach Möglichkeit entfernen:

```txt
requests>=2 # needed for API
```

### 10.3.e Nicht-Paket-Zeilen behandeln

Folgende Zeilen nicht als normale Dependency aufnehmen, aber als Warning oder unsupported erfassen:

```txt
-r other-requirements.txt
-c constraints.txt
--index-url https://example.com
-e .
git+https://example.com/project.git
```

Für Milestone 10 reicht es, solche Zeilen robust zu erkennen und nicht falsch zu parsen.

Rekursives Auflösen von -r other.txt ist ausdrücklich kein Pflichtteil von Milestone 10.

---

# 10.4 Dependency-Namen normalisieren

## Ziel

Gleiche Dependencies sollen vergleichbar sein.

## Aufgaben

### 10.4.a Namen kanonisieren

Namen normalisieren:

- lowercase
- _ zu -
- . zu -
- mehrere Trennzeichen vereinheitlichen

Beispiele:

- Google_Auth -> google-auth
- my.package -> my-package
- My__Package -> my-package

### 10.4.b Originalwert behalten

Neben dem normalisierten Namen muss der Originalwert erhalten bleiben.

Wichtig für Export und Debugging:

- raw_value
- name
- normalized_name

### 10.4.c Doppelte Dependencies nachvollziehbar lassen

Wenn dieselbe Dependency mehrfach vorkommt, nicht hart deduplizieren.

Beispiel:

- pytest aus pyproject.toml als development
- pytest aus requirements-dev.txt als development

Beide sollen nachvollziehbar bleiben, weil Quelle und Constraint unterschiedlich sein können.

---

# 10.5 Dependency Analyzer in Export Pipeline integrieren

## Ziel

Die Dependency Detection soll automatisch beim Erzeugen der Exporte laufen.

## Aufgaben

### 10.5.a Analyzer-Modul erstellen

Vorgeschlagene Datei:

```text
src/repocontext/dependencies.py
```

Alternativ passend zur bestehenden Projektstruktur.

Das Modul sollte eine zentrale Funktion anbieten, z. B.:

```python
analyze_dependencies(repo_root, files) -> DependencyReport
```

### 10.5.b Full Export erweitern

full.txt soll einen neuen Abschnitt bekommen.

Vorschlag:

```text
# Dependencies

## Summary

Runtime dependencies: X
Development dependencies: Y
Optional dependencies: Z
Unknown dependencies: N

## Dependency Files

- pyproject.toml
- requirements.txt

## Runtime Dependencies

- click >=8.0
- tomli

## Development Dependencies

- pytest >=8
- ruff

## Optional Dependencies

- docs: mkdocs

## Unsupported / Warnings

- requirements.txt: -r base.txt is not resolved
```

### 10.5.c AI Export erweitern

ai.txt soll eine kompakte, für KI nützliche Zusammenfassung bekommen.

Vorschlag:

```text
## Dependencies

Runtime:
- click
- tomli

Development:
- pytest
- ruff

Optional:
- docs: mkdocs

Detected files:
- pyproject.toml
- requirements.txt
```

### 10.5.d Keine Export-Abbrüche

Wenn Dependency Parsing fehlschlägt, müssen full.txt und ai.txt trotzdem erzeugt werden.

Warnings sollen sichtbar sein, aber nicht fatal.

---

# 10.6 CLI / Info-Ausgabe prüfen

## Ziel

Falls sinnvoll, Dependency-Informationen auch über bestehende CLI-Info-Ausgaben verfügbar machen.

## Aufgaben

### 10.6.a Bestehende CLI prüfen

Prüfen, ob repocontext info oder ähnliche Befehle bereits Projektanalyse ausgeben.

### 10.6.b Nur integrieren, wenn passend

Keine neue große CLI bauen, wenn es nicht zur bestehenden Struktur passt.

Falls passend, ergänzen:

```text
Dependency files: 2
Runtime dependencies: 5
Development dependencies: 4
Optional dependencies: 1
Unknown dependencies: 0
```

### 10.6.c Keine unnötige Scope-Ausweitung

Milestone 10 bleibt primär Export- und Analyse-Funktionalität.

---

# 10.7 Tests für pyproject.toml

## Ziel

Die TOML-basierte Dependency Detection absichern.

## Aufgaben

### 10.7.a Test für PEP-621 Runtime Dependencies

Testprojekt mit:

```toml
[project]
dependencies = [
  "click>=8",
  "requests>=2.31",
]
```

Erwartung:

- click erkannt
- requests erkannt
- Typ runtime
- Source File pyproject.toml
- Source Section project.dependencies

### 10.7.b Test für PEP-621 Optional Dependencies

Testprojekt mit:

```toml
[project.optional-dependencies]
dev = ["pytest>=8"]
docs = ["mkdocs"]
```

Erwartung:

- pytest erkannt
- mkdocs erkannt
- Typ optional
- Gruppen dev und docs nachvollziehbar

### 10.7.c Test für Poetry Dependencies

Testprojekt mit:

```toml
[tool.poetry.dependencies]
python = "^3.12"
click = "^8.1"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
```

Erwartung:

- click als runtime
- pytest als development
- python nicht als normale Dependency

### 10.7.d Test für weitere Poetry Groups

Testprojekt mit:

```toml
[tool.poetry.group.docs.dependencies]
mkdocs = "^1.6"

[tool.poetry.group.lint.dependencies]
ruff = "^0.6"

[tool.poetry.group.extra.dependencies]
rich = "^13"
```

Erwartung:

- mkdocs als development
- ruff als development
- rich als optional

### 10.7.e Test für ungültige TOML

Ungültige pyproject.toml.

Erwartung:

- kein Crash
- Warning vorhanden
- Export läuft weiter

---

# 10.8 Tests für requirements.txt

## Ziel

Die requirements-basierte Dependency Detection absichern.

## Aufgaben

### 10.8.a Test für einfache requirements.txt

Datei:

```txt
requests>=2.31
click==8.1.7
```

Erwartung:

- requests erkannt
- click erkannt
- Typ runtime

### 10.8.b Test für requirements-dev.txt

Datei:

```txt
pytest>=8
ruff
```

Erwartung:

- pytest erkannt
- ruff erkannt
- Typ development

### 10.8.c Test für Kommentare und Leerzeilen

Datei:

```txt
# comment
requests>=2

click # inline comment
```

Erwartung:

- nur requests
- nur click
- keine Kommentarzeilen als Dependencies

### 10.8.d Test für unsupported Lines

Datei:

```txt
-r base.txt
--index-url https://example.com/simple
-e .
git+https://example.com/example.git
```

Erwartung:

- kein Crash
- keine falschen Paketnamen
- Warning oder unsupported entries vorhanden

### 10.8.e Test für requirements-Unterordner

Dateien:

```text
requirements/base.txt
requirements/dev.txt
requirements/docs.txt
```

Erwartung:

- Dateien werden erkannt
- base.txt wird unknown oder runtime, je nach Implementationsentscheidung
- dev.txt wird development
- docs.txt wird development

---

# 10.9 Export-Regressionstests

## Ziel

Sicherstellen, dass Dependency Detection wirklich in den erzeugten Exporten sichtbar ist.

## Aufgaben

### 10.9.a full.txt enthält Dependency-Abschnitt

Ein Test soll prüfen:

- Dependencies-Abschnitt vorhanden
- Runtime Dependencies sichtbar
- Development Dependencies sichtbar
- erkannte Dependency-Dateien sichtbar
- Warnings sichtbar, falls vorhanden

### 10.9.b ai.txt enthält Dependency-Zusammenfassung

Ein Test soll prüfen:

- Dependency Summary vorhanden
- wichtige Runtime Dependencies sichtbar
- wichtige Development Dependencies sichtbar
- erkannte Dependency-Dateien sichtbar

### 10.9.c Export bleibt stabil ohne Dependency-Dateien

Repository ohne pyproject.toml und ohne requirements.txt.

Erwartung:

- kein Crash
- Export enthält entweder leeren Dependency-Abschnitt oder sinnvollen Hinweis
- bestehende Exporte bleiben kompatibel

---

# 10.10 Dokumentation aktualisieren

## Ziel

README und relevante Dokumentation sollen erklären, dass RepoContext Dependencies erkennt.

## Aufgaben

### 10.10.a README Feature-Liste ergänzen

Ergänzen:

```text
- Dependency detection from pyproject.toml and requirements.txt
```

### 10.10.b Export-Beispiel ergänzen

Falls README Beispielausgaben enthält, Dependency-Abschnitt ergänzen.

### 10.10.c Grenzen dokumentieren

Dokumentieren:

- keine Paketinstallation
- keine Netzwerkabfragen
- statische Analyse
- unsupported requirement lines werden nicht vollständig aufgelöst
- rekursive -r Includes optional/nicht zwingend in Milestone 10
- keine Lockfile-Analyse in diesem Milestone

---

# 10.11 Akzeptanzkriterien

Milestone 10 gilt als fertig, wenn alle folgenden Punkte erfüllt sind:

1. pyproject.toml wird erkannt.
2. PEP-621 project.dependencies wird erkannt.
3. PEP-621 project.optional-dependencies wird erkannt.
4. Poetry Runtime Dependencies werden erkannt.
5. Poetry Development Dependencies werden erkannt.
6. Weitere Poetry-Gruppen werden sinnvoll klassifiziert.
7. requirements.txt wird erkannt.
8. Dev/Test/Docs requirements-Dateien werden als Development Dependencies klassifiziert.
9. Kommentare und Leerzeilen in requirements-Dateien werden ignoriert.
10. Inline-Kommentare in requirements-Dateien werden korrekt behandelt.
11. Unsupported requirements-Zeilen führen nicht zu falschen Dependencies.
12. Ungültige Dependency-Dateien brechen den Export nicht ab.
13. Dependency-Namen werden normalisiert.
14. Originalwerte bleiben nachvollziehbar.
15. full.txt enthält Dependency-Informationen.
16. ai.txt enthält eine kompakte Dependency-Zusammenfassung.
17. Tests decken pyproject.toml ab.
18. Tests decken requirements.txt ab.
19. Export-Regressionstests sind vorhanden.
20. README oder passende Dokumentation ist aktualisiert.
21. Die komplette bestehende Testsuite bleibt grün.

---

# 10.12 Empfohlene Implementierungsreihenfolge

## Patch 10.1

Dependency-Modell und Analyzer-Grundstruktur.

Enthält:

- Dependency-Dataclasses
- DependencyReport
- Sortierung
- leere Analysefunktion
- erste Unit Tests

## Patch 10.2

pyproject.toml Analyse.

Enthält:

- PEP-621 Runtime Dependencies
- PEP-621 Optional Dependencies
- Poetry Runtime Dependencies
- Poetry Dev Dependencies
- Poetry Groups
- TOML Fehlerbehandlung
- Tests

## Patch 10.3

requirements.txt Analyse.

Enthält:

- requirements Discovery
- einfache Requirement-Zeilen
- Kommentarhandling
- Development-Dateityp-Erkennung
- unsupported Lines
- Tests

## Patch 10.4

Export-Integration in full.txt.

Enthält:

- neuer Dependencies-Abschnitt
- Summary
- Runtime/Development/Optional-Listen
- Warnings
- Regressionstests

## Patch 10.5

AI Export Integration.

Enthält:

- kompakte Dependency-Zusammenfassung in ai.txt
- sinnvolle Sortierung
- Regressionstests

## Patch 10.6

Dokumentation und Feinschliff.

Enthält:

- README Update
- eventuell CLI Info Update
- Stabilisierung
- komplette Testsuite

---

# 10.13 Nicht-Ziele für Milestone 10

Folgende Dinge gehören nicht zwingend zu Milestone 10:

- Installation oder Validierung von Paketen
- Netzwerkzugriff auf PyPI
- vollständige Resolver-Logik
- Lockfile-Analyse
- poetry.lock
- uv.lock
- pdm.lock
- rekursives vollständiges Auflösen von -r other.txt
- Sicherheitsanalyse von Dependencies
- Lizenzanalyse
- Dependency Vulnerability Scanning
- JavaScript package.json Support
- Node/npm/yarn/pnpm Support

Diese Themen können später eigene Milestones oder Erweiterungen werden.

---

# 10.14 Hinweise für spätere Milestones

Mögliche spätere Erweiterungen:

- Lockfile Detection
- Dependency Version Conflict Summary
- Vulnerability Summary
- License Summary
- Package Manager Detection
- uv Support
- pip-tools Support
- pdm Support
- poetry.lock Support
- JavaScript package.json Support
- Python import graph mit Dependency Mapping verbinden
