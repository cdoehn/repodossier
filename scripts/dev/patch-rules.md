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

1. Standardannahme bleibt `<repo-root>`.
2. Zusätzlich soll das Script mit `git rev-parse --show-toplevel` das tatsächliche Repo-Root ermitteln.
3. Wenn das gefundene Repo-Root nicht zu RepoDossier gehört, abbrechen.
4. Wenn das aktuelle Verzeichnis kein Git-Repo ist, nach `<repo-root>` wechseln und dort erneut prüfen.
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

Für Snapshots, Prüfungen und Exporte werden RepoDossier-/previous project name-Befehle oder vorhandene Exportdateien genutzt.

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


### c: Erfolgsmarker als letzte Zeile

`c` gibt bei erfolgreichem Patchlauf als allerletzte Zeile fett grün aus:

```text
ERFOLG
```

Regeln:

1. Diese Zeile erscheint nur bei Exit-Code 0 des Patchscripts.
2. Sie steht nach Logfile- und Endzeit-Ausgabe.
3. Nach `ERFOLG` gibt `c` nichts Weiteres mehr aus.
4. Fehlerläufe zeigen kein `ERFOLG`.


### Progress-Renderer: Active-Zentrierung

In der zweispaltigen Roadmap/Milestone-Ansicht richtet der Progress-Renderer die Mittelpunkte der lila `active`-Bereiche vertikal zueinander aus.

Wenn der lila Bereich einer Spalte weiter oben liegt als der lila Bereich der anderen Spalte, fügt der Renderer vor dem früheren lila Bereich Leerzeilen ein. Dadurch werden die aktuellen Arbeitsbereiche optisch auf gleicher Höhe sichtbar, statt dass eine Spalte oben schon aktiv ist und die andere erst weit unten.


### Download-Link-Markierung in Chat-Antworten

Wenn ein Patchscript bereitgestellt wird, soll der Downloadlink im Chat sichtbar hervorgehoben werden.

Format:

```text
🟩 **Download:** **[dateiname.sh herunterladen](sandbox:/mnt/data/dateiname.sh)**
```

Regeln:

1. Der Linktext selbst ist fett.
2. Vor dem Link steht eine farbliche/visuelle Markierung, bevorzugt `🟩 **Download:**`.
3. Kein riesiges Patchscript direkt in die Antwort schreiben, wenn ein Downloadlink möglich ist.


### c: Kontextansicht am Erfolgsende

`c` validiert und bereitet die Roadmap/Milestone-Kontextansicht früh vor, zeigt sie aber bei erfolgreichem Patchlauf erst unten im Abschlussbereich.

Reihenfolge bei Erfolg:

1. Patchscript läuft.
2. `c` verschiebt das Script nach `~/Downloads/done/`.
3. `c` zeigt Logfile- und Endzeit-Hinweise.
4. `c` zeigt die Roadmap/Milestone-Kontextansicht.
5. `c` gibt als letzte Zeile fett grün `ERFOLG` aus.

Dadurch geht die Kontextansicht nicht am Anfang der Ausgabe verloren.


### c: Erfolgsmarker als letzte Zeile

`c` gibt bei erfolgreichem Patchlauf als allerletzte Zeile fett grün aus:

```text
ERFOLG
```

Fehlerläufe zeigen kein `ERFOLG`.


### c-Wait-Modus im Vordergrund

Der frühere Hintergrund-Wächter wurde wieder entfernt.

Stattdessen kann `c` im sichtbaren Vordergrund blockieren und auf neue Download-Patchscripts warten:

```bash
c --wait
```

Verhalten:

1. `c --wait` läuft im aktuellen Terminal und zeigt alle Ausgaben sichtbar an.
2. Beim Start werden bereits vorhandene `*.sh`-Dateien in `~/Downloads` als gesehen markiert.
3. Danach wartet `c --wait` auf das nächste neue `*.sh`-Patchscript direkt in `~/Downloads`.
4. Ein erkanntes Script wird über den normalen `c`-Runner ausgeführt.
5. Nach dem Patchlauf wartet `c --wait` wieder auf das nächste Script.
6. Stoppen mit `Ctrl+C`.

