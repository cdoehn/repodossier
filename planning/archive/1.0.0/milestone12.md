MILESTONE 12 – Important File Ranking

Ziel:
RepoContext soll eine robuste, nachvollziehbare und testbare Rangliste wichtiger Dateien erzeugen. Diese Rangliste soll nicht nur nach Dateinamen oder Heuristiken funktionieren, sondern mehrere Signale kombinieren:

- Entrypoints
- Import-Graph-Zentralität
- Call-Graph-Zentralität
- Dokumentationsrelevanz
- Projektstruktur
- bestehende Export-Nutzung in ai.txt / full.txt

Die Rangliste soll später besonders im AI Export helfen, damit wichtige Dateien weiter oben erscheinen und RepoContext für große Projekte bessere Kontext-Pakete erzeugt.

Quelle laut Roadmap:
Milestone 12 – Important File Ranking
- Entrypoint detection
- Import graph centrality
- Call graph centrality
- Documentation ranking
:contentReference[oaicite:0]{index=0}


1. Analyse des aktuellen Stands

1.1.a Prüfen, wo Important Files aktuell erzeugt werden
- Relevante Dateien suchen:
  - repocontext/exporters/ai.py
  - repocontext/exporters/full.py
  - repocontext/analyzers/*
  - tests/test_ai_exporter.py
  - tests/test_full_exporter.py
- Ziel:
  - Verstehen, ob Important Files aktuell nur heuristisch sortiert werden
  - Verstehen, ob Symbol Index, Import Graph, Call Graph und Dependencies bereits verfügbar sind
  - Verstehen, ob es schon eine interne Ranking-Funktion gibt

1.1.b Prüfen, welche Datenstrukturen bereits existieren
- Import Graph aus Milestone 6:
  - Welche Struktur liefert der Import Analyzer?
  - Gibt es Kanten Datei -> Datei oder Modul -> Modul?
  - Gibt es bereits Export-Modelle?
- Call Graph aus Milestone 7:
  - Welche Struktur liefert der Call Analyzer?
  - Gibt es Funktionsaufrufe mit Datei-Kontext?
- AI Export aus Milestone 8:
  - Wie wird Important Files aktuell aufgebaut?
  - Wo wird die Reihenfolge bestimmt?
- Documentation Export aus Milestone 9:
  - Welche Dokumentationsdateien werden erkannt?
- Dependency Detection aus Milestone 10:
  - Ob Abhängigkeiten Einfluss auf Entrypoints geben können
- Database Schema Extraction aus Milestone 11:
  - Ob Datenbankdateien oder Schema-Dateien eventuell als wichtige Dateien einfließen

1.1.c Bestehende Tests lesen
- Ziel:
  - Keine bestehenden Export-Erwartungen kaputtmachen
  - Sortierlogik nur dort ändern, wo Milestone 12 sie verbessern soll
  - Regression-Tests ergänzen statt bestehende Tests blind umzuschreiben


2. Datenmodell für Important File Ranking einführen

2.1.a Neue Ranking-Datenstruktur planen
- Sinnvoll wäre eine kleine interne Struktur, z. B.:
  - ImportantFileScore
    - path: str
    - score: float oder int
    - reasons: list[str]
    - signals:
      - entrypoint_score
      - import_centrality_score
      - call_centrality_score
      - documentation_score
      - structural_score
- Vorteil:
  - Tests können nicht nur Reihenfolge, sondern auch Gründe prüfen
  - Export kann später erklären, warum eine Datei wichtig ist
  - Ranking bleibt nachvollziehbar

2.1.b Ort der Implementierung festlegen
- Empfohlen:
  - repocontext/analyzers/important_files.py
- Alternativ, falls bestehende Struktur anders ist:
  - repocontext/ranking.py
  - repocontext/exporters/importance.py
- Wichtig:
  - Ranking nicht direkt hart in ai.py verstecken
  - Exporter sollen Ranking nur verwenden, nicht selbst alle Heuristiken enthalten

2.1.c Public/Internal API definieren
- Beispiel-Funktion:
  - rank_important_files(...)
- Mögliche Eingaben:
  - files
  - symbols
  - import_graph
  - call_graph
  - docs
  - project metadata
- Ausgabe:
  - sortierte Liste von ImportantFileScore oder vergleichbarer Struktur

2.1.d Deterministische Sortierung erzwingen
- Sortierung:
  1. score absteigend
  2. Pfadtiefe oder Kategorie
  3. Pfad alphabetisch
- Ziel:
  - Tests sind stabil
  - Exporte ändern sich nicht zufällig


3. Entrypoint Detection

3.1.a Python Entrypoints erkennen
- Zu erkennen:
  - __main__.py
  - main.py
  - cli.py
  - app.py
  - server.py
  - manage.py
  - wsgi.py
  - asgi.py
- Besonders wichtig für RepoContext:
  - CLI-Entrypoint aus pyproject.toml scripts
  - Module, die als Konsolenkommando konfiguriert sind

3.1.b pyproject.toml scripts auswerten
- Prüfen:
  - [project.scripts]
  - [tool.poetry.scripts], falls unterstützt oder sinnvoll
- Beispiel:
  - repocontext = "repocontext.cli:main"
- Daraus ableiten:
  - repocontext/cli.py bekommt EntryPoint-Score
  - Ziel-Funktion main bekommt ggf. Symbol-Relevanz

3.1.c Test für pyproject Entrypoint hinzufügen
- Testprojekt anlegen mit:
  - pyproject.toml
  - src/example/cli.py
- Erwartung:
  - cli.py steht hoch im Ranking
  - reason enthält sinngemäß "entrypoint" oder "project script"

3.1.d Test für __main__.py hinzufügen
- Testprojekt:
  - package/__main__.py
  - package/core.py
- Erwartung:
  - __main__.py bekommt Entrypoint-Punkte

3.1.e Test für klassische Dateinamen hinzufügen
- Dateien:
  - app.py
  - main.py
  - random_helper.py
- Erwartung:
  - app.py/main.py werden höher gerankt als reine Helper-Dateien


4. Import Graph Centrality

4.1.a Import-Eingangsgrad berechnen
- Signal:
  - Dateien, die von vielen anderen Dateien importiert werden, sind zentral
- Beispiel:
  - core.py wird von cli.py, exporter.py, scanner.py importiert
  - core.py bekommt höhere Import-Zentralität

4.1.b Import-Ausgangsgrad vorsichtig berücksichtigen
- Dateien, die viele andere importieren, sind nicht automatisch zentral
- Möglich:
  - kleiner Bonus für Koordinationsdateien
  - aber weniger Gewicht als Eingangsgrad
- Ziel:
  - Keine künstliche Überbewertung von Sammeldateien

4.1.c Transitive Zentralität optional vorbereiten
- Für Milestone 12 reicht wahrscheinlich einfacher Degree-Score
- Nicht überkomplizieren
- Optional:
  - PageRank-artige Logik später möglich
- Jetzt:
  - robuste einfache Metrik

4.1.d Pfadauflösung stabil machen
- Import Graph kann Modulnamen oder Pfade enthalten
- Ranking braucht möglichst Pfade
- Aufgabe:
  - Prüfen, ob bestehender Import Graph schon Pfade liefert
  - Falls nein: Mapping Modul -> Datei nutzen oder einfache bestehende Resolver-Funktion verwenden
- Keine große neue Resolver-Architektur bauen, wenn nicht nötig

4.1.e Tests für Import-Zentralität ergänzen
- Testprojekt:
  - cli.py importiert core
  - api.py importiert core
  - worker.py importiert core
  - core.py importiert nichts
- Erwartung:
  - core.py bekommt Import-Centrality-Reason
  - core.py steht höher als isolierte helper.py


5. Call Graph Centrality

5.1.a Datei-Zentralität aus Call Graph ableiten
- Signal:
  - Wenn viele Aufrufe in Funktionen einer Datei landen, ist diese Datei wichtig
- Beispiel:
  - cli.py ruft exporter.run()
  - tests oder andere Module rufen scanner.scan()
  - scanner.py / exporter.py bekommen Call-Zentralität

5.1.b Eingehende Calls stärker gewichten als ausgehende Calls
- Eingehende Calls:
  - Datei wird benutzt
  - zentraler Baustein
- Ausgehende Calls:
  - Datei orchestriert
  - kann auch wichtig sein, aber niedriger gewichten
- Gewichtung konservativ halten

5.1.c Methoden und Funktionen berücksichtigen
- Falls Call Graph Symbole enthält:
  - Symbol -> Datei auflösen
- Wenn Symbol nicht auflösbar:
  - Signal ignorieren statt Fehler werfen
- Ziel:
  - Ranking darf nie wegen unvollständigem Call Graph crashen

5.1.d Tests für Call-Zentralität ergänzen
- Testprojekt:
  - cli.py ruft service.run()
  - api.py ruft service.run()
  - worker.py ruft service.run()
- Erwartung:
  - service.py bekommt Call-Centrality-Reason
  - service.py wird höher gerankt als unbenutzte Datei

5.1.e Test für robuste Behandlung leerer Call Graphs
- Eingabe:
  - Dateien vorhanden
  - call_graph leer
- Erwartung:
  - Ranking funktioniert trotzdem
  - kein Absturz
  - andere Signale bleiben aktiv


6. Documentation Ranking

6.1.a Dokumentationsdateien erkennen
- Hoch ranken:
  - README.md
  - README.rst
  - ARCHITECTURE.md
  - SPEC.md
  - TASKS.md
  - ROADMAP.md
  - CHANGELOG.md
  - CONTRIBUTING.md
- Aber:
  - Dokumentation soll wichtige Code-Dateien nicht komplett verdrängen
  - README und ARCHITECTURE dürfen im AI-Kontext trotzdem weit oben erscheinen

6.1.b Dokumentationsgewicht differenzieren
- Mögliche Gewichtung:
  - README: sehr hoch
  - ARCHITECTURE/SPEC: hoch
  - TASKS/ROADMAP: mittel
  - CHANGELOG/CONTRIBUTING: niedriger
- Ziel:
  - AI Export bekommt zuerst Projektverständnis
  - Danach zentrale Code-Dateien

6.1.c Dokumentation im Unterordner erkennen
- Beispiele:
  - docs/architecture.md
  - docs/spec.md
  - docs/usage.md
- Ranking:
  - docs/architecture.md wichtiger als docs/random-note.md
- Heuristik:
  - Dateiname enthält architecture/spec/usage/overview/readme

6.1.d Tests für Dokumentationsranking ergänzen
- Testprojekt:
  - README.md
  - docs/architecture.md
  - docs/random.md
  - src/core.py
- Erwartung:
  - README.md und architecture.md bekommen Documentation-Reason
  - random.md bekommt keinen oder geringeren Score

6.1.e Dokumentationsranking mit bestehendem docs.txt Export abstimmen
- Wichtig:
  - Milestone 9 bleibt unverändert funktionsfähig
  - docs.txt muss nicht neu sortiert werden, außer es ist bereits Teil der Architektur
  - Milestone 12 fokussiert primär Important Files / AI-Relevanz


7. Structural Ranking

7.1.a Projektstruktur-Heuristiken ergänzen
- Wichtige Strukturdateien:
  - pyproject.toml
  - setup.py
  - setup.cfg
  - requirements.txt
  - package.json, falls generisch unterstützt
  - Dockerfile, falls vorhanden
  - Makefile, falls vorhanden
- Gewicht:
  - pyproject.toml hoch
  - requirements.txt mittel
  - reine Lockfiles eher niedrig oder ignorieren

7.1.b Package-Initialisierer nicht überbewerten
- __init__.py kann wichtig sein, ist aber oft leer
- Heuristik:
  - leer oder fast leer: niedriger Score
  - enthält Exports/öffentliche API: mittlerer Score
- Wenn aktuell zu aufwendig:
  - __init__.py nur kleiner Strukturbonus

7.1.c Tests für Strukturdateien ergänzen
- Testprojekt:
  - pyproject.toml
  - README.md
  - src/package/cli.py
  - src/package/core.py
- Erwartung:
  - pyproject.toml erscheint unter Important Files
  - aber nicht zwingend über README oder CLI


8. Score-Gewichtung festlegen

8.1.a Erste sinnvolle Gewichtung definieren
- Vorschlag:
  - Entrypoint: sehr hoch
  - Documentation: hoch
  - Import incoming centrality: hoch
  - Call incoming centrality: hoch
  - Import outgoing centrality: niedrig bis mittel
  - Call outgoing centrality: niedrig bis mittel
  - Structural config: mittel
- Wichtig:
  - Nicht zu viele magische Spezialfälle
  - Lieber wenige klare Signale

8.1.b Score normalisieren
- Problem:
  - Große Projekte haben mehr Imports/Calls
  - Kleine Projekte dürfen nicht verzerrt werden
- Lösung:
  - Degree-Werte deckeln oder logarithmisch skalieren
- Beispiel:
  - min(max_score, count * weight)
  - oder log1p(count) * weight
- Für Tests einfacher:
  - deterministische einfache Deckelung

8.1.c Reasons erzeugen
- Jede Datei kann mehrere Gründe haben:
  - entrypoint
  - imported by N files
  - called by N files
  - documentation
  - project configuration
- Export muss nicht zwingend alle Details zeigen
- Intern für Tests und Debugging nützlich

8.1.d Keine übergenaue Reihenfolge erzwingen
- Tests sollten nicht jeden Platz prüfen
- Besser:
  - Datei A rankt vor Datei B
  - Datei enthält Reason X
  - Top-N enthält erwartete Dateien


9. Integration in AI Export

9.1.a Bestehende Important Files Sektion finden
- Datei:
  - wahrscheinlich repocontext/exporters/ai.py
- Aufgabe:
  - aktuelle Sortierung ersetzen oder erweitern
  - neue Ranking-Funktion nutzen

9.1.b Ausgabeformat stabil halten
- Bestehende Überschrift beibehalten:
  - Important Files
- Keine unnötigen Formatänderungen
- Nur Reihenfolge und ggf. kurze Gründe verbessern, falls bestehendes Format das erlaubt

9.1.c Gründe optional anzeigen
- Falls aktueller AI Export schon Beschreibungen nutzt:
  - Reason ergänzen
- Falls nicht:
  - Nur sortierte Pfade ausgeben
- Nicht das Format unnötig brechen

9.1.d Regression-Test für AI Export ergänzen
- Test:
  - Projekt mit README, pyproject script, zentraler core.py
- Erwartung:
  - Important Files enthält diese Dateien
  - Entrypoint und zentrale Dateien erscheinen vor unwichtigen Dateien
  - AI Export bleibt valide


10. Integration in Full Export

10.1.a Prüfen, ob full.txt Important Files nutzt
- Wenn ja:
  - gleiche Ranking-Funktion verwenden
- Wenn nein:
  - nicht künstlich neue Sektion einführen, außer Roadmap/Architektur verlangt es schon
- Ziel:
  - Kein unnötiger Scope Creep

10.1.b Falls Full Export File Summary sortiert
- Ranking kann dort optional nicht eingreifen
- Milestone 12 meint primär Important File Ranking
- Full Export sollte nur geändert werden, wenn bestehende Important-Files-Sektion betroffen ist

10.1.c Regression-Test für full.txt nur falls betroffen
- Wenn full.txt Important Files enthält:
  - Test anpassen/ergänzen
- Wenn nicht:
  - keine unnötigen Full-Exporter-Tests bauen


11. CLI/Output-Verhalten prüfen

11.1.a Bestehende Befehle unverändert lassen
- repocontext full
- repocontext export-ai
- repocontext export-docs
- repocontext info
- Keine neuen CLI-Flags nötig für Milestone 12

11.1.b Kein Konfigurationsfeature vorziehen
- .repocontext.yml ist Milestone 15
- Also:
  - keine Ranking-Konfiguration einbauen
  - keine Include/Exclude-Optionen neu erfinden

11.1.c Keine Split-Export-Logik vorziehen
- Split Exports ist Milestone 16
- Also:
  - Important Ranking nur vorbereiten
  - keine Multi-Part-Exports bauen


12. Tests im Detail

12.1.a Neue Testdatei anlegen
- Empfehlung:
  - tests/test_important_file_ranking.py
- Inhalt:
  - reine Unit-Tests für Ranking
  - kleine künstliche Projektstrukturen
  - keine riesigen Golden-Files

12.1.b Test: Entrypoint aus pyproject
- Setup:
  - pyproject.toml mit [project.scripts]
  - src/demo/cli.py
  - src/demo/core.py
- Erwartung:
  - cli.py wird als Entrypoint erkannt
  - pyproject.toml bekommt Strukturbonus

12.1.c Test: Import-Zentralität
- Setup:
  - mehrere Dateien importieren core.py
- Erwartung:
  - core.py rankt vor leaf.py

12.1.d Test: Call-Zentralität
- Setup:
  - mehrere Funktionen rufen service.run
- Erwartung:
  - service.py rankt vor unused.py

12.1.e Test: Dokumentationsranking
- Setup:
  - README.md
  - docs/architecture.md
  - docs/random.md
- Erwartung:
  - README und architecture höher als random

12.1.f Test: kombinierte Signale
- Setup:
  - README.md
  - pyproject.toml
  - src/demo/cli.py
  - src/demo/core.py
  - src/demo/helper.py
- Erwartung:
  - Top-Dateien enthalten README, cli, core, pyproject
  - helper.py nicht in Top 3, falls keine Signale

12.1.g Test: deterministische Sortierung
- Setup:
  - zwei gleich bewertete Dateien
- Erwartung:
  - alphabetische stabile Reihenfolge

12.1.h Test: leere optionale Graphen
- Setup:
  - keine Importdaten
  - keine Calldaten
- Erwartung:
  - Ranking funktioniert mit Entrypoint/Dokumentation trotzdem

12.1.i Test: unbekannte Graph-Knoten
- Setup:
  - Import Graph enthält Knoten, die nicht in files vorhanden sind
- Erwartung:
  - kein Absturz
  - unbekannte Knoten werden ignoriert

12.1.j Bestehende Exporttests erweitern
- AI Export:
  - Important Files nutzt neue Reihenfolge
- Full Export:
  - nur falls betroffen


13. Dokumentation aktualisieren

13.1.a README aktualisieren
- Ergänzen:
  - RepoContext priorisiert wichtige Dateien
  - Signale:
    - Entrypoints
    - Import Graph
    - Call Graph
    - Dokumentation
- Keine zu langen Details
- Nutzerorientiert beschreiben

13.1.b MILESTONE12.md erstellen oder aktualisieren, falls Projektstil das vorsieht
- Inhalt:
  - Ziel
  - implementierte Signale
  - Tests
  - erwartetes Verhalten
- Wichtig:
  - Keine Checkbox-Statuslogik als Wahrheit verwenden
  - Datei ist Beschreibung, nicht Fortschrittsquelle

13.1.c Keine unnötige TASKS.md-Änderung
- Nur ändern, wenn im RepoContext-Projekt üblich und ausdrücklich sinnvoll
- Falls TASKS.md existiert und nicht gebraucht wird:
  - unangetastet lassen


14. Abschlussprüfung

14.1.a Syntax prüfen
- Befehl:
  - python3 -m compileall repocontext tests

14.1.b Tests ausführen
- Befehl:
  - python3 -m pytest --color=yes

14.1.c Exporte erzeugen
- Wichtig:
  - Use RepoContext CLI exports for final checks; do not use deprecated snapshot scripts.
- Stattdessen:
  - repocontext full
  - repocontext export-ai
  - repocontext export-docs

14.1.d Ergebnisdateien prüfen
- Prüfen:
  - full.txt existiert
  - ai.txt existiert
  - docs.txt existiert
- Prüfen:
  - ai.txt enthält Important Files
  - Important Files enthalten zentrale Dateien
  - Reihenfolge wirkt plausibel

14.1.e Git Status prüfen
- Befehl:
  - git status --short

14.1.f Commit erstellen
- Commit-Nachricht:
  - Add important file ranking

14.1.g Letzte Prüfung
- Befehl:
  - git log --oneline --decorate -5
  - git status --short


15. Sinnvolle Patch-Reihenfolge

15.1.a Patch 1: Ranking-Modul und Basistests
- Neue Datei:
  - repocontext/analyzers/important_files.py
- Neue Tests:
  - tests/test_important_file_ranking.py
- Enthält:
  - Datenstruktur
  - Dokumentationsscore
  - Strukturdateiscore
  - deterministische Sortierung

15.1.b Patch 2: Entrypoint Detection
- Ergänzen:
  - pyproject script parsing
  - bekannte Entrypoint-Dateinamen
  - __main__.py
- Tests:
  - pyproject scripts
  - main.py/cli.py
  - __main__.py

15.1.c Patch 3: Import Graph Centrality
- Ergänzen:
  - eingehende Import-Kanten zählen
  - ausgehende Import-Kanten leicht werten
  - unbekannte Knoten ignorieren
- Tests:
  - zentrale importierte Datei rankt höher

15.1.d Patch 4: Call Graph Centrality
- Ergänzen:
  - eingehende Calls pro Datei zählen
  - ausgehende Calls optional leicht werten
  - Symbol/File-Mapping robust behandeln
- Tests:
  - häufig aufgerufene Datei rankt höher
  - leerer Call Graph crasht nicht

15.1.e Patch 5: AI Export Integration
- ai.py anpassen
- Important Files Ranking verwenden
- Bestehende AI Export Tests erweitern
- Format stabil halten

15.1.f Patch 6: README/Doku und Abschlussprüfung
- README aktualisieren
- ggf. MILESTONE12.md ergänzen
- vollständige Tests
- repocontext full
- repocontext export-ai
- repocontext export-docs
- Commit


16. Definition of Done

16.1.a Funktional
- RepoContext erkennt wichtige Dateien anhand mehrerer Signale
- Entrypoints werden priorisiert
- Import-zentrale Dateien werden priorisiert
- Call-zentrale Dateien werden priorisiert
- Dokumentationsdateien werden sinnvoll priorisiert
- Strukturdateien wie pyproject.toml werden berücksichtigt

16.1.b Robustheit
- Ranking funktioniert auch ohne Import Graph
- Ranking funktioniert auch ohne Call Graph
- Ranking funktioniert auch ohne pyproject.toml
- Ranking ignoriert unbekannte oder nicht auflösbare Graph-Knoten
- Sortierung ist deterministisch

16.1.c Export
- ai.txt nutzt das neue Important File Ranking
- Bestehende Exportstruktur bleibt stabil
- full.txt wird nicht unnötig verändert
- docs.txt bleibt Milestone-9-konform

16.1.d Tests
- Neue Unit-Tests für Ranking vorhanden
- Export-Regression-Test vorhanden
- Gesamte Testsuite grün

16.1.e Projektregeln
- Use RepoContext CLI exports for final checks; do not use deprecated snapshot scripts.
- RepoContext CLI für Abschlussprüfung verwenden
- Keine unnötigen Konfigurationsfeatures aus Milestone 15 vorziehen
- Keine Split-Export-Features aus Milestone 16 vorziehen
- Keine Secret Detection aus Milestone 14 vorziehen
