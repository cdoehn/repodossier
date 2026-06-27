# Milestone 2 – File Scanner

- [x] **2.1 Text/Binary Detection**
  - [x] 2.1.a `is_text_file()`

    Erkennt, ob eine Datei als UTF-8-Text gelesen werden kann. Diese Funktion bildet die Grundlage dafür, ob eine Datei überhaupt weiter analysiert werden soll oder nicht.

  - [x] 2.1.b `is_binary_file()`

    Erkennt Binärdateien anhand einfacher Heuristiken (z. B. Nullbytes). Binärdateien werden später nicht vollständig eingelesen oder analysiert.

  - [x] 2.1.c Unit Tests

    Erstellt eine vollständige Testsuite für die Text- und Binärerkennung. Alle typischen sowie fehlerhaften Eingaben sollen zuverlässig getestet werden.

  **Ziel:**
  - Dateien zuverlässig als Text oder Binärdatei erkennen.
  - UTF-8-basierte Textprüfung implementieren.
  - Grundlage für alle weiteren Scan-Schritte schaffen.

---

- [x] **2.2 Language Detection**
  - [x] 2.2.a `detect_language_from_extension()`

    Ermittelt die Programmiersprache oder den Dateityp anhand der Dateiendung. Unterstützt werden zunächst die wichtigsten Formate wie Python, Bash, Markdown, YAML oder JSON.

  - [x] 2.2.b `detect_language_from_filename()`

    Erkennt bekannte Dateien ohne Dateiendung wie `README`, `LICENSE`, `Dockerfile` oder `Makefile`. Dadurch können auch solche Dateien korrekt klassifiziert werden.

  - [x] 2.2.c Unit Tests

    Prüft die Spracherkennung für bekannte und unbekannte Dateinamen sowie verschiedene Schreibweisen und Groß-/Kleinschreibung.

  **Ziel:**
  - Programmiersprache bzw. Dateityp erkennen.
  - Dateiendungen und bekannte Dateinamen auswerten.
  - Sprache später für Parser und Statistiken verwenden.

---

- [x] **2.3 File Scanner**
  - [x] 2.3.a `scan_single_file()`

    Implementiert den zentralen Scanner für eine einzelne Datei. Er sammelt alle aktuell verfügbaren Informationen und erstellt daraus ein `FileInfo`-Objekt.

  - [x] 2.3.b `scan_multiple_files()`

    Führt den Dateiscanner für beliebig viele Dateien aus und liefert eine Liste aller erzeugten `FileInfo`-Objekte in der ursprünglichen Reihenfolge zurück.

  - [x] 2.3.c Unit Tests

    Testet sämtliche Scannerfunktionen einschließlich Fehlerfällen, Reihenfolge der Ergebnisse und korrekter Metadatenerfassung.

  **Ziel:**
  - Zentrale Scan-Funktion für einzelne Dateien erstellen.
  - Mehrere Dateien komfortabel in einem Aufruf scannen.
  - Alle Metadaten in `FileInfo` sammeln.

---

- [x] **2.4 File Metadata**
  - [x] 2.4.a File size detection

    Ermittelt die Dateigröße in Bytes und speichert sie im `FileInfo`-Objekt. Diese Information wird später unter anderem für Statistiken und Exportlimits benötigt.

  - [x] 2.4.b Language stored in `FileInfo`

    Übernimmt die erkannte Sprache dauerhaft in das `FileInfo`-Objekt, sodass spätere Verarbeitungsschritte sie nicht erneut bestimmen müssen.

  - [x] 2.4.c Binary/Text flags stored in `FileInfo`

    Speichert den Text-/Binärstatus ebenfalls im `FileInfo`-Objekt. Dadurch können nachfolgende Module Binärdateien direkt überspringen.

  **Ziel:**
  - Grundlegende Dateimetadaten speichern.
  - Größe, Sprache sowie Text/Binärstatus erfassen.
  - `FileInfo` als zentrale Datenstruktur erweitern.

---

