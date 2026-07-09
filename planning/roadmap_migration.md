# PatchHarbor / RepoDossier Migration Roadmap

Stand dieser Roadmap: nach `PATCHHARBOR.08d`.

Diese Datei beschreibt die strategische Migrationsroute von RepoDossier nach PatchHarbor bis zur vollständigen Bereinigung beider Repositories.

Sie ergänzt `milestones.md`:

- `milestones.md` beschreibt konkrete Patch-/Commit-Schritte.
- `roadmap_migration.md` beschreibt Phasen, Zielbild, Abhängigkeiten, Risiken und Abschlusskriterien.

Repos:

- Quellrepo: `repo_dossier`
- Zielrepo: `patch-harbor`

---

## 0. Einbindung in Kontextvorschau und Repo-Kontext

Empfohlener Ablageort im Zielrepo:

    planning/roadmap_migration.md

Empfohlene Referenz in künftigen Patchscripts:

    # repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"planning/roadmap_migration.md","start":80,"end":150,"label":"Migration roadmap – current phase"}

Empfohlene Referenz zusammen mit Milestones:

    # repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"planning/roadmap_migration.md","start":80,"end":150,"label":"Migration roadmap"}
    # repodossier-meta: {"type":"progress","panel":"milestone","status":"active","file":"planning/milestones.md","start":120,"end":180,"label":"Current migration milestone"}

Damit die Datei in der Kontextvorschau auftaucht:

1. Datei im Repo ablegen: `planning/roadmap_migration.md`.
2. Datei mit Git tracken.
3. Sicherstellen, dass sie nicht durch Ignore-/Exportregeln ausgeschlossen wird.
4. In künftigen Patchscripts die passenden Zeilenbereiche per `repodossier-meta` referenzieren.
5. Repo-Kontext/Export wie gewohnt neu erzeugen.

Empfohlener Commit:

    git add planning/roadmap_migration.md
    git commit -m "Add migration roadmap"

---

## 1. Zielbild der Migration

### PatchHarbor am Ende

PatchHarbor ist ein eigenständiges, generisches Entwicklungs- und Patch-Workflow-Tool.

PatchHarbor enthält:

- generische Patchscript-Metadatenprüfung
- generisches Patchscript-Linting
- generischen Runner-Core
- Runner-Statusmodell
- Preflight-Prüfungen
- Lifecycle-Planung
- Display-/Footer-Renderer
- explizite CLI-Kommandos
- Wrapper-Konfiguration
- Wrapper-Planung
- Wrapper-Rendering
- ggf. Export-/Audit-/Dev-Helper, sofern generisch genug
- klare Tests und öffentliche Dokumentation
- saubere Packaging-/pipx-Unterstützung

PatchHarbor enthält nicht:

- lokale Nutzerpfade
- private Mailadressen
- Gerätenamen
- RepoDossier-spezifische Hardcodings im Core
- alte temporäre Migrationsartefakte
- Shell-Alias-Mutationen ohne expliziten Nutzeraufruf
- Source-Repo-spezifische Exportlogik im generischen Kern

### RepoDossier am Ende

RepoDossier bleibt ein fachliches Repository für RepoDossier selbst.

RepoDossier enthält nur noch:

- fachliche RepoDossier-Logik
- source-spezifische dünne Wrapper, falls nötig
- Projekt-Dokumentation
- Tests für RepoDossier
- klare Hinweise, wie PatchHarbor installiert oder genutzt wird

RepoDossier enthält nicht mehr:

- duplizierte generische Patch-Runner-Logik
- duplizierte generische Lint-Logik
- duplizierte generische Lifecycle-/Display-/Helper-Logik
- alte tote Scripts
- temporäre Migrationslogs
- private lokale Werte

---

## 2. Leitprinzipien

### 2.1 Kleine Commits

Jeder Patch soll nur eine kleine, überprüfbare Sache tun.

Gute Commit-Größe:

- ein Modul plus Tests
- ein Dokument plus Tests
- ein Wrapper plus Focused Tests
- eine Akzeptanzdokumentation

Schlechte Commit-Größe:

