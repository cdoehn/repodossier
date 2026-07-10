# MILESTONE19.md — Rename RepoContext to RepoDossier

## Ziel

Das Projekt wird sauber von `RepoContext` / `repocontext` zu `RepoDossier` / `repodossier` umbenannt.

Die Umbenennung soll nicht als blindes globales Suchen-und-Ersetzen erfolgen, sondern schrittweise und testbar:

- Neuer Produktname: `RepoDossier`
- Neuer CLI-Befehl: `repodossier`
- Neues Python-Package: `repodossier`
- Alter CLI-Befehl `repocontext` bleibt vorerst als Legacy-Alias erhalten
- Alte Config-Namen werden vorerst weiter akzeptiert
- Dokumentation, Tests, Packaging und interne Namen werden konsistent angepasst
- Alte Namensreste bleiben nur dort erhalten, wo sie bewusst als Legacy-Kompatibilität dokumentiert sind

Die Export-Dateien bleiben unverändert:

- `full.txt`
- `ai.txt`
- `docs.txt`
- `changed.txt`

---

## 19.1 Projekt-Metadaten und CLI-Alias vorbereiten

### Ziel

Das Projekt soll zuerst unter dem neuen Namen installierbar und ausführbar werden, ohne die alte CLI-Nutzung sofort zu brechen.

### Aufgaben

1. `pyproject.toml` aktualisieren:
   - Projektname auf `repodossier` ändern
   - Beschreibung von RepoContext auf RepoDossier aktualisieren
   - URLs, Keywords und sonstige Metadaten prüfen und aktualisieren

2. CLI-Scripts anpassen:
   - Neuer Befehl:
     - `repodossier = "repodossier.cli:main"`
   - Alter Legacy-Befehl bleibt erhalten:
     - `repocontext = "repodossier.cli:main"`

3. Tests ergänzen oder anpassen:
   - `repodossier --help` funktioniert
   - `repocontext --help` funktioniert weiterhin als Legacy-Alias
   - Beide Befehle zeigen konsistente Hilfeausgaben

4. Dokumentation in diesem Schritt noch nur minimal ändern:
   - Keine vollständige README-Umschreibung
   - Nur technische Stellen, die für Tests oder Packaging nötig sind

### Akzeptanzkriterien

- Projekt kann mit neuem Namen installiert werden
- `repodossier --help` funktioniert
- `repocontext --help` funktioniert weiterhin
- Bestehende Tests bleiben grün oder werden kontrolliert angepasst
- Es gibt noch keine vollständige Entfernung aller alten Namen

### Commit-Vorschlag

`Add RepoDossier metadata and CLI alias`

---

## 19.2 Python-Package von repocontext nach repodossier umbenennen

### Ziel

Die interne Python-Package-Struktur wird auf den neuen Namen umgestellt.

### Aufgaben

1. Package-Verzeichnis verschieben:
   - `src/repocontext/`
   - nach:
   - `src/repodossier/`

2. Alle Imports in `src/` aktualisieren:
   - `repocontext`
   - zu:
   - `repodossier`

3. Alle Imports in `tests/` aktualisieren:
   - `repocontext`
   - zu:
   - `repodossier`

4. Testdaten, Fixtures und Hilfsfunktionen prüfen:
   - Pfade
   - Modulnamen
   - CLI-Runner
   - erwartete Fehlermeldungen

5. Optionales Legacy-Package prüfen:
   - Falls sinnvoll, kleines Kompatibilitätspackage `src/repocontext/` behalten
   - Dieses soll nur auf `repodossier` weiterleiten
   - Nicht mehr als Hauptpackage verwenden

### Akzeptanzkriterien

- Alle produktiven Imports verwenden `repodossier`
- Tests importieren primär `repodossier`
- Das neue Package ist installierbar
- Der alte CLI-Befehl `repocontext` funktioniert weiterhin
- Kein unbeabsichtigter harter Bruch durch fehlende Modulpfade

