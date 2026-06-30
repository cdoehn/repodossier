Milestone 6 – Import Graph

Ziel:
RepoContext soll Python-Imports aus allen Projektdateien erkennen, auf lokale Module auflösen
und daraus einen Modul-Abhängigkeitsgraphen erzeugen. Das ist die Grundlage für spätere
AI-Exports, Important-File-Ranking und Call-Graph-Erweiterungen.

Nicht Teil von Milestone 6:
- Kein Call Graph. Das kommt in Milestone 7.
- Kein Dependency Detection aus pyproject.toml/requirements.txt. Das kommt in Milestone 10.
- Kein voll ausgebautes Ranking. Das kommt in Milestone 12.
- Kein ai.txt Export. Das kommt in Milestone 8.


6.1 Import-Analyse: AST Parser

6.1.a Import-Datenmodell anlegen
- Neue interne Struktur für einzelne Imports erstellen, z. B. ImportReference.
- Felder:
  - source_path
  - source_module
  - imported_module
  - imported_name
  - alias
  - import_type: "import" oder "from"
  - level für relative Imports
  - line_number
  - is_relative
  - is_local oder unresolved
- Ziel: Jeder einzelne Import wird sauber und testbar repräsentiert.

6.1.b AST-basierte Import-Erkennung implementieren
- Python-Dateien mit ast.parse einlesen.
- ast.Import erkennen:
  - import os
  - import pathlib as p
  - import package.module
- ast.ImportFrom erkennen:
  - from pathlib import Path
  - from .module import thing
  - from ..subpackage import helper
- Syntaxfehler sollen nicht den gesamten Export abbrechen.
- Bei SyntaxError Datei überspringen oder als Analysefehler sammeln.
- Ziel: robuste Import-Sammlung pro Datei.

6.1.c Edge Cases für Imports abdecken
- Mehrere Namen in einer Zeile:
  - import os, sys
  - from x import a, b as c
- Aliase:
  - import numpy as np
  - from pathlib import Path as P
- Relative Imports:
  - from .scanner import scan_files
  - from ..git import discover_repo
- Wildcard:
  - from module import *
- Ziel: Parser ist vollständig genug für normale Python-Projekte.

6.1.d Tests für reine Import-Erkennung schreiben
- Tests mit kleinen Code-Snippets.
- Erwartete ImportReference-Objekte prüfen.
- Keine echten Projektdateien nötig.
- Testfälle:
  - absolute imports
  - from imports
  - aliases
  - multiple imports
  - relative imports
  - wildcard imports
  - syntax error handling


6.2 Modulnamen und lokale Dateien auflösen

6.2.a Python-Dateien zu Modulnamen mappen
- Aus Repository-Dateipfaden Modulnamen ableiten.
- Beispiele:
  - src/repocontext/scanner.py -> repocontext.scanner
  - src/repocontext/__init__.py -> repocontext
  - tests/test_scanner.py -> tests.test_scanner
- src-Layout erkennen.
- Normales Root-Layout erkennen.
- Ziel: Jede lokale Python-Datei bekommt einen kanonischen Modulnamen.

6.2.b Lokale Modulauflösung für absolute Imports implementieren
- Import gegen bekannte lokale Module matchen.
- Beispiele:
  - import repocontext.scanner -> lokale Datei src/repocontext/scanner.py
  - from repocontext.git import discover_repo -> lokale Datei src/repocontext/git.py
- Nicht-lokale Imports bleiben unresolved/external.
- Ziel: Nur echte lokale Modulabhängigkeiten werden Graph-Kanten.

6.2.c Relative Imports korrekt auflösen
- Relative Imports anhand des source_module und level berechnen.
- Beispiele:
  - source repocontext.exporter
  - from .scanner import scan_files -> repocontext.scanner
  - from ..utils import x -> übergeordnetes Paket korrekt berechnen
- Ungültige relative Imports nicht crashen lassen.
- Ziel: Paketinterne Imports werden korrekt verbunden.

6.2.d Imports auf Datei-Ziele abbilden
- Wenn imported_module ein lokales Modul ist, Zielpfad setzen.
- Wenn imported_module ein lokales Paket ist, __init__.py als Ziel verwenden.
- Optional: from package import module ebenfalls erkennen, wenn module lokal existiert.
- Ziel: Graph kann später Datei-zu-Datei und Modul-zu-Modul darstellen.