- mehrere Migrationsphasen gleichzeitig
- Source-Repo und Zielrepo ohne klare Grenze mischen
- neue API plus echte Source-Adoption plus Cleanup in einem Schritt
- alte Scripts löschen, bevor Parität belegt ist

### 2.2 Reparatur vor Fortschritt

Wenn ein Patch fehlschlägt:

- nicht mit dem nächsten Milestone weitermachen
- Fehlerklasse bestimmen
- nur den kaputten Patch reparieren
- Commit-Message beibehalten, außer es gibt einen guten Grund
- Patch-ID als `-fix1`, `-fix2` usw.
- Focused Smoke muss den zuletzt roten Fall enthalten

### 2.3 Bestehende Tests sind Vertrag

Bestehende Tests dürfen nicht abgeschwächt werden, nur weil ein neuer Patch etwas anders ausgeben möchte.

Besonders kritisch:

- CLI-Ausgaben
- Exit-Codes
- Fehlerwörter wie `problem:`
- Runner-Status
- Lint-Regel-IDs
- private-value Guards
- source-specific-value Guards

### 2.4 Generisch bleibt generisch

PatchHarbor-Core darf keine RepoDossier-Speziallogik bekommen.

Erlaubt:

- generische Wrapper-Specs
- generische Alias-Specs
- generische Lifecycle-Defaults
- generische Runner-Phasen
- generische Render-APIs

Nicht erlaubt:

- harte Annahme eines bestimmten Home-Pfads
- harte Annahme eines bestimmten RepoDossier-Checkout-Pfads
- private Mailadressen
- Workstationnamen
- alte source-spezifische Runner-Namen im PatchHarbor-Core
- alte RepoDossier-Lint-Codes als neue PatchHarbor-Standards

### 2.5 Source-Adoption ist separat

Eine Source-Adoption ist erst erlaubt, wenn Zielrepo-Seite und Planungsseite stabil sind.

Phasenfolge:

1. Zielrepo kann generisch modellieren.
2. Zielrepo kann generisch planen.
3. Zielrepo kann generisch rendern.
4. Zielrepo dokumentiert Akzeptanz.
5. Erst dann Source-Repo additiv ändern.
6. Erst nach Parität alte Source-Logik ersetzen.
7. Erst nach längerem grünen Zustand alte Source-Logik löschen.

---

## 3. Phasenübersicht

### Phase A – Zielrepo-Grundlage

Status: weitgehend abgeschlossen.

Umfasst:

- Zielrepo-Skeleton
- Workflow-Regeln
- Patchscript-Linting
- Runner-Core
- Runner-Display
- CLI `run-script`
- Runner-/Compatibility-Acceptance

Ergebnis:

PatchHarbor kann explizite Patchscripts prüfen und ausführen.

### Phase B – Source-Wrapper-Kompatibilität

Status: weitgehend abgeschlossen.

Umfasst:

- Source-Wrapper-Inventar
- Compatibility-Konfigurationsmodell
- Wrapper-Planungs-API
- Wrapper-Rendering-API
- Source-Wrapper-Acceptance

Ergebnis:

PatchHarbor kann source-spezifische Wrapper modellieren, planen und rendern, ohne Source-Repos zu ändern.

### Phase C – Source-side Adoption vorbereiten

Status: aktuell.

Umfasst:

- Source-side Adoption Inventory
- Runner Wrapper Draft
- Alias Compatibility Plan
- Runner Compatibility Tests Plan
- Source-side Adoption Acceptance

Ergebnis:

Die echte RepoDossier-Adoption ist vorbereitet und begrenzt.

### Phase D – Erste echte RepoDossier-Adoption

Status: offen.

Umfasst:

- additiver RepoDossier Wrapper
- Focused Tests
- optionaler Alias-Plan
- Acceptance

Ergebnis:

RepoDossier kann PatchHarbor explizit nutzen, ohne den alten Workflow zu löschen.

### Phase E – Download Runner Parität und Ablösung

Status: offen.

Umfasst:

