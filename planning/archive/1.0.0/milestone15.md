# MILESTONE 15 – Configuration Support

Ziel: RepoContext bekommt eine optionale Projektkonfiguration über `.repocontext.yml`, mit der Nutzer Exporte gezielt steuern können, ohne jedes Mal viele CLI-Optionen anzugeben. Die Konfiguration soll robust, optional, gut dokumentiert und durch Tests abgesichert sein.

## 15.1 – Configuration File Discovery

### 15.1.a – Add config module
- Neue Datei: `src/repocontext/config.py`
- Verantwortlichkeit:
  - `.repocontext.yml` im Repository-Root finden
  - Konfiguration laden
  - Defaults bereitstellen
  - Konfiguration validieren
- Keine Exportlogik in dieses Modul mischen.

### 15.1.b – Repository-root based config lookup
- Die Konfigurationsdatei wird ausschließlich im Repository-Root gesucht.
- Wenn RepoContext aus einem Unterordner gestartet wird, muss trotzdem die `.repocontext.yml` aus dem Repository-Root verwendet werden.
- Wenn keine Konfigurationsdatei existiert, läuft RepoContext unverändert mit Defaults weiter.

### 15.1.c – Add config model / dataclass
- Eine zentrale Config-Struktur einführen, z. B.:
  - `RepoContextConfig`
  - `IncludeExcludeConfig`
  - `ExportLimitsConfig`
- Defaults müssen klar definiert sein.
- Leere `.repocontext.yml` darf nicht crashen.

### 15.1.d – Tests for config discovery
- Tests:
  - keine `.repocontext.yml` vorhanden → Defaults
  - `.repocontext.yml` im Repository-Root vorhanden → wird geladen
  - Start aus Unterverzeichnis → Root-Konfig wird gefunden
  - leere Datei → Defaults
  - ungültiges YAML → verständliche Fehlermeldung

## 15.2 – YAML Parsing and Validation

### 15.2.a – Add YAML dependency strategy
- Prüfen, ob `PyYAML` bereits vorhanden ist.
- Falls nicht vorhanden:
  - `pyproject.toml` um `PyYAML` erweitern
  - Import sauber kapseln
- Fehler bei fehlender YAML-Unterstützung dürfen nicht kryptisch sein.

### 15.2.b – Supported `.repocontext.yml` schema
- Unterstützte Struktur:

```yaml
include:
  paths: []
  globs: []

exclude:
  paths: []
  globs: []

limits:
  max_file_bytes: null
  max_total_files: null
  max_export_bytes: null
  max_line_count: null
```

### 15.2.c – Validation rules
- Unbekannte Top-Level-Keys sollen eine klare Fehlermeldung erzeugen.
- Falsche Typen sollen eine klare Fehlermeldung erzeugen.
- Listenwerte müssen Strings sein.
- Limits müssen positive Integer oder `null` sein.
- Negative Werte sind ungültig.
- `0` ist ungültig, außer es gibt einen fachlich klaren Grund.

### 15.2.d – Tests for validation
- Tests:
  - gültige vollständige Konfiguration
  - gültige Teilkonfiguration
  - unbekannter Top-Level-Key
  - falscher Typ bei `include.paths`
  - falscher Typ bei `exclude.globs`
  - falscher Typ bei Limit
  - negatives Limit
  - String innerhalb Listen erlaubt
  - Nicht-String innerhalb Listen verboten

## 15.3 – Include Filters

### 15.3.a – Include path support
- `include.paths` implementieren.
- Wenn `include.paths` gesetzt ist:
  - Nur Dateien unter diesen Pfaden werden berücksichtigt.
  - Pfade sind relativ zum Repository-Root.
  - Dateien außerhalb der Include-Pfade werden aus allen Exporten ausgeschlossen.
- Wenn `include.paths` leer oder nicht gesetzt ist:
  - bisheriges Verhalten unverändert.

### 15.3.b – Include glob support
- `include.globs` implementieren.
- Glob-Muster relativ zum Repository-Root.
- Beispiele:
  - `src/**/*.py`
  - `tests/**/*.py`
  - `*.md`
- Wenn Include-Globs gesetzt sind:
  - Nur passende Dateien werden berücksichtigt.
- `include.paths` und `include.globs` sollen additiv wirken:
  - Datei ist enthalten, wenn sie zu mindestens einer Include-Regel passt.
  - Wenn keine Include-Regel gesetzt ist, ist grundsätzlich alles enthalten.

### 15.3.c – Include filter integration
- Include-Filter müssen vor Analyse und Export greifen.
- Betroffen:
  - full export
  - ai export
  - docs export
  - changed export, soweit sinnvoll
  - Symbol Extraction
  - Import Graph
  - Call Graph
  - Dependency/Schema/Secret Detection, soweit dateibasiert
- Kein Export soll Dateien analysieren, die durch Include-Regeln ausgeschlossen sind.

