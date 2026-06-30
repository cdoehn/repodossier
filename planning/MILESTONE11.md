# MILESTONE 11 – Database Schema Extraction

Ziel:
RepoContext soll Datenbank-Schemas statisch bzw. sicher aus Projektdateien erkennen und strukturiert in den Exporten sichtbar machen.

Milestone 11 erweitert RepoContext um eine Database-Schema-Analyse für typische Projekt-Repositories.

Erkannt werden sollen insbesondere:

- SQLite-Datenbankdateien
- SQLite-Schema über sqlite_master / sqlite_schema
- CREATE TABLE Statements in SQL-Dateien
- Tabellenübersichten
- Spaltenübersichten
- Primärschlüssel / Foreign Keys, soweit einfach erkennbar
- Warnings bei kaputten oder nicht lesbaren Datenbanken

Wichtig:
- Kein Ausführen von Projektcode.
- Keine Migrationen ausführen.
- Keine Datenbankdaten exportieren.
- Nur Schema/Metadaten exportieren.
- Nur Git-tracked Dateien berücksichtigen.
- Binary-Datenbankdateien dürfen analysiert werden, aber nicht als Source Dump ausgegeben werden.
- Bestehende full.txt, ai.txt und docs.txt Funktionalität darf nicht regressieren.
- Use RepoContext CLI exports for final checks; do not use deprecated snapshot scripts.
- Tests semantisch passend einsortieren.

====================================================================
11.0 – Bestandsprüfung vor Implementierung
====================================================================

11.0.a – Aktuelle Export-Pipeline prüfen

Ziel:
Klären, wo die neue Schema-Analyse sauber eingehängt wird.

Zu prüfen:
- src/repocontext/exporters/full.py
- src/repocontext/exporters/ai.py
- src/repocontext/exporters/__init__.py
- src/repocontext/scanner.py
- src/repocontext/models.py
- src/repocontext/cli.py
- tests/test_full_exporter.py
- tests/test_ai_exporter.py

Akzeptanzkriterien:
- Klarheit, wie Analyzer aktuell integriert sind.
- Database Schema wird als eigener Analyzer geplant.
- Exporter bekommen nur fertige Schema-Daten, keine direkte sqlite-Logik.


11.0.b – Aktuelle Scanner-Grenzen prüfen

Ziel:
Klären, wie Binärdateien und Git-tracked Datenbankdateien aktuell behandelt werden.

Zu prüfen:
- Werden .db/.sqlite/.sqlite3 Dateien als binary erkannt?
- Sind binary files in scanned_files enthalten?
- Werden binary files im full.txt Source Dump übersprungen?
- Sind relative Pfade stabil verfügbar?

Akzeptanzkriterien:
- SQLite-Dateien können trotz Binary-Status als Kandidaten erkannt werden.
- Source Dump bleibt unverändert sicher.
- Schema-Analyse nutzt nur Metadaten/Pfade.

====================================================================
11.1 – Database Schema Datenmodell
====================================================================

11.1.a – Neues Modul schema.py anlegen

Neue Datei:
- src/repocontext/schema.py

Ziel:
Alle Datenbank-Schema-Funktionen sauber vom Scanner und von den Exportern trennen.

Akzeptanzkriterien:
- Kein sqlite-Code in full.py oder ai.py.
- Modul ist importierbar.
- Bestehende Tests bleiben grün.


11.1.b – SchemaColumn Dataclass einführen

Datenstruktur für eine Tabellenspalte.

Felder:
- name
- data_type
- nullable
- default_value
- primary_key_position
- raw_definition optional

Beispiel:
- id INTEGER PRIMARY KEY
- name TEXT NOT NULL
- created_at TEXT DEFAULT CURRENT_TIMESTAMP

Akzeptanzkriterien:
- Spalten sind stabil sortierbar.
- Fehlende Typen werden robust als leer/unknown behandelt.
- Keine Datenbankwerte werden gespeichert.


11.1.c – SchemaForeignKey Dataclass einführen

Datenstruktur für Foreign Keys.

Felder:
- table
- from_column
- to_table
- to_column
- on_update
- on_delete
- match

Akzeptanzkriterien:
- SQLite PRAGMA foreign_key_list kann abgebildet werden.
- Fehlende Felder crashen nicht.
- Ausgabe bleibt kompakt.


11.1.d – SchemaIndex Dataclass einführen

