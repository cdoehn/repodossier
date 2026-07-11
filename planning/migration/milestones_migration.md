# PatchHarbor / RepoDossier Migration – fein granulierte Milestones

Stand: nach `PATCHHARBOR.09d-fix2` in Arbeit / letzter bekannter Verlauf.

Diese Datei ersetzt die bisherige grobe Migrations-Milestoneplanung. Ziel ist, die weiteren Patches deutlich kleiner zu schneiden, damit Fehler leichter isolierbar sind und Repair-Patches weniger Umfang haben.

Repos:

- Quellrepo: `repo_dossier`
- Zielrepo: `patch-harbor`

Wichtig:

- Diese Datei soll im Quellrepo unter `planning/milestones_migration.md` liegen.
- Künftige Patchscripts sollen diese Datei im `repodossier-meta`-Milestone-Panel referenzieren.
- Die Roadmap bleibt strategisch in `planning/roadmap_migration.md`.
- Diese Datei ist der operative Patch-Schnitt.

---

## 0. Grundregeln ab jetzt

### 0.1 Patchgröße

Ein normaler Patch soll möglichst nur eine der folgenden Änderungen enthalten:

- eine neue Dokumentationsdatei
- eine neue Testdatei
- eine kleine Änderung an genau einer bestehenden Datei
- eine kleine neue API-Datei plus eine direkt passende Testdatei
- eine reine Akzeptanz-/Planungsdatei plus Test
- eine Reparatur an genau den Dateien des fehlgeschlagenen Patches

Wenn ein Patch mehr als zwei Ziel-Dateien braucht, muss der Patch vorher begründen, warum das nicht sinnvoll kleiner geschnitten werden kann.

### 0.2 Source-Repo vs. Target-Repo

Patches müssen klar einem Scope zugeordnet sein:

- `target-only`: nur `patch-harbor`
- `source-only`: nur `repo_dossier`
- `dual-read`: ein Repo wird geändert, das andere nur geprüft
- `dual-change`: beide Repos werden geändert; nur erlaubt, wenn vorher ein Acceptance-/Preflight-Patch das ausdrücklich freigibt

Aktuell bevorzugt:

- PatchHarbor-Zielrepo für generische APIs, Planung, Rendering, Doku
- RepoDossier-Quellrepo nur für additive Source-Adoption
- Dual-change vermeiden

### 0.3 Fix-Regel

Wenn ein Patch fehlschlägt:

- keine neue Milestone-Nummer starten
- Fix-ID verwenden, z. B. `PATCHHARBOR.09d-fix3`
- Commit-Message des ursprünglichen Patches beibehalten
- nur die kaputten Dateien anfassen
- Focused Smoke muss den zuletzt roten Fall enthalten
- wenn ein Text-Rewrite Python-Code erzeugt: `ast.parse` oder `py_compile` direkt danach

### 0.4 Keine Escape-Hölle

Bei Tests mit Shell-Aliasen, Quotes oder verschachtelten Strings:

- keine einzelnen hochgeescapten Assert-Zeilen ersetzen
- ganze Testfunktion ersetzen
- danach Syntax prüfen
- wenn exakte Formatierung nicht Vertrag ist, robuste Assertions verwenden

### 0.5 Keine Self-referential Guards

Wenn ein Test verbotene Strings sucht, darf die getrackte Testdatei diese Strings nicht wörtlich enthalten.

Dynamisch zusammensetzen:

- `"/home/" + "exampleuser"`
- `"user" + "@"`
- `"Example" + "Laptop"`
- `"~/" + "Projects"`
- `"run_latest_" + "download_patch"`
- `chr(96) * 3`

### 0.6 Bestehender Vertrag gewinnt

Bei CLI-, Alias-, Runner- und Lint-Ausgabe:

- tatsächlichen bestehenden Output lesen
- bestehende Tests als Vertrag behandeln
- nur additiv erweitern, wenn der Patch nicht explizit Migration des Vertrags ist

