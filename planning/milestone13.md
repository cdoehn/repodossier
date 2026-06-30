# Milestone 13 – Changed Export

Ziel:
RepoContext soll einen gezielten Export der geänderten Dateien erzeugen können.
Der neue Export `changed.txt` soll nur relevante Änderungen enthalten und optional gegen einen Branch vergleichbar sein, z. B. gegen `main`.

---

## 13.1 – Git Diff Basis

### 13.1.a – Git-Diff-Dateiliste gegen Working Tree ermitteln
Ziel:
Ermittle Dateien, die im aktuellen Working Tree geändert sind.

Umsetzung:
- Neue Git-Funktion ergänzen, z. B. `get_changed_files(...)`
- Nutze `git diff --name-only`
- Berücksichtige geänderte, aber nicht gestagte Dateien
- Berücksichtige gestagte Dateien über `git diff --cached --name-only`
- Ergebnisse zusammenführen und deduplizieren
- Nur Dateien zurückgeben, keine Ordner

Tests:
- Repository mit unveränderten Dateien ergibt leere Liste
- Geänderte Datei wird erkannt
- Gestagte Datei wird erkannt
- Datei wird nicht doppelt zurückgegeben, wenn staged und unstaged geändert

---

### 13.1.b – Git-Diff-Dateiliste inklusive untracked Dateien
Ziel:
Untracked Dateien sollen im Changed Export auftauchen, wenn sie nicht ignoriert sind.

Umsetzung:
- `git ls-files --others --exclude-standard` einbinden
- Untracked Dateien mit Diff-Dateien zusammenführen
- .gitignore respektieren
- Sortierte, stabile Ausgabe sicherstellen

Tests:
- Neue untracked Textdatei wird erkannt
- Ignorierte Datei wird nicht erkannt
- Sortierung ist stabil

---

### 13.1.c – Gelöschte Dateien behandeln
Ziel:
Gelöschte Dateien sollen im Changed Export sichtbar sein, ohne dass versucht wird, ihren Inhalt zu lesen.

Umsetzung:
- Diff-Status mit `git status --porcelain` oder `git diff --name-status` ergänzen
- Deleted-Dateien mit Status markieren
- Scanner/Exporter darf bei deleted files nicht crashen
- Im Export klar ausgeben: Datei gelöscht

Tests:
- Gelöschte Datei erscheint als deleted
- Export läuft ohne FileNotFoundError
- Deleted-Datei enthält keinen Source-Dump

---

## 13.2 – Changed Export Datenmodell

### 13.2.a – ChangedFile-Modell einführen
Ziel:
Ein internes Modell für geänderte Dateien schaffen.

Umsetzung:
- Dataclass ergänzen, z. B. `ChangedFile`
- Felder:
  - `path`
  - `status`
  - `is_tracked`
  - `is_untracked`
  - `is_deleted`
  - optional `diff`
- Statuswerte z. B.:
  - modified
  - added
  - deleted
  - renamed
  - untracked

Tests:
- Modell kann alle erwarteten Statuswerte abbilden
- Deleted/untracked Flags sind korrekt ableitbar

---

### 13.2.b – Changed-Dateien mit bestehendem Scanner verbinden
Ziel:
Changed Export soll vorhandene Scanner-Logik wiederverwenden.

Umsetzung:
- Für existierende geänderte Dateien vorhandene FileInfo erzeugen
- Binary-Erkennung wiederverwenden
- Token-/Line-Count wiederverwenden
- Sprache/Lang-Erkennung wiederverwenden
- Deleted-Dateien separat behandeln

Tests:
- Changed Textdatei bekommt normale FileInfo
- Changed Binary-Datei wird erkannt und nicht gedumpt
- Deleted-Datei wird nicht gescannt

---

## 13.3 – changed.txt Exporter MVP

### 13.3.a – ChangedExporter erstellen
Ziel:
Eigenen Exporter für `changed.txt` implementieren.

Umsetzung:
- Neue Datei z. B. `src/repocontext/changed_exporter.py`
- Export-Struktur:
  1. Titel/Header
  2. Repository Summary
  3. Compare Mode
  4. Changed Files Summary
  5. Diff Summary
  6. Changed File Contents
  7. Deleted Files
  8. Binary/Skipped Files
- Bestehende Formatierungshelfer wiederverwenden, wenn vorhanden

Tests:
- Export enthält Header
- Export enthält Summary
- Export enthält geänderte Dateien
- Export enthält Source-Inhalte für Textdateien

---

### 13.3.b – Changed Files Summary ausgeben
Ziel:
Am Anfang von `changed.txt` eine kompakte Übersicht erzeugen.