Datenstruktur für Indizes.

Felder:
- name
- table
- unique
- columns
- origin
- partial

Akzeptanzkriterien:
- SQLite PRAGMA index_list und index_info können abgebildet werden.
- Interne SQLite-Indizes können optional ausgeblendet werden.
- Sortierung ist deterministisch.


11.1.e – SchemaTable Dataclass einführen

Datenstruktur für Tabellen.

Felder:
- name
- table_type
- columns
- foreign_keys
- indexes
- create_sql
- source_file

table_type Beispiele:
- table
- view
- virtual_table
- unknown

Akzeptanzkriterien:
- Normale Tabellen werden erkannt.
- Views können erkannt oder separat geführt werden.
- CREATE SQL bleibt nachvollziehbar, aber Datenbankdaten fehlen.


11.1.f – DatabaseSchemaReport Dataclass einführen

Übergeordnete Struktur.

Felder:
- database_files
- tables
- views
- sql_schema_files
- create_statements
- warnings
- errors
- unsupported_files

Akzeptanzkriterien:
- Leerer Report ist möglich.
- Fehlerhafte Datenbanken führen zu Warning statt Crash.
- Sortierung ist stabil.


11.1.g – Stabile Sortierung definieren

Sortierung:
1. source_file
2. table_type
3. table name
4. column position/name

Akzeptanzkriterien:
- Export-Ausgabe ist deterministisch.
- Tests hängen nicht von sqlite-Reihenfolge ab.

====================================================================
11.2 – Database File Discovery
====================================================================

11.2.a – SQLite-Dateiendungen erkennen

Erkennen:
- .db
- .sqlite
- .sqlite3
- .db3
- .s3db

Akzeptanzkriterien:
- Git-tracked SQLite-Dateien werden als Kandidaten aufgenommen.
- Nicht vorhandene oder untracked Dateien werden nicht analysiert.


11.2.b – SQLite Magic Header prüfen

Ziel:
Nicht jede .db Datei blind als SQLite behandeln.

SQLite-Dateien beginnen typischerweise mit:
- SQLite format 3

Akzeptanzkriterien:
- Echte SQLite-Dateien werden erkannt.
- Falsche .db Dateien werden als unsupported/warning behandelt.
- Kein Crash bei kleinen/leeren Dateien.


11.2.c – SQL-Dateien erkennen

Erkennen:
- .sql
- Dateien unter migrations/
- Dateien unter schema/
- Dateien unter sql/
- optional: *.sqlite.sql

Akzeptanzkriterien:
- SQL-Dateien werden als mögliche CREATE TABLE Quellen erkannt.
- Nur Git-tracked Dateien werden analysiert.
- Binäre Dateien werden nicht als SQL gelesen.


11.2.d – Generated Exports ausschließen

Ausschließen:
- full.txt
- ai.txt
- docs.txt
- changed.txt

Akzeptanzkriterien:
- Keine Self-Reference.
- Wiederholte Exporte wachsen nicht durch eigene Schema-Ausgabe.


11.2.e – Discovery Tests schreiben

Testfälle:
- database.sqlite wird erkannt.
- app.db wird erkannt.
- random.db ohne SQLite Header wird als unsupported markiert.
- schema.sql wird erkannt.
- src/app.py wird nicht erkannt.
- full.txt wird nicht erkannt.

Akzeptanzkriterien:
- Discovery ist deterministisch.
- Tests liegen in tests/test_schema.py oder semantisch passender Datei.

====================================================================
11.3 – SQLite Schema Extraction
====================================================================

11.3.a – SQLite-Verbindung read-only öffnen

Ziel:
SQLite-Dateien sicher lesen.

Anforderung:
- sqlite3 stdlib verwenden
- read-only mode verwenden, wenn möglich
- keine Änderungen an der DB
- keine Migrationen
- keine User-Queries

Akzeptanzkriterien:
- Datenbankdatei wird nicht verändert.
- Fehler werden als Warning erfasst.
- Kein Projektcode wird ausgeführt.


11.3.b – Tabellen aus sqlite_schema lesen

Query nur gegen Schema-Metadaten:

SELECT type, name, tbl_name, sql
FROM sqlite_schema
WHERE type IN ('table', 'view')
ORDER BY type, name

Akzeptanzkriterien:
- Tabellen werden erkannt.
- Views werden erkannt.
- sqlite interne Tabellen werden optional ausgeblendet oder klar markiert.