---

# Milestone 09 – Erste echte Source-side Runner-Adoption

Status: läuft.

Ziel von Milestone 09:

RepoDossier bekommt einen additiven PatchHarbor-Runner-Wrapper und optional additive Alias-Kompatibilität. Der alte lokale Runner, `c`, `r` und Export-Scripts bleiben unverändert, bis spätere Paritätspatches etwas anderes erlauben.

---

## 09d-Serie – Alias-Kompatibilität abschließen

### PATCHHARBOR.09d-fix2 – Alias-Kompatibilität stabil reparieren

**Commit:** `Add PatchHarbor runner alias compatibility`  
**Scope:** source-only  
**Dateien:**

```text
scripts/dev/install_aliases.sh
tests/test_dev_alias_installer.py
```

**Ziel:**

- `patchharbor-patch` additiv ergänzen.
- `c` bleibt auf altem Download-Runner.
- `r` bleibt auf Export-Wrapper.
- Keine Shell-RC-Datei beim Patchlauf schreiben.
- Zielrepo bleibt unverändert.

**Kleinschnitt-Hinweis:**

Wenn dieser Patch noch einmal scheitert, dann Fix nur an einer Ursache:

- `09d-fix3a`: nur Installer-Patch idempotent machen
- `09d-fix3b`: nur Testfunktion reparieren
- `09d-fix3c`: nur Smoke/Validation anpassen

---

## 09e-Serie – Kontrollierten c-Alias-Umschaltplan dokumentieren

### PATCHHARBOR.09e1 – c-Alias Ist-Vertrag dokumentieren

**Commit:** `Document current c alias contract`  
**Scope:** source-only oder target-only?  
**Empfehlung:** source-only, weil es RepoDossier-Alias-Vertrag betrifft.  
**Datei:**

```text
planning/patchharbor/c-alias-contract.md
```

**Inhalt:**

- aktueller `c`-Alias
- aktueller Zielpfad
- was `c` heute macht
- welche Outputs wichtig sind
- was nicht still geändert werden darf

**Keine Tests außer Dokument-Existenztest, falls sinnvoll.**

---

### PATCHHARBOR.09e2 – c-Alias Umschaltkriterien dokumentieren

**Commit:** `Document c alias switch criteria`  
**Scope:** source-only  
**Datei:**

```text
planning/patchharbor/c-alias-switch-criteria.md
```

**Inhalt:**

- welche Paritätstests vor Umschaltung grün sein müssen
- Rollback-Bedingungen
- ob `c` überhaupt umgeschaltet werden soll oder dauerhaft Legacy bleiben darf
- explizite Entscheidung: nicht in diesem Patch umschalten

---

### PATCHHARBOR.09e3 – c-Alias Umschaltplan testen

**Commit:** `Add c alias switch plan tests`  
**Scope:** source-only  
**Datei:**

```text
tests/test_c_alias_switch_plan.py
```

**Ziel:**

- Planungsdokumente existieren.
- Plan sagt: keine stille Umschaltung.
- Plan nennt Rollback.
- Plan nennt Paritätstests.
- Keine privaten Werte.

---

## 09f-Serie – Source-side Runner Adoption Acceptance

### PATCHHARBOR.09f1 – Source-side Runner Adoption Acceptance Dokument

**Commit:** `Add source-side runner adoption acceptance documentation`  
**Scope:** source-only oder target-only?  
**Empfehlung:** source-only, weil Adoption im Quellrepo stattfand.  
**Datei:**

```text
planning/patchharbor/source-runner-adoption-acceptance.md
```

**Inhalt:**

- Wrapper existiert.
- Wrapper ist additiv.
- Wrapper-Smoke existiert.
- Alias `patchharbor-patch` ist additiv.
- `c` und `r` bleiben erhalten.
- Export nicht migriert.

---

### PATCHHARBOR.09f2 – Source-side Runner Adoption Acceptance Tests