### Commit-Vorschlag

`Rename Python package to repodossier`

---

## 19.3 Config-Namen migrieren und Legacy-Kompatibilität behalten

### Ziel

Neue RepoDossier-Konfigurationsnamen werden eingeführt, alte RepoContext-Konfigurationsnamen bleiben vorerst nutzbar.

### Neue Config-Namen

- `.repodossier.toml`
- `.repodossier.yml`
- `.repodossier.yaml`
- `[tool.repodossier]`

### Alte Legacy-Config-Namen

- `.repocontext.toml`
- `.repocontext.yml`
- `.repocontext.yaml`
- `[tool.repocontext]`

### Aufgaben

1. Config-Discovery auf neue Namen erweitern:
   - Neue RepoDossier-Namen zuerst prüfen
   - Alte RepoContext-Namen danach als Fallback akzeptieren

2. Prioritätsregeln festlegen:
   - Neue Config gewinnt vor alter Config
   - Wenn neue und alte Config gleichzeitig existieren, neue Config verwenden
   - Optional Warnung ausgeben, wenn alte Config ignoriert wird

3. Legacy-Warnung einbauen:
   - Bei Verwendung alter Config soll eine klare Warnung erscheinen
   - Beispiel:
     - `Warning: repocontext config is deprecated. Use repodossier instead.`

4. Tests ergänzen:
   - Neue `.repodossier.*` Config wird erkannt
   - Neue `[tool.repodossier]` Config wird erkannt
   - Alte `.repocontext.*` Config wird noch erkannt
   - Alte `[tool.repocontext]` Config wird noch erkannt
   - Neue Config hat Priorität vor alter Config

5. Fehlermeldungen und Help-Texte prüfen:
   - Neue Beispiele verwenden `repodossier`
   - Legacy-Hinweise dürfen `repocontext` enthalten

### Akzeptanzkriterien

- Neue Config-Namen funktionieren vollständig
- Alte Config-Namen funktionieren weiterhin als Legacy-Fallback
- Priorität ist eindeutig getestet
- Alte Config-Nutzung ist als deprecated erkennbar
- Keine bestehende Projektkonfiguration bricht unnötig

### Commit-Vorschlag

`Add RepoDossier config names with repocontext legacy support`

---

## 19.4 CLI-Kommandos und Help-Ausgaben auf RepoDossier umstellen

### Ziel

Alle sichtbaren CLI-Ausgaben sollen RepoDossier als aktuellen Namen verwenden.

### Aufgaben

1. CLI-Hilfe prüfen und aktualisieren:
   - Produktname
   - Beschreibung
   - Beispiele
   - Fehlertexte
   - Config-Hinweise

2. Alle CLI-Beispiele auf neuen Befehl umstellen:
   - `repodossier full`
   - `repodossier export-ai`
   - `repodossier export-docs`
   - `repodossier changed`

3. Legacy-Alias testen:
   - `repocontext` bleibt ausführbar
   - Doku bewirbt aber primär `repodossier`

4. Tests für Help-Ausgaben aktualisieren:
   - Neue Hilfe enthält `RepoDossier`
   - Neue Hilfe enthält `repodossier`
   - Alte Hilfe darf `repocontext` nur als Legacy-Alias erwähnen

5. Snapshot-/Texttests prüfen:
   - Erwartete Strings aktualisieren
   - Alte Namen nur bewusst erlauben

### Akzeptanzkriterien

- CLI fühlt sich sichtbar wie RepoDossier an
- Neuer Befehl ist der Hauptbefehl
- Alter Befehl ist nur noch Legacy
- Help- und Error-Ausgaben sind konsistent
- Tests sind angepasst und grün

### Commit-Vorschlag

`Update CLI output for RepoDossier`

---

## 19.5 Tests vollständig auf neue Namen umstellen

### Ziel