11.3.c – SQLite interne Tabellen behandeln

Interne Tabellen:
- sqlite_sequence
- sqlite_stat1
- sqlite_stat4
- Tabellen mit sqlite_ Prefix

Entscheidung:
- Standardmäßig ausblenden.
- Optional als Hinweis zählen.

Akzeptanzkriterien:
- Export wird nicht durch interne SQLite-Tabellen zugemüllt.
- Verhalten ist getestet.


11.3.d – Spalten über PRAGMA table_info lesen

Für jede Tabelle:

PRAGMA table_info(table_name)

Erfassen:
- cid
- name
- type
- notnull
- dflt_value
- pk

Akzeptanzkriterien:
- Spaltennamen erscheinen.
- Datentypen erscheinen.
- PRIMARY KEY wird sichtbar.
- NOT NULL wird sichtbar.
- Default-Werte werden sichtbar, aber nicht übertrieben ausgewertet.


11.3.e – Foreign Keys über PRAGMA foreign_key_list lesen

Für jede Tabelle:

PRAGMA foreign_key_list(table_name)

Akzeptanzkriterien:
- Foreign Keys werden sichtbar.
- Referenzierte Tabelle und Spalten werden sichtbar.
- Keine Fehler bei Tabellen ohne Foreign Keys.


11.3.f – Indizes über PRAGMA index_list und index_info lesen

Für jede Tabelle:

PRAGMA index_list(table_name)
PRAGMA index_info(index_name)

Akzeptanzkriterien:
- Indizes werden sichtbar.
- Unique-Indizes werden markiert.
- Interne Auto-Indizes können optional ausgeblendet werden.


11.3.g – Kaputte SQLite-Dateien robust behandeln

Fehlerfälle:
- keine SQLite-Datei
- beschädigte DB
- verschlüsselte DB
- Permission Error
- sqlite3.DatabaseError

Akzeptanzkriterien:
- Kein Crash.
- Warning enthält Datei und Fehlertyp.
- Export läuft weiter.


11.3.h – SQLite Unit Tests schreiben

Testfälle:
- einfache Tabelle
- mehrere Tabellen
- Tabelle mit Primary Key
- Tabelle mit NOT NULL und DEFAULT
- Foreign Key
- Index
- View
- kaputte DB

Akzeptanzkriterien:
- Schema wird korrekt extrahiert.
- Keine DB-Inhalte erscheinen im Report.
- Fehlerfälle sind abgedeckt.

====================================================================
11.4 – CREATE TABLE Parsing aus SQL-Dateien
====================================================================

11.4.a – CREATE TABLE Statements finden

Ziel:
SQL-Dateien ohne SQLite DB lesen und CREATE TABLE Statements extrahieren.

Erkennen:
- CREATE TABLE users (...);
- CREATE TABLE IF NOT EXISTS users (...);
- CREATE TEMP TABLE temp_data (...);

Akzeptanzkriterien:
- Mehrere CREATE TABLE Statements pro Datei werden erkannt.
- Groß-/Kleinschreibung egal.
- Whitespace und Zeilenumbrüche robust.


11.4.b – Statement-Splitting robust machen

Ziel:
CREATE TABLE Blöcke bis zum passenden Semikolon erfassen.

Wichtig:
- Nicht an Semikolons in Strings scheitern, soweit einfach möglich.
- Klammern zählen.
- Kommentare möglichst ignorieren.

Akzeptanzkriterien:
- Normale Migrationsdateien funktionieren.
- Parser ist konservativ.
- Bei unklarem SQL lieber raw CREATE Statement erfassen statt falsch parsen.


11.4.c – Tabellennamen aus CREATE TABLE extrahieren

Erkennen:
- users
- public.users optional
- "users"
- [users]
- `users`
- IF NOT EXISTS users

Akzeptanzkriterien:
- Tabellenname wird stabil extrahiert.
- Bei unbekanntem Namen wird unknown + Warning verwendet.


11.4.d – Einfache Spalten aus CREATE TABLE parsen

Ziel:
Einfache Spaltenübersicht aus SQL-Dateien erzeugen.

Beispiele:
- id INTEGER PRIMARY KEY
- name TEXT NOT NULL
- email TEXT UNIQUE
- created_at TEXT DEFAULT CURRENT_TIMESTAMP