- [x] **2.5 Line Statistics**
  - [x] 2.5.a Total line counting

    Zählt sämtliche Zeilen einer Textdatei. Diese Kennzahl wird später sowohl für Repository-Statistiken als auch für Exportübersichten verwendet.

  - [x] 2.5.b Empty line counting

    Ermittelt die Anzahl leerer oder ausschließlich aus Whitespace bestehender Zeilen. Dadurch lassen sich später aussagekräftigere Code-Statistiken erstellen.

  - [x] 2.5.c Store values in `FileInfo`

    Speichert sowohl die Gesamtzahl der Zeilen als auch die Anzahl leerer Zeilen dauerhaft im `FileInfo`-Objekt.

  **Ziel:**
  - Gesamtanzahl der Zeilen berechnen.
  - Leere bzw. Whitespace-Zeilen zählen.
  - Ergebnisse dauerhaft in `FileInfo` speichern.

---

- [x] **2.6 Comment Statistics**
  - [x] 2.6.a Count Python comments

    Zählt Kommentarzeilen in Python-Dateien. Es werden nur echte Kommentarzeilen berücksichtigt, nicht jedoch Inline-Kommentare hinter Programmcode.

  - [x] 2.6.b Count shell comments

    Zählt Kommentarzeilen in Bash-/Shell-Skripten. Shebang-Zeilen (`#!/bin/bash`) werden dabei ausdrücklich nicht als Kommentare gezählt.

  - [x] 2.6.c Store comment count in `FileInfo`

    Überträgt die berechnete Anzahl der Kommentarzeilen in das `FileInfo`-Objekt. Je nach erkannter Sprache wird automatisch der passende Kommentarzähler verwendet.

  **Ziel:**
  - Kommentarzeilen sprachabhängig zählen.
  - Zunächst Python und Bash unterstützen.
  - Kommentarstatistik in `FileInfo` speichern.

---

- [ ] **2.7 Token Estimation**
  - [ ] 2.7.a Simple token estimation

    Implementiert eine einfache Schätzung der Anzahl an KI-Tokens pro Datei. Eine exakte Tokenisierung ist zunächst nicht erforderlich; eine robuste Näherung genügt.

  - [x] 2.7.b Store estimated tokens in `FileInfo`

    Speichert die geschätzte Tokenanzahl im `FileInfo`-Objekt. Diese Information wird später verwendet, um Exportgrößen abzuschätzen und große Projekte sinnvoll aufzuteilen.

  - [ ] 2.7.c Unit Tests

    Prüft die Tokenabschätzung mit verschiedenen Dateigrößen und Inhalten, um reproduzierbare Ergebnisse sicherzustellen.

  **Ziel:**
  - Grobe Tokenanzahl für KI-Kontext abschätzen.
  - Werte pro Datei berechnen und speichern.
  - Grundlage für Kontextgrößen und Exportlimits schaffen.

---

- [ ] **2.8 Content Loading**
  - [ ] 2.8.a Load UTF-8 text content

    Liest den vollständigen Inhalt einer UTF-8-Textdatei ein. Binärdateien werden dabei weiterhin ignoriert.

  - [ ] 2.8.b Store content in `FileInfo`

    Speichert den eingelesenen Dateiinhalt direkt im `FileInfo`-Objekt, sodass spätere Exportmodule ihn unmittelbar verwenden können.

  - [ ] 2.8.c Unit Tests

    Testet das Einlesen unterschiedlich großer Textdateien sowie verschiedene Sonderfälle wie leere Dateien oder Unicode-Inhalte.

  **Ziel:**
  - Den vollständigen Inhalt von Textdateien laden.
  - Inhalt direkt in `FileInfo` verfügbar machen.
  - Vorbereitung für spätere Exporter und Analysen.

---

- [ ] **2.9 Repository Scanner**
  - [ ] 2.9.a Implement `RepositoryScanner.scan()`

    Implementiert die eigentliche Repository-Scan-Funktion, welche alle Git-Dateien durchläuft und den Dateiscanner für jede Datei aufruft.

  - [ ] 2.9.b Scan complete repository

    Führt den vollständigen Scan eines Git-Repositories durch und erzeugt eine vollständige Sammlung aller `FileInfo`-Objekte.

  - [ ] 2.9.c Unit Tests

    Testet den Repositoryscanner mit kleinen Test-Repositories und überprüft Vollständigkeit, Reihenfolge und Fehlerbehandlung.

  **Ziel:**
  - Den kompletten Repository-Scan implementieren.
  - Alle Git-Dateien automatisch scannen.
  - Liste aller `FileInfo`-Objekte erzeugen.