### 15.3.d – Tests for include filters
- Tests:
  - Include-Pfad `src` nimmt nur Dateien aus `src`
  - Include-Pfad `tests` nimmt nur Tests
  - Include-Glob `src/**/*.py`
  - Include-Glob `*.md`
  - Kombination aus Pfad und Glob
  - keine Include-Regel → bisheriges Verhalten
  - Start aus Unterverzeichnis → Include-Regeln bleiben repository-root relativ

## 15.4 – Exclude Filters

### 15.4.a – Exclude path support
- `exclude.paths` implementieren.
- Dateien unter diesen Pfaden werden ausgeschlossen.
- Pfade relativ zum Repository-Root.
- Beispiele:
  - `.venv`
  - `build`
  - `dist`
  - `node_modules`
  - `tmp`

### 15.4.b – Exclude glob support
- `exclude.globs` implementieren.
- Beispiele:
  - `*.log`
  - `*.sqlite`
  - `**/__pycache__/**`
  - `private/**`
- Glob-Excludes sollen auf normalisierte relative Pfade angewendet werden.

### 15.4.c – Exclude wins over include
- Wenn eine Datei sowohl durch Include als auch Exclude getroffen wird:
  - Exclude gewinnt.
- Das muss explizit getestet und dokumentiert werden.

### 15.4.d – Default excludes prüfen
- Prüfen, ob bestehende Ausschlüsse bereits existieren.
- Keine bestehenden sinnvollen Defaults kaputtmachen.
- `.repocontext.yml` ergänzt die bestehenden Mechanismen, ersetzt sie nicht blind.
- Falls bestehende Ausschlusslogik existiert:
  - sauber zentralisieren oder kompatibel anbinden.

### 15.4.e – Tests for exclude filters
- Tests:
  - Exclude-Pfad schließt Ordner aus
  - Exclude-Glob schließt Dateien aus
  - Exclude gewinnt über Include
  - mehrere Exclude-Regeln
  - Exclude auf Datei
  - Exclude auf Verzeichnis
  - Start aus Unterverzeichnis → Exclude-Regeln bleiben repository-root relativ

## 15.5 – Export Limits

### 15.5.a – Max file bytes
- `limits.max_file_bytes` implementieren.
- Dateien oberhalb dieses Limits werden nicht vollständig exportiert.
- Verhalten:
  - Datei bleibt in Summary/Tree sichtbar, wenn sie grundsätzlich erkannt wird.
  - Im Source Dump erscheint ein klarer Hinweis, dass die Datei wegen Limit übersprungen wurde.
- Keine stillen Drops.

### 15.5.b – Max total files
- `limits.max_total_files` implementieren.
- Wenn mehr Dateien gefunden werden als erlaubt:
  - Export begrenzen
  - klaren Hinweis im Export ausgeben
  - deterministische Sortierung verwenden
- Keine zufällige Auswahl.

### 15.5.c – Max export bytes
- `limits.max_export_bytes` implementieren.
- Export soll nicht endlos wachsen.
- Wenn Limit erreicht ist:
  - sauber abbrechen
  - Hinweis am Ende oder an passender Stelle ausgeben
  - kein kaputter halbformatierter Export, soweit vermeidbar

### 15.5.d – Max line count
- `limits.max_line_count` implementieren.
- Pro Datei oder global klar definieren.
- Bevorzugt pro Datei:
  - Datei wird nur bis zu dieser Zeilenzahl ausgegeben.
  - Hinweis ergänzen, dass Rest gekürzt wurde.
- Verhalten dokumentieren.

### 15.5.e – Tests for export limits
- Tests:
  - große Datei über `max_file_bytes`
  - viele Dateien über `max_total_files`
  - Export über `max_export_bytes`
  - Datei über `max_line_count`
  - Kombination mehrerer Limits
  - Hinweise erscheinen im Export
  - deterministisches Verhalten

## 15.6 – CLI Integration

### 15.6.a – Config automatically used by export commands
- `.repocontext.yml` wird automatisch berücksichtigt bei:
  - `repocontext full`
  - `repocontext export-ai`
  - `repocontext export-docs`
  - `repocontext changed`
- Keine Pflichtoption nötig.

### 15.6.b – Optional `--config` CLI argument
- Optionalen Parameter prüfen/implementieren:
  - `--config PATH`
- Wenn gesetzt:
  - explizite Datei verwenden
  - Pfade darin trotzdem relativ zum Repository-Root interpretieren, außer bewusst anders dokumentiert
- Wenn Datei nicht existiert:
  - klare Fehlermeldung

### 15.6.c – Optional `--no-config`
- Optionalen Parameter prüfen/implementieren:
  - `--no-config`
- Damit kann Konfiguration bewusst ignoriert werden.
- Hilfreich für Debugging und Tests.

### 15.6.d – CLI help verbessern
- argparse-Hilfe ergänzen:
  - `--config`
  - `--no-config`
  - kurze Beschreibung zur `.repocontext.yml`
- Roadmap-Hinweis beachten:
  - argparse-Beschreibungen sollen gut verständlich sein.

