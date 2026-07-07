# Patch Workflow Rules

Diese Datei dokumentiert die aktuell geltenden Arbeitsregeln für `n`, Fixes und Commit-Patches in diesem Chat.

Sie liegt unter `scripts/dev/`, weil sie zur Entwicklungs- und Patch-Infrastruktur gehört, nicht zur Runtime-Logik von RepoDossier.

---

## 1. Bedeutung von `n`

Wenn Christian nur schreibt:

```text
n
```

gilt das als Kurzform für:

> Der letzte Patch wurde erfolgreich ausgeführt, die Tests waren grün, und der Commit wurde erstellt. Gib den nächsten sinnvollen kleinen Commit für den aktuellen Milestone.

Daraus folgt:

1. Nicht nachfragen, ob der letzte Patch erfolgreich war.
2. Den letzten Patch als grün / committed behandeln.
3. Direkt den nächsten sinnvollen Commit liefern.
4. Keine Wiederholung des vorherigen Patches.
5. Wenn aus dem Chat klar ist, dass der letzte Schritt ein Fix war, den Fix als abgeschlossen behandeln.
6. Wenn Christian statt `n` eine Fehlermeldung, ein Logfile oder Terminalausgabe mit Fehlern postet, hat der Fix Vorrang.

---

## 2. Bedeutung von geposteten Fehlern

Wenn Christian Terminalausgaben, Tracebacks, Syntaxfehler, Testfehler oder Logfiles mit Fehlern postet, gilt:

> Der aktuelle Patch ist noch nicht abgeschlossen. Repariere genau diesen Patch.

Daraus folgt:

1. Nicht zum nächsten Milestone-Schritt springen.
2. Zuerst den Fehler analysieren.
3. Einen gezielten Fix-Patch liefern.
4. Der Fix-Patch muss die ursprünglich geplanten Tests erneut ausführen.
5. Bei grünem Testlauf soll der ursprünglich geplante Commit erstellt werden.
6. Falls der ursprüngliche Commit noch nicht erstellt wurde, nutzt der Fix dieselbe Commit-Message.
7. Falls bereits committed wurde und ein neuer Fix nötig ist, bekommt der Fix einen eigenen Commit.
8. Im Footer wird der Fix als aktuelle Aufgabe markiert.

---

## 3. Ausgabeformat für Patches und Fixes

Für zukünftige Commit- und Fix-Antworten gilt:

1. Patches, Fixes und Next-Commit-Scripts werden als Download-Link zu einer `.sh`-Bashscript-Datei bereitgestellt.
2. Keine riesigen Bash-Scripts direkt ins Chatfenster posten, wenn ein Download-Link möglich ist.
3. Kurz und knapp erklären, was der Patch oder Fix macht.
4. Bei Bedarf darf Christian um zusätzliche Eingaben, Logausgaben oder Testergebnisse gebeten werden.
5. Die `.sh`-Datei muss direkt ausführbar oder mit `bash <datei>.sh` ausführbar sein.
6. Der Script-Footer bleibt Teil des `.sh`-Scripts und wird beim Ausführen im Terminal angezeigt.

---

## 4. Repo-Root-Erkennung

Das Script soll das Repository-Root selbst finden.

Regeln:

1. Standardannahme bleibt `~/market_research/repo_dossier`.
2. Zusätzlich soll das Script mit `git rev-parse --show-toplevel` das tatsächliche Repo-Root ermitteln.
3. Wenn das gefundene Repo-Root nicht zu RepoDossier gehört, abbrechen.
4. Wenn das aktuelle Verzeichnis kein Git-Repo ist, nach `~/market_research/repo_dossier` wechseln und dort erneut prüfen.
5. Wenn RepoDossier nicht gefunden wird, klar abbrechen und keinen Commit erstellen.

Beispiel-Logik:

```bash
REPO_CANDIDATE="$HOME/market_research/repo_dossier"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
  REPO_ROOT="$(git rev-parse --show-toplevel)"
else
  cd "$REPO_CANDIDATE" || {
    echo "Fehler: RepoDossier-Verzeichnis nicht gefunden: $REPO_CANDIDATE"
    return 1
  }
  REPO_ROOT="$(git rev-parse --show-toplevel)"
fi

case "$REPO_ROOT" in
  */repo_dossier) ;;
  *)
    echo "Fehler: falsches Repository: $REPO_ROOT"
    return 1
    ;;
esac

cd "$REPO_ROOT" || return 1
```

---

## 5. Virtuelle Umgebung

Wenn `.venv` existiert, wird sie aktiviert.

Regeln:

1. Dafür bevorzugt Helper-Funktionen aus `scripts/dev/repo_patch_helper.py` verwenden, sofern vorhanden und nutzbar.
2. Fallback ist direkte Bash-Aktivierung.
3. Es wird immer `python3` verwendet.

Fallback:

```bash
if [ -d .venv ]; then
  source .venv/bin/activate
fi
```

---

## 6. Repository-lokaler Helper

Die bevorzugte Helper-Datei liegt im Projekt:

```text
scripts/dev/repo_patch_helper.py
```

Die frühere externe Datei unter folgendem Pfad ist nur noch Fallback:

```text
~/dev-scripts/repo_patch_helper.py
```

Vor Nutzung des repo-lokalen Helpers kann geprüft werden:

```bash
[ -f "$REPO_HELPER" ] && python3 -m py_compile "$REPO_HELPER"
```

Wenn der Helper fehlt oder syntaktisch defekt ist:

1. Nicht blind abbrechen, wenn ein einfacher manueller Fallback möglich ist.
2. Bei Helper-bezogenen Patches manuelle Shell-Fallbacks nutzen.
3. Bei normalen Projektpatches klar melden, dass der Helper fehlt oder defekt ist.
4. Wenn der Helper selbst repariert wird, nicht den defekten Helper für die Reparatur voraussetzen.

---

## 7. Logging

Alle Ausgaben sollen geloggt werden.

Regeln:

1. `stdout` und `stderr` zusammen in eine Logdatei schreiben.
2. Das Logging soll auch bei erfolgreichem Lauf passieren.
3. Dafür bevorzugt Helper-Funktionen aus `scripts/dev/repo_patch_helper.py` verwenden.
4. Bei Fehlern soll das Log per `xclip` in die Zwischenablage kopiert werden, wenn verfügbar.
5. Wenn `xclip` nicht installiert ist, nur Hinweis ausgeben.
6. Der Pfad zur Logdatei soll im Terminal sichtbar sein.

Typisches Pattern:

```bash
RUN_LOG="$(mktemp)"
exec > >(tee -a "$RUN_LOG") 2>&1
echo "Logfile: $RUN_LOG"
```

---

## 8. Keine Aider-Prompts

Bei Commit-Patches gilt:

1. Kein Aider verwenden.
2. Keine Aider-Prompts ausgeben.
3. Direkte Python-/Bash-Patches liefern.
4. Nur wenn Christian ausdrücklich Aider verlangt, darf Aider verwendet werden.

---

## 9. Kein `bundle_project.sh`

`bundle_project.sh` wird nicht mehr verwendet.

Für Snapshots, Prüfungen und Exporte werden RepoDossier-/RepoContext-Befehle oder vorhandene Exportdateien genutzt.

---

## 10. Tests

Jeder Commit-Patch führt relevante Tests aus.

Regeln:

1. `--color=yes` verwenden.
2. Bei Testfehlern keinen Commit erstellen.
3. Optionale Testdateien nur ausführen, wenn sie existieren.
4. Nach Fixes dieselben relevanten Tests erneut ausführen.
5. Testausgaben werden gemeinsam mit allen anderen Ausgaben geloggt.
6. Wenn Tests fehlen, aber der Patch sinnvoll prüfbar ist, mindestens Syntax-/Smoke-Checks ausführen.

Bevorzugt mit Helper:

```bash
python3 "$REPO_HELPER" pytest-existing --repo . --log "$TEST_LOG" tests/test_x.py tests/test_y.py
```