Akzeptanzkriterien:
- Spaltennamen werden erkannt.
- Datentyp wird best-effort erkannt.
- Table Constraints werden nicht als Spalten missverstanden.


11.4.e – Table Constraints konservativ behandeln

Erkennen oder überspringen:
- PRIMARY KEY (...)
- FOREIGN KEY (...) REFERENCES ...
- UNIQUE (...)
- CHECK (...)

Akzeptanzkriterien:
- Constraints crashen nicht.
- Constraints werden optional als raw_definition oder Warning erfasst.
- Keine falschen Spalten daraus erzeugen.


11.4.f – SQL Parser Grenzen dokumentieren

Nicht-Ziele:
- vollständiger SQL Parser
- Dialekt-spezifische Vollständigkeit
- Stored Procedures
- komplexe Migration Engines
- ORM Runtime-Auswertung

Akzeptanzkriterien:
- README oder Code-Kommentar erklärt best-effort Parser.
- Tests decken typische Fälle ab.


11.4.g – SQL Parsing Tests schreiben

Testfälle:
- CREATE TABLE users
- CREATE TABLE IF NOT EXISTS users
- mehrere Tabellen in einer Datei
- quoted identifiers
- table constraints
- comments
- kaputtes SQL

Akzeptanzkriterien:
- Parser liefert nützliche Ergebnisse.
- Fehler erzeugen Warning statt Crash.

====================================================================
11.5 – Database Schema Analyzer
====================================================================

11.5.a – analyze_database_schemas Funktion einführen

Öffentliche Funktion:

analyze_database_schemas(repo_root, files=None) -> DatabaseSchemaReport

Ablauf:
1. Kandidaten aus Git-tracked/scanned files bestimmen
2. SQLite-Dateien analysieren
3. SQL-Dateien analysieren
4. Report sortieren
5. Warnings sammeln

Akzeptanzkriterien:
- Zentrale API ist stabil.
- Exporter rufen nur diese Funktion auf.
- Keine doppelten Dateisuchen in Exportern.


11.5.b – Scanner-FileInfos unterstützen

files Parameter soll akzeptieren:
- Path
- str
- FileInfo mit path/relative_path
- vorhandene scanned_files aus FullExportContext

Akzeptanzkriterien:
- Bestehende Export-Pipeline kann direkt genutzt werden.
- Tests mit einfachen Paths und FileInfo-artigen Objekten.


11.5.c – Keine Datenbankinhalte lesen/exportieren

Ziel:
Nur Schema-Metadaten.

Nicht erlaubt im Report:
- SELECT * FROM table
- Row Counts aus echten Tabellen
- konkrete User-/App-Daten
- Beispielwerte aus Tabellen

Akzeptanzkriterien:
- Tests prüfen, dass eingefügte Testdaten nicht im Export erscheinen.
- Schema-Report enthält nur Struktur.


11.5.d – Analyzer Tests schreiben

Testfälle:
- Repo ohne DB
- Repo mit SQLite DB
- Repo mit SQL-Datei
- Repo mit SQLite DB und SQL-Datei
- kaputte DB plus gültige SQL-Datei
- generated exports ausgeschlossen

Akzeptanzkriterien:
- Report ist vollständig.
- Report ist stabil sortiert.
- Fehler verhindern keine Teilergebnisse.

====================================================================
11.6 – full.txt Export Integration
====================================================================

11.6.a – Database Schema Section in full.txt ergänzen

Neue Sektion:
# Database Schema

Empfohlene Position:
- nach Dependencies
- vor Complete Source Export

Begründung:
Schema ist Projektstruktur, aber kein Source Dump.

Akzeptanzkriterien:
- full.txt enthält Database Schema.
- Reihenfolge ist stabil.
- Bestehende Sections bleiben erhalten.


11.6.b – Summary rendern

Beispiel:

# Database Schema

## Summary

Database files: 1
SQL schema files: 2
Tables: 5
Views: 1
Warnings: 0

Akzeptanzkriterien:
- Leerer Zustand ist verständlich.
- Zahlen stimmen mit Report überein.


11.6.c – Database Files rendern

Beispiel:

## Database Files

- data/app.sqlite
- schema/schema.sql

Akzeptanzkriterien:
- Dateien sind repo-relativ.
- Sortierung stabil.


11.6.d – Table Summaries rendern

Beispiel:

## Tables