Sicherheitsregeln:

1. Kein Hintergrundprozess.
2. Keine automatische Ausführung bereits vorhandener alter Scripts.
3. Nicht als root.
4. Nur `*.sh` direkt in `~/Downloads`.
5. Nur Scripts, die maximal 30 Sekunden alt sind.
6. Gültige `repodossier-meta` bleiben Pflicht.
7. Roadmap- und Milestone-Progress-Metadaten bleiben Pflicht.
8. `bash -n` muss grün sein.
9. Bereits angewendete SHA-256-Hashes werden übersprungen.
10. Jede gesehene Datei/Hash-Kombination wird nur einmal gestartet.

Der frühere Modus `c --watch-up`, `c --watch-status`, `c --watch-down` wird nicht mehr verwendet.



### c: Erfolgsleiste als letzte Zeile

Bei erfolgreichem Patchlauf gibt `c` als allerletzte Zeile eine fette grüne Erfolgsleiste über die Terminalbreite aus.

Die sichtbare Zeile beginnt mit:

```text
ERFOLG  ERFOLG  ERFOLG
```

Fehlerläufe zeigen keine Erfolgsleiste.


### Patch-Preflight-Linter

Neue Download-Patchscripts sollen zusätzlich mit dem repo-lokalen Preflight-Linter prüfbar sein:

    python3 scripts/dev/lint_patch_script.py --script ~/Downloads/patch.sh --repo .

Der Linter prüft vor der eigentlichen Ausführung:

1. gültige `repodossier-meta` über den bestehenden Metadata-Validator,
2. Roadmap- und Milestone-Progress-Metadaten,
3. kein `bundle_project.sh`,
4. keine eigene globale `tee`-Logumleitung,
5. keine Clipboard-Tools wie `xclip`, `xsel` oder `wl-copy`,
6. kein Aider-Aufruf in direkten Patchscripts,
7. `git diff`, `git log` und `git show` nur mit `--no-pager` oder `GIT_PAGER=cat`,
8. vorhandene Footer-Funktion,
9. vorhandene Tests oder Syntax-/Smoke-Checks,
10. keine literal Triple-Backticks in Patch-Heredocs.

Der Linter ist die technische Vorstufe für `c --dry-run` und soll verhindern, dass formal fehlerhafte Patches überhaupt in den normalen Patchlauf kommen.


### Workflow-Verbesserungen Commit-Serie

Die nächsten Workflow-Verbesserungen werden in fünf kleinen Commits umgesetzt:

1. `Add patch script preflight linter`
2. `Add patch runner dry-run mode`
3. `Add progress anchor metadata resolution`
4. `Extend r export runner modes`
5. `Normalize patch workflow rules schema`

Der Quarantäne-Ordner für Downloads wird bewusst nicht umgesetzt.


### Patch-Preflight-Linter: Heredoc-Bewusstsein

Der Patch-Preflight-Linter prüft Workflow-Verbote in echten Shell-Zeilen außerhalb von Heredoc-Bodies.

Grund:

1. Patchscripts erzeugen häufig Tests.
2. Diese Tests müssen verbotene Begriffe wie `bundle_project.sh`, `xclip`, `aider` oder `git diff` als Test-Fixtures enthalten dürfen.
3. Solche Fixture-Strings sind keine ausgeführten Patch-Kommandos.
4. Deshalb ignoriert der Linter Workflow-Verbote innerhalb von Heredoc-Bodies.
5. Nach Ende eines Heredocs werden Shell-Kommandos wieder normal geprüft.

Literal Triple-Backticks bleiben weiterhin global verboten, auch innerhalb von Heredocs. Wenn ein Test Triple-Backticks erzeugen muss, soll er sie über `chr(96) * 3` zusammensetzen.


### Patch-Preflight-Linter: Git-Diff-Ausnahmen

Der Linter verbietet `git diff`, `git log` und `git show` ohne `--no-pager`, wenn dabei Terminalausgabe entstehen kann.

Erlaubte Ausnahme:

    git diff --cached --quiet

