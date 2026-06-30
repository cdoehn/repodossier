Milestone 5 – Symbol Extraction

Ziel:
RepoContext soll Python-Code statisch analysieren und daraus einen Symbol-Index erzeugen.
Der Symbol-Index soll Funktionen, Klassen und Methoden pro Datei erkennen und später für ai.txt,
Architektur-Zusammenfassungen, Import Graph und Call Graph wiederverwendbar sein.

Wichtig:
- Nur statische Analyse, kein Code ausführen.
- Primär Python-Support.
- Robust gegen Syntaxfehler, leere Dateien und ungewöhnliche Dateien.
- Ausgabe zunächst als interne Datenstruktur, noch kein eigener Export nötig.
- Bestehende Full-Export-Funktionalität darf nicht kaputtgehen.


5.1 – Grundstruktur für Symbol Extraction

5.1a – Neues Modul für Symbol Extraction anlegen
- Datei anlegen, z. B. src/repocontext/symbols.py
- Saubere interne API vorbereiten
- Keine CLI-Änderung in diesem Schritt
- Keine Export-Änderung in diesem Schritt
- Ziel: Symbol-Logik getrennt vom Full Export halten

5.1b – Datenmodell für Symbole definieren
- Symbol-Datenstruktur erstellen, z. B. Dataclass SymbolInfo
- Felder:
  - name
  - kind
  - file_path
  - line_start
  - line_end optional
  - parent optional
- kind soll mindestens unterstützen:
  - function
  - class
  - method
- Ziel: Einheitliche Struktur für alle gefundenen Symbole

5.1c – Datenmodell für Datei-Symbolindex definieren
- Struktur erstellen, z. B. FileSymbolIndex
- Felder:
  - file_path
  - symbols
  - errors optional
- Ziel: Eine Datei kann erfolgreich analysiert werden oder Fehler sauber speichern

5.1d – Öffentliche Analysefunktion vorbereiten
- Funktion erstellen, z. B. extract_symbols_from_file(path)
- Datei lesen
- Python-AST parsen
- Noch keine vollständige Symbolsuche nötig
- Fehler sauber abfangen
- Ziel: stabile Einstiegsmethode


5.2 – Function Discovery

5.2a – Top-Level-Funktionen erkennen
- ast.FunctionDef erkennen
- Funktionsname speichern
- Startzeile speichern
- Datei speichern
- kind = function
- Nur echte Top-Level-Funktionen, keine Methoden innerhalb von Klassen

5.2b – Async-Funktionen erkennen
- ast.AsyncFunctionDef zusätzlich unterstützen
- Gleich behandeln wie normale Funktionen
- kind = function
- Ziel: async def darf nicht fehlen

5.2c – Verschachtelte Funktionen bewusst behandeln
- Entscheidung implementieren:
  - entweder zunächst ignorieren
  - oder mit parent speichern
- Empfehlung für MVP:
  - verschachtelte Funktionen ignorieren
- Ziel: Symbolindex bleibt einfach und stabil

5.2d – Tests für Function Discovery ergänzen
- Datei mit einfacher Funktion testen
- Datei mit mehreren Funktionen testen
- Datei mit async Funktion testen
- Sicherstellen, dass Funktionen innerhalb von Klassen nicht als Top-Level-Funktion gezählt werden


5.3 – Class Discovery

5.3a – Klassen erkennen
- ast.ClassDef erkennen
- Klassenname speichern
- Startzeile speichern
- Datei speichern
- kind = class
- Ziel: alle Top-Level-Klassen in Python-Dateien finden

5.3b – Klassen mit Vererbung robust verarbeiten
- Klassen unabhängig von Basisklassen erkennen
- Keine komplexe Auswertung der Basisklassen nötig
- Kein Import- oder Name-Resolving
- Ziel: class Foo(Bar) darf problemlos analysiert werden

5.3c – Verschachtelte Klassen bewusst behandeln
- Empfehlung für MVP:
  - verschachtelte Klassen zunächst ignorieren
- Alternativ nur mit parent erfassen, falls einfach möglich
- Ziel: keine unnötige Komplexität

5.3d – Tests für Class Discovery ergänzen
- Einfache Klasse testen
- Mehrere Klassen testen
- Klasse mit Basisklasse testen
- Klasse mit Methoden testen


5.4 – Method Discovery

5.4a – Methoden innerhalb von Klassen erkennen
- Innerhalb von ast.ClassDef nach FunctionDef suchen
- Methodenname speichern
- kind = method
- parent = Klassenname
- Startzeile speichern
- Datei speichern

5.4b – Async-Methoden erkennen
- ast.AsyncFunctionDef innerhalb von Klassen unterstützen
- kind = method
- parent = Klassenname
- Ziel: async def innerhalb class korrekt erfassen

5.4c – Spezialmethoden nicht herausfiltern
- __init__, __str__, __repr__ usw. normal erfassen
- Keine Sonderlogik
- Ziel: vollständiger und erwartbarer Symbolindex

5.4d – Tests für Method Discovery ergänzen
- Klasse mit einer Methode
- Klasse mit mehreren Methoden
- Klasse mit __init__
- Klasse mit async Methode
- Sicherstellen, dass Methoden parent korrekt gesetzt haben


5.5 – Symbol Index über mehrere Dateien

5.5a – Repository-weite Symbol-Analyse vorbereiten
- Funktion erstellen, z. B. build_symbol_index(files)
- Liste von Dateien entgegennehmen
- Nur Python-Dateien analysieren
- Nicht-Python-Dateien überspringen

5.5b – Integration mit bestehendem File Scanner vorbereiten
- Vorhandene Dateiliste aus Full Export / Scanner wiederverwenden
- Keine doppelte Dateisuche implementieren, wenn vermeidbar
- Ziel: Symbol Extraction nutzt bestehende RepoContext-Struktur

