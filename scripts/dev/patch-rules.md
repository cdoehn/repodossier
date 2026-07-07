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
5. Keine lange Erklärung außerhalb des Scriptblocks.
6. Wenn aus dem Chat klar ist, dass der letzte Schritt ein Fix war, dann den Fix als abgeschlossen behandeln.
7. Wenn Christian statt `n` eine Fehlermeldung postet, hat der Fix Vorrang.

---

## 2. Bedeutung von geposteten Fehlern

Wenn Christian Terminalausgaben, Tracebacks, Syntaxfehler oder Testfehler postet, gilt:

> Der aktuelle Patch ist noch nicht abgeschlossen. Repariere genau diesen Patch.

Daraus folgt:

1. Nicht zum nächsten Milestone-Schritt springen.
2. Zuerst den Fehler analysieren.
3. Einen gezielten Fix-Patch liefern.
4. Der Fix-Patch muss die ursprünglich geplanten Tests erneut ausführen.
5. Bei grünem Testlauf soll der ursprünglich geplante Commit erstellt werden.
6. Falls der ursprüngliche Commit noch nicht erstellt wurde, nutzt der Fix dieselbe Commit-Message.
7. Falls bereits committed wurde und ein neuer Fix nötig ist, bekommt der Fix einen eigenen Commit.
8. Im Footer wird der Fix als aktuelle gelbe Aufgabe markiert.

---

## 3. Ein-Codeblock-Regel

Für zukünftige Commit- und Fix-Antworten gilt:

1. Genau ein Bash-Codeblock.
2. Keine separate Browser-Übersicht nach dem Codeblock.
3. Die Aufgabenübersicht steht unten im Script als Footer.
4. Der Footer ist dadurch im Browser sichtbar und erscheint beim Ausführen auch im Terminal.
5. Erklärtext außerhalb des Codeblocks nur minimal, wenn unbedingt nötig.
6. Keine literal Markdown-Code-Fences im Heredoc ausgeben, weil das das Chat-Codefenster beschädigen kann.

---

## 4. Projektpfad

Standardpfad:

```bash
~/market_research/repo_dossier
```

Patch-Scripts starten grundsätzlich mit:

```bash
REPO_DIR="$HOME/market_research/repo_dossier"

cd "$REPO_DIR" || {
  echo "Fehler: Projektverzeichnis nicht gefunden: $REPO_DIR"
  return 1
}
```

---

## 5. Virtuelle Umgebung

Wenn `.venv` existiert, wird sie aktiviert:

```bash
if [ -d .venv ]; then
  source .venv/bin/activate
fi
```

Es wird immer `python3` verwendet.

---

## 6. Repository-lokaler Helper

Die bevorzugte Helper-Datei liegt jetzt im Projekt:

```text
scripts/dev/repo_patch_helper.py
```

Sie ersetzt die frühere externe Helper-Datei unter:

```text
~/dev-scripts/repo_patch_helper.py
```

Die externe Datei kann als Fallback existieren, soll aber nicht mehr bevorzugt werden.

Zukünftige Patches sollen zuerst die repo-lokale Datei verwenden:

```bash
REPO_HELPER="scripts/dev/repo_patch_helper.py"
```

Vor Nutzung kann geprüft werden:

```bash
[ -f "$REPO_HELPER" ] && python3 -m py_compile "$REPO_HELPER"
```

Wenn der Helper fehlt oder syntaktisch defekt ist:

1. Nicht blind abbrechen, wenn ein einfacher manueller Fallback möglich ist.
2. Bei Helper-bezogenen Patches manuelle Shell-Fallbacks nutzen.
3. Bei normalen Projektpatches klar melden, dass der Helper fehlt oder defekt ist.

---

## 7. Python-Heredoc-Imports

Wenn Python-Patches Helper brauchen:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("scripts/dev").resolve()))
from repo_patch_helper import (
    replace_once,
    write_text,
    write_test,
)
```

Für reine Dateierzeugung kann auch ohne Helper gearbeitet werden, wenn das robuster ist.

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

Für Snapshots, Prüfungen und Exporte werden RepoDossier/RepoContext-Befehle oder vorhandene Exportdateien genutzt.

---

## 10. Tests

Jeder Commit-Patch führt relevante Tests aus.

Bevorzugt:

```bash
python3 "$REPO_HELPER" pytest-existing --repo . --log "$TEST_LOG" tests/test_x.py tests/test_y.py
```

Fallback:

```bash
python3 -m pytest --color=yes tests/test_x.py tests/test_y.py 2>&1 | tee "$TEST_LOG"
TEST_STATUS=${PIPESTATUS[0]}
```

Regeln:

1. `--color=yes` verwenden.
2. Testausgabe in Log speichern.
3. Bei Testfehlern keinen Commit erstellen.
4. Bei Testfehlern Log in die Zwischenablage kopieren, wenn möglich.
5. Optionale Testdateien nur ausführen, wenn sie existieren.
6. Nach Fixes dieselben relevanten Tests erneut ausführen.

---

## 11. Syntaxchecks

Bei Python-Änderungen:

```bash
python3 -m compileall ...
```

oder mit Helper:

```bash
python3 "$REPO_HELPER" compile --repo . --log "$TEST_LOG" path1 path2
```

Wenn der Helper selbst repariert wird, zuerst direkt prüfen:

```bash
python3 -m py_compile scripts/dev/repo_patch_helper.py
```

---

## 12. Clipboard bei Fehlern

Bei Fehlern wird der Log kopiert, wenn möglich.

Mit Helper:

```bash
python3 "$REPO_HELPER" copy-log "$TEST_LOG" || true
```

Fallback:

```bash
if command -v xclip >/dev/null 2>&1; then
  cat "$TEST_LOG" | xclip -selection clipboard
fi
```

---

## 13. Commit-Regeln

Bei grünem Testlauf:

```bash
git add ...
git commit -m "..."
```

oder mit Helper:

```bash
python3 "$REPO_HELPER" commit-if-changed --repo . --message "Commit message" path1 path2
```

Regeln:

1. Commit nur bei staged Änderungen.
2. Wenn nichts zu committen ist, klar ausgeben.
3. Commit-Messages auf Englisch, kurz und präzise.
4. Keine unrelated Dateien committen.
5. Keine ungewollten Planning-Dateien committen.
6. Danach immer `git status --short`.

---

## 14. Git ohne Pager

Immer:

```bash
git --no-pager diff
git --no-pager log
```

oder Helper:

```bash
python3 "$REPO_HELPER" diff --repo . path1 path2
python3 "$REPO_HELPER" status --repo .
```

Nie plain `git diff` oder `git log`, wenn dadurch ein Pager hängen bleiben kann.

---

## 15. Footer-Pflicht

Jeder Patch- oder Fixblock enthält unten im Script eine Footer-Funktion.

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
Gelb  = aktuell / laufender Fix / gerade bearbeitet
Cyan  = nächste geplante Schritte / noch nicht begonnen
Rot   = echte Probleme, Testfehler, Blocker, nicht committed
```

Wichtig:

- Zukünftige Aufgaben nie rot markieren.
- Rot nur bei echten Problemen.

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
raise SystemExit(main()) + "literal backslash+n außerhalb eines Strings"
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
3. Genau einen Bash-Codeblock.
4. Repo-lokalen Helper verwenden, wenn möglich.
5. Tests laufen lassen.
6. Bei grünem Ergebnis committen.
7. Footer unten im Script.
8. Keine separate Übersicht außerhalb des Scripts.

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