### 15.6.e – Tests for CLI integration
- Tests:
  - Export nutzt `.repocontext.yml` automatisch
  - `--no-config` ignoriert Datei
  - `--config custom.yml` nutzt Custom-Datei
  - fehlende Custom-Datei → Fehler
  - Hilfe enthält Config-Optionen

## 15.7 – Export Visibility / Metadata

### 15.7.a – Config summary in full export
- Im `full.txt` eine kurze Konfigurationsübersicht ergänzen.
- Inhalt:
  - ob Config aktiv ist
  - verwendeter Config-Pfad
  - aktive Include-Regeln
  - aktive Exclude-Regeln
  - aktive Limits
- Keine übermäßig lange Ausgabe.

### 15.7.b – Config summary in AI export
- Im `ai.txt` ebenfalls kurz sichtbar machen:
  - Config aktiv ja/nein
  - wichtigste Filter/Limits
- Ziel: KI sieht, dass Export absichtlich gefiltert oder gekürzt ist.

### 15.7.c – Config summary in docs export
- Prüfen, ob `docs.txt` eine Config Summary braucht.
- Wenn ja:
  - kurz und dokumentationsnah halten.
- Wenn nein:
  - bewusst begründen und testen, dass Verhalten sinnvoll bleibt.

### 15.7.d – Tests for config metadata
- Tests:
  - full export enthält Config-Hinweis
  - ai export enthält Config-Hinweis
  - Hinweise bei Defaults sind nicht störend
  - aktive Filter/Limits erscheinen korrekt

## 15.8 – Documentation

### 15.8.a – README documentation
- README um `.repocontext.yml` erweitern.
- Inhalte:
  - Zweck
  - Beispiel
  - Include/Exclude-Regeln
  - Limits
  - Exclude gewinnt über Include
  - CLI-Optionen `--config` und `--no-config`, falls implementiert

### 15.8.b – Example config file
- Beispiel ergänzen, z. B.:
  - `.repocontext.example.yml`
  - oder README-Codeblock
- Wenn Datei angelegt wird:
  - sicherstellen, dass sie im Export sinnvoll behandelt wird
  - nicht versehentlich als aktive Config nutzen

### 15.8.c – Docs export should include config documentation
- Wenn README/SPEC/ARCHITECTURE/TASKS extrahiert werden, muss die neue Dokumentation im docs export sichtbar sein.
- Regressionstest ergänzen.

### 15.8.d – Tests for documentation
- Tests:
  - README erwähnt `.repocontext.yml`
  - README erklärt Include
  - README erklärt Exclude
  - README erklärt Limits
  - README erklärt Exclude-vor-Include
  - docs export enthält Config-Dokumentation

## 15.9 – Final Integration and Regression

### 15.9.a – Full test suite
- Gesamte Testsuite ausführen.
- Keine bestehenden Milestones dürfen regressieren:
  - Full Export
  - AI Export
  - Docs Export
  - Changed Export
  - Secret Detection
  - Dependency Detection
  - Schema Extraction
  - Ranking
  - Import/Call Graph

### 15.9.b – Manual acceptance scenario
- Temporär eine `.repocontext.yml` im Projekt testen:

```yaml
include:
  paths:
    - src
    - tests
  globs:
    - "*.md"

exclude:
  paths:
    - .venv
    - build
    - dist
  globs:
    - "*.log"
    - "*.sqlite"

limits:
  max_file_bytes: 200000
  max_total_files: 500
  max_export_bytes: 2000000
  max_line_count: 2000
```

- Dann ausführen:
  - `repocontext full`
  - `repocontext export-ai`
  - `repocontext export-docs`
  - `repocontext changed`
- Prüfen:
  - Config wird erkannt
  - Filter greifen
  - Limits greifen
  - Hinweise erscheinen
  - keine Secrets werden unmaskiert ausgegeben

### 15.9.c – Final changed command repository-root handling
- Speziell prüfen, dass `repocontext changed` aus Unterordnern weiterhin korrekt funktioniert.
- `.repocontext.yml` muss auch dabei aus dem Repository-Root geladen werden.

### 15.9.d – Final commit
- Nach grünem Testlauf Commit erstellen:
  - `Add configuration support`
- Danach:
  - `git status --short`
  - `git log --oneline --decorate -5`

## Akzeptanzkriterien

Milestone 15 gilt als fertig, wenn:

- `.repocontext.yml` optional unterstützt wird.
- Ohne Config bleibt das bisherige Verhalten erhalten.
- Include-Filter funktionieren.
- Exclude-Filter funktionieren.
- Exclude gewinnt über Include.
- Export-Limits funktionieren.
- Gefilterte oder gekürzte Exporte enthalten klare Hinweise.
- Export-Kommandos nutzen Config automatisch.
- Start aus Unterverzeichnissen funktioniert korrekt.
- CLI-Hilfe ist verständlich.
- README/Dokumentation ist aktualisiert.
- Relevante Regressionstests sind vorhanden.
- Die vollständige Testsuite ist grün.