- Verhalten des alten Download-Runners exakt inventarisieren
- Paritätstests
- PatchHarbor Download-Runner-API, falls nötig
- alter Runner wird dünner Wrapper
- `c`-Workflow bleibt kontrolliert

Ergebnis:

Der etablierte Download-Patch-Workflow läuft über PatchHarbor oder ist sauber kompatibel.

### Phase F – Export Runner Migration

Status: offen.

Umfasst:

- Export Runner Inventar
- generisches Exportmodell
- Export-Planung
- Export-Ausführung
- RepoDossier Export Wrapper
- Acceptance

Ergebnis:

Exportlogik ist sauber zwischen generisch und source-spezifisch getrennt.

### Phase G – Helper-Migration

Status: offen.

Umfasst:

- Public-Repo-Audit
- Dev-Environment-Checks
- sonstige Scripts
- Klassifikation: migrieren, behalten, löschen, dokumentieren

Ergebnis:

PatchHarbor enthält generische Developer-Helfer; RepoDossier enthält nur source-spezifische Logik.

### Phase H – Packaging, Installation, CLI-Hardening

Status: offen.

Umfasst:

- CLI-Oberfläche prüfen
- Packaging-Metadaten härten
- pipx-Smoke
- README/Docs
- Versionierung

Ergebnis:

PatchHarbor ist installierbar und als Tool nutzbar.

### Phase I – RepoDossier Cleanup

Status: offen.

Umfasst:

- alte Logik entfernen
- Docs aktualisieren
- Tests aktualisieren
- Migrationsreste entfernen
- source-spezifische Wrapper behalten

Ergebnis:

RepoDossier ist bereinigt und nutzt PatchHarbor sauber.

### Phase J – PatchHarbor Public Readiness

Status: offen.

Umfasst:

- temporäre Migrationsdocs konsolidieren
- Public API Review
- CLI-Verträge finalisieren
- Tests/Docs/Release vorbereiten

Ergebnis:

PatchHarbor ist als eigenständiges öffentliches Projekt bereit.

### Phase K – End-to-End Acceptance und Release

Status: offen.

Umfasst:

- Dual-Repo-Smoke
- Rollback-Notes
- Completion Checklist
- Release-Vorbereitung
- Branch-Bereinigung

Ergebnis:

Migration abgeschlossen, beide Repos sauber.

---

## 4. Roadmap nach Patches

### 08 – Source-side Adoption vorbereiten

Bereits begonnen.

Noch offen:

    PATCHHARBOR.08e  Add source-side adoption acceptance documentation

Ziel:

- 08a–08d abschließen
- Noch keine RepoDossier-Mutation
- Klare Freigabe für Milestone 09

Risiko:

- Zu früh Source-Repo ändern
- Alias/Wrapper/Download-Verhalten vermischen

Abschlusskriterium:

- Zielrepo Full-Suite grün
- Acceptance-Dokument sagt klar, was noch nicht getan wurde

---

### 09 – Erste echte RepoDossier-Adoption

Geplante Reihenfolge:

    PATCHHARBOR.09a  Add source-side adoption preflight inventory
    PATCHHARBOR.09b  Add PatchHarbor patch runner wrapper
    PATCHHARBOR.09c  Add PatchHarbor runner wrapper smoke tests
    PATCHHARBOR.09d  Add PatchHarbor runner alias compatibility
    PATCHHARBOR.09e  Document controlled c alias switch plan
    PATCHHARBOR.09f  Add source-side runner adoption acceptance

Ziel:

- RepoDossier bekommt additiven PatchHarbor-Wrapper.
- Bestehender Runner bleibt erhalten.
- Bestehender `c`-Workflow bleibt zunächst erhalten.
- Kein Export-Script wird geändert.

Wichtige Source-Datei:

    scripts/dev/run_patchharbor_patch.sh

Geplante Minimalform:

    #!/usr/bin/env bash
    set -euo pipefail
    exec patchharbor run-script "$@"

Abschlusskriterium:

- RepoDossier Tests grün
- PatchHarbor Tests grün
- Wrapper funktioniert mit `--no-execute`
- alter Runner existiert weiter
- keine privaten Werte