Die Test-Suite soll RepoDossier als Hauptnamen abbilden und alte Namen nur noch gezielt als Legacy-Fälle testen.

### Aufgaben

1. Testdateien prüfen:
   - Dateinamen mit `repocontext` prüfen und ggf. umbenennen
   - Testklassen und Testfunktionen mit altem Namen prüfen
   - Fixtures und Hilfstexte aktualisieren

2. Tests für neue CLI ergänzen:
   - `repodossier full`
   - `repodossier export-ai`
   - `repodossier export-docs`
   - `repodossier changed`
   - `repodossier --help`

3. Legacy-Tests isolieren:
   - Alte CLI `repocontext` funktioniert
   - Alte Config-Namen funktionieren
   - Alte Namen erscheinen nur in Legacy-Testfällen

4. Grep-Test oder Namensprüfung ergänzen:
   - Alte Namensreste sollen gefunden werden
   - Erlaubte Legacy-Treffer sollen explizit erlaubt sein
   - Unbeabsichtigte Treffer sollen Tests fehlschlagen lassen

5. Alle Tests ausführen:
   - vollständige pytest-Suite
   - relevante CLI-End-to-End-Tests
   - README-/Dokumentations-Tests, falls vorhanden

### Akzeptanzkriterien

- Tests verwenden RepoDossier als Standard
- Legacy-Verhalten ist separat und bewusst getestet
- Keine zufälligen alten Namen bleiben in Test-Erwartungen übrig
- Vollständige Test-Suite ist grün

### Commit-Vorschlag

`Update tests for RepoDossier naming`

---

## 19.6 README und Dokumentation aktualisieren

### Ziel

Die öffentliche Dokumentation wird vollständig auf RepoDossier umgestellt.

### Aufgaben

1. `README.md` aktualisieren:
   - Titel
   - Beschreibung
   - Installation
   - Quickstart
   - CLI-Beispiele
   - Config-Beispiele
   - Export-Modi
   - Legacy-Hinweise

2. Alte Beispiele ersetzen:
   - `repocontext full`
   - zu:
   - `repodossier full`

3. Config-Beispiele ersetzen:
   - `[tool.repocontext]`
   - zu:
   - `[tool.repodossier]`

4. Legacy-Abschnitt ergänzen:
   - Alter CLI-Befehl `repocontext` wird vorerst unterstützt
   - Alte Config-Namen werden vorerst unterstützt
   - Neue Projects sollen `repodossier` verwenden

5. Weitere Dokumentation aktualisieren:
   - `architecture.md`
   - `planning/spec.md`
   - Milestone-Dateien nur soweit nötig
   - Keine unnötige historische Umschreibung alter Milestones

6. README-Dokumentationstests aktualisieren:
   - Befehle
   - Beispielausgaben
   - erwartete Dateinamen
   - erwartete Help-Texte

### Akzeptanzkriterien

- README bewirbt nur noch RepoDossier als aktuellen Namen
- Beispiele sind kopierbar und funktionieren
- Legacy-Verhalten ist kurz dokumentiert
- Dokumentationstests sind grün
- Alte historische Namensreste sind nur dort vorhanden, wo sie bewusst sinnvoll sind

### Commit-Vorschlag

`Update documentation for RepoDossier`

---

## 19.7 Alte Architektur- und Spec-Dateien bereinigen

### Ziel

Alte RepoContext-spezifische Dateinamen werden neutral oder RepoDossier-konform benannt.

### Aufgaben

1. Architekturdatei prüfen und umbenennen:
   - `REPOCONTEXT_ARCHITECTURE.md`
   - zu:
   - `architecture.md`

2. Spec-Datei prüfen und umbenennen:
   - `REPOCONTEXT_SPEC_v1.3.txt`
   - zu:
   - `planning/spec.md`