**Commit:** `Add source-side runner adoption acceptance tests`  
**Scope:** source-only  
**Datei:**

```text
tests/test_source_runner_adoption_acceptance.py
```

**Ziel:**

- prüft 09b/09c/09d Artefakte
- prüft, dass alte Runner existieren
- prüft, dass keine `c`-Umschaltung dokumentiert ist
- prüft keine privaten Werte

---

### PATCHHARBOR.09f3 – Dual-Repo Sanity Smoke nach 09

**Commit:** `Add source runner adoption sanity smoke`  
**Scope:** source-only, Zielrepo read-only  
**Datei:**

```text
tests/test_patchharbor_source_adoption_sanity.py
```

**Ziel:**

- PatchHarbor-Zielrepo über `PATCHHARBOR_TARGET_REPO` finden
- Wrapper-No-Execute-Smoke
- Alias-Dry-Run-Smoke
- Zielrepo nicht mutieren

Wenn dieser Patch zu groß wird, aufteilen:

- `09f3a`: Wrapper sanity
- `09f3b`: Alias dry-run sanity

---

# Milestone 10 – Download Runner Parität vor Ablösung

Ziel: Der bestehende lokale Download-Runner darf erst ersetzt oder dünner gemacht werden, wenn sein Verhalten in kleinen Tests abgebildet ist.

---

## 10a-Serie – Verhalten inventarisieren

### PATCHHARBOR.10a1 – Download Runner Datei-Inventar

**Commit:** `Document download runner file inventory`  
**Scope:** source-only  
**Datei:**

```text
planning/patchharbor/download-runner-file-inventory.md
```

**Inhalt:**

- beteiligte Dateien
- Eingabe-/Ausgabeorte
- Downloads, done, failed
- Logfile
- Metadatenvalidator
- Helper

---

### PATCHHARBOR.10a2 – Download Runner Ablauf-Inventar

**Commit:** `Document download runner lifecycle flow`  
**Scope:** source-only  
**Datei:**

```text
planning/patchharbor/download-runner-lifecycle-flow.md
```

**Inhalt:**

- Auswahl neuestes Patchscript
- Metadata OK/Fehler
- Wiederholung
- Freshness
- bash -n
- Ausführung
- success move
- fail move
- Log-Verbleib

---

### PATCHHARBOR.10a3 – Download Runner Output-Vertrag

**Commit:** `Document download runner output contract`  
**Scope:** source-only  
**Datei:**

```text
planning/patchharbor/download-runner-output-contract.md
```

**Inhalt:**

- wichtige UI-Zeilen
- Footer
- Fehlertexte
- Done/Current/Next/Problem
- keine Änderung ohne Test

---

### PATCHHARBOR.10a4 – Download Runner Inventar-Tests

**Commit:** `Add download runner inventory tests`  
**Scope:** source-only  
**Datei:**

```text
tests/test_download_runner_inventory_docs.py
```

---

## 10b-Serie – Paritätstests in kleinen Scheiben

### PATCHHARBOR.10b1 – Download Runner Metadata Parity Test

**Commit:** `Add download runner metadata parity test`  
**Scope:** source-only  
**Datei:**

```text
tests/test_download_runner_metadata_parity.py
```

**Ziel:**

- gültige Metadaten akzeptiert
- ungültige Metadaten stoppen vor Ausführung

---

### PATCHHARBOR.10b2 – Download Runner Freshness Parity Test

**Commit:** `Add download runner freshness parity test`  
**Scope:** source-only  
**Datei:**

```text
tests/test_download_runner_freshness_parity.py
```

---

### PATCHHARBOR.10b3 – Download Runner Repeat Parity Test

**Commit:** `Add download runner repeat parity test`  
**Scope:** source-only  
**Datei:**

```text
tests/test_download_runner_repeat_parity.py
```

---

### PATCHHARBOR.10b4 – Download Runner Syntax Failure Parity Test

