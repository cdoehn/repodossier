# Milestone 4 – `.gitignore` Integration

Ziel: RepoContext soll automatisch sicherstellen, dass die eigenen Exportdateien in `.gitignore` stehen.

Exportdateien:

- `full.txt`
- `ai.txt`
- `docs.txt`
- `changed.txt`

Wichtig: Es geht nicht darum, dass `.gitignore` im aktuellen Projekt zufällig schon passt, sondern dass RepoContext diese Einträge automatisch, reproduzierbar und idempotent verwaltet.


## 4.1 – Grundmodell und Konstanten

### 4.1.a `REPOCONTEXT_EXPORT_FILES` definieren

Neues Modul anlegen:

`src/repocontext/gitignore.py`

Darin zentrale Konstante definieren:

    REPOCONTEXT_EXPORT_FILES = (
        "full.txt",
        "ai.txt",
        "docs.txt",
        "changed.txt",
    )

Ziel:
- Die Export-Dateinamen stehen nur an einer Stelle.
- Spätere Exporter für `ai.txt`, `docs.txt` und `changed.txt` können dieselbe Konstante verwenden.


### 4.1.b RepoContext-Block-Header definieren

Im selben Modul definieren:

    REPOCONTEXT_GITIGNORE_HEADER = "# RepoContext exports"

Ziel:
- RepoContext schreibt seine eigenen `.gitignore`-Einträge sauber gruppiert.
- Bestehende `.gitignore`-Inhalte bleiben verständlich.


### 4.1.c Öffentliche Ensure-Funktion vorbereiten

Funktion anlegen:

    def ensure_repocontext_gitignore_entries(repository_root: Path | str) -> bool:

Rückgabe:
- `True`, wenn `.gitignore` erstellt oder geändert wurde.
- `False`, wenn bereits alle Einträge vorhanden waren.

Ziel:
- Die Funktion ist später einfach aus Exportern oder CLI aufrufbar.
- Tests können sauber prüfen, ob eine Änderung passiert ist.


---

## 4.2 – `.gitignore` lesen und Zustand erkennen

### 4.2.a `.gitignore`-Pfad aus Repository Root ermitteln

Immer aus dem Repository Root arbeiten:

    gitignore_path = repository_root / ".gitignore"

Nicht aus `Path.cwd()`.

Ziel:
- Funktioniert auch, wenn `repocontext` aus einem Unterordner gestartet wird.


### 4.2.b Fehlende `.gitignore` unterstützen

Wenn `.gitignore` nicht existiert:
- neue Datei erzeugen
- RepoContext-Block mit allen vier Exportdateien schreiben

Ziel:
- RepoContext funktioniert auch in sehr kleinen oder neuen Repositories.


### 4.2.c Bestehende `.gitignore` mit UTF-8 lesen

Bestehende Datei mit UTF-8 lesen.

Bei Fehlern:
- `OSError` nicht verschlucken
- Fehler später im CLI verständlich melden

Ziel:
- Keine stillen oder halb kaputten Änderungen.


### 4.2.d Vorhandene Einträge in der gesamten Datei erkennen

Prüfen, ob diese Einträge irgendwo bereits vorhanden sind:

    full.txt
    ai.txt
    docs.txt
    changed.txt

Wichtig:
- Nicht nur im RepoContext-Block suchen.
- Auch Einträge außerhalb des Blocks gelten als vorhanden.

Ziel:
- Keine doppelten `.gitignore`-Einträge erzeugen.


---

## 4.3 – Fehlende Einträge bestimmen

### 4.3.a Missing Entries berechnen

Beispiel:

Vorhanden:

    full.txt
    ai.txt

Fehlend:

    docs.txt
    changed.txt

Ziel:
- Nur fehlende Einträge ergänzen.
- Bestehende Einträge nicht duplizieren.


### 4.3.b Idempotenz sicherstellen

Wenn alle vier Einträge bereits vorhanden sind:

- Datei nicht anfassen
- keine neue Leerzeile anhängen
- keinen neuen Header erzeugen
- Rückgabe `False`

Ziel:
- Mehrfaches Ausführen von `repocontext` darf `.gitignore` nicht ständig verändern.


### 4.3.c Reihenfolge stabil halten

Neue Einträge immer in dieser Reihenfolge schreiben:

    full.txt
    ai.txt
    docs.txt
    changed.txt

Ziel:
- Reproduzierbare Diffs.
- Klare Ordnung im RepoContext-Block.


---

## 4.4 – `.gitignore` robust aktualisieren