---

### 10 – Download Runner Parität und kontrollierte Ablösung

Geplante Reihenfolge:

    PATCHHARBOR.10a  Add download runner behavior inventory
    PATCHHARBOR.10b  Add download runner parity tests
    PATCHHARBOR.10c  Add download runner planning API
    PATCHHARBOR.10d  Add download runner execution API
    PATCHHARBOR.10e  Use PatchHarbor for download patch runner
    PATCHHARBOR.10f  Add download runner adoption acceptance

Ziel:

- Verhalten des alten lokalen Download-Runners exakt erhalten oder bewusst dokumentiert ändern.
- `done`/`failed`/Log/Freshness/Repeat/Metadata werden nicht versehentlich verändert.
- `c` kann später kontrolliert auf PatchHarbor-Basis laufen.

Risiko:

- Der bestehende Komfortworkflow ist produktiv wichtig.
- Schon kleine Output- oder Pfadänderungen können die tägliche Arbeit stören.
- Deswegen erst Paritätstests, dann Ablösung.

Abschlusskriterium:

- Alter Workflow funktioniert oder ist dokumentiert ersetzt.
- Paritätstests grün.
- Rollback ist klar.

---

### 11 – Export Runner Migration

Geplante Reihenfolge:

    PATCHHARBOR.11a  Add export runner inventory
    PATCHHARBOR.11b  Add export runner model
    PATCHHARBOR.11c  Add export runner planning API
    PATCHHARBOR.11d  Add export runner execution API
    PATCHHARBOR.11e  Use PatchHarbor for RepoDossier exports
    PATCHHARBOR.11f  Add export runner adoption acceptance

Ziel:

- Exportlogik generisch machen, soweit sinnvoll.
- RepoDossier-spezifische Export-Defaults im Quellrepo lassen.
- `r`-Workflow nicht heimlich brechen.

Risiko:

- Exportlogik ist wahrscheinlich stärker repo-spezifisch als Patch-Runner-Logik.
- Nicht alles gehört nach PatchHarbor.

Abschlusskriterium:

- RepoDossier Export weiterhin grün.
- PatchHarbor enthält nur generische Export-Bausteine.
- `r`-Workflow ist dokumentiert.

---

### 12 – Helper-Migration

Geplante Reihenfolge:

    PATCHHARBOR.12a  Add development helper inventory
    PATCHHARBOR.12b  Classify generic development helpers
    PATCHHARBOR.12c  Add public repository audit helpers
    PATCHHARBOR.12d  Add development environment helpers
    PATCHHARBOR.12e  Use PatchHarbor development helpers
    PATCHHARBOR.12f  Add helper migration acceptance

Ziel:

- Audit-/Public-/Environment-Helfer prüfen.
- Generische Helfer nach PatchHarbor.
- RepoDossier-spezifische Helfer bleiben in RepoDossier.

Abschlusskriterium:

- Helfer sind klassifiziert.
- Duplikate sind reduziert.
- Beide Repos bleiben grün.

---

### 13 – Packaging, CLI und pipx

Geplante Reihenfolge:

    PATCHHARBOR.13a  Review PatchHarbor CLI surface
    PATCHHARBOR.13b  Harden PatchHarbor packaging metadata
    PATCHHARBOR.13c  Add pipx installation smoke checks
    PATCHHARBOR.13d  Document RepoDossier PatchHarbor dependency
    PATCHHARBOR.13e  Add packaging acceptance

Ziel:

- PatchHarbor kann sauber installiert werden.
- CLI ist konsistent.
- RepoDossier-Doku erklärt, wie PatchHarbor erwartet wird.

Abschlusskriterium:

- `pipx install` oder lokaler pipx-Smoke grün
- CLI-Hilfe konsistent
- README und Entwicklerdocs aktuell

---

### 14 – RepoDossier Cleanup

Geplante Reihenfolge:

    PATCHHARBOR.14a  Add RepoDossier cleanup inventory
    PATCHHARBOR.14b  Remove replaced source-side logic
    PATCHHARBOR.14c  Update RepoDossier developer documentation
    PATCHHARBOR.14d  Update RepoDossier migration tests
    PATCHHARBOR.14e  Add RepoDossier cleanup acceptance