und allgemein `git diff ... --quiet`.

Grund:

- `--quiet` erzeugt keine Diff-Ausgabe.
- Der Befehl dient nur als Exit-Code-Check, zum Beispiel vor einem Commit.
- Dadurch kann kein Pager hängen bleiben.


### Patch-Preflight-Linter: Quoted diagnostic text

Der Linter prüft echte Shell-Kommandos. Quoted Diagnose- oder Erklärungstexte werden für Kommando-Regeln ignoriert.

Beispiele, die als Text erlaubt sind:

    echo "git diff --cached --quiet is documented here"
    echo 'bundle_project.sh xclip aider git diff are quoted diagnostics'

Echte unquoted Befehle bleiben verboten, zum Beispiel:

    git diff -- src
    ./bundle_project.sh


### Patch-Preflight-Linter: Heredoc-Bewusstsein

Der Linter ist heredoc-bewusst: Workflow-Verbote werden nur in echten Shell-Zeilen außerhalb von Heredoc-Bodies geprüft. Test-Fixtures dürfen verbotene Begriffe als Strings enthalten. Literal Triple-Backticks bleiben global verboten.


### Progress-Renderer: feste Statusmarker

Der Progress-Renderer verwendet feste einspaltige Statusmarker statt farbiger Emoji-Quadrate.

Grund:

1. Emoji-Quadrate können je nach Terminal/Font als doppelte oder uneinheitliche Breite gerendert werden.
2. Dadurch verschieben sich Line-Number-Spalten und Text optisch.
3. Feste Marker bleiben stabil:
   - `✓` = done
   - `■` = active
   - `~` = partial
   - `!` = todo
4. Die Farbcodierung bleibt erhalten.


### c: Dry-run-Modus

`c` kann ein Download-Patchscript prüfen, ohne es auszuführen:

    c --dry-run
    c --dry-run ~/Downloads/patch.sh

Der Dry-run macht:

1. neuestes oder explizit angegebenes Patchscript auswählen,
2. `repodossier-meta` validieren,
3. Progress-Kontext vorbereiten,
4. Patch-Preflight-Linter ausführen,
5. Wiederholungsprüfung ausführen,
6. Frischeprüfung ausführen,
7. `bash -n` ausführen,
8. Kontext unten anzeigen,
9. mit grüner Zeile `DRY-RUN OK` enden.

Der Dry-run macht ausdrücklich nicht:

1. Patchscript ausführen,
2. Commit erstellen,
3. Script nach `done/` verschieben,
4. Script nach `failed/` verschieben,
5. Applied-Ledger aktualisieren.

### c: Dry-run-Syntaxfehler

Wenn `c --dry-run` bei `bash -n` einen Syntaxfehler findet, bleibt das Script unverändert in `~/Downloads`.

Es wird nicht nach `failed/` verschoben, weil Dry-run ausdrücklich keine Datei-Bewegungen durchführen soll.

### c: Wait-Umgebungsisolation

Wenn `c --wait` ein Patchscript startet, darf die interne Variable `C_RUNNER_WAIT_CHILD` nicht in das Patchscript selbst weitergereicht werden. Sonst verhalten sich Tests, die `c` in Subprozessen starten, fälschlich wie Wait-Kindprozesse.


### c: Selbstkopie bei Runner-Updates

`c` startet sich aus einer temporären Selbstkopie, bevor es ein Patchscript ausführt.

Grund:

1. Manche Patchscripts ändern `scripts/dev/run_latest_download_patch.sh`.
2. Bash kann ein laufendes Script teilweise weiter aus der Datei lesen.
3. Wenn die Datei während des Laufs überschrieben wird, kann das laufende `c` am Ende syntaktisch stolpern.
4. Die temporäre Selbstkopie entkoppelt den laufenden Prozess von Änderungen an der Quell-Datei.

Interne Variablen wie `C_RUNNER_SELF_COPY`, `C_RUNNER_ORIGINAL`, `C_RUNNER_TEMP_COPY`, `C_RUNNER_WAIT_CHILD` und `C_RUNNER_WATCH_CHILD` dürfen nicht in Patchscripts weitergereicht werden.