### 4.4.a Wenn `.gitignore` fehlt oder leer ist

Ergebnis:

    # RepoContext exports
    full.txt
    ai.txt
    docs.txt
    changed.txt

Mit abschließender Newline.

Ziel:
- Saubere Minimaldatei erzeugen.


### 4.4.b Wenn `.gitignore` existiert, aber kein RepoContext-Block vorhanden ist

Am Ende anhängen:

    # RepoContext exports
    full.txt
    ai.txt
    docs.txt
    changed.txt

Dabei nur fehlende Einträge aufnehmen.

Beispiel vorher:

    .venv/
    __pycache__/

Beispiel nachher:

    .venv/
    __pycache__/

    # RepoContext exports
    full.txt
    ai.txt
    docs.txt
    changed.txt

Ziel:
- Bestehende `.gitignore`-Inhalte bleiben erhalten.
- RepoContext ergänzt nur seinen eigenen Block.


### 4.4.c Wenn RepoContext-Block bereits vorhanden ist

Fehlende Einträge direkt im bestehenden Block ergänzen.

Beispiel vorher:

    # RepoContext exports
    full.txt

Beispiel nachher:

    # RepoContext exports
    full.txt
    ai.txt
    docs.txt
    changed.txt

Ziel:
- Kein zweiter RepoContext-Block.
- Bestehender Block wird sauber vervollständigt.


### 4.4.d Finale Newline normalisieren

Nach einer Änderung soll `.gitignore` mit einer abschließenden Newline enden.

Ziel:
- Saubere Git-Diffs.
- Keine unnötigen Whitespace-Änderungen.


---

## 4.5 – Integration in Full Export

### 4.5.a Vor oder während `full.txt`-Generierung ausführen

In `generate_full_export()` oder direkt davor:

    ensure_repocontext_gitignore_entries(repository_root)

Ziel:
- `full.txt` wird automatisch ignoriert, sobald RepoContext läuft.
- Spätere Exportdateien sind ebenfalls schon abgedeckt.


### 4.5.b Repository Root verwenden

Die Integration muss den bereits gefundenen Repository Root verwenden.

Nicht:

    Path.cwd()

Sondern:

    repository_root

Ziel:
- Korrektes Verhalten bei Aufruf aus Unterordnern.


### 4.5.c Exportlogik und `.gitignore`-Logik getrennt halten

`.gitignore`-Management bleibt in:

    src/repocontext/gitignore.py

`exporters/full.py` ruft nur die Hilfsfunktion auf.

Ziel:
- Saubere Architektur.
- Spätere Exporter können dieselbe Funktion verwenden.


---

## 4.6 – CLI-Verhalten

### 4.6.a Minimaler Output bleibt erhalten

Normaler Erfolg bleibt z. B.:

    Wrote /path/to/repo/full.txt

Kein zusätzlicher Output nötig.

Ziel:
- CLI bleibt ruhig.
- Skriptfreundliches Verhalten.


### 4.6.b Schreibfehler verständlich melden

Wenn `.gitignore` nicht geschrieben werden kann, soll die CLI verständlich abbrechen.

Beispiel:

    Error: Could not update .gitignore: ...

Ziel:
- User erkennt, ob `.gitignore` oder `full.txt` das Problem ist.


### 4.6.c Exit-Code bei Fehler

Wenn `.gitignore` nicht aktualisiert werden kann:

- Export abbrechen
- CLI gibt `1` zurück

Ziel:
- Keine halbkorrekte Ausführung.
- Automatisierte Tests und Skripte erkennen Fehler.


---

## 4.7 – Unit Tests für `.gitignore`-Modul

Neue Testdatei:

    tests/test_gitignore.py


### 4.7.a Test: fehlende `.gitignore` wird erstellt

Setup:
- temporäres Repository-Verzeichnis ohne `.gitignore`

Ausführen:

    ensure_repocontext_gitignore_entries(repo_path)

Assert:
- Rückgabe ist `True`
- `.gitignore` existiert
- Datei enthält:

    # RepoContext exports
    full.txt
    ai.txt
    docs.txt
    changed.txt


### 4.7.b Test: vorhandene `.gitignore` wird erhalten

Vorher:

    .venv/
    __pycache__/

Nachher:
- `.venv/` ist noch vorhanden
- `__pycache__/` ist noch vorhanden
- RepoContext-Block wurde ergänzt

Ziel:
- Bestehende Ignore-Regeln dürfen nicht verloren gehen.


### 4.7.c Test: keine Duplikate

Vorher:

    full.txt

