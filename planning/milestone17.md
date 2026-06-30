Milestone 17 – Bash Support

Ziel:
RepoContext soll Bash/Shell-Skripte deutlich besser verstehen:
- Bash-Funktionen erkennen
- Bash-Funktionen im Symbol Index anzeigen
- einfache Bash-Funktionsaufrufe als Call Graph ausgeben
- alles sauber in full.txt, ai.txt und ggf. changed.txt/docs-relevante Exporte integrieren
- ohne Shell-Code auszuführen

Wichtige Grundentscheidung:
Für Milestone 17 reicht ein robuster statischer Parser auf Text-/Regex-/Zeilenbasis.
Keine echte Bash-Ausführung.
Kein sourcing.
Keine Expansion von Variablen.
Keine komplette Bash-Grammatik.
Ziel ist: nützlich, sicher, testbar, stabil.


17.1 – Bash-Dateien zuverlässig erkennen

17.1.a – Bestehende Language Detection prüfen
- Prüfen, wie aktuell Dateitypen erkannt werden.
- Sicherstellen, dass typische Bash-Dateien als Bash/Shell erkannt werden:
  - *.sh
  - *.bash
  - bash-Shebang: #!/usr/bin/env bash
  - sh-Shebang: #!/bin/sh
  - zsh nur dann, wenn vorhandene Architektur das sauber erlaubt.
- Ziel: Bash-Parser wird nur auf passenden Textdateien ausgeführt.

17.1.b – Tests für Bash-Dateierkennung ergänzen
- Testdateien/Fälle:
  - scripts/deploy.sh
  - scripts/build.bash
  - Datei ohne Extension mit #!/usr/bin/env bash
  - Datei ohne Extension mit #!/bin/bash
  - normale Python-Datei darf nicht als Bash erkannt werden.
- Tests an semantisch passender Stelle einfügen, nicht einfach am Dateiende anhängen.

17.1.c – Commit
Commit-Vorschlag:
Detect Bash source files


17.2 – Bash Function Discovery implementieren

17.2.a – Bash-Funktionssyntax definieren
Folgende Formen sollen erkannt werden:

1. POSIX/Bash-Form:
   my_func() {
     echo "hello"
   }

2. Bash function keyword:
   function my_func {
     echo "hello"
   }

3. Bash function keyword mit Klammern:
   function my_func() {
     echo "hello"
   }

4. Einzeilige Funktion:
   my_func() { echo "hello"; }

5. Funktion mit Leerzeichen:
   my_func () {
     echo "hello"
   }

Nicht als Funktion erkennen:
- if ...
- for ...
- while ...
- case ...
- echo()
- command substitutions
- Kommentare
- Strings
- Array-Zuweisungen
- einfache Befehlsaufrufe mit Klammern im Argument

17.2.b – Parser-Modul ergänzen
- Falls es bereits ein zentrales Symbol-Extractor-Modul gibt:
  - Bash-Erkennung dort integrieren.
- Falls die Architektur sauberer ist:
  - neues internes Modul ergänzen, z. B. bash_symbols.py oder shell_symbols.py.
- Der Parser soll zurückgeben:
  - Funktionsname
  - Datei
  - Startzeile
  - Endzeile, falls mit vertretbarem Aufwand bestimmbar
  - Symboltyp: function
  - Sprache: bash/shell
  - optional Signatur: my_func()

17.2.c – Funktionskörper grob bestimmen
- Für Call Graph später muss der Body ungefähr bekannt sein.
- Minimal:
  - Start bei Funktionsdefinition
  - Ende über geschweifte Klammern zählen
  - Kommentare und Strings müssen nicht perfekt sein, aber offensichtliche Fälle sollen nicht brechen.
- Einzeilige Funktionen müssen korrekt abgeschlossen werden.
- Bei nicht sauber abschließbarer Funktion:
  - Symbol trotzdem erkennen
  - Endzeile konservativ setzen oder offen lassen, je nach bestehendem Datenmodell.

17.2.d – Tests für Bash Function Discovery
Fixture mit mehreren Funktionen:
- simple_func() { ... }
- function keyword_func { ... }
- function keyword_paren_func() { ... }
- spaced_func () { ... }
- one_line_func() { echo ok; }
- nested control blocks innerhalb einer Funktion:
  if ...; then
    other_func
  fi