### Progress-Metadaten: anchor statt Zeilennummern

Progress-Einträge dürfen weiterhin konkrete Zeilenbereiche verwenden:

    # repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"planning/roadmap_next.md","start":10,"end":20}

Alternativ darf ein stabiler Anchor verwendet werden:

    # repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"planning/roadmap_next.md","anchor":"## Full Markdown Export"}

Regeln:

1. Ein Progress-Eintrag braucht entweder `start` und `end` zusammen oder `anchor`.
2. `anchor` muss ein nichtleerer String sein.
3. Der Anchor muss im referenzierten Repo-Dateiinhalt vorkommen.
4. Wenn der Anchor auf eine Markdown-Überschrift zeigt, rendert der Progress-Renderer den Abschnitt bis zur nächsten Überschrift gleicher oder höherer Ebene.
5. Wenn der Anchor auf normalen Text zeigt, rendert der Progress-Renderer nur diese Zeile plus den konfigurierten Kontext.
6. Explizite `start`/`end`-Bereiche bleiben vollständig kompatibel.


### r: Export-Modi

Der `r`-Runner unterstützt explizite Export-Modi:

    r
    r all
    r full
    r ai
    r docs
    r changed
    r --dry-run full ai
    r --list-modes

Regeln:

1. Ohne Argumente bleibt `r` kompatibel und führt `all` aus.
2. `all` entspricht `full`, `ai`, `docs`, `changed`.
3. Alias-Modi bleiben kurz:
   - `quick` = `ai`
   - `doc` = `docs`
   - `changes` = `changed`
4. `--dry-run` zeigt die geplanten Befehle, führt aber keine Exporte aus.
5. Unbekannte Modi brechen mit Exit-Code 2 ab.


### Patch workflow rules schema

Die menschlich lesbaren Regeln in dieser Datei werden zusätzlich durch eine normalisierte maschinenlesbare Regeldatei gespiegelt:

    scripts/dev/patch-workflow-rules.json

Die zugehörige Schema-Beschreibung liegt hier:

    scripts/dev/patch-workflow-rules.schema.json

Validierung:

    python3 scripts/dev/validate_patch_workflow_rules.py

Ziel:

1. wichtige Patch-Regeln haben stabile IDs,
2. Kategorien und Schweregrade sind normalisiert,
3. Tests können Regeln prüfen, ohne Markdown-Struktur zu parsen,
4. künftige Runner- und Linter-Erweiterungen können dieselbe Regelbasis verwenden.

Neue Workflow-Regeln sollen bevorzugt in beiden Formen gepflegt werden:

1. lesbar in `scripts/dev/patch-rules.md`,
2. strukturiert in `scripts/dev/patch-workflow-rules.json`.


### Dev environment doctor

Für neue Rechner oder frisch kopierte Arbeitsbäume gibt es einen schnellen lokalen Check:

    python3 scripts/dev/check_dev_environment.py

Der Check prüft unter anderem:

1. Git-Repository und Repo-Root,
2. Git-Identität (`user.name`, `user.email`),
3. Python und pytest,
4. `repodossier` CLI und `pipx`,
5. wichtige Dev-Runner wie `c` und `r`,
6. maschinenlesbare Workflow-Regeln und Validator.

Mit `--strict` schlägt der Check auch dann fehl, wenn optionale Komfortwerkzeuge wie `pipx` oder die global verfügbare `repodossier` CLI fehlen.


### Progress context column packing

Der Progress-Renderer packt Roadmap- und Milestone-Spalte unabhängig voneinander.

Regeln:

1. Ein langer Block in einer Spalte darf den Folgestatus der anderen Spalte nicht nach unten schieben.
2. Innerhalb einer Spalte schließen Statusbereiche direkt aneinander an, wenn der Textbereich fortlaufend ist.
3. Wenn eine Spalte kürzer ist, darf sie mit weiterem verfügbarem Kontext aus derselben Datei aufgefüllt werden.
4. Side-by-side bleibt Standard, nutzt aber nur eine schmale Lücke zwischen den Spalten.
5. `NO_COLOR=1` bleibt für Tests und Log-Auswertung unterstützt.