6.2.e Tests für Modulauflösung schreiben
- Test-Projektstruktur künstlich anlegen.
- Prüfen:
  - src layout
  - package __init__.py
  - absolute local import
  - relative local import
  - external import bleibt external
  - unresolved import bleibt unresolved


6.3 Dependency Graph bauen

6.3.a Graph-Datenmodell anlegen
- Struktur für Modulabhängigkeiten erstellen, z. B. ImportGraph.
- Enthalten:
  - modules
  - edges
  - external_imports
  - unresolved_imports
  - errors
- Edge-Felder:
  - source_module
  - target_module
  - source_path
  - target_path
  - import_type
  - imported_name
  - line_number
- Ziel: Ein zentraler, später exportierbarer Graph.

6.3.b Graph Builder implementieren
- Alle gescannten Python-Dateien analysieren.
- Modulnamen berechnen.
- Imports sammeln.
- Lokale Kanten erzeugen.
- Externe/unresolved Imports getrennt sammeln.
- Ziel: Ein Funktionsaufruf erzeugt den kompletten Import Graph des Repos.

6.3.c Deduplizierung implementieren
- Gleiche Kanten nicht mehrfach ausgeben.
- Trotzdem optional mehrere Importstellen intern behalten oder line_number aggregieren.
- Ziel: Export bleibt kompakt und lesbar.

6.3.d Adjazenzlisten erzeugen
- depends_on:
  - Modul -> welche Module es importiert
- used_by:
  - Modul -> welche Module es importieren
- Ziel: Graph ist für Export und spätere Rankings nutzbar.

6.3.e Einfache Graph-Metriken ergänzen
- Anzahl lokaler Module
- Anzahl lokaler Kanten
- Anzahl externer Imports
- Anzahl unresolved Imports
- Optional:
  - root modules ohne lokale eingehende Kanten
  - leaf modules ohne lokale ausgehende Kanten
- Noch keine Centrality-Rankings. Das kommt später.

6.3.f Tests für kompletten Graph Builder schreiben
- Mini-Projekt mit mehreren Modulen.
- Prüfen:
  - Kanten A -> B
  - Kanten B -> C
  - externe Imports getrennt
  - unresolved Imports getrennt
  - keine Duplikate
  - depends_on und used_by korrekt


6.4 Integration in bestehenden Exporter

6.4.a Import Graph in bestehende Analyse-Pipeline einhängen
- Dort einbauen, wo aktuell Files, Summary und Symbol Index erzeugt werden.
- Nur Python-Dateien berücksichtigen.
- Fehler dürfen Export nicht abbrechen.
- Ziel: full.txt kann Import Graph Informationen enthalten.

6.4.b Kompakte Import-Graph-Sektion für full.txt erstellen
- Neue Sektion z. B.:

  ## Import Graph

  Summary:
  - Local modules: X
  - Local dependencies: Y
  - External imports: Z
  - Unresolved imports: N

  Local dependencies:
  - repocontext.cli -> repocontext.exporter
  - repocontext.exporter -> repocontext.scanner
  - repocontext.exporter -> repocontext.symbols

  External imports:
  - argparse
  - ast
  - pathlib

  Unresolved imports:
  - optional_missing_package

- Ziel: Milestone 6 ist sichtbar nutzbar, auch wenn ai.txt erst in Milestone 8 kommt.

6.4.c Ausgabe begrenzen und stabil sortieren
- Alphabetisch sortieren.
- Große Listen begrenzen, z. B. Top/erste 200 Kanten.
- Deterministische Ausgabe für Tests.
- Ziel: Snapshots und Tests bleiben stabil.

6.4.d Tests für full.txt Integration schreiben
- Export auf Fixture-Projekt laufen lassen.
- Prüfen:
  - Import Graph Sektion vorhanden
  - lokale Dependency sichtbar
  - externe Imports sichtbar
  - Ausgabe deterministisch


6.5 CLI/Info Integration, falls sinnvoll

6.5.a repocontext info optional erweitern
- Falls info aktuell Repository-Statistiken zeigt:
  - Python modules: X
  - Import dependencies: Y
