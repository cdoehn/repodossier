MILESTONE 8 – AI Export

Ziel:
RepoContext erzeugt zusätzlich zu full.txt einen kompakten, KI-optimierten Export ai.txt.
ai.txt soll nicht den kompletten Source-Dump ersetzen, sondern eine verdichtete Orientierung für LLMs liefern:
- Was ist das Projekt?
- Welche Dateien sind wichtig?
- Welche Symbole gibt es?
- Wie hängen Module/Imports zusammen?
- Welche Funktionen/Methoden rufen sich gegenseitig auf?

Wichtig:
- Use RepoContext CLI exports for final checks; do not use deprecated snapshot scripts.
- Milestone-Dateien nicht als Fortschrittswahrheit benutzen.
- Fortschritt aus Code, Tests und aktuellem full.txt ableiten.
- TASKS.md nur anfassen, wenn ausdrücklich verlangt.
- Tests semantisch passend einsortieren, nicht einfach ans Dateiende hängen.
- Bei Implementierung wie gewohnt Python-Heredoc-Patchblöcke mit Tests und Commit.

====================================================================
8.0 – Bestandsprüfung vor Implementierung
====================================================================

8.0.a – Prüfen, wo Exporter aktuell sitzen
Ziel:
Ermitteln, welche bestehende Exportstruktur für full.txt genutzt wird.

Zu prüfen:
- CLI-Kommandos / Entry Points
- full.txt Exporter
- vorhandene Summary-/Tree-/Source-Dump-Renderer
- vorhandene Symbol-Index-Struktur aus Milestone 5
- vorhandene Import-Graph-Struktur aus Milestone 6
- vorhandene Call-Graph-Struktur aus Milestone 7

Ergebnis:
Klarheit, ob ai.txt als eigener Exporter oder als Modus des bestehenden Exporters implementiert werden soll.

Empfehlung:
Eigener AI-Exporter, aber Wiederverwendung bestehender Scanner-/Graph-/Symbol-Funktionen.

Mögliche Dateien:
- repocontext/cli.py
- repocontext/exporters/full_exporter.py
- repocontext/exporters/__init__.py
- repocontext/symbols.py oder ähnliches
- repocontext/import_graph.py oder ähnliches
- repocontext/call_graph.py oder ähnliches
- tests/test_full_exporter.py
- neue Tests: tests/test_ai_exporter.py


====================================================================
8.1 – AI Exporter Grundstruktur
====================================================================

8.1.a – Eigenen ai.txt Exporter anlegen
Ziel:
Eine zentrale Funktion/Klasse für den AI Export schaffen.

Soll enthalten:
- Exportpfad ai.txt
- deterministische Ausgabe
- klar getrennte Sektionen
- keine vollständigen Quelltexte
- Wiederverwendung bestehender Repo-Daten

Vorgeschlagene Struktur in ai.txt:

# AI CONTEXT

## Project
...

## Architecture Summary
...

## Important Files
...

## Symbol Index
...

## Import Graph
...

## Call Graph
...

## Notes
...

Akzeptanzkriterien:
- ai.txt kann programmatisch erzeugt werden.
- Ausgabe ist stabil sortiert.
- Leere Daten führen nicht zu Fehlern.
- Keine Duplikate.
- Keine Source-Dump-Massen wie in full.txt.


8.1.b – Minimalen Smoke-Test für ai.txt-Erzeugung
Ziel:
Absichern, dass der Exporter eine Datei schreibt.

Testfall:
- kleines temporäres Repo
- 1 Python-Datei
- Export ausführen
- ai.txt existiert
- ai.txt enthält "# AI CONTEXT"
- ai.txt enthält Sektionen für Architecture Summary, Important Files, Symbol Index, Import Graph, Call Graph

Akzeptanzkriterien:
- Test grün
- ai.txt wird nicht leer erzeugt


====================================================================
8.2 – Architecture Summary
====================================================================

8.2.a – Architecture Summary Renderer implementieren
Ziel:
Eine kurze Projektübersicht generieren.

