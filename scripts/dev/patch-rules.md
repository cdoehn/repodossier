# Patch Workflow Rules

Diese Datei dokumentiert die aktuell geltenden Arbeitsregeln für `n`, Fixes, Download-Patches und Commit-Patches in diesem Chat.

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

## 4. Ausführung mit `c`

Auf dem Zielsystem wird das Kürzel `c` als Bash-Funktion eingerichtet.

`c` ruft den repo-lokalen Runner auf:

```text
scripts/dev/run_latest_download_patch.sh
```

Ohne Argumente macht `c` Folgendes:

1. Aus `~/Downloads` das neueste `*.sh`-Patchscript holen.
2. Das Script mit `bash -n` syntaktisch prüfen.
3. `stdout` und `stderr` zusammen in eine Logdatei schreiben.
4. Das Script ausführen.
5. Bei Erfolg das Script nach `~/Downloads/done/` verschieben.
6. Bei Fehler das Script nach `~/Downloads/failed/` verschieben.
7. Die Logdatei in `~/Downloads` belassen.

Optional kann ein konkretes Script angegeben werden:

```bash
c ~/Downloads/mein_patch.sh
```

---

## 5. Logging und Clipboard

Ab jetzt übernimmt `c` die zentrale Log-Verwaltung.

Regeln für einzelne Patch-Scripts:

1. Patch-Scripts sollen keine eigene globale `exec > >(tee ...) 2>&1`-Logumleitung mehr einrichten.
2. Patch-Scripts sollen keine eigene Clipboard-Logik mit `xclip` mehr enthalten.
3. Patch-Scripts sollen normal auf `stdout` und `stderr` schreiben.
4. Patch-Scripts müssen korrekte Exit-Codes liefern.
5. `c` schreibt die vollständige Ausgabe in eine Logdatei unter `~/Downloads`.
6. Wenn Christian Fehler postet, genügt die Terminalausgabe oder die von `c` erzeugte Logdatei.

Das macht Sinn, weil Logging, Syntaxprüfung und Verschieben der Download-Scripts dadurch zentral, einheitlich und weniger fehleranfällig werden.

---

## 6. Repo-Root-Erkennung

Patch-Scripts sollen das Repository-Root selbst finden.

Regeln:

1. Standardannahme bleibt `~/market_research/repo_dossier`.
2. Zusätzlich soll das Script mit `git rev-parse --show-toplevel` das tatsächliche Repo-Root ermitteln.
3. Wenn das gefundene Repo-Root nicht zu RepoDossier gehört, abbrechen.
4. Wenn das aktuelle Verzeichnis kein Git-Repo ist, nach `~/market_research/repo_dossier` wechseln und dort erneut prüfen.
5. Wenn RepoDossier nicht gefunden wird, klar abbrechen und keinen Commit erstellen.

---

## 7. Virtuelle Umgebung

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

## 8. Repository-lokaler Helper

Die bevorzugte Helper-Datei liegt im Projekt:

```text
scripts/dev/repo_patch_helper.py
```

Die frühere externe Datei unter folgendem Pfad ist nur noch Fallback:

```text
~/dev-scripts/repo_patch_helper.py
```

Wenn der Helper fehlt oder syntaktisch defekt ist:

1. Nicht blind abbrechen, wenn ein einfacher manueller Fallback möglich ist.
2. Bei Helper-bezogenen Patches manuelle Shell-Fallbacks nutzen.
3. Bei normalen Projektpatches klar melden, dass der Helper fehlt oder defekt ist.
4. Wenn der Helper selbst repariert wird, nicht den defekten Helper für die Reparatur voraussetzen.

---

## 9. Keine Aider-Prompts

Bei Commit-Patches gilt:

1. Kein Aider verwenden.
2. Keine Aider-Prompts ausgeben.
3. Direkte Python-/Bash-Patches liefern.
4. Nur wenn Christian ausdrücklich Aider verlangt, darf Aider verwendet werden.

---

## 10. Kein `bundle_project.sh`

`bundle_project.sh` wird nicht mehr verwendet.

Für Snapshots, Prüfungen und Exporte werden RepoDossier-/RepoContext-Befehle oder vorhandene Exportdateien genutzt.