Nachher:
- `full.txt` kommt nur einmal vor
- fehlende Einträge werden ergänzt

Ziel:
- Einträge werden global erkannt, nicht doppelt geschrieben.


### 4.7.d Test: teilweise vorhandener RepoContext-Block wird ergänzt

Vorher:

    # RepoContext exports
    full.txt

Nachher:

    # RepoContext exports
    full.txt
    ai.txt
    docs.txt
    changed.txt

Ziel:
- Bestehender RepoContext-Block wird vervollständigt.


### 4.7.e Test: Idempotenz

Funktion zweimal ausführen.

Assert:
- erster Lauf gibt `True` zurück
- zweiter Lauf gibt `False` zurück
- Dateiinhalt bleibt beim zweiten Lauf exakt gleich

Ziel:
- Wiederholtes Ausführen erzeugt keine neuen Diffs.


### 4.7.f Test: Reihenfolge stabil

Nach Ergänzung müssen die Einträge in dieser Reihenfolge stehen:

    full.txt
    ai.txt
    docs.txt
    changed.txt

Ziel:
- Reproduzierbare Ausgabe.


---

## 4.8 – Integrationstests CLI / Full Export

Wahrscheinlich in:

    tests/test_cli.py


### 4.8.a Default CLI erstellt `.gitignore`, wenn sie fehlt

Setup:
- Git-Testrepo ohne `.gitignore`

Aufruf:

    main([])

Assert:
- `full.txt` existiert
- `.gitignore` existiert
- `.gitignore` enthält alle vier Exportdateien


### 4.8.b Default CLI ergänzt vorhandene `.gitignore`

Setup:
- Git-Testrepo mit vorhandener `.gitignore`

Vorher:

    .venv/

Aufruf:

    main([])

Assert:
- `.venv/` bleibt erhalten
- RepoContext-Einträge werden ergänzt


### 4.8.c CLI aus Unterordner schreibt `.gitignore` in Repository Root

Setup:
- Git-Testrepo
- Unterordner `nested/dir`
- `monkeypatch.chdir(nested_dir)`

Aufruf:

    main([])

Assert:
- `<repo-root>/.gitignore` wurde geändert
- keine `.gitignore` im Unterordner


### 4.8.d `full.txt` erscheint nach erstem Lauf nicht als untracked

Setup:
- Git-Testrepo ohne `.gitignore`
- `main([])` ausführen
- danach `git status --short` prüfen

Assert:
- `full.txt` erscheint nicht als untracked

Ziel:
- Das eigentliche Milestone-4-Problem wird getestet.


---

## 4.9 – Export-Selbstaufnahme verhindern

### 4.9.a Verhalten bei bereits getracktem `full.txt` prüfen

Wichtig:
- `.gitignore` entfernt keine bereits getrackten Dateien aus Git.
- Wenn `full.txt` bereits getrackt ist, bleibt es getrackt.

Entscheidung:
- In Milestone 4 nicht automatisch `git rm --cached full.txt` ausführen.

Ziel:
- Keine überraschenden Git-Änderungen durch RepoContext.


### 4.9.b Optional spätere Warnung vorbereiten

Später möglich:

    RepoContext export file is Git-tracked: full.txt

Aber für Milestone 4 nicht zwingend.

Ziel:
- Milestone 4 bleibt fokussiert auf `.gitignore` Auto-Add.


---

# Empfohlene Implementierungsreihenfolge

## Teilpatch 1: 4.1 bis 4.4

Implementieren:
- neues Modul `src/repocontext/gitignore.py`
- Konstanten
- Ensure-Funktion
- Lesen, Erkennen, Ergänzen, Schreiben
- Unit Tests in `tests/test_gitignore.py`

Ziel:
- `.gitignore`-Logik ist isoliert fertig und getestet.


## Teilpatch 2: 4.5 bis 4.6

Implementieren:
- Integration in Full Export
- CLI-Fehlerbehandlung für `.gitignore`

Ziel:
- `repocontext` aktualisiert `.gitignore` automatisch beim Export.


## Teilpatch 3: 4.8

Implementieren:
- CLI-/Integrationstests

Ziel:
- Nachweis, dass Default CLI `.gitignore` korrekt erstellt oder ergänzt.


## Teilpatch 4: 4.9 optional

Nur umsetzen, wenn danach ein echtes Problem sichtbar wird.

Ziel:
- Optionaler Schutz oder Warnung bei bereits getrackten Exportdateien.


# Vorschlag für den nächsten konkreten Schritt

Als nächstes sinnvoll:

    mache 4.1 bis 4.4