### users
Source: data/app.sqlite
Columns:
- id INTEGER PRIMARY KEY NOT NULL
- name TEXT NOT NULL
- email TEXT

Foreign keys:
- role_id -> roles.id

Indexes:
- users_email_idx UNIQUE (email)

Akzeptanzkriterien:
- Tabellen sind lesbar.
- Spalten sind kompakt.
- Foreign Keys und Indizes erscheinen, falls vorhanden.
- Keine Datenbankinhalte erscheinen.


11.6.e – CREATE SQL optional begrenzen

CREATE SQL kann lang sein.

Regel:
- entweder gar nicht ausgeben
- oder nur gekürzt / in kompakter Form
- oder nur bei SQL-Dateien raw statement zeigen

Empfehlung:
Im full.txt die CREATE Statements anzeigen, aber pro Statement begrenzen.

Akzeptanzkriterien:
- Export bleibt nicht unnötig riesig.
- Tests prüfen Begrenzung.


11.6.f – Warnings rendern

Beispiel:

## Schema Warnings

- data/broken.db: could not read SQLite schema: DatabaseError

Akzeptanzkriterien:
- Bei keinen Warnings: No schema warnings.
- Fehler sind verständlich.
- Keine Stacktraces im Export.


11.6.g – full.txt Regression Tests schreiben

Testfälle:
- full.txt enthält Database Schema Section
- SQLite Tabelle erscheint
- SQL CREATE TABLE erscheint
- Spalten erscheinen
- Datenbankinhalte erscheinen nicht
- kaputte DB erzeugt Warning
- Repo ohne DB erzeugt leeren Hinweis

Akzeptanzkriterien:
- Full Export bleibt grün.
- Keine Regression in bestehenden Full Export Tests.

====================================================================
11.7 – ai.txt Export Integration
====================================================================

11.7.a – Database Schema Summary in ai.txt ergänzen

Neue Sektion:
## Database Schema

Empfohlene Position:
- nach Dependencies
- vor Symbol Index oder nach Architecture Summary

Akzeptanzkriterien:
- ai.txt enthält kompakte Schema-Zusammenfassung.
- Keine vollständigen CREATE Dumps.
- Keine Datenbankinhalte.


11.7.b – Kompakte Tabellenübersicht rendern

Beispiel:

## Database Schema

Detected database/schema files:
- data/app.sqlite
- migrations/001_init.sql

Tables:
- users: id INTEGER PK, name TEXT, email TEXT
- roles: id INTEGER PK, name TEXT

Relationships:
- users.role_id -> roles.id

Akzeptanzkriterien:
- KI bekommt schnelle Orientierung.
- Ausgabe ist begrenzt.
- Große Schemas werden gekürzt.


11.7.c – AI Export Limits einführen

Begrenzungen:
- max Tabellen z. B. 30
- max Spalten pro Tabelle z. B. 20
- max Relationships z. B. 50
- danach Hinweis: ... N more

Akzeptanzkriterien:
- ai.txt bleibt kompakt.
- Tests prüfen Truncation.


11.7.d – ai.txt Regression Tests schreiben

Testfälle:
- ai.txt enthält Database Schema
- Tabelle erscheint
- Spalten erscheinen kompakt
- Relationship erscheint
- große Schemas werden begrenzt
- Repo ohne DB erzeugt sinnvollen Hinweis

Akzeptanzkriterien:
- AI Export bleibt stabil.
- Keine Source-Dump-Massen.

====================================================================
11.8 – CLI / Info Integration prüfen
====================================================================

11.8.a – repocontext info optional erweitern

Falls passend ergänzen:

Database schema:
  Database files: 1
  SQL schema files: 2
  Tables: 5
  Views: 1

Akzeptanzkriterien:
- Nur ergänzen, wenn es sauber zur bestehenden info-Ausgabe passt.
- Kein neuer CLI-Befehl nötig.


11.8.b – Keine neue CLI erzwingen

Nicht nötig:
- repocontext schema
- repocontext db

Milestone 11 bleibt Analyzer + Export Integration.

Akzeptanzkriterien:
- CLI bleibt einfach.
- Bestehende Kommandos bleiben kompatibel.


11.8.c – CLI Tests nur bei Info-Änderung

Wenn repocontext info erweitert wird:
- Test für Info-Ausgabe ergänzen
- Fehlerfälle abdecken

Akzeptanzkriterien:
- CLI Tests bleiben grün.