Ziel:

- Alte, ersetzte Source-Logik entfernen.
- Nur source-spezifische Wrapper behalten.
- RepoDossier-Dokumentation aktualisieren.

Risiko:

- Zu frühes Löschen.
- Versehentlich noch genutzte Scripts entfernen.
- Deshalb erst Cleanup-Inventar.

Abschlusskriterium:

- RepoDossier Full-Suite grün
- keine toten Scripts
- Doku passt zum neuen Workflow

---

### 15 – PatchHarbor Cleanup und Public Readiness

Geplante Reihenfolge:

    PATCHHARBOR.15a  Add PatchHarbor cleanup inventory
    PATCHHARBOR.15b  Clean up migration documentation
    PATCHHARBOR.15c  Consolidate PatchHarbor documentation
    PATCHHARBOR.15d  Review PatchHarbor public API
    PATCHHARBOR.15e  Add PatchHarbor public readiness acceptance

Ziel:

- PatchHarbor wird von Migrationsrepo zu sauberem Tool.
- Temporäre Migrationsartefakte werden entfernt oder historisch markiert.
- Öffentliche API und CLI werden stabilisiert.

Abschlusskriterium:

- Doku ist nutzerverständlich
- Public API bewusst
- CLI-Verträge dokumentiert
- keine privaten/source-spezifischen Reste

---

### 16 – End-to-End Acceptance

Geplante Reihenfolge:

    PATCHHARBOR.16a  Add dual repository end-to-end smoke
    PATCHHARBOR.16b  Add migration rollback notes
    PATCHHARBOR.16c  Add migration completion checklist
    PATCHHARBOR.16d  Add final migration acceptance

Ziel:

- Beide Repos zusammen prüfen.
- Rollback dokumentieren.
- Migration offiziell abschließen.

Abschlusskriterium:

- PatchHarbor grün
- RepoDossier grün
- E2E-Smoke grün
- keine privaten Werte
- keine Migrationsreste
- Rollback-Doku vorhanden

---

### 17 – Release und Branch-Hygiene

Geplante Reihenfolge:

    PATCHHARBOR.17a  Document PatchHarbor release version
    PATCHHARBOR.17b  Prepare PatchHarbor release
    PATCHHARBOR.17c  Prepare RepoDossier follow-up release
    PATCHHARBOR.17d  Add branch cleanup plan
    PATCHHARBOR.17e  Add final repository hygiene acceptance

Ziel:

- Releasefähigkeit herstellen.
- Branches und temporäre Arbeitsstände bereinigen.
- Beide Repos in sauberem Endzustand.

Abschlusskriterium:

- Tags/Releases vorbereitet
- Branches bereinigt
- keine untracked Artefakte
- beide Repos installierbar und testbar

---

## 5. Abhängigkeitsgraph

Vereinfachte Reihenfolge:

    06 Runner foundation
      -> 07 Wrapper compatibility foundation
        -> 08 Source-side adoption planning
          -> 09 First source-side wrapper adoption
            -> 10 Download runner parity and switch
              -> 11 Export runner migration
                -> 12 Helper migration
                  -> 13 Packaging and installation
                    -> 14 RepoDossier cleanup
                    -> 15 PatchHarbor cleanup
                      -> 16 End-to-end acceptance
                        -> 17 Release and branch hygiene

Wichtige Sperren:

- 09 darf nicht starten, bevor 08e grün ist.
- 10 darf nicht den alten Runner ersetzen, bevor 10b Paritätstests grün sind.
- 11 darf `r` nicht ändern, bevor Export-Inventar und Export-Tests stehen.
- 14 darf nichts löschen, bevor Ersatz und Akzeptanz grün sind.
- 17 darf erst kommen, wenn beide Repos sauber und grün sind.

---

## 6. Teststrategie

### Zielrepo PatchHarbor

Standard:

    python3 -m compileall src tests
    PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py'
    PYTHONPATH=src python3 -m patchharbor doctor --repo .