Umsetzung:
- Anzahl geänderter Dateien
- Anzahl added/modified/deleted/untracked
- Anzahl Textdateien
- Anzahl Binary/skipped
- Optional gesamte geschätzte Tokenzahl

Beispiel:
Changed Files:
- Total: 5
- Modified: 2
- Added: 1
- Deleted: 1
- Untracked: 1

Tests:
- Summary zählt korrekt
- Deleted und untracked werden separat gezählt
- Leerer Changed Export zeigt 0 Dateien

---

### 13.3.c – Changed File Contents ausgeben
Ziel:
Nur Inhalte geänderter existierender Textdateien dumpen.

Umsetzung:
- Für jede geänderte Textdatei:
  - Dateipfad
  - Status
  - Sprache
  - Zeilenzahl
  - Token-Schätzung
  - Inhalt
- Binary-Dateien überspringen mit Hinweis
- Deleted-Dateien separat listen

Tests:
- Textdatei-Inhalt erscheint
- Binary-Inhalt erscheint nicht
- Deleted-Datei erscheint nicht im Source Dump

---

## 13.4 – Diff Integration

### 13.4.a – Unified Diff erfassen
Ziel:
`changed.txt` soll optional oder standardmäßig den eigentlichen Git-Diff enthalten.

Umsetzung:
- Git-Funktion ergänzen, z. B. `get_diff(...)`
- Nutze `git diff -- <file>`
- Für staged Änderungen zusätzlich `git diff --cached -- <file>`
- Für untracked Dateien optional keinen Git-Diff, sondern als added content behandeln
- Diff-Limits beachten, falls bereits Export-Limits existieren

Tests:
- Modified-Datei enthält Unified Diff
- Staged-Datei enthält Cached Diff
- Untracked-Datei crasht nicht
- Leerer Diff wird sauber behandelt

---

### 13.4.b – Diff Section im Export ergänzen
Ziel:
Vor dem Source Dump soll eine kompakte Diff-Ansicht stehen.

Umsetzung:
- Section `# Git Diff`
- Pro Datei:
  - Pfad
  - Status
  - Diff-Codeblock
- Große Diffs begrenzen oder klar markieren, falls Limit erreicht
- Binary-Diffs überspringen

Tests:
- Diff Section vorhanden
- Diff enthält erwartete geänderte Zeilen
- Binary-Datei wird als skipped markiert

---

## 13.5 – Compare Against Branch Support

### 13.5.a – Branch-Vergleich im Git-Modul implementieren
Ziel:
Changed Export soll gegen einen Branch vergleichen können.

Umsetzung:
- Funktion z. B. `get_changed_files_against_branch(branch)`
- Nutze:
  - `git diff --name-status <branch>...HEAD`
- Drei-Punkt-Vergleich bevorzugen, damit Branch-Basis sauber ist
- Fehler bei nicht existierendem Branch verständlich behandeln

Tests:
- Änderung gegenüber main wird erkannt
- Nicht existierender Branch liefert klare Exception oder Result-Fehler
- Leerer Vergleich ergibt leere Liste

---

### 13.5.b – Diff gegen Branch erfassen
Ziel:
Diff-Inhalte sollen bei Branch-Vergleich korrekt erzeugt werden.

Umsetzung:
- Funktion z. B. `get_diff_against_branch(branch, path=None)`
- Nutze:
  - `git diff <branch>...HEAD`
  - optional mit Pfadfilter
- Compare Mode im Export anzeigen:
  - Working tree
  - Against branch: main

Tests:
- Diff gegen Branch enthält committed Änderungen
- Working Tree Mode bleibt unverändert
- Compare Mode steht korrekt im Export

---

## 13.6 – CLI Integration

### 13.6.a – Neuer CLI-Befehl `changed` oder `export-changed`
Ziel:
RepoContext soll `changed.txt` per CLI erzeugen können.

Umsetzung:
- CLI-Subcommand ergänzen, bevorzugt:
  - `repocontext changed`
- Ausgabe standardmäßig:
  - `changed.txt`
- Optionen:
  - `--output changed.txt`
  - `--branch main`
  - optional `--include-diff`
  - optional `--no-diff`

Tests:
- `repocontext changed` erzeugt changed.txt
- `--output custom.txt` funktioniert
- `--branch main` ruft Branch-Vergleich auf

---

### 13.6.b – Hauptworkflow optional erweitern
Ziel:
Falls RepoContext bereits mehrere Exporte in einem Lauf erzeugt, soll `changed.txt` dort sinnvoll integrierbar sein.