Fallback:

```bash
python3 -m pytest --color=yes tests/test_x.py tests/test_y.py
```

---

## 11. Syntaxchecks

Bei Python-Änderungen werden Syntaxchecks ausgeführt.

Bevorzugt mit Helper:

```bash
python3 "$REPO_HELPER" compile --repo . --log "$TEST_LOG" path1 path2
```

Wenn der Helper selbst repariert wird, zuerst direkt prüfen:

```bash
python3 -m py_compile scripts/dev/repo_patch_helper.py
```

---

## 12. Clipboard bei Fehlern

Bei Fehlern wird der relevante Log kopiert, wenn möglich.

Mit Helper:

```bash
python3 "$REPO_HELPER" copy-log "$RUN_LOG" || true
```

Fallback:

```bash
if command -v xclip >/dev/null 2>&1; then
  cat "$RUN_LOG" | xclip -selection clipboard
fi
```

---

## 13. Commit-Regeln

Regeln:

1. Commit nur bei staged Änderungen.
2. Wenn nichts zu committen ist, klar ausgeben.
3. Commit-Messages auf Englisch, kurz und präzise.
4. Keine unrelated Dateien committen.
5. Keine ungewollten Planning-Dateien committen.
6. Danach immer `git status --short`.
7. Git-Ausgaben ohne Pager anzeigen.

Bevorzugt mit Helper:

```bash
python3 "$REPO_HELPER" commit-if-changed --repo . --message "Commit message" path1 path2
```

Fallback:

```bash
git add path1 path2

if git diff --cached --quiet; then
  echo "Keine Änderungen zum Committen."
else
  git commit -m "Commit message"
fi

git status --short
```

---

## 14. Git ohne Pager

Immer:

```bash
git --no-pager diff
git --no-pager log
git --no-pager status
```

oder Helper:

```bash
python3 "$REPO_HELPER" diff --repo . path1 path2
python3 "$REPO_HELPER" status --repo .
```

Nie plain `git diff` oder `git log`, wenn dadurch ein Pager hängen bleiben kann.

---

## 15. Footer-Pflicht

Jeder Patch- oder Fixscript enthält unten eine Footer-Funktion.

Der Footer wird aufgerufen:

1. Bei Patchfehlern.
2. Bei Syntaxfehlern.
3. Bei Testfehlern.
4. Bei Commitfehlern.
5. Bei Erfolg.

Der Footer enthält:

1. Letzte zwei erledigte Aufgaben.
2. Aktuelle Aufgabe oder aktueller Fix.
3. Nächste voraussichtliche Schritte.
4. Problemzeile nur bei echten Fehlern.

---

## 16. Footer-Farben

Farbschema:

```text
Grün  = erledigt / committed / Tests grün
Lila  = aktuell / laufender Fix / gerade bearbeitet
Gelb  = nächste geplante Schritte / noch nicht begonnen
Rot   = echte Probleme, Testfehler, Blocker, nicht committed
```

Regeln:

1. Zukünftige Aufgaben nicht rot markieren.
2. Rot ist nur für echte Probleme.
3. Erledigte Schritte grün markieren.
4. Aktuelle Aufgabe lila markieren.
5. Nächste Schritte gelb markieren.

Empfohlene ANSI-Farben:

```bash
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
```

---

## 17. Fix-Nummern

Fixes werden im Footer klar benannt, zum Beispiel:

```text
4.4.a-fix
4.4.a-fix2
DEV.1-fix
```

Wenn ein Fix noch zum ursprünglichen Commit führt, bleibt die Commit-Message normalerweise dieselbe wie beim geplanten Ursprungspatch.

---

## 18. Umgang mit Helper-Fehlern

Wenn `scripts/dev/repo_patch_helper.py` selbst defekt ist:

1. Nicht den defekten Helper für die Reparatur voraussetzen.
2. Erst mit `python3 -m py_compile` prüfen.
3. Manuellen Fallback für Footer, Clipboard, Git und Tests verwenden.
4. Nur gezielt reparieren, nicht global gefährliche Ersetzungen durchführen.
5. Besonders vorsichtig mit literal `backslash+n`: nicht alle Vorkommen in Python-Dateien global ersetzen, weil sie in String-Literalen gültig sein können.
6. Wenn nur das physische Dateiende betroffen ist, nur das Dateiende reparieren.

---

## 19. Umgang mit literal backslash+n

Bekannte Fehlerquelle:

```text
SyntaxError: unexpected character after line continuation character
```

bei Zeilen wie:

```python
raise SystemExit(main())\n
```

Regeln:

1. Nicht pauschal alle backslash+n-Sequenzen in Python-Dateien ersetzen.
2. Prüfen, ob die Sequenz außerhalb eines Strings steht.
3. Wenn nur das Dateiende betroffen ist, gezielt das Dateiende reparieren.
4. Danach `python3 -m py_compile` ausführen.

---

## 20. Markdown-Fence-Regel

In generierten Dateien und Patches vorsichtig mit Markdown-Fences umgehen.

Regeln:

1. Innerhalb von Python-Heredocs keine literal Triple-Backticks erzeugen.
2. Wenn ein Markdown-Fence in generiertem Markdown nötig ist, in Python `fence = chr(96) * 3` verwenden.
3. In Chat-Antworten für Bash-Code bevorzugt Tilde-Fences verwenden.
4. Der Python-Heredoc darf nicht selbst literal Triple-Backticks enthalten.

---

## 21. Verhalten bei Abschlussprüfungen

Bei Abschlussprüfungen:

1. Keine Bundle-Skripte.
2. Relevante Tests laufen lassen.
3. Falls nötig RepoDossier-Exports verwenden.
4. Ergebnis ehrlich bewerten.
5. Unklarheiten ausdrücklich benennen.

---

## 22. Aktueller Projektstand für Footer

Aktuelle zuletzt bekannte Aufgabenfolge:

```text
4.4.a – Add full exporter model opt-in selector
4.4.b – Add remaining exporter model opt-in selectors
4.4.c – Centralize exporter model opt-in dispatch
DEV.1 – Add repository-local patch helper
DEV.2 – Add patch workflow rules
```

Nächste voraussichtliche Richtung:

```text
4.4.d – Full/AI/Docs/Changed Regression gegen bestehende Ausgabe absichern
4.4.e – erste echte Legacy-Export-Umschaltung kontrolliert vorbereiten
```

Diese Reihenfolge ist Orientierung. Fehlerfixes haben Vorrang.

---

## 23. Kurzfassung für `n`

Wenn Christian `n` schreibt:

1. Letzten Patch als grün behandeln.
2. Nächsten sinnvollen Commit liefern.
3. Patch als Download-Link zu einer `.sh`-Datei bereitstellen.
4. Repo-lokalen Helper verwenden, wenn möglich.
5. Alle Ausgaben in ein Logfile schreiben.
6. Tests laufen lassen.
7. Bei grünem Ergebnis committen.
8. Footer unten im Script.
9. Keine separate lange Übersicht außerhalb des Scripts.

---

## 24. Kurzfassung für Fixes

Wenn Christian einen Fehler postet:

1. Aktuellen Patch reparieren.
2. Nicht weitergehen.
3. Keine neue Feature-Aufgabe beginnen.
4. Tests erneut laufen lassen.
5. Bei Erfolg committen.
6. Footer zeigt Fix als aktuelle Aufgabe.
7. Rot nur für echte Probleme.
8. Ausgabe wieder als Download-Link zu einer `.sh`-Datei bereitstellen.

---

## 25. Wichtigste Prioritäten

Priorität bei Konflikten:

1. Sicherheit des Repos: keine falschen Repos patchen.
2. Fehlerfix vor neuem Feature.
3. Tests und Syntaxchecks vor Commit.
4. Keine unrelated Dateien committen.
5. Logs immer speichern.
6. Download-`.sh` statt riesigem Chat-Codeblock.
7. Footer immer im Script.