5.5c – Aggregierten Symbolindex erzeugen
- Ausgabe z. B. als Liste von FileSymbolIndex
- Oder als RepositorySymbolIndex
- Enthalten:
  - analysierte Dateien
  - gefundene Symbole
  - Analysefehler
- Ziel: spätere Exporte können direkt darauf zugreifen

5.5d – Fehlerhafte Dateien sauber behandeln
- SyntaxError abfangen
- UnicodeDecodeError abfangen
- OSError abfangen
- Fehler im Index speichern
- Verarbeitung der restlichen Dateien fortsetzen
- Ziel: eine kaputte Datei darf den Export nicht abbrechen


5.6 – Symbolsortierung und Stabilität

5.6a – Symbole stabil sortieren
- Sortierung nach:
  - file_path
  - line_start
  - kind
  - name
- Ziel: deterministische Ausgabe für Tests und Git-Diffs

5.6b – Pfade konsistent darstellen
- Relative Repo-Pfade verwenden
- Keine absoluten lokalen Pfade im Index
- Ziel: portable Ausgabe

5.6c – Doppelte Symbole nicht künstlich deduplizieren
- Gleiche Namen in verschiedenen Dateien erlauben
- Gleiche Methodennamen in verschiedenen Klassen erlauben
- Ziel: realistische Codebasis korrekt abbilden

5.6d – Tests für stabile Reihenfolge ergänzen
- Mehrere Dateien testen
- Mehrere Symbole pro Datei testen
- Erwartete Reihenfolge prüfen


5.7 – Symbolformatierung für spätere Exporte

5.7a – Kleine Formatierungsfunktion erstellen
- Funktion z. B. format_symbol_index(symbol_index)
- Noch nicht zwingend in full.txt einbauen
- Ausgabe menschenlesbar vorbereiten
- Ziel: spätere Nutzung in ai.txt erleichtern

5.7b – Ausgabeformat definieren
- Beispiel:
  src/foo.py
    class AppConfig:12
    method AppConfig.load:18
    function main:42
- Methoden mit Klassen-Prefix darstellen
- Ziel: leicht lesbare Symbolübersicht

5.7c – Leere Symbol-Dateien sinnvoll behandeln
- Dateien ohne Symbole entweder ausblenden oder als leer darstellen
- Empfehlung:
  - im internen Index behalten
  - in formatierter Ausgabe ausblenden
- Ziel: keine unnötig lange Ausgabe

5.7d – Tests für Formatierung ergänzen
- Funktionen formatieren
- Klassen formatieren
- Methoden formatieren
- Parent-Anzeige prüfen


5.8 – CLI- oder Export-Integration vorbereiten

5.8a – Noch keine Pflicht-Integration in full.txt
- Milestone 5 soll primär Symbol Extraction liefern
- Full Export darf unverändert bleiben
- Ziel: Risiko klein halten

5.8b – Optional Debug-Ausgabe vorbereiten
- Falls sinnvoll: interne Funktion für spätere CLI
- Noch kein neuer offizieller CLI-Befehl nötig
- Ziel: Milestone 8 kann Symbol Index in ai.txt verwenden

5.8c – Sicherstellen, dass bestehende CLI unverändert funktioniert
- repocontext full läuft weiter
- repocontext info läuft weiter
- Bestehende Tests bleiben grün

5.8d – Keine neuen Exportdateien erzeugen
- Kein symbols.txt in diesem Milestone
- Kein ai.txt in diesem Milestone
- Ziel: Scope sauber halten


5.9 – Tests und Qualitätssicherung

5.9a – Unit-Tests für symbols.py anlegen
- Neue Testdatei z. B. tests/test_symbols.py
- Kleine temporäre Python-Dateien verwenden
- Keine großen Fixture-Dateien nötig

5.9b – Fehlerfälle testen
- Datei mit SyntaxError
- Datei mit ungültigem Encoding, falls einfach testbar
- Nicht vorhandene Datei
- Leere Datei
- Nicht-Python-Datei

5.9c – Integrationstest mit mehreren Dateien
- Mini-Repo-Struktur im tmp_path erzeugen
- Mehrere Python-Dateien
- Eine fehlerhafte Python-Datei
- Eine Nicht-Python-Datei
- Erwartung:
  - gültige Symbole werden gefunden
  - Fehler werden protokolliert
  - Verarbeitung läuft weiter

5.9d – Regressionstest für bestehende Exporte
- Bestehende Full-Export-Tests laufen lassen
- Sicherstellen, dass Milestone 5 keine Ausgabe kaputtmacht


5.10 – Abschlusskriterien für Milestone 5

5.10a – Function Discovery abgeschlossen
- Top-Level-Funktionen werden erkannt
- Async-Funktionen werden erkannt
- Tests vorhanden

5.10b – Class Discovery abgeschlossen
- Klassen werden erkannt
- Klassen mit Basisklassen funktionieren
- Tests vorhanden

5.10c – Method Discovery abgeschlossen
- Methoden werden erkannt
- Async-Methoden werden erkannt
- Parent-Klasse wird gespeichert
- Tests vorhanden

5.10d – Symbol Index abgeschlossen
- Mehrere Dateien können analysiert werden
- Python-Dateien werden berücksichtigt
- Nicht-Python-Dateien werden übersprungen
- Fehlerhafte Dateien brechen die Analyse nicht ab

5.10e – Qualität abgeschlossen
- Tests grün
- Bestehende Exporte unverändert funktionsfähig
- Code sauber getrennt
- Keine unnötigen neuen CLI-Features
- Keine neuen Exportdateien außerhalb des Milestone-Scopes