====================================================================
11.9 – Dokumentation aktualisieren
====================================================================

11.9.a – README Feature-Liste ergänzen

Ergänzen:
- Database schema extraction from SQLite databases and SQL schema files

Akzeptanzkriterien:
- README erwähnt Database Schema als umgesetzt.
- Planned-Liste widerspricht nicht.


11.9.b – Output full.txt aktualisieren

full.txt Sektionen dokumentieren:
- Database Schema

Akzeptanzkriterien:
- README passt zur tatsächlichen Section Order.


11.9.c – Output ai.txt aktualisieren

ai.txt Sektionen dokumentieren:
- Database Schema

Akzeptanzkriterien:
- README passt zur tatsächlichen AI-Ausgabe.


11.9.d – Grenzen dokumentieren

Dokumentieren:
- keine Datenbankdaten
- keine Migration-Ausführung
- keine ORM Runtime-Analyse
- SQL Parsing ist best-effort
- SQLite wird read-only analysiert
- kaputte DBs erzeugen Warnings

Akzeptanzkriterien:
- Nutzer versteht Sicherheitsgrenzen.
- Keine übertriebene Doku.


11.9.e – README Tests ergänzen

Bestehende README Regression Tests erweitern.

Testfälle:
- README erwähnt Database Schema Extraction
- README erwähnt keine Datenbankdaten werden exportiert
- README dokumentiert Database Schema Section

Akzeptanzkriterien:
- Dokumentation bleibt konsistent.

====================================================================
11.10 – Tests und Qualitätssicherung
====================================================================

11.10.a – Neue Testdatei tests/test_schema.py anlegen

Inhalt:
- Datenmodelltests
- Discovery Tests
- SQLite Extraction Tests
- SQL CREATE TABLE Parsing Tests
- Analyzer Tests

Akzeptanzkriterien:
- Tests sind semantisch sortiert.
- Keine Tests blind ans Dateiende anderer Dateien anhängen.


11.10.b – Export Tests semantisch passend ergänzen

Mögliche Dateien:
- tests/test_full_exporter.py
- tests/test_ai_exporter.py
- optional tests/test_full_exporter_schema.py
- optional tests/test_ai_exporter_schema.py

Akzeptanzkriterien:
- Exportintegration ist separat und gut lesbar.
- Bestehende Tests bleiben wartbar.


11.10.c – Safety Test: keine Datenbankdaten im Export

Test:
- SQLite DB mit Tabelle users
- Insert mit konkretem Wert, z. B. VerySecretUserName
- Export erzeugen
- Assert:
  - Tabelle users erscheint
  - Spalte name erscheint
  - VerySecretUserName erscheint nicht

Akzeptanzkriterien:
- Datenschutz-/Safety-Verhalten ist abgesichert.


11.10.d – Robustheitstest für kaputte DB

Test:
- Datei broken.sqlite mit Zufallsbytes
- Export erzeugen
- Assert:
  - kein Crash
  - Warning erscheint
  - restlicher Export wird geschrieben

Akzeptanzkriterien:
- RepoContext bleibt robust.


11.10.e – Vollständiger Testlauf

Befehl:
python3 -m pytest --color=yes

Akzeptanzkriterien:
- Alle bestehenden Tests grün.
- Neue Schema Tests grün.
- Keine Regression bei full.txt, ai.txt, docs.txt.


11.10.f – CLI Smoke Checks

Befehle:
repocontext --version
repocontext info
repocontext full
repocontext export-ai
repocontext export-docs

Akzeptanzkriterien:
- Alle relevanten Kommandos funktionieren.
- full.txt enthält Database Schema.
- ai.txt enthält Database Schema.
- docs.txt bleibt docs-only.

====================================================================
Empfohlene Implementierungsreihenfolge
====================================================================

Patch 11.1 – Schema Datenmodell und Discovery

Umfang:
- src/repocontext/schema.py anlegen
- SchemaColumn
- SchemaForeignKey
- SchemaIndex
- SchemaTable
- DatabaseSchemaReport
- SQLite/SQL Candidate Discovery
- Tests für Datenmodell und Discovery

Ziel:
Grundstruktur steht, aber noch keine echte SQLite-Extraktion.


Patch 11.2 – SQLite Schema Extraction