### Progress context status compatibility

Der Progress-Renderer behält die etablierten Statusmarker bei:

1. `done` → `✓`
2. `active` → `■`
3. `partial` → `~`
4. `todo` → `!`

Bei überlappenden Bereichen gilt eine explizite Priorität:

1. `active` schlägt `todo`,
2. `todo` schlägt `partial`,
3. `partial` schlägt `done`.

Die Marker bleiben festbreit formatiert, damit bestehende Log- und Testauswertung stabil bleibt.


### Progress context active center alignment

Der Progress-Renderer richtet Roadmap- und Milestone-Spalte am aktiven Bereich aus.

Regeln:

1. Wenn beide Spalten `active`-Bereiche enthalten, wird die Mitte der aktiven Bereiche auf dieselbe Ausgabehöhe gebracht.
2. Oberhalb des aktiven Bereichs wird zuerst mit vorhandenem Text aus derselben Datei aufgefüllt.
3. Wenn der Dateianfang erreicht ist, darf oberhalb Leerraum entstehen.
4. Unterhalb wird mit weiterem verfügbarem Kontext aufgefüllt, solange Dateiinhalt vorhanden ist.
5. Statusmarker und Prioritäten bleiben kompatibel: `✓`, `■`, `~`, `!`.


### Progress context below-active fill

Nach der vertikalen Ausrichtung der `active`-Bereiche füllt der Progress-Renderer unterhalb jedes aktiven Bereichs weiter auf, sofern in der Datei noch Text vorhanden ist.

Regeln:

1. Mindestens eine folgende Kontextzeile nach `active` wird ergänzt, wenn die Datei sie enthält.
2. Die Active-Mitte bleibt zwischen Roadmap und Milestone ausgerichtet.
3. Wenn kein Text mehr folgt, darf unterhalb Leerraum entstehen.


### Progress context anchor-safe fill

`active`-Ausrichtung und Kontextauffüllung unterscheiden zwischen expliziten Zeilenbereichen und Anchor-Bereichen.

Regeln:

1. `start`/`end`-basierte `active`-Bereiche dürfen unterhalb um verfügbare Kontextzeilen ergänzt werden.
2. Anchor-basierte Bereiche bleiben auf ihre aufgelöste Range begrenzt.
3. Heading-Anchor dürfen nicht in den nächsten Markdown-Abschnitt hineinlaufen.
4. Plain-Text-Anchor dürfen bei `context: 0` nicht automatisch die Folgezeile einschließen.


### Public repository hygiene

RepoDossier is intended to be safe for a public repository.

Rules:

1. Tracked files must not contain contributor-specific home paths, user names, private email addresses, or workstation names.
2. Local convenience aliases are installed by `scripts/dev/install_aliases.sh`.
3. Alias installation writes local paths only to the user's shell rc file, not to tracked repository files.
4. Public hygiene can be checked with:

       python3 scripts/dev/audit_public_repo.py --tracked

5. Before publishing or force-pushing rewritten history, run:

       python3 scripts/dev/audit_public_repo.py --history

History rewrite is an explicit maintenance step and must not happen automatically inside normal patch scripts.


### Export runner default modes

The development export runner is repository-agnostic and can run in any Git repository.

Default modes stay intentionally small:

    full ai

Additional modes such as `docs` and `changed` are explicit opt-ins.


### Export runner mode compatibility

The development export runner preserves mode compatibility:

1. `--list-modes` prints canonical modes without requiring a Git repository.
2. Normal default modes are `full ai`.
3. Dry-run default modes are `full ai docs changed` so all actions are visible.
4. Aliases are accepted: `quick` -> `ai`, `doc` -> `docs`, `changes` -> `changed`.


### Export runner dry-run output

The development export runner dry-run output is part of the compatibility contract.
It must print concrete command preview lines such as `Befehl: repodossier full`.
`--list-modes` includes `all`; `all` expands to `full ai docs changed`.