**Commit:** `Add download runner syntax failure parity test`  
**Scope:** source-only  
**Datei:**

```text
tests/test_download_runner_syntax_parity.py
```

---

### PATCHHARBOR.10b5 – Download Runner Success Lifecycle Parity Test

**Commit:** `Add download runner success lifecycle parity test`  
**Scope:** source-only  
**Datei:**

```text
tests/test_download_runner_success_lifecycle_parity.py
```

---

### PATCHHARBOR.10b6 – Download Runner Failure Lifecycle Parity Test

**Commit:** `Add download runner failure lifecycle parity test`  
**Scope:** source-only  
**Datei:**

```text
tests/test_download_runner_failure_lifecycle_parity.py
```

---

### PATCHHARBOR.10b7 – Download Runner Footer Parity Test

**Commit:** `Add download runner footer parity test`  
**Scope:** source-only  
**Datei:**

```text
tests/test_download_runner_footer_parity.py
```

---

## 10c-Serie – PatchHarbor Download Runner APIs, falls nötig

Nur wenn 10b zeigt, dass generische Zielrepo-API fehlt.

### PATCHHARBOR.10c1 – Target Download Runner Inventory

**Commit:** `Add target download runner API inventory`  
**Scope:** target-only  
**Datei:**

```text
docs/download-runner-api-inventory.md
```

---

### PATCHHARBOR.10c2 – Download Runner Selection API

**Commit:** `Add download runner selection API`  
**Scope:** target-only  
**Dateien:**

```text
src/patchharbor/download_selection.py
tests/test_download_selection.py
```

---

### PATCHHARBOR.10c3 – Download Runner Lifecycle Execution API

**Commit:** `Add download runner lifecycle execution API`  
**Scope:** target-only  
**Dateien:**

```text
src/patchharbor/download_runner.py
tests/test_download_runner.py
```

Falls zu groß:

- `10c3a`: Modell/Dataclasses
- `10c3b`: no-execute behavior
- `10c3c`: success move
- `10c3d`: failure move
- `10c3e`: logs

---

## 10d-Serie – Source Runner dünner machen

### PATCHHARBOR.10d1 – Source Download Runner Wrapper Draft

**Commit:** `Document source download runner wrapper draft`  
**Scope:** source-only  
**Datei:**

```text
planning/patchharbor/source-download-runner-wrapper-draft.md
```

---

### PATCHHARBOR.10d2 – Source Download Runner Wrapper Test Harness

**Commit:** `Add source download runner wrapper test harness`  
**Scope:** source-only  
**Datei:**

```text
tests/test_source_download_runner_wrapper_harness.py
```

---

### PATCHHARBOR.10d3 – Switch internal implementation behind old filename

**Commit:** `Use PatchHarbor for download patch runner internals`  
**Scope:** source-only  
**Datei:**

```text
scripts/dev/run_latest_download_patch.sh
```

**Sehr riskant. Nur wenn 10b und 10c grün.**

---

### PATCHHARBOR.10d4 – Download Runner Adoption Acceptance Doc

**Commit:** `Add download runner adoption acceptance documentation`  
**Scope:** source-only  
**Datei:**

```text
planning/patchharbor/download-runner-adoption-acceptance.md
```

---

### PATCHHARBOR.10d5 – Download Runner Adoption Acceptance Test

**Commit:** `Add download runner adoption acceptance tests`  
**Scope:** source-only  
**Datei:**

```text
tests/test_download_runner_adoption_acceptance.py
```

---

# Milestone 11 – Export Runner Migration in kleinen Teilen

---

## 11a-Serie – Export-Inventar

### PATCHHARBOR.11a1 – Export Runner File Inventory

**Commit:** `Document export runner file inventory`  
**Scope:** source-only  
**Datei:**

```text
planning/patchharbor/export-runner-file-inventory.md
```

### PATCHHARBOR.11a2 – Export Runner Behavior Inventory