- Kommentare mit fake_func() { sollen ignoriert werden.

Erwartung:
- alle echten Funktionen werden gefunden
- fake/comment Funktionen nicht
- Zeilennummern stimmen
- kein Crash bei ungewöhnlicher Formatierung

17.2.e – Commit
Commit-Vorschlag:
Add Bash function discovery


17.3 – Bash Symbol Index integrieren

17.3.a – Symbolmodell prüfen
- Prüfen, wie Python-Klassen/Funktionen aktuell in den Symbol Index kommen.
- Bash-Funktionen sollen dieselbe Exportstruktur verwenden, soweit sinnvoll.
- Keine separate Sonderausgabe bauen, wenn die bestehende Symbol-Ausgabe erweiterbar ist.

17.3.b – Bash-Funktionen in ai.txt aufnehmen
- Im AI Export sollen Bash-Funktionen im Symbol Index erscheinen.
- Format soll konsistent mit bestehenden Symbolen sein.
- Beispiel:
  - scripts/deploy.sh
    - function deploy_app() at line 12
    - function rollback_app() at line 48

17.3.c – Bash-Funktionen in full.txt aufnehmen
- full.txt enthält ohnehin Source Dump.
- Zusätzlich soll der Symbol Index im Full Export Bash-Funktionen anzeigen, falls Symbol Index dort schon enthalten ist.
- Keine neue große Sondersektion, wenn vorhandene Symbol-Sektion genügt.

17.3.d – Changed Export prüfen
- Wenn changed.txt Symbol-/Callgraph-Informationen für geänderte Dateien enthält:
  - Bash-Symbole dort ebenfalls berücksichtigen.
- Wenn changed.txt aktuell nur Diffs/Dateien enthält:
  - nichts künstlich erweitern.
- Verhalten an bestehender Exportarchitektur ausrichten.

17.3.e – Tests für Export-Integration
- Minimaler Repo-Fixture mit Bash-Datei.
- ai export erzeugen.
- Prüfen:
  - Bash-Datei erscheint
  - Bash-Funktion erscheint im Symbol Index
  - keine Python-spezifische Beschriftung für Bash-Funktionen
- Falls Full Export Symbol Index enthält:
  - full export ebenfalls testen.

17.3.f – Commit
Commit-Vorschlag:
Include Bash functions in symbol exports


17.4 – Bash Call Graph implementieren

17.4.a – Call-Graph-Scope definieren
Milestone 17 soll einfache Bash-Funktionsaufrufe erkennen:

Erkennen:
- deploy_app
- rollback_app
- build_assets "$target"
- if deploy_app; then ...
- deploy_app && restart_service
- deploy_app || rollback_app
- deploy_app | tee log.txt

Nicht zwingend erkennen:
- variable Funktionsaufrufe: "$cmd"
- eval
- source dynamischer Dateien
- command substitutions mit komplexer Syntax
- Funktionsnamen, die nur in Strings vorkommen
- externe Programme als Calls

17.4.b – Known Bash functions sammeln
- Vor Call-Analyse alle Bash-Funktionen pro Repository oder pro Datei sammeln.
- Calls nur dann als Funktionsaufruf werten, wenn der Name im bekannten Symbolindex enthalten ist.
- Dadurch werden externe Commands wie echo, grep, sed, awk nicht fälschlich als interne Calls gezählt.

17.4.c – Bash-Builtins und Keywords ignorieren
Ignorieren:
- if, then, else, elif, fi
- for, while, until, do, done
- case, esac
- function
- return, exit
- local, declare, export, readonly
- echo, printf, cd, pwd, test
- [, [[
- source, .
- command, builtin
- true, false

17.4.d – Body-Zeilen analysieren
- Kommentare entfernen oder überspringen.
- Heredocs möglichst robust ignorieren, mindestens nicht crashen.
- Pro Zeile mögliche Kommandopositionen analysieren:
  - Zeilenanfang
  - nach ;
  - nach &&
  - nach ||
  - nach |
  - nach then/do optional, falls einfach erkennbar
- Wenn Token einem bekannten Bash-Funktionsnamen entspricht:
  - Edge caller -> callee erzeugen.

17.4.e – Rekursion und Selbstaufrufe erlauben
- Selbstaufruf darf als Edge erscheinen, falls Funktion sich selbst aufruft.
- Keine Endlosschleifen, da statische Analyse.

17.4.f – Dateiübergreifende Calls
Basisvariante:
- Wenn Funktion A in Datei 1 eine bekannte Funktion B aus Datei 2 aufruft, darf Edge A -> B erzeugt werden.
- Keine Prüfung, ob Datei 2 tatsächlich gesourced wird.
- Optional im Output kennzeichnen nur über vorhandene Dateiangabe.

Alternative, falls zu riskant:
- Erst nur same-file Calls.
- Cross-file Calls als späteren Ausbau notieren.
- Entscheidung nach bestehender Call-Graph-Architektur treffen.

Empfehlung:
- Wenn der bestehende Python-Callgraph repo-global arbeitet: Bash ebenfalls repo-global.
- Wenn er dateilokal arbeitet: Bash zunächst dateilokal.

17.4.g – Tests für Bash Call Graph
Fixture:
- main() ruft build und deploy auf.
- deploy() ruft restart_service auf.
- rollback() wird nicht aufgerufen.
- fake calls in Kommentaren und Strings werden ignoriert.
- echo/grep/sed werden ignoriert.
- if build; then deploy; fi wird erkannt.
- build && deploy || rollback wird erkannt.

Erwartung:
- main -> build
- main -> deploy
- deploy -> restart_service
- main -> rollback, falls in entsprechender Zeile wirklich erreichbar-statisch enthalten
- keine Edges zu echo/grep/sed
- keine Edges aus Kommentaren

17.4.h – Commit
Commit-Vorschlag:
Add Bash call graph analysis


17.5 – Call Graph Export-Integration

17.5.a – Bestehende Call-Graph-Ausgabe prüfen
- Prüfen, wie Python Call Graph aktuell in ai.txt/full.txt dargestellt wird.
- Bash-Edges sollen in dieselbe Struktur integriert werden.
- Keine zweite konkurrierende Call-Graph-Sektion bauen, außer die Architektur erzwingt es.

17.5.b – Bash Call Graph in ai.txt ausgeben
Beispielausgabe:
- scripts/deploy.sh:main -> scripts/deploy.sh:build
- scripts/deploy.sh:main -> scripts/deploy.sh:deploy
- scripts/deploy.sh:deploy -> scripts/deploy.sh:restart_service

17.5.c – Bash Call Graph in full.txt ausgeben
- Falls Full Export Call Graph enthält:
  - Bash-Edges ebenfalls ausgeben.
- Wenn Full Export aus Platzgründen anders priorisiert:
  - bestehende Export-Limits respektieren.

17.5.d – Split Export Kompatibilität prüfen
- Milestone 16 hat Split Exports eingeführt.
- Bash-Symbolindex und Bash-Callgraph dürfen Split Exports nicht kaputt machen.
- Wenn ai.txt wegen Limit geteilt wird:
  - Bash-Sektionen müssen normal mitsplitten.
- Keine Sonderlogik, wenn bestehendes Split-System allgemein funktioniert.

17.5.e – Tests
- ai export mit Bash Call Graph erzeugen.
- Prüfen:
  - Edges erscheinen
  - Funktionsnamen erscheinen
  - keine externen Commands erscheinen
- Optional Split-Test:
  - kleines Limit setzen
  - Export läuft trotzdem ohne Fehler.

17.5.f – Commit
Commit-Vorschlag:
Export Bash call graph information


17.6 – Robustheit und Edge Cases

17.6.a – Kommentare und Strings verbessern
- Fake-Funktionen in Kommentaren ignorieren:
  # fake_func() {
- Fake-Calls in Kommentaren ignorieren:
  # deploy_app
- Strings nicht perfekt parsen, aber offensichtliche quoted-only fake calls nicht als echte Calls zählen, wenn praktikabel.

17.6.b – Heredoc-Schutz ergänzen
- Parser soll bei heredocs nicht crashen.
- Inhalt von heredocs soll idealerweise nicht als Funktionsdefinition oder Call zählen.
- Test:
  cat <<EOF
  fake_func() {
  deploy_app
  EOF

17.6.c – Subshells und Gruppen tolerieren
- Parser soll nicht crashen bei:
  (
    deploy_app
  )
  {
    deploy_app
  }
- Funktionsgrenzen dürfen dadurch nicht offensichtlich falsch werden.

17.6.d – ungewöhnliche Namen
Bash-Funktionsnamen erlauben:
- Buchstaben
- Zahlen nicht als erstes Zeichen
- Unterstrich
- Bindestrich optional nur dann, wenn bestehender Stil und Bash-Kompatibilität bewusst unterstützt werden sollen.

Empfehlung:
- Für Milestone 17 konservativ:
  [A-Za-z_][A-Za-z0-9_]*
- Bindestrich später optional ergänzen, falls gewünscht.

17.6.e – Tests
- heredoc wird ignoriert
- Kommentare werden ignoriert
- Parser crasht nicht bei subshell/grouping
- ungültige Funktionsnamen werden nicht erkannt

17.6.f – Commit
Commit-Vorschlag:
Harden Bash parsing edge cases


17.7 – Dokumentation aktualisieren

17.7.a – README ergänzen
- Kurz erwähnen:
  - RepoContext erkennt Bash-Funktionen.
  - Bash-Funktionen erscheinen im Symbol Index.
  - einfache Bash-Funktionsaufrufe erscheinen im Call Graph.
  - Analyse ist statisch und führt keine Shell-Skripte aus.

17.7.b – Docs/Featureliste aktualisieren
- Falls es docs/ oder Feature-Übersicht gibt:
  - Bash Support eintragen.
- Kein übertriebener Detailtext.
- Keine falschen Versprechen wie vollständige Bash-Grammatik.

17.7.c – Beispiel ergänzen
Optional, falls Beispiele vorhanden:
- scripts/deploy.sh als Mini-Beispiel erwähnen.
- Beispielausgabe für Symbol Index und Call Graph.

17.7.d – argparse-Hilfe prüfen
Roadmap-Hinweis:
- argparse soll allgemein gut beschrieben sein.
- Für Milestone 17 nur prüfen, ob bestehende CLI-Hilfen nicht falsch sind.
- Keine große argparse-Überarbeitung in Milestone 17, außer notwendig.
- Eigene spätere Aufgabe dafür offenlassen.

17.7.e – Commit
Commit-Vorschlag:
Document Bash analysis support


17.8 – Abschlussprüfung Milestone 17

17.8.a – Gesamttests ausführen
- python3 -m pytest --color=yes
- Zusätzlich relevante Export-Kommandos mit RepoContext selbst:
  - repocontext full
  - repocontext export-ai
  - repocontext export-docs
  - repocontext changed, falls sinnvoll und verfügbar
- Kein bundle_project.sh verwenden.

17.8.b – Generierte Exporte prüfen
Zu prüfen:
- full.txt enthält Bash-Dateien korrekt.
- ai.txt enthält Bash-Funktionen im Symbol Index.
- ai.txt enthält Bash Call Graph, wenn Bash Calls vorhanden sind.
- docs.txt bleibt sinnvoll und wird nicht mit Symbolanalyse überladen.
- changed.txt funktioniert weiterhin.
- Split Exports funktionieren weiterhin, falls Limits greifen.

17.8.c – Regressionen prüfen
Besonders aufpassen:
- Python Symbol Extraction darf nicht kaputtgehen.
- Python Call Graph darf nicht kaputtgehen.
- Secret Detection aus Milestone 14 darf Bash-Dateien weiterhin maskieren.
- Config Include/Exclude aus Milestone 15 muss Bash-Dateien korrekt berücksichtigen.
- Split Exports aus Milestone 16 dürfen Bash-Sektionen nicht zerreißen oder verlieren.

17.8.d – Abschlussbericht
Am Ende gegen Roadmap-Kriterien prüfen:
- Bash function discovery umgesetzt
- Bash symbol index umgesetzt
- Bash call graph umgesetzt

17.8.e – Abschluss-Commit, falls Doku/Test-Fixes nötig
Commit-Vorschlag:
Finalize Bash support milestone


Empfohlene Commit-Reihenfolge:

1. Detect Bash source files
2. Add Bash function discovery
3. Include Bash functions in symbol exports
4. Add Bash call graph analysis
5. Export Bash call graph information
6. Harden Bash parsing edge cases
7. Document Bash analysis support
8. Optional: Finalize Bash support milestone


Nicht in Milestone 17 aufnehmen:

- Vollständiger Bash-Parser
- ShellCheck-Integration
- Ausführung von Bash-Code
- dynamisches source/eval Tracking
- Datenflussanalyse
- Erkennung externer Programme als Dependency Graph
- argparse-Großüberarbeitung
- Remote Git URL Input
- Recent Commit Context
- Code Compression / Token Saving Mode
- Projektumbenennung