Inhalt:
- erkannte Projektart, soweit möglich
- zentrale Entry-Points
- Paket-/Modulstruktur
- wichtigste Top-Level-Verzeichnisse
- Hinweis auf CLI, Tests, Dokumentation, falls vorhanden

Beispiel:

## Architecture Summary

This repository appears to be a Python CLI project.

Main entry points:
- repocontext/cli.py

Core areas:
- Repository discovery
- File scanning
- Full export generation
- Symbol extraction
- Import graph analysis
- Call graph analysis

Tests:
- tests/

Akzeptanzkriterien:
- Funktioniert auch ohne README.
- Funktioniert auch bei kleinen Repos.
- Nutzt vorhandene Datei-/Tree-/Scanner-Daten.
- Keine Halluzinationen: Nur aus vorhandenen Dateien ableiten.


8.2.b – Tests für Architecture Summary
Ziel:
Absichern, dass sinnvolle Architekturhinweise erscheinen.

Testfälle:
- Repo mit pyproject.toml und CLI-Datei
- Repo ohne pyproject.toml
- Repo mit tests/
- Repo mit package/src-Struktur

Akzeptanzkriterien:
- Summary enthält vorhandene zentrale Dateien.
- Summary behauptet nichts, was nicht aus dem Repo ableitbar ist.


====================================================================
8.3 – Important Files
====================================================================

8.3.a – Important Files Heuristik implementieren
Ziel:
Wichtige Dateien für LLM-Kontext priorisieren.

Erste Ranking-Regeln:
1. pyproject.toml, setup.py, requirements.txt
2. README.md, ARCHITECTURE.md, SPEC.md, TASKS.md
3. CLI-/Entrypoint-Dateien
4. Dateien mit vielen Symbolen
5. Dateien mit vielen eingehenden Imports
6. Dateien mit hoher Call-Graph-Relevanz
7. Tests zu Kernmodulen

Ausgabeformat:

## Important Files

- pyproject.toml
  Reason: Python project configuration.

- repocontext/cli.py
  Reason: CLI entry point.

- repocontext/exporters/full_exporter.py
  Reason: Export pipeline implementation.

Akzeptanzkriterien:
- deterministische Reihenfolge
- begrenzte Ausgabe, z. B. Top 20
- nachvollziehbare Gründe
- keine Binärdateien
- keine generierten Exporte wie full.txt/ai.txt/docs.txt/changed.txt


8.3.b – Tests für Important Files
Ziel:
Ranking stabil absichern.

Testfälle:
- pyproject.toml wird bevorzugt
- README.md wird erkannt
- CLI-Datei wird erkannt
- generierte Exportdateien werden ausgeschlossen
- Sortierung bleibt stabil

Akzeptanzkriterien:
- Tests zeigen, dass wichtige Dateien oben landen.
- Keine zufällige Reihenfolge durch Sets/Dicts.


====================================================================
8.4 – Symbol Index Integration
====================================================================

8.4.a – Symbol Index in ai.txt einbauen
Ziel:
Vorhandene Symbol-Extraktion aus Milestone 5 im AI Export anzeigen.

Ausgabeformat:

## Symbol Index

### repocontext/cli.py
- function main
- function build_parser

### repocontext/scanner.py
- class FileInfo
- function scan_repository

Akzeptanzkriterien:
- Klassen, Funktionen und Methoden erscheinen.
- Gruppierung nach Datei.
- Sortierung stabil.
- Bei fehlenden Symbolen erscheint ein kurzer Hinweis statt Fehler.


8.4.b – Symbol Index Tests
Ziel:
Absichern, dass Symbole korrekt und kompakt im AI Export auftauchen.

Testfälle:
- Python-Datei mit Klasse
- Python-Datei mit Funktion
- Python-Datei mit Methode
- Datei ohne Symbole
- Syntaxfehlerhafte Datei darf Export nicht crashen, falls bestehendes Verhalten das vorsieht

Akzeptanzkriterien:
- ai.txt enthält relevante Symbolnamen.
- Methoden werden nicht doppelt als freie Funktionen gezählt, falls das Projekt das bisher trennt.


