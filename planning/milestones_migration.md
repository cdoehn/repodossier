# PatchHarbor / RepoDossier Migration – verbleibende Milestones

Stand dieser Planung: nach `PATCHHARBOR.08d`, also nachdem PatchHarbor die generische Runner-/Compatibility-Grundlage, die Source-Wrapper-Grundlage und die Source-side-Adoption-Planung weitgehend dokumentiert hat.

Diese Datei beschreibt die noch offenen Milestones bis zum Abschluss der Migration und zur vollständigen Bereinigung beider Repositories:

- Quellrepo: `repo_dossier`
- Zielrepo: `patch-harbor`

Die Datei ist bewusst als langfristige Arbeitsgrundlage geschrieben. Einzelne Punkte können später in kleinere Patch-Commits aufgeteilt werden, wenn Tests oder Scope es verlangen.

---

## 0. Kontextvorschau / Einbindung in den Repo-Kontext

Empfohlener Ablageort im Zielrepo:

```text
planning/milestones.md
```

Alternativ, wenn PatchHarbor Planungsdateien lieber unter `docs/` hält:

```text
docs/milestones.md
```

Für die Patch-Runner-Kontextvorschau kann die Datei in zukünftigen Patchscripts über `repodossier-meta` referenziert werden:

```bash
# repodossier-meta: {"type":"progress","panel":"milestone","status":"active","file":"planning/milestones.md","start":120,"end":180,"label":"PATCHHARBOR.09 Source-side runner adoption"}
```

Empfohlen ist, in jedem künftigen Patchscript neben Roadmap/Status auch den passenden Abschnitt dieser Datei als `panel:"milestone"` zu referenzieren. Dadurch kann die Kontextanzeige gezielt den aktuellen Milestone anzeigen, statt nur die allgemeine Roadmap.

Damit die Datei im RepoDossier-/PatchHarbor-Export sichtbar wird:

1. Datei im Repo ablegen, z. B. `planning/milestones.md`.
2. Datei mit Git tracken.
3. Sicherstellen, dass sie nicht durch `.gitignore`, Export-Ignore-Regeln oder Split-Konfiguration ausgeschlossen wird.
4. Bei künftigen Patchscripts den passenden Abschnitt per `repodossier-meta` referenzieren.
5. Danach den normalen Repo-Kontext-/Export-Befehl ausführen.

Wenn die Kontextvorschau nur getrackte Dateien berücksichtigt, reicht typischerweise:

```bash
git add planning/milestones.md
git commit -m "Add migration milestones"
```

---

## 1. Aktueller stabiler Stand

### Abgeschlossen oder als abgeschlossen geplant

```text
PATCHHARBOR.01   Dev-Script-Inventar im Quellrepo
PATCHHARBOR.02   Zielrepo-Skeleton
PATCHHARBOR.03   erste Extraktionsphase
PATCHHARBOR.04   Workflow-Rules-Grundlage
PATCHHARBOR.05   Patch-Script-Linting-Grundlage
PATCHHARBOR.06   Runner-/Compatibility-Grundlage
PATCHHARBOR.07   Source-Wrapper-/Compatibility-Grundlage
PATCHHARBOR.08a  Source-side-Adoption-Inventar
PATCHHARBOR.08b  Source-side Runner-Wrapper-Draft
PATCHHARBOR.08c  Source-side Alias-Kompatibilitätsplan
PATCHHARBOR.08d  Source-side Runner-Kompatibilitätstestplan
```

### Wichtiges Prinzip ab hier

Bis zur echten Adoption im Quellrepo gilt:

- PatchHarbor bleibt das generische Zielrepo.
- RepoDossier bleibt zunächst Quelle und Nutzer des Workflows.
- Source-seitige Änderungen müssen klein, reversibel und mit Focused Tests abgesichert sein.
- Keine alten RepoDossier-Spezialnamen in PatchHarbor-Core übernehmen.
- Keine privaten Pfade, Mailadressen, Gerätenamen oder lokalen Checkout-Pfade in getrackten Dateien speichern.
- Alte Scripts erst löschen, wenn Ersatz plus Paritätstests grün sind.