Umsetzung:
- Prüfen, ob `repocontext full`, `export-ai`, `export-docs` getrennt sind
- Changed Export als separaten Befehl halten
- Nur wenn bestehende Architektur es nahelegt: in `repocontext all` oder ähnlichen Workflow aufnehmen
- Keine unnötige Kopplung an full/ai/docs

Tests:
- Bestehende Befehle bleiben unverändert grün
- Neuer Changed-Befehl beeinflusst full/ai/docs nicht

---

## 13.7 – .gitignore Integration prüfen

### 13.7.a – changed.txt in .gitignore sicherstellen
Ziel:
Da Milestone 4 bereits Exportdateien in .gitignore verwaltet, muss `changed.txt` korrekt berücksichtigt werden.

Umsetzung:
- Prüfen, ob `changed.txt` bereits automatisch ergänzt wird
- Falls nicht:
  - .gitignore-Integration um `changed.txt` ergänzen
- Keine doppelten Einträge erzeugen

Tests:
- changed.txt wird in .gitignore ergänzt
- Wiederholter Lauf erzeugt keinen doppelten Eintrag
- Bestehende full.txt/ai.txt/docs.txt-Regeln bleiben erhalten

---

## 13.8 – Dokumentation

### 13.8.a – README für Changed Export ergänzen
Ziel:
Nutzer sollen wissen, wie `changed.txt` erzeugt wird.

Umsetzung:
- README-Abschnitt ergänzen:
  - Zweck von changed.txt
  - Standardaufruf
  - Branch-Vergleich
  - Beispielausgabe
- Use RepoContext CLI exports for final checks; do not use deprecated snapshot scripts.

Beispiel-Kommandos:
- `repocontext changed`
- `repocontext changed --branch main`
- `repocontext changed --output changed.txt`

Tests:
- README enthält Changed Export
- README enthält `repocontext changed`
- Use RepoContext CLI exports for final checks; do not use deprecated snapshot scripts.

---

### 13.8.b – CLI Help prüfen
Ziel:
Argparse-Hilfe soll verständlich sein.

Umsetzung:
- Beschreibung für Changed-Befehl ergänzen
- Optionen klar erklären
- Branch-Vergleich benennen
- Output-Datei benennen

Tests:
- `repocontext changed --help` enthält branch/output
- CLI-Test prüft relevante Help-Texte

---

## 13.9 – Abschlussprüfung Milestone 13

### 13.9.a – Vollständige Testabdeckung
Ziel:
Alle neuen Funktionen sind mit Unit- und CLI-Tests abgedeckt.

Prüfen:
- Git changed files
- Untracked files
- Deleted files
- Branch comparison
- Diff generation
- Export formatting
- CLI changed command
- .gitignore changed.txt
- README docs

Tests:
- `python3 -m pytest --color=yes`

---

### 13.9.b – RepoContext Selbstexport
Ziel:
Milestone 13 mit RepoContext selbst prüfen.

Kommandos:
- `repocontext full`
- `repocontext export-ai`
- `repocontext export-docs`
- `repocontext changed`

Prüfen:
- `full.txt` enthält neue Changed-Export-Komponenten
- `ai.txt` priorisiert relevante neue Dateien sinnvoll
- `docs.txt` enthält README-Dokumentation
- `changed.txt` enthält aktuelle Änderungen

---

### 13.9.c – Final Review
Ziel:
Bestätigen, dass Milestone 13 vollständig umgesetzt ist.

Checkliste:
- Git diff integration vorhanden
- changed.txt generation vorhanden
- Compare against branch support vorhanden
- CLI-Aufruf vorhanden
- Tests grün
- Dokumentation aktualisiert
- Use RepoContext CLI exports for final checks; do not use deprecated snapshot scripts.
- Keine unnötigen Hilfsdateien
- Git status sauber nach Commit

---

## Empfohlene Implementierungsreihenfolge

1. 13.1.a – Git-Diff-Dateiliste gegen Working Tree
2. 13.1.b – Untracked Dateien
3. 13.1.c – Deleted Dateien
4. 13.2.a – ChangedFile-Modell
5. 13.2.b – Scanner-Verbindung
6. 13.3.a – ChangedExporter MVP
7. 13.3.b – Changed Files Summary
8. 13.3.c – Changed File Contents
9. 13.4.a – Unified Diff erfassen
10. 13.4.b – Diff Section im Export
11. 13.5.a – Branch-Vergleich Dateien
12. 13.5.b – Branch-Vergleich Diff
13. 13.6.a – CLI-Befehl
14. 13.6.b – Workflow-Kompatibilität prüfen
15. 13.7.a – .gitignore changed.txt
16. 13.8.a – README
17. 13.8.b – CLI Help
18. 13.9.a – Tests
19. 13.9.b – RepoContext Selbstexport
20. 13.9.c – Final Review