Umfang:
- read-only SQLite Analyse
- sqlite_schema lesen
- PRAGMA table_info
- PRAGMA foreign_key_list
- PRAGMA index_list / index_info
- Fehlerbehandlung
- SQLite Tests

Ziel:
Echte SQLite-Dateien liefern Tabellen, Spalten, FKs und Indizes.


Patch 11.3 – SQL CREATE TABLE Parser

Umfang:
- .sql Dateien analysieren
- CREATE TABLE Statements erkennen
- Tabellennamen extrahieren
- einfache Spalten parsen
- Constraints konservativ behandeln
- SQL Parser Tests

Ziel:
Schema aus SQL/Migrationsdateien wird best-effort erkannt.


Patch 11.4 – Analyzer zusammenführen

Umfang:
- analyze_database_schemas(repo_root, files=None)
- SQLite + SQL Ergebnisse zusammenführen
- Warnings sammeln
- Sortierung stabilisieren
- Analyzer Tests

Ziel:
Eine zentrale API liefert vollständigen DatabaseSchemaReport.


Patch 11.5 – full.txt Integration

Umfang:
- Database Schema Section in full.txt
- Summary
- Database Files
- Table Summaries
- Warnings
- Full Export Regression Tests

Ziel:
Schema ist im vollständigen Export sichtbar.


Patch 11.6 – ai.txt Integration

Umfang:
- kompakte Database Schema Section in ai.txt
- Tabellenübersicht
- Relationships
- Limits/Truncation
- AI Export Regression Tests

Ziel:
KI bekommt kompakte Datenbankstruktur ohne Source-/Daten-Müll.


Patch 11.7 – Dokumentation und Feinschliff

Umfang:
- README aktualisieren
- README Tests ergänzen
- optional repocontext info erweitern
- Gesamttests
- CLI Smoke Checks

Ziel:
Milestone 11 ist abschließbar.

====================================================================
Definition of Done für Milestone 11
====================================================================

Milestone 11 ist fertig, wenn:

1. Es gibt ein eigenes Schema-Analysemodul.
2. SQLite-Dateien werden erkannt.
3. SQLite-Dateien werden sicher/read-only analysiert.
4. Tabellen werden aus SQLite erkannt.
5. Views werden erkannt oder sauber behandelt.
6. Spalten werden aus SQLite erkannt.
7. Primary Keys werden sichtbar.
8. NOT NULL und Default-Werte werden sichtbar.
9. Foreign Keys werden sichtbar.
10. Indizes werden sichtbar, soweit einfach möglich.
11. SQL-Dateien werden erkannt.
12. CREATE TABLE Statements werden aus SQL-Dateien erkannt.
13. Tabellennamen werden aus CREATE TABLE extrahiert.
14. Einfache Spalten werden aus CREATE TABLE extrahiert.
15. Kaputte oder falsche DB-Dateien crashen nicht.
16. Fehler werden als Warnings ausgegeben.
17. Es werden keine Datenbankinhalte exportiert.
18. full.txt enthält eine Database Schema Section.
19. ai.txt enthält eine kompakte Database Schema Section.
20. docs.txt bleibt documentation-only und wird nicht mit DB-Schema vermischt.
21. Exportdateien full.txt/ai.txt/docs.txt/changed.txt werden nicht als Schema-Input verwendet.
22. Tests decken Discovery ab.
23. Tests decken SQLite Extraction ab.
24. Tests decken SQL CREATE TABLE Parsing ab.
25. Tests decken Exportintegration ab.
26. Tests prüfen, dass DB-Daten nicht im Export erscheinen.
27. README ist aktualisiert.
28. Die komplette Testsuite ist grün.
29. Es gibt einen Commit für die Umsetzung.

====================================================================
Nicht-Ziele für Milestone 11
====================================================================

Folgende Dinge gehören nicht zu Milestone 11:

- Migrationen ausführen
- Alembic/Django/SQLAlchemy Runtime-Auswertung
- ORM-Modelle vollständig interpretieren
- Datenbankdaten exportieren
- Row Counts aus Tabellen
- PostgreSQL/MySQL Live-Verbindungen
- Netzwerkzugriff
- vollständiger SQL Parser
- ER-Diagramme
- Graphviz-Ausgabe
- Schema-Diff zwischen Datenbanken
- Performance-Optimierung für riesige Datenbanken
- Secret Detection in DB-Inhalten

Diese Themen können spätere Milestones oder Erweiterungen werden.