---

# Milestone 08 – Source-side Adoption vorbereiten und abschließen

## PATCHHARBOR.08e – Source-side Adoption Acceptance

**Commit:** `Add source-side adoption acceptance documentation`

**Ziel:**  
Abschlussdokumentation für 08a–08d. Noch keine Source-Repo-Änderung.

**Dateien im Zielrepo:**

```text
docs/source-side-adoption-acceptance.md
tests/test_source_side_adoption_acceptance.py
```

**Inhalt:**

- Was 08a–08d vorbereitet haben.
- Was noch nicht getan wurde.
- Welche Voraussetzungen für echte RepoDossier-Adoption gelten.
- Explizite Non-Goals:
  - kein RepoDossier-Patch
  - keine Wrapper-Datei
  - keine Alias-Installation
  - keine Export-Migration
  - keine Löschung alter Scripts

**Akzeptanz:**

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest tests.test_source_side_adoption_acceptance
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py'
PYTHONPATH=src python3 -m patchharbor doctor --repo .
```

---

# Milestone 09 – Erste echte Source-side Runner-Adoption in RepoDossier

Ab hier wird erstmals das Quellrepo gezielt geändert. Jeder Patch muss klar sagen, ob er Zielrepo, Quellrepo oder beide Repos ändert.

## PATCHHARBOR.09a – Source-side Adoption Preflight Inventory

**Commit:** `Add source-side adoption preflight inventory`

**Ziel:**  
Vor jeder echten RepoDossier-Mutation prüfen, ob der aktuelle Stand wirklich bereit ist.

**Repos:**

- Zielrepo: PatchHarbor
- Quellrepo: RepoDossier
- Änderung bevorzugt zunächst im Zielrepo als Dokumentation/Test, noch ohne Source-Mutation.

**Prüfen:**

- PatchHarbor ist installiert oder über `PYTHONPATH` nutzbar.
- `patchharbor run-script` funktioniert.
- RepoDossier besitzt noch den bestehenden lokalen Runner.
- Keine uncommitted Änderungen in beiden Repos.
- Git-Identität in beiden Repos vorhanden.
- Tests in beiden Repos grundsätzlich grün.

**Akzeptanz:**

- Dokumentierte Preflight-Liste.
- Tests/Smokes, die keine Source-Dateien ändern.

---

## PATCHHARBOR.09b – Add RepoDossier PatchHarbor Runner Wrapper

**Commit:** `Add PatchHarbor patch runner wrapper`

**Ziel:**  
Erste echte additive Source-Repo-Änderung: eine neue dünne Wrapper-Datei in RepoDossier hinzufügen.

**Neue Datei im Quellrepo:**

```text
scripts/dev/run_patchharbor_patch.sh
```

**Geplante Form:**

```bash
#!/usr/bin/env bash
set -euo pipefail
exec patchharbor run-script "$@"
```

**Wichtig:**

- Bestehender Runner bleibt unverändert.
- Keine Alias-Änderung.
- Keine done/failed-Mutation.
- Kein Ersatz von `run_latest_download_patch.sh`.
- Keine Export-Scripts anfassen.

**Tests im Quellrepo:**

```text
tests/test_patchharbor_runner_wrapper.py
```

**Akzeptanz:**

- Wrapper existiert.
- `bash -n scripts/dev/run_patchharbor_patch.sh` grün.
- Wrapper enthält `patchharbor run-script`.
- Wrapper enthält `"$@"`.
- Bestehender Runner existiert weiter.
- Keine privaten Werte.

---

## PATCHHARBOR.09c – Add RepoDossier Runner Wrapper Smoke Tests

**Commit:** `Add PatchHarbor runner wrapper smoke tests`

**Ziel:**  
Nicht nur statisch testen, sondern einen ungefährlichen No-Execute-Smoke über den neuen Wrapper ermöglichen.

**Tests:**

- Temporäres Patchscript erzeugen.
- Wrapper mit `--no-execute` aufrufen.
- Erwartete Runner-Phasen prüfen.
- Sicherstellen, dass keine Ausführung und keine Dateimutation passiert.

**Wichtig:**

- Kein echter Migrationspatch wird ausgeführt.
- Keine done/failed-Verzeichnisse mutieren.
- Kein Alias wird benötigt.

---

## PATCHHARBOR.09d – Add Source-side Alias Compatibility Update

**Commit:** `Add PatchHarbor runner alias compatibility`

**Ziel:**  
Alias-Installer im Quellrepo additiv erweitern, ohne bestehende Aliase still zu brechen.

**Betroffene Datei im Quellrepo:**

```text
scripts/dev/install_aliases.sh
```

**Ziel:**

- Neuen optionalen Alias ergänzen, z. B. `patchharbor-patch`.
- Bestehendes `c` zunächst nicht ändern.
- Bestehendes `r` nicht ändern.
- Keine Shell-RC-Dateien direkt im Patch ändern; nur Installer-Logik.

**Akzeptanz:**

- Installer enthält neuen Alias.
- Bestehender `c`-Alias bleibt erhalten.
- Export-Alias bleibt erhalten.
- Tests prüfen Inhalt, nicht lokale Shell-Konfiguration.

---

## PATCHHARBOR.09e – Optional Controlled `c` Alias Switch Plan

**Commit:** `Document controlled c alias switch plan`

**Ziel:**  
Noch kein Umschalten, sondern Plan und Tests für späteren Wechsel, falls gewünscht.

**Warum separat:**  
`c` ist der etablierte Komfortbefehl. Eine stille Änderung kann den Arbeitsfluss brechen.

**Inhalt:**

- Wann darf `c` auf neuen Wrapper zeigen?
- Welche Paritätstests müssen grün sein?
- Wie wird zurückgerollt?
- Wie wird der Nutzer informiert?

**Akzeptanz:**  
Dokumentation + Tests; keine Shell-Änderung.

---

## PATCHHARBOR.09f – Source-side Runner Adoption Acceptance

**Commit:** `Add source-side runner adoption acceptance`

**Ziel:**  
Abschluss von Milestone 09.

**Akzeptanz:**

- Neuer Wrapper existiert und ist getestet.
- Bestehender Runner existiert weiterhin.
- Optionaler Alias ist geplant oder additiv vorhanden.
- Keine Export-Migration.
- Keine Löschung alter Scripts.
- Beide Repos grün.

---

# Milestone 10 – Download Runner Parität und schrittweise Ablösung

## PATCHHARBOR.10a – Download Runner Behavior Inventory

**Commit:** `Add download runner behavior inventory`

**Ziel:**  
Exaktes Verhalten von `run_latest_download_patch.sh` dokumentieren.

**Zu inventarisieren:**

- Download-Verzeichnis
- Auswahl des neuesten Scripts
- Metadata-Prüfung
- Wiederholungsprüfung
- Freshness
- bash -n
- Ausführung
- Logfile
- done/failed-Move
- Footer
- Fehlerfälle

---

## PATCHHARBOR.10b – Add Download Runner Parity Tests

**Commit:** `Add download runner parity tests`

**Ziel:**  
Focused Tests gegen das alte Verhalten im Quellrepo.

**Wichtig:**  
Erst testen, dann ersetzen.

---

## PATCHHARBOR.10c – Add PatchHarbor Download Runner Plan API

**Commit:** `Add download runner planning API`

**Ziel:**  
Falls noch nicht ausreichend vorhanden: generische Planung für Download-Runner-Verhalten in PatchHarbor erweitern.

**Wichtig:**  
Planung zuerst, Mutation später.

---

## PATCHHARBOR.10d – Add PatchHarbor Download Runner Execution API

**Commit:** `Add download runner execution API`

**Ziel:**  
Generisches Ausführen eines neuesten Download-Patches, sofern die Parität klar ist.

**Achtung:**  
Dies ist der erste riskantere Zielrepo-Schritt nach der expliziten Runner-API.

---

## PATCHHARBOR.10e – Switch RepoDossier Download Runner to PatchHarbor Internals

**Commit:** `Use PatchHarbor for download patch runner`

**Ziel:**  
Der alte Source-Runner wird dünner Wrapper um PatchHarbor.

**Wichtig:**

- Alter Dateiname kann erhalten bleiben.
- `c` Workflow bleibt äußerlich gleich.
- done/failed-Verhalten bleibt gleich.
- Logs bleiben nutzbar.
- Rollback möglich.

---

## PATCHHARBOR.10f – Download Runner Adoption Acceptance

**Commit:** `Add download runner adoption acceptance`

**Ziel:**  
Abschluss der Download-Runner-Ablösung.

---

# Milestone 11 – Export Runner Migration

## PATCHHARBOR.11a – Export Runner Inventory

**Commit:** `Add export runner inventory`

**Betroffene Quellrepo-Dateien:**

```text
scripts/dev/r.sh
scripts/dev/run_repodossier_exports.sh
```

**Ziel:**  
Export-Verhalten exakt inventarisieren, bevor generische Teile migriert werden.

---

## PATCHHARBOR.11b – Export Runner Target Model

**Commit:** `Add export runner model`

**Ziel:**  
PatchHarbor bekommt ein generisches Modell für Export-Jobs, aber ohne RepoDossier-Speziallogik.

---

## PATCHHARBOR.11c – Export Runner Planning API

**Commit:** `Add export runner planning API`

**Ziel:**  
Export-Aktionen planen, ohne Dateien zu erzeugen oder Befehle auszuführen.

---

## PATCHHARBOR.11d – Export Runner Execution API

**Commit:** `Add export runner execution API`

**Ziel:**  
Generische Ausführung mit klarer Fehlerbehandlung.

---

## PATCHHARBOR.11e – RepoDossier Export Wrapper Adoption

**Commit:** `Use PatchHarbor for RepoDossier exports`

**Ziel:**  
RepoDossier-Export-Scripts dünner machen und auf PatchHarbor delegieren.

---

## PATCHHARBOR.11f – Export Runner Adoption Acceptance

**Commit:** `Add export runner adoption acceptance`

**Ziel:**  
Abschluss Export-Migration.

---

# Milestone 12 – Audit-, Public-Repo- und Dev-Environment-Helper

## PATCHHARBOR.12a – Helper Inventory

**Commit:** `Add development helper inventory`

**Zu prüfen:**

- Public-Repo-Audit
- Dev-Environment-Checks
- Branch-/Release-Hilfen
- sonstige scripts/dev-Helfer

---

## PATCHHARBOR.12b – Generic Helper Classification

**Commit:** `Classify generic development helpers`

**Ziel:**  
Entscheiden:

- gehört nach PatchHarbor
- bleibt in RepoDossier
- wird gelöscht
- wird dokumentiert, aber nicht migriert

---

## PATCHHARBOR.12c – Public Audit Helper Migration

**Commit:** `Add public repository audit helpers`

**Ziel:**  
Generische Audit-Helfer nach PatchHarbor migrieren.

---

## PATCHHARBOR.12d – Dev Environment Helper Migration

**Commit:** `Add development environment helpers`

**Ziel:**  
Generische Environment-Checks nach PatchHarbor migrieren.

---

## PATCHHARBOR.12e – Helper Adoption in RepoDossier

**Commit:** `Use PatchHarbor development helpers`

**Ziel:**  
RepoDossier ruft generische PatchHarbor-Helfer auf.

---

## PATCHHARBOR.12f – Helper Migration Acceptance

**Commit:** `Add helper migration acceptance`

**Ziel:**  
Abschluss der Helper-Migration.

---

# Milestone 13 – Packaging, CLI, Installation und pipx

## PATCHHARBOR.13a – PatchHarbor CLI Surface Review

**Commit:** `Review PatchHarbor CLI surface`

**Ziel:**  
Alle CLI-Kommandos prüfen:

- `doctor`
- `lint-script`
- `run-script`
- spätere Wrapper-/Export-/Helper-Kommandos

---

## PATCHHARBOR.13b – Packaging Metadata Hardening

**Commit:** `Harden PatchHarbor packaging metadata`

**Ziel:**  
`pyproject.toml`, Entry Points, README, Lizenz, Paketdaten prüfen.

---

## PATCHHARBOR.13c – pipx Installation Smoke

**Commit:** `Add pipx installation smoke checks`

**Ziel:**  
PatchHarbor lokal und isoliert per pipx installieren/testen.

---

## PATCHHARBOR.13d – RepoDossier Dependency Documentation

**Commit:** `Document RepoDossier PatchHarbor dependency`

**Ziel:**  
Dokumentieren, wie RepoDossier PatchHarbor erwartet:

- als pipx Tool
- als venv Dependency
- als lokaler Entwicklungscheckout

---

## PATCHHARBOR.13e – Packaging Acceptance

**Commit:** `Add packaging acceptance`

**Ziel:**  
Abschluss Installation/Distribution.

---

# Milestone 14 – Vollständige Source-Repo-Bereinigung RepoDossier

## PATCHHARBOR.14a – RepoDossier Cleanup Inventory

**Commit:** `Add RepoDossier cleanup inventory`

**Ziel:**  
Alle alten Scripts markieren:

- behalten
- dünner Wrapper
- löschen
- später klären

---

## PATCHHARBOR.14b – Remove Replaced Source Logic

**Commit:** `Remove replaced source-side logic`

**Ziel:**  
Nur Logik löschen, die nachweislich durch PatchHarbor ersetzt ist.

**Wichtig:**  
Keine Löschung ohne Paritätstest.

---

## PATCHHARBOR.14c – Update RepoDossier Developer Documentation

**Commit:** `Update RepoDossier developer documentation`

**Ziel:**  
README/Docs auf neuen Workflow aktualisieren.

---

## PATCHHARBOR.14d – Update RepoDossier Tests and CI Expectations

**Commit:** `Update RepoDossier migration tests`

**Ziel:**  
Tests auf neuen Zustand bringen.

---

## PATCHHARBOR.14e – RepoDossier Cleanup Acceptance

**Commit:** `Add RepoDossier cleanup acceptance`

**Ziel:**  
RepoDossier ist bereinigt, aber Workflow weiterhin nutzbar.

---

# Milestone 15 – PatchHarbor-Bereinigung und Public Readiness

## PATCHHARBOR.15a – PatchHarbor Internal Cleanup Inventory

**Commit:** `Add PatchHarbor cleanup inventory`

**Ziel:**  
Zielrepo auf temporäre Migrationsartefakte prüfen.

---

## PATCHHARBOR.15b – Remove Temporary Migration Docs or Mark Historical

**Commit:** `Clean up migration documentation`

**Ziel:**  
Temporäre Dateien entweder löschen oder als historische Migrationsdokumente markieren.

---

## PATCHHARBOR.15c – Consolidate Documentation

**Commit:** `Consolidate PatchHarbor documentation`

**Ziel:**  
Aus vielen Migrationsdocs eine klare Nutzer-/Entwicklerdoku machen.

---

## PATCHHARBOR.15d – Public API Review

**Commit:** `Review PatchHarbor public API`

**Ziel:**  
Prüfen:

- Modulnamen
- Dataclasses
- Exceptions
- CLI-Verträge
- Exit-Codes
- Output-Verträge

---

## PATCHHARBOR.15e – PatchHarbor Public Readiness Acceptance

**Commit:** `Add PatchHarbor public readiness acceptance`

**Ziel:**  
PatchHarbor ist als eigenständiges öffentliches Tool sauber.

---

# Milestone 16 – End-to-End Migration Acceptance

## PATCHHARBOR.16a – Dual-Repo End-to-End Smoke

**Commit:** `Add dual repository end-to-end smoke`

**Ziel:**  
Beide Repos im Zusammenspiel prüfen.

**Prüfen:**

- PatchHarbor Tests grün.
- RepoDossier Tests grün.
- RepoDossier kann PatchHarbor-Wrapper nutzen.
- Alter Komfortworkflow funktioniert oder ist bewusst ersetzt.
- Exportworkflow funktioniert.
- Keine privaten Werte in beiden Repos.

---

## PATCHHARBOR.16b – Migration Rollback Notes

**Commit:** `Add migration rollback notes`

**Ziel:**  
Dokumentieren, wie man bei Problemen zurückkommt.

---

## PATCHHARBOR.16c – Migration Completion Checklist

**Commit:** `Add migration completion checklist`

**Ziel:**  
Finale Checkliste:

- beide Repos grün
- installierbar
- keine alten toten Scripts
- keine privaten Werte
- Docs aktuell
- Tags/Releases geplant
- Remote-Branches bereinigt

---

## PATCHHARBOR.16d – Final Migration Acceptance

**Commit:** `Add final migration acceptance`

**Ziel:**  
Migration offiziell abgeschlossen.

---

# Milestone 17 – Release und Branch-Bereinigung

## PATCHHARBOR.17a – Versioning Decision

**Commit:** `Document PatchHarbor release version`

**Ziel:**  
Festlegen, ob erster Release `0.1.0`, `1.0.0` oder anderer Stand wird.

---

## PATCHHARBOR.17b – PatchHarbor Release Preparation

**Commit:** `Prepare PatchHarbor release`

**Ziel:**  
Release-Notes, Tag, Build, Installationstest.

---

## PATCHHARBOR.17c – RepoDossier Follow-up Release Preparation

**Commit:** `Prepare RepoDossier follow-up release`

**Ziel:**  
RepoDossier-Version nach Migration vorbereiten.

---

## PATCHHARBOR.17d – Branch Cleanup Plan

**Commit:** `Add branch cleanup plan`

**Ziel:**  
Lokale und Remote-Branches prüfen und alte Migrationsbranches löschen.

---

## PATCHHARBOR.17e – Final Repository Hygiene Acceptance

**Commit:** `Add final repository hygiene acceptance`

**Ziel:**  
Beide Repos sind sauber:

- klare main-Branches
- keine toten Migrationsbranches
- keine untracked Migrationsartefakte
- keine privaten Pfade
- keine alten temporären Logs
- installierbarer Endzustand

---

# Abschlussdefinition

Die Migration ist vollständig abgeschlossen, wenn alle folgenden Punkte wahr sind:

## PatchHarbor

- eigenständiges GitHub-Projekt
- installierbar
- CLI dokumentiert
- Tests grün
- keine privaten Werte
- generische APIs statt RepoDossier-Speziallogik
- Release vorbereitet oder veröffentlicht

## RepoDossier

- nutzt PatchHarbor für generische Patch-/Runner-/Helper-Logik
- enthält nur noch source-spezifische Wrapper und Projektlogik
- alte duplizierte Scripts gelöscht oder historisch dokumentiert
- Tests grün
- Entwicklerdoku aktuell
- Installation weiterhin klar

## Beide Repos

- keine ungeklärten Migrationsreste
- keine uncommitted Änderungen
- keine privaten Pfade oder Mailadressen
- keine temporären Logs im Repo
- Branches bereinigt
- End-to-End-Smoke grün

---

# Empfohlene direkte nächste Commits

Ausgehend vom aktuellen Stand nach 08d:

```text
PATCHHARBOR.08e  Add source-side adoption acceptance documentation
PATCHHARBOR.09a  Add source-side adoption preflight inventory
PATCHHARBOR.09b  Add PatchHarbor patch runner wrapper
PATCHHARBOR.09c  Add PatchHarbor runner wrapper smoke tests
PATCHHARBOR.09d  Add PatchHarbor runner alias compatibility
PATCHHARBOR.09e  Document controlled c alias switch plan
PATCHHARBOR.09f  Add source-side runner adoption acceptance
```

Danach erst:

```text
PATCHHARBOR.10x  Download runner parity and replacement
PATCHHARBOR.11x  Export runner migration
PATCHHARBOR.12x  Helper migration
PATCHHARBOR.13x  Packaging / pipx / CLI hardening
PATCHHARBOR.14x  RepoDossier cleanup
PATCHHARBOR.15x  PatchHarbor public readiness cleanup
PATCHHARBOR.16x  End-to-end final acceptance
PATCHHARBOR.17x  Release and branch cleanup
```