====================================================================
8.5 – Import Graph Integration
====================================================================

8.5.a – Import Graph in ai.txt einbauen
Ziel:
Vorhandenen Import Graph aus Milestone 6 kompakt darstellen.

Ausgabeformat:

## Import Graph

- repocontext/cli.py
  imports:
  - repocontext.exporters.full_exporter
  - repocontext.git

- repocontext/exporters/full_exporter.py
  imports:
  - repocontext.scanner
  - repocontext.symbols

Akzeptanzkriterien:
- interne Imports werden bevorzugt.
- externe Imports können optional separat erscheinen.
- Leere Imports werden kompakt behandelt.
- Ausgabe ist stabil sortiert.


8.5.b – Import Graph Tests
Ziel:
Absichern, dass vorhandene Importdaten korrekt in ai.txt landen.

Testfälle:
- Datei importiert internes Modul
- Datei importiert externes Modul
- relative Imports
- Datei ohne Imports

Akzeptanzkriterien:
- ai.txt zeigt interne Abhängigkeiten verständlich.
- Keine rohen Python-Objekt-Repräsentationen.


====================================================================
8.6 – Call Graph Integration
====================================================================

8.6.a – Call Graph in ai.txt einbauen
Ziel:
Vorhandenen Call Graph aus Milestone 7 kompakt darstellen.

Ausgabeformat:

## Call Graph

- repocontext.cli.main
  calls:
  - repocontext.cli.build_parser
  - repocontext.exporters.ai_exporter.export_ai_context

- repocontext.scanner.scan_repository
  calls:
  - repocontext.scanner.scan_file

Akzeptanzkriterien:
- Call Graph wird nicht zu lang.
- Ausgabe ist begrenzt, z. B. Top N Callers oder pro Datei maximal N Calls.
- Bei leerem Call Graph erscheint ein Hinweis.
- Method Calls werden so angezeigt, wie sie Milestone 7 aktuell modelliert.


8.6.b – Call Graph Tests
Ziel:
Absichern, dass Calls lesbar im AI Export erscheinen.

Testfälle:
- Funktion ruft Funktion auf
- Methode ruft Methode auf
- mehrere Calls werden stabil sortiert
- keine Calls führt zu sauberer leerer Sektion

Akzeptanzkriterien:
- ai.txt enthält Caller und Callee.
- Keine Duplikate.
- Keine instabile Reihenfolge.


====================================================================
8.7 – CLI / Pipeline Integration
====================================================================

8.7.a – ai.txt in normalen Exportlauf integrieren
Ziel:
RepoContext soll ai.txt regulär erzeugen können.

Zu klären aus bestehendem Code:
- Gibt es bereits einen Standardbefehl, der full.txt erzeugt?
- Gibt es Unterkommandos?
- Gibt es bereits Exportoptionen?

Mögliche Varianten:
1. Standardlauf erzeugt full.txt und ai.txt.
2. Neuer expliziter Befehl:
   repocontext export-ai
3. Bestehender Exportbefehl bekommt Option:
   repocontext export --ai

Empfehlung:
Wenn full.txt aktuell automatisch erzeugt wird, ai.txt ebenfalls im normalen Exportlauf erzeugen.
Zusätzlich kann ein direkter CLI-Pfad sinnvoll sein, falls die Architektur das schon unterstützt.

Akzeptanzkriterien:
- Nutzer kann ai.txt ohne Sonderwissen erzeugen.
- Bestehende full.txt-Erzeugung bleibt unverändert grün.
- Bestehende CLI-Tests bleiben grün.


8.7.b – CLI Tests
Ziel:
Absichern, dass ai.txt über die CLI entsteht.

Testfälle:
- CLI-Lauf erzeugt ai.txt
- ai.txt enthält AI CONTEXT
- bestehende full.txt-Erzeugung bleibt erhalten
- Use RepoContext CLI exports for final checks; do not use deprecated snapshot scripts.

Akzeptanzkriterien:
- CLI-Test grün
- keine Regression in bestehenden Tests