3. Alte Release-Datei prüfen:
   - `RELEASE_1.0.0.md`
   - entscheiden:
     - löschen, falls keine echte Release-Historie
     - oder in `CHANGELOG.md` überführen
     - oder nach `docs/releases/1.0.0.md` verschieben

4. Interne Links aktualisieren:
   - README-Links
   - Planning-Links
   - Architektur-Links
   - Tests, die Dateinamen erwarten

5. Alte Dateien nicht doppelt behalten:
   - Keine alten REPOCONTEXT-Dateien als Kopien liegen lassen
   - Keine widersprüchliche Doku

### Akzeptanzkriterien

- Architektur und Spec haben saubere neue Pfade
- README und Tests verweisen auf neue Pfade
- Keine veralteten REPOCONTEXT-Dateinamen bleiben unbeabsichtigt im Projektroot
- Release-/Changelog-Frage ist sauber entschieden

### Commit-Vorschlag

`Rename architecture and spec documents`

---

## 19.8 Alte Namensreste suchen und bewusst bereinigen

### Ziel

Alle alten Namensvarianten werden systematisch gesucht und entweder ersetzt oder bewusst als Legacy erlaubt.

### Zu suchende Varianten

- `RepoContext`
- `repocontext`
- `REPOCONTEXT`
- `repo_context`
- `Repo Context`
- `repo-context`

### Aufgaben

1. Grep-Prüfung ausführen:
   - in `README.md`
   - in `pyproject.toml`
   - in `src/`
   - in `tests/`
   - in `planning/`
   - in `docs/`, falls vorhanden

2. Treffer klassifizieren:
   - Muss ersetzt werden
   - Darf als Legacy bleiben
   - Darf als historische Erwähnung bleiben
   - Muss aus Tests entfernt werden

3. Unerwünschte Treffer ersetzen:
   - Produktname
   - CLI-Beispiele
   - Config-Beispiele
   - Fehlermeldungen
   - interne Kommentare
   - Testnamen

4. Erlaubte Treffer dokumentieren:
   - Legacy-CLI-Alias
   - Legacy-Config-Fallback
   - Migration-Hinweis
   - historische Milestone-Texte, falls bewusst nicht geändert

5. Optional einen automatischen Test ergänzen:
   - Der Test erlaubt alte Namen nur in definierten Dateien oder definierten Textstellen

### Akzeptanzkriterien

- Alte Namen sind nicht mehr zufällig im Projekt verteilt
- Jeder verbleibende alte Name hat einen klaren Grund
- Neue Namen sind konsistent
- Grep-Ausgabe ist kurz und erklärbar

### Commit-Vorschlag

`Clean up remaining RepoContext naming references`

---

## 19.9 Finale Integrationsprüfung

### Ziel

Nach der Umbenennung wird das Projekt vollständig geprüft.

### Aufgaben

1. Vollständige Tests ausführen:
   - `python3 -m pytest --color=yes`

2. CLI manuell prüfen:
   - `repodossier --help`
   - `repodossier full`
   - `repodossier export-ai`
   - `repodossier export-docs`
   - `repodossier changed`
   - `repocontext --help`

3. RepoDossier selbst auf das Projekt anwenden:
   - `repodossier full`
   - `repodossier export-ai`
   - `repodossier export-docs`
   - optional `repodossier changed`

4. Export-Dateien prüfen:
   - `full.txt`
   - `ai.txt`
   - `docs.txt`
   - `changed.txt`

5. Alte-Namen-Grep erneut ausführen:
   - nur erlaubte Legacy-/Migrationsstellen dürfen übrig bleiben

6. Git-Status prüfen:
   - keine unerwarteten Dateien
   - keine alten doppelten Dateien
   - keine temporären Testdateien
   - keine generierten Artefakte versehentlich committen, falls sie nicht vorgesehen sind

### Akzeptanzkriterien