**Commit:** `Document export runner behavior inventory`  
**Scope:** source-only  
**Datei:**

```text
planning/patchharbor/export-runner-behavior-inventory.md
```

### PATCHHARBOR.11a3 – Export Runner Inventory Tests

**Commit:** `Add export runner inventory tests`  
**Scope:** source-only  
**Datei:**

```text
tests/test_export_runner_inventory_docs.py
```

---

## 11b-Serie – Zielrepo Exportmodell

### PATCHHARBOR.11b1 – Export Job Model

**Commit:** `Add export job model`  
**Scope:** target-only  
**Dateien:**

```text
src/patchharbor/export_model.py
tests/test_export_model.py
```

### PATCHHARBOR.11b2 – Export Plan Model

**Commit:** `Add export plan model`  
**Scope:** target-only  
**Dateien:**

```text
src/patchharbor/export_planning.py
tests/test_export_planning.py
```

### PATCHHARBOR.11b3 – Export Render/Display Helpers

**Commit:** `Add export display helpers`  
**Scope:** target-only  
**Dateien:**

```text
src/patchharbor/export_display.py
tests/test_export_display.py
```

---

## 11c-Serie – Source-Adoption Export

### PATCHHARBOR.11c1 – Export Source Wrapper Draft

**Commit:** `Document source export wrapper draft`  
**Scope:** source-only  
**Datei:**

```text
planning/patchharbor/source-export-wrapper-draft.md
```

### PATCHHARBOR.11c2 – Export Wrapper Smoke Tests

**Commit:** `Add source export wrapper smoke tests`  
**Scope:** source-only  
**Datei:**

```text
tests/test_source_export_wrapper_smoke.py
```

### PATCHHARBOR.11c3 – Switch r wrapper additively or internally

**Commit:** `Use PatchHarbor for source exports`  
**Scope:** source-only  
**Dateien nach Bedarf:**

```text
scripts/dev/r.sh
scripts/dev/run_repodossier_exports.sh
```

Wenn zu groß:

- `11c3a`: nur `r.sh`
- `11c3b`: nur `run_repodossier_exports.sh`
- `11c3c`: Tests

---

# Milestone 12 – Dev Helper Migration

---

## 12a-Serie – Helper-Inventar

### PATCHHARBOR.12a1 – Helper File Inventory

**Commit:** `Document development helper file inventory`  
**Scope:** source-only  
**Datei:**

```text
planning/patchharbor/helper-file-inventory.md
```

### PATCHHARBOR.12a2 – Helper Classification

**Commit:** `Classify development helpers`  
**Scope:** source-only  
**Datei:**

```text
planning/patchharbor/helper-classification.md
```

### PATCHHARBOR.12a3 – Helper Inventory Tests

**Commit:** `Add helper inventory tests`  
**Scope:** source-only  
**Datei:**

```text
tests/test_helper_inventory_docs.py
```

---

## 12b-Serie – Public Audit Helpers

### PATCHHARBOR.12b1 – Public Audit Model

**Commit:** `Add public audit model`  
**Scope:** target-only

### PATCHHARBOR.12b2 – Public Audit Checks

**Commit:** `Add public audit checks`  
**Scope:** target-only

### PATCHHARBOR.12b3 – Public Audit CLI

**Commit:** `Add public audit CLI`  
**Scope:** target-only

### PATCHHARBOR.12b4 – Source Public Audit Wrapper

**Commit:** `Use PatchHarbor public audit helper`  
**Scope:** source-only

---

## 12c-Serie – Dev Environment Helpers

### PATCHHARBOR.12c1 – Environment Check Model

**Commit:** `Add environment check model`  
**Scope:** target-only

### PATCHHARBOR.12c2 – Environment Check CLI

**Commit:** `Add environment check CLI`  
**Scope:** target-only

### PATCHHARBOR.12c3 – Source Environment Wrapper

**Commit:** `Use PatchHarbor environment helper`  
**Scope:** source-only

---