- Nur machen, wenn es sauber zur bestehenden info-Ausgabe passt.
- Ziel: schnelle Sichtprüfung im Terminal.

6.5.b Keine neuen CLI-Kommandos erzwingen
- Kein separates import-graph Kommando nötig, außer Architektur ist bereits darauf vorbereitet.
- Milestone 6 soll primär Backend + Exportintegration liefern.


6.6 Fehlerbehandlung und Qualitätsregeln

6.6.a Analysefehler sammeln statt crashen
- SyntaxError
- UnicodeDecodeError
- unerwartete AST-Probleme
- Ziel: RepoContext bleibt robust bei gemischten Repos.

6.6.b Binär-/Nicht-Python-Dateien ignorieren
- Nur .py Dateien analysieren.
- Bereits vorhandene Scanner-Ergebnisse nutzen.
- Ziel: keine Doppelarbeit und keine unnötigen Fehler.

6.6.c Keine externen Pakete erzwingen
- AST reicht aus.
- Kein networkx.
- Keine Runtime-Import-Ausführung.
- Ziel: sicher, schnell, pipx-freundlich.

6.6.d Deterministische Ausgabe sicherstellen
- Sortierung nach source_module, target_module, line_number.
- Tests dürfen nicht von Dateisystem-Reihenfolge abhängen.


6.7 Test- und Qualitätsabschluss

6.7.a Unit Tests für Parser
- Import-Erkennung isoliert testen.

6.7.b Unit Tests für Resolver
- Pfad-zu-Modul und Import-zu-Modul testen.

6.7.c Unit Tests für Graph Builder
- Kompletten Graph aus Mini-Projekt testen.

6.7.d Exporter Tests erweitern
- full.txt enthält Import Graph.
- Export bleibt stabil.
- Bestehende Full Export Tests weiter grün.

6.7.e CLI Tests prüfen
- Nur erweitern, falls CLI-Ausgabe geändert wird.

6.7.f Gesamttests laufen lassen
- python3 -m pytest --color=yes

6.7.g Version/Info prüfen
- repocontext --version
- repocontext info

6.7.h Bundle erzeugen
- Use RepoContext CLI exports for project snapshots and final checks.


Empfohlene Implementierungs-Reihenfolge:

1. 6.1.a
2. 6.1.b
3. 6.1.c
4. 6.1.d
5. 6.2.a
6. 6.2.b
7. 6.2.c
8. 6.2.d
9. 6.2.e
10. 6.3.a
11. 6.3.b
12. 6.3.c
13. 6.3.d
14. 6.3.e
15. 6.3.f
16. 6.4.a
17. 6.4.b
18. 6.4.c
19. 6.4.d
20. 6.5.a nur falls passend
21. 6.6.a bis 6.6.d als Härtung
22. 6.7.a bis 6.7.h Abschluss


Sinnvolle Aufteilung in praktische Arbeitspakete:

Paket 1:
- 6.1.a bis 6.1.d
- Ergebnis: Import Parser funktioniert isoliert.

Paket 2:
- 6.2.a bis 6.2.e
- Ergebnis: lokale Module und relative Imports werden korrekt aufgelöst.

Paket 3:
- 6.3.a bis 6.3.f
- Ergebnis: vollständiger Import Graph wird gebaut.

Paket 4:
- 6.4.a bis 6.4.d
- Ergebnis: Import Graph erscheint stabil in full.txt.

Paket 5:
- 6.5 bis 6.7
- Ergebnis: Härtung, Tests, CLI-Check, Bundle.


Akzeptanzkriterien für Milestone 6:

- Python-Dateien werden per AST analysiert.
- import und from import werden erkannt.
- Aliase werden korrekt gespeichert.
- Relative Imports werden korrekt aufgelöst.
- Lokale Modulabhängigkeiten werden als Graph-Kanten erzeugt.
- Externe Imports werden getrennt von lokalen Imports behandelt.
- Unresolved Imports crashen nicht.
- Syntaxfehlerhafte Python-Dateien crashen nicht den Export.
- full.txt enthält eine Import Graph Sektion.
- Ausgabe ist deterministisch sortiert.
- Bestehende Tests bleiben grün.
- Neue Tests decken Parser, Resolver, Graph Builder und Exportintegration ab.