- Vollständige Tests sind grün
- Neuer CLI-Befehl funktioniert
- Alter CLI-Alias funktioniert
- Exporte funktionieren
- Doku ist konsistent
- Keine unerklärten alten Namensreste bleiben übrig
- Git-Status ist sauber erklärbar

### Commit-Vorschlag

`Finalize RepoDossier rename`

---

## 19.10 Optional: Repository und externe Namen umstellen

### Ziel

Nach erfolgreicher Code-Umbenennung können externe Namen angepasst werden.

### Aufgaben

1. GitHub-Repository umbenennen:
   - von bisherigem Namen
   - zu:
   - `repodossier` oder `repo-dossier`

2. Lokale Remote-URL prüfen:
   - `git remote -v`

3. Falls nötig Remote-URL aktualisieren:
   - neue GitHub-URL setzen

4. README-Badges prüfen:
   - Build
   - Tests
   - Coverage
   - PyPI
   - GitHub Links

5. Falls Veröffentlichung geplant:
   - PyPI-Verfügbarkeit final prüfen
   - Package-Name `repodossier` reservieren
   - Testveröffentlichung prüfen
   - Release-Prozess vorbereiten

### Akzeptanzkriterien

- Externer Repo-Name passt zu RepoDossier
- Remote zeigt auf korrekten Pfad
- README-Links funktionieren
- Optionaler Veröffentlichungsname ist konsistent

### Commit-Vorschlag

`Update repository links for RepoDossier`

---

## Gesamt-Akzeptanz für Milestone 19

Milestone 19 gilt als abgeschlossen, wenn:

1. Das Projekt sichtbar `RepoDossier` heißt.
2. Der neue CLI-Befehl `repodossier` vollständig funktioniert.
3. Der alte CLI-Befehl `repocontext` vorerst als Legacy-Alias funktioniert.
4. Das Python-Package intern `repodossier` heißt.
5. Neue Config-Namen mit `repodossier` funktionieren.
6. Alte Config-Namen mit `repocontext` weiterhin als Legacy-Fallback funktionieren.
7. README und Hauptdokumentation den neuen Namen verwenden.
8. Alte Namen nur noch an bewusst erlaubten Legacy- oder Migrationsstellen vorkommen.
9. Die vollständige pytest-Suite grün ist.
10. RepoDossier kann seine eigenen Export-Dateien erzeugen.
11. Keine alten doppelten Architektur-/Spec-Dateien im Projektroot liegen bleiben.
12. Git-Status nach Abschluss sauber und erklärbar ist.

---

## Vorgeschlagene Commit-Reihenfolge

1. `Add RepoDossier metadata and CLI alias`
2. `Rename Python package to repodossier`
3. `Add RepoDossier config names with repocontext legacy support`
4. `Update CLI output for RepoDossier`
5. `Update tests for RepoDossier naming`
6. `Update documentation for RepoDossier`
7. `Rename architecture and spec documents`
8. `Clean up remaining RepoContext naming references`
9. `Finalize RepoDossier rename`

---

## Nicht-Ziele

Folgende Dinge gehören nicht zwingend zu Milestone 19:

1. Export-Dateien umbenennen
   - `full.txt`, `ai.txt`, `docs.txt`, `changed.txt` bleiben unverändert

2. Legacy-Alias sofort entfernen
   - `repocontext` bleibt vorerst erhalten

3. Alte Config-Unterstützung sofort entfernen
   - alte `repocontext`-Config bleibt vorerst nutzbar

4. Komplette historische Milestone-Dateien umschreiben
   - alte Milestones dürfen historische Namen enthalten, wenn sie bewusst als Historie gelten

5. Neue Features einbauen
   - Milestone 19 ist eine Umbenennung, kein Feature-Milestone

6. Veröffentlichung auf PyPI erzwingen
   - PyPI kann später erfolgen

7. GitHub-Repository zwingend sofort umbenennen
   - externe Umbenennung kann nach erfolgreicher Code-Migration erfolgen