# Milestone 13 – Packaging, pipx und CLI-Härtung

---

## 13a-Serie – CLI Review

### PATCHHARBOR.13a1 – CLI Command Inventory

**Commit:** `Document PatchHarbor CLI command inventory`  
**Scope:** target-only

### PATCHHARBOR.13a2 – CLI Exit Code Contract

**Commit:** `Document PatchHarbor CLI exit code contract`  
**Scope:** target-only

### PATCHHARBOR.13a3 – CLI Help Snapshot Tests

**Commit:** `Add CLI help snapshot tests`  
**Scope:** target-only

---

## 13b-Serie – Packaging

### PATCHHARBOR.13b1 – pyproject Metadata Review

**Commit:** `Harden PatchHarbor pyproject metadata`  
**Scope:** target-only

### PATCHHARBOR.13b2 – README Installation Section

**Commit:** `Document PatchHarbor installation`  
**Scope:** target-only

### PATCHHARBOR.13b3 – pipx Smoke Script

**Commit:** `Add pipx smoke script`  
**Scope:** target-only

### PATCHHARBOR.13b4 – Packaging Acceptance

**Commit:** `Add packaging acceptance documentation`  
**Scope:** target-only

---

# Milestone 14 – RepoDossier Cleanup in kleinen Teilen

---

## 14a-Serie – Cleanup-Inventar

### PATCHHARBOR.14a1 – RepoDossier Script Cleanup Inventory

**Commit:** `Document RepoDossier script cleanup inventory`  
**Scope:** source-only

### PATCHHARBOR.14a2 – Replaced Logic Map

**Commit:** `Document replaced source logic map`  
**Scope:** source-only

### PATCHHARBOR.14a3 – Cleanup Safety Tests

**Commit:** `Add RepoDossier cleanup safety tests`  
**Scope:** source-only

---

## 14b-Serie – Alte Logik entfernen, nur mit Parität

Jede Löschung einzeln.

### PATCHHARBOR.14b1 – Remove obsolete metadata helper wrapper

**Commit:** `Remove obsolete metadata helper wrapper`  
**Scope:** source-only

### PATCHHARBOR.14b2 – Remove obsolete lint wrapper

**Commit:** `Remove obsolete lint wrapper`  
**Scope:** source-only

### PATCHHARBOR.14b3 – Remove obsolete runner helper part 1

**Commit:** `Remove obsolete runner helper part 1`  
**Scope:** source-only

### PATCHHARBOR.14b4 – Remove obsolete runner helper part 2

**Commit:** `Remove obsolete runner helper part 2`  
**Scope:** source-only

Nur wenn Tests beweisen, dass nichts mehr genutzt wird.

---

## 14c-Serie – RepoDossier Doku

### PATCHHARBOR.14c1 – Update RepoDossier Developer Workflow Docs

**Commit:** `Update RepoDossier developer workflow documentation`

### PATCHHARBOR.14c2 – Update RepoDossier Install Docs

**Commit:** `Update RepoDossier installation documentation`

### PATCHHARBOR.14c3 – Update RepoDossier Migration Notes

**Commit:** `Update RepoDossier migration notes`

---

# Milestone 15 – PatchHarbor Cleanup und Public Readiness

---

## 15a-Serie – Target Cleanup-Inventar

### PATCHHARBOR.15a1 – PatchHarbor Migration Artifact Inventory

**Commit:** `Document PatchHarbor migration artifacts`

### PATCHHARBOR.15a2 – PatchHarbor Public Docs Inventory

**Commit:** `Document PatchHarbor public docs inventory`

---

## 15b-Serie – Docs konsolidieren

### PATCHHARBOR.15b1 – Consolidate Runner Docs

**Commit:** `Consolidate runner documentation`

### PATCHHARBOR.15b2 – Consolidate Compatibility Docs

**Commit:** `Consolidate compatibility documentation`

### PATCHHARBOR.15b3 – Consolidate CLI Docs