---

## 11. Tests

Jeder Commit-Patch führt relevante Tests aus.

Regeln:

1. `--color=yes` verwenden.
2. Bei Testfehlern keinen Commit erstellen.
3. Optionale Testdateien nur ausführen, wenn sie existieren.
4. Nach Fixes dieselben relevanten Tests erneut ausführen.
5. Testausgaben werden normal ausgegeben; `c` übernimmt die Logdatei.
6. Wenn Tests fehlen, aber der Patch sinnvoll prüfbar ist, mindestens Syntax-/Smoke-Checks ausführen.

---

## 12. Syntaxchecks

Bei Python-Änderungen werden Syntaxchecks ausgeführt.

Bevorzugt mit Helper:

```bash
python3 "$REPO_HELPER" compile --repo . path1 path2
```

Wenn der Helper selbst repariert wird, zuerst direkt prüfen:

```bash
python3 -m py_compile scripts/dev/repo_patch_helper.py
```

Der Download-Patch selbst wird vor Ausführung bereits durch `c` mit `bash -n` geprüft.

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

---

## 14. Git ohne Pager

Immer:

```bash
git --no-pager diff
git --no-pager log
git --no-pager status
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
3. Manuellen Fallback für Footer, Git und Tests verwenden.
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
raise SystemExit(main())\\n
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
DEV.3 – Add c download patch runner
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
4. Patch-Script schreibt normal nach stdout/stderr.
5. `c` übernimmt Syntaxprüfung, Logdatei, farbige Struktur, 60-Minuten-Warnung und Verschieben nach done/failed.
6. Repo-lokalen Helper verwenden, wenn möglich.
7. Tests laufen lassen.
8. Bei grünem Ergebnis committen.
9. Footer unten im Script.

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
5. `c` verwaltet Download-Scripts, Wiederholungsprüfung und Logs zentral.
6. Download-`.sh` statt riesigem Chat-Codeblock.
7. Footer immer im Script.

---

## c-Runner UX, Farben und 60-Minuten-Sicherheitsbremse

Der Download-Patch-Runner `c` ist die zentrale Ausführungsschicht für heruntergeladene Patchscripts.

Regeln:

1. `c` nutzt eine eigene Türkis/Cyan-Akzentfarbe, damit seine Ausgaben klar von Patch-Ausgaben unterscheidbar sind.
2. `c` strukturiert die Ausgabe in sichtbare Abschnitte: Start, Sicherheitsprüfung, Syntaxprüfung, Ausführung und Abschluss.
3. `c` sagt explizit, was es gerade tut: welches Script, welches Logfile, welcher Ordner, welcher Check und welches Ergebnis.
4. Erfolg wird grün markiert.
5. Warnungen werden gelb markiert.
6. Fehler werden rot markiert.
7. Pfade und Logfiles werden farblich hervorgehoben.
8. `c` führt ohne Rückfrage nur Patchscripts aus, die höchstens 60 Minuten alt sind.
9. Wenn das neueste gefundene Patchscript älter als 60 Minuten ist, zeigt `c` eine Warnung an.
10. Ein älteres Patchscript wird nur nach ausdrücklicher Bestätigung ausgeführt.
11. Ohne Bestätigung bleibt das Script in `~/Downloads` liegen und wird weder nach `done` noch nach `failed` verschoben.
12. `c` wird getestet: Auswahl des neuesten Scripts, erfolgreiche Ausführung, Fehler-Ausführung, Syntaxfehler, Logdatei, done/failed-Verschiebung und Altersbestätigung.

Einzelne Patchscripts sollen weiterhin keine eigene globale Logumleitung und keine eigene Clipboard-Logik enthalten. `c` übernimmt diese Verantwortung zentral.

---

## c-Runner Wiederholungsprüfung und r-Runner

### c: bereits angewendete Scripts

`c` erkennt bereits erfolgreich angewendete Patchscripts über SHA-256-Hash.

Regeln:

1. Erfolgreich ausgeführte Scripts werden in `~/Downloads/done/.applied_patch_hashes.tsv` protokolliert.
2. Zusätzlich vergleicht `c` neue Scripts gegen bereits vorhandene `*.sh`-Dateien in `~/Downloads/done`.
3. Wenn ein Script bereits angewendet wurde, warnt `c` rot.
4. Ein bereits angewendetes Script wird nicht automatisch erneut ausgeführt.
5. Eine erneute Ausführung ist nur nach ausdrücklicher Bestätigung erlaubt.
6. Ohne Bestätigung bleibt das Script in `~/Downloads` liegen und wird weder nach `done` noch nach `failed` verschoben.

### c: Selbst-Update-Sicherheit

`c` startet sich vor der eigentlichen Patch-Ausführung als temporäre Kopie neu.

Grund:

1. Manche Patches aktualisieren `scripts/dev/run_latest_download_patch.sh`.
2. Wenn Bash ein Script ausführt, das währenddessen überschrieben wird, kann die laufende Shell später aus der neuen Datei weiterlesen und mit Syntaxfehlern abbrechen.
3. Die temporäre Kopie verhindert diese Selbstüberschreibung während der laufenden Ausführung.
4. Dadurch darf ein Patch den `c`-Runner selbst sicher aktualisieren.

### r: RepoDossier-Export für aktuelles Repo

Das Kürzel `r` ruft den repo-lokalen Runner auf:

```text
scripts/dev/run_repodossier_exports.sh
```

`r` macht Folgendes:

1. Aktuelles Git-Repo erkennen.
2. In dieses Repo-Root wechseln.
3. `repodossier full` ausführen.
4. `repodossier export-ai` ausführen.
5. `full.txt` nach `~/Downloads/full.txt` kopieren.
6. `ai.txt` nach `~/Downloads/ai.txt` kopieren.
7. `scripts/dev/patch-rules.md` nach `~/Downloads/patch-rules.md` kopieren, wenn die Datei vorhanden ist.
8. Vorhandene Dateien in `~/Downloads` werden überschrieben.

`r` ist bewusst für das aktuelle Git-Repo gedacht, nicht nur für das RepoDossier-Entwicklungsrepo.

`r` soll keinen Box-Rahmen mit `╔`, `║` oder `╚` rendern. Stattdessen nutzt `r` eine einfache farbige Überschrift mit Trennlinie und die normalen Abschnittsmarker.

---

## Patch-Metadaten und Progress-Kontext

Jedes neue Download-Patchscript soll oben maschinenlesbare JSON-Kommentarzeilen enthalten.

Format:

```bash
# repodossier-meta: {"type":"patch","id":"DEV.6","title":"Add progress renderer","commit":"Add patch metadata progress renderer"}
# repodossier-meta: {"type":"progress","panel":"roadmap","status":"done","file":"planning/ROADMAP.md","start":1,"end":20}
# repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"planning/ROADMAP.md","start":21,"end":30}
# repodossier-meta: {"type":"progress","panel":"milestone","status":"partial","file":"planning/MILESTONE4.md","start":40,"end":50}
# repodossier-meta: {"type":"progress","panel":"milestone","status":"todo","file":"planning/MILESTONE4.md","start":51,"end":70}
# repodossier-meta: {"type":"display","context":4,"layout":"side-by-side","frame":false}
```

Pflicht für `type=patch`:

1. `id`
2. `title`
3. `commit`

Pflicht für normale `c`-Patchscripts: mindestens ein `type=progress`-Eintrag für `roadmap` und mindestens ein `type=progress`-Eintrag für `milestone`.

1. `panel`: `roadmap` oder `milestone`
2. `status`: `done`, `active`, `partial`, `todo`
3. `file`: repo-relativer Pfad
4. `start`: Startzeile
5. `end`: Endzeile

Farben:

1. `done` = grün
2. `active` = lila
3. `partial` = gelb
4. `todo` = rot

`c` validiert diese Metadaten vor der Ausführung mit `scripts/dev/validate_patch_metadata.py`.

Progress-Metadaten sind für normale `c`-Patchscripts Pflicht. `c` rendert mit `scripts/dev/show_progress_context.py` Roadmap links und Milestone rechts, ohne Rahmen und mit Kontextzeilen oberhalb und unterhalb. Wenn ein Patch keine Roadmap- und Milestone-Progress-Zeilen enthält, wird er vor der Ausführung blockiert.