====================================================================
8.8 – Export-Hygiene und .gitignore
====================================================================

8.8.a – Prüfen, ob ai.txt bereits in .gitignore behandelt wird
Ziel:
Milestone 4 hatte Auto-add für ai.txt vorgesehen. In Milestone 8 muss nur geprüft werden, ob das praktisch funktioniert.

Akzeptanzkriterien:
- ai.txt wird nicht versehentlich versioniert.
- Falls Auto-add-Mechanismus existiert, ai.txt wird berücksichtigt.
- Keine unnötige Änderung, wenn bereits korrekt.


8.8.b – Tests für Exportausschluss
Ziel:
Absichern, dass ai.txt nicht selbst wieder als Input in Exporte einfließt.

Testfälle:
- ai.txt existiert bereits
- neuer Export läuft
- ai.txt wird nicht als Important File aufgenommen
- ai.txt wird nicht im Symbol/Import/Call-Kontext analysiert, falls generierte Dateien ausgeschlossen werden sollen

Akzeptanzkriterien:
- Kein Self-Reference-Loop.
- Kein wachsender Export durch vorherigen Export.


====================================================================
8.9 – Gesamtvalidierung
====================================================================

8.9.a – Vollständiger Testlauf
Ziel:
Alle bestehenden Tests plus neue AI-Export-Tests laufen lassen.

Befehl bei Umsetzung:
python3 -m pytest --color=yes

Zusätzlich sinnvoll:
repocontext --version
repocontext info
repocontext normaler Exportlauf, je nach vorhandener CLI

Akzeptanzkriterien:
- Alle Tests grün.
- ai.txt wird erzeugt.
- full.txt bleibt funktional.
- Keine Regression in Symbol-, Import- oder Call-Graph-Tests.


8.9.b – Manuelle Prüfung von ai.txt
Ziel:
ai.txt auf praktische Nutzbarkeit für LLMs prüfen.

Checkliste:
- Ist die Datei kurz genug?
- Erkennt man sofort die Architektur?
- Sind wichtige Dateien gut begründet?
- Sind Symbol Index, Import Graph und Call Graph vorhanden?
- Ist die Ausgabe stabil und lesbar?
- Gibt es keine riesigen Source-Dumps?
- Gibt es keine generierten Exportdateien als wichtige Dateien?


====================================================================
Empfohlene Implementierungsreihenfolge
====================================================================

1. 8.1.a – AI Exporter Grundstruktur
2. 8.1.b – Minimaler ai.txt Smoke-Test
3. 8.2.a – Architecture Summary
4. 8.2.b – Architecture Summary Tests
5. 8.3.a – Important Files
6. 8.3.b – Important Files Tests
7. 8.4.a – Symbol Index Integration
8. 8.4.b – Symbol Index Tests
9. 8.5.a – Import Graph Integration
10. 8.5.b – Import Graph Tests
11. 8.6.a – Call Graph Integration
12. 8.6.b – Call Graph Tests
13. 8.7.a – CLI / Pipeline Integration
14. 8.7.b – CLI Tests
15. 8.8.a – Export-Hygiene / .gitignore prüfen
16. 8.8.b – Exportausschluss Tests
17. 8.9.a – Vollständiger Testlauf
18. 8.9.b – Manuelle ai.txt Prüfung


====================================================================
Definition of Done für Milestone 8
====================================================================

Milestone 8 ist fertig, wenn:

- ai.txt wird zuverlässig erzeugt.
- ai.txt enthält:
  - AI CONTEXT Header
  - Architecture Summary
  - Important Files
  - Symbol Index
  - Import Graph
  - Call Graph
- Die Ausgabe ist deterministisch.
- Die Ausgabe ist kompakt und LLM-freundlich.
- Bestehender full.txt Export funktioniert weiterhin.
- Generierte Exportdateien werden nicht versehentlich als wichtige Projektdateien behandelt.
- Alle bestehenden Tests sind grün.
- Neue Tests für AI Export sind grün.
- Es gibt einen Commit für die Umsetzung.