**Commit:** `Consolidate CLI documentation`

### PATCHHARBOR.15b4 – Mark Migration Docs Historical

**Commit:** `Mark migration documentation historical`

---

## 15c-Serie – Public API

### PATCHHARBOR.15c1 – Public API Inventory

**Commit:** `Document PatchHarbor public API inventory`

### PATCHHARBOR.15c2 – Public API Stability Tests

**Commit:** `Add public API stability tests`

### PATCHHARBOR.15c3 – Public Readiness Acceptance

**Commit:** `Add PatchHarbor public readiness acceptance`

---

# Milestone 16 – Dual-Repo End-to-End Acceptance

---

## 16a-Serie – E2E Smokes

### PATCHHARBOR.16a1 – Dual Repo Discovery Smoke

**Commit:** `Add dual repository discovery smoke`

### PATCHHARBOR.16a2 – Dual Repo Wrapper Smoke

**Commit:** `Add dual repository wrapper smoke`

### PATCHHARBOR.16a3 – Dual Repo Export Smoke

**Commit:** `Add dual repository export smoke`

### PATCHHARBOR.16a4 – Dual Repo Private Value Audit

**Commit:** `Add dual repository private value audit`

---

## 16b-Serie – Abschlussdokumente

### PATCHHARBOR.16b1 – Migration Rollback Notes

**Commit:** `Add migration rollback notes`

### PATCHHARBOR.16b2 – Migration Completion Checklist

**Commit:** `Add migration completion checklist`

### PATCHHARBOR.16b3 – Final Migration Acceptance

**Commit:** `Add final migration acceptance`

---

# Milestone 17 – Release und Branch-Hygiene

---

## 17a-Serie – Versionierung

### PATCHHARBOR.17a1 – PatchHarbor Version Decision

**Commit:** `Document PatchHarbor release version`

### PATCHHARBOR.17a2 – RepoDossier Follow-up Version Decision

**Commit:** `Document RepoDossier follow-up release version`

---

## 17b-Serie – Release

### PATCHHARBOR.17b1 – PatchHarbor Release Notes

**Commit:** `Add PatchHarbor release notes`

### PATCHHARBOR.17b2 – PatchHarbor Release Build Smoke

**Commit:** `Add PatchHarbor release build smoke`

### PATCHHARBOR.17b3 – RepoDossier Follow-up Release Notes

**Commit:** `Add RepoDossier follow-up release notes`

---

## 17c-Serie – Branch Cleanup

### PATCHHARBOR.17c1 – Branch Inventory

**Commit:** `Document migration branch inventory`

### PATCHHARBOR.17c2 – Local Branch Cleanup Commands

**Commit:** `Document local branch cleanup commands`

### PATCHHARBOR.17c3 – Remote Branch Cleanup Commands

**Commit:** `Document remote branch cleanup commands`

### PATCHHARBOR.17c4 – Final Repository Hygiene Acceptance

**Commit:** `Add final repository hygiene acceptance`

---

# Operativer nächster Pfad

Ab sofort halten wir uns an diese feinere Reihenfolge.

Direkt als nächstes:

```text
PATCHHARBOR.09d-fix2
```

Wenn 09d-fix2 grün ist:

```text
PATCHHARBOR.09e1
PATCHHARBOR.09e2
PATCHHARBOR.09e3
PATCHHARBOR.09f1
PATCHHARBOR.09f2
PATCHHARBOR.09f3a
PATCHHARBOR.09f3b
```

Erst danach beginnt Milestone 10.

---

# Abschlussdefinition

Die Migration ist erst abgeschlossen, wenn:

- PatchHarbor generisch und installierbar ist
- RepoDossier nur noch source-spezifische Wrapper/Fachlogik enthält
- beide Repos grün sind
- End-to-End-Smokes grün sind
- private Werte geprüft sind
- alte Migrationsartefakte bereinigt oder historisch markiert sind
- Branches und Releases vorbereitet sind