Focused Tests zusätzlich je Patch:

- neues Modul
- neue Dokumentationsdatei
- neue CLI-Ausgabe
- letzter roter Fehlerfall bei Fix-Patches

### Quellrepo RepoDossier

Vor Source-Adoption:

- keine Änderung ohne Preflight
- bestehende Tests grün
- Focused Tests für betroffene Scripts
- keine privaten Werte
- keine alten Workflows still brechen

Nach Source-Adoption:

- Wrapper-Smoke
- alter Runner existiert weiter
- Alias-Installer unverändert oder additiv
- Export-Scripts unverändert, bis Export-Migration startet

### Dual-Repo

Später ab Milestone 16:

- PatchHarbor als Tool nutzbar
- RepoDossier kann PatchHarbor nutzen
- beide Full-Suites grün
- keine lokalen Pfade in getrackten Dateien
- keine temporären Logs im Repo

---

## 7. Risiken und Gegenmaßnahmen

### Risiko: Zu frühe Source-Mutation

Gegenmaßnahme:

- Erst Zielrepo-Planung und Acceptance.
- Source-Patches additiv und klein.
- Keine alten Scripts löschen.

### Risiko: Bestehender Komfortworkflow bricht

Gegenmaßnahme:

- `c` zunächst nicht ändern.
- alter Runner bleibt erhalten.
- Wrapper zusätzlich einführen.
- Paritätstests vor Umschalten.

### Risiko: Generischer Core wird source-spezifisch

Gegenmaßnahme:

- RepoDossier-Namen nur in Docs/Tests, wenn bewusst.
- Keine lokalen Pfade.
- Keine source-spezifischen Runnernamen im PatchHarbor-Core.
- Konstanten und APIs generisch halten.

### Risiko: Self-referential Guards

Gegenmaßnahme:

- Verbotene Strings in Tests dynamisch zusammensetzen.
- Beispiel: `"run_latest_" + "download_patch"`.
- Keine verbotenen Literale in getrackten Testdateien.

### Risiko: CLI-Verträge brechen

Gegenmaßnahme:

- Bestehende CLI-Tests nie abschwächen.
- Output-Wörter wie `problem:` als API-Vertrag behandeln.
- Exit-Codes dokumentieren.

### Risiko: Cleanup löscht zu viel

Gegenmaßnahme:

- Erst Cleanup-Inventar.
- Dann Parität belegen.
- Dann löschen.
- Rollback dokumentieren.

---

## 8. Definition of Done

Die Migration ist abgeschlossen, wenn diese Bedingungen erfüllt sind.

### PatchHarbor

- eigenständiges Projekt
- installierbar
- CLI dokumentiert
- Tests grün
- generische APIs
- keine RepoDossier-Core-Hardcodings
- keine privaten Werte
- Public-Readiness-Doku vorhanden

### RepoDossier

- nutzt PatchHarbor für generische Runner-/Lint-/Helper-Logik
- enthält nur source-spezifische Wrapper und Fachlogik
- alte duplizierte Logik gelöscht oder historisch dokumentiert
- Tests grün
- Entwicklerdoku aktuell
- bestehender Workflow funktioniert oder ist bewusst ersetzt

### Beide Repos

- keine uncommitted Änderungen
- keine temporären Logs
- keine privaten Pfade oder Mailadressen
- keine toten Migrationsbranches
- E2E-Smoke grün
- Release-/Tag-Plan klar

---

## 9. Direkter nächster Abschnitt

Der direkte nächste Roadmap-Schritt nach `PATCHHARBOR.08d` ist:

    PATCHHARBOR.08e – Source-side Adoption Acceptance

Danach beginnt die erste echte Source-Adoption:

    PATCHHARBOR.09a – Source-side Adoption Preflight Inventory
    PATCHHARBOR.09b – Add PatchHarbor patch runner wrapper

Bis `PATCHHARBOR.09b` gilt weiterhin:

- keine RepoDossier-Dateien ändern
- keine Aliase installieren
- keine alten Scripts ersetzen
- keine Export-Scripts anfassen
