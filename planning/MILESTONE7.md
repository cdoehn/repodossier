Milestone 7 – Call Graph

Ziel:
RepoContext soll statisch erkennen, welche Funktionen/Methoden andere Funktionen/Methoden aufrufen, und daraus einen Call Graph erzeugen, der später in full.txt und ai.txt genutzt werden kann.

Empfohlene Reihenfolge:

7.1 – Call-Graph-Grundmodell

7.1.a – Datenmodell für Call-Graph-Kanten einführen
- Neue Struktur für CallEdge oder ähnliches.
- Felder:
  - caller_file
  - caller_name
  - caller_qualified_name
  - callee_name
  - callee_qualified_name, falls auflösbar
  - line_number
  - call_type, z. B. function, method, attribute, unknown
  - confidence, z. B. local, imported, unresolved
- Ziel: Der Call Graph ist nicht nur Text, sondern intern sauber modelliert.

7.1.b – Container für CallGraph einführen
- Struktur für:
  - edges: Liste aller Aufrufkanten
  - callers_by_symbol
  - callees_by_symbol
- Optional:
  - helper methods wie get_calls_from(symbol) und get_callers_of(symbol)
- Ziel: Spätere Exporter müssen nicht selbst filtern oder gruppieren.

7.1.c – Serialisierbare Ausgabeform vorbereiten
- CallGraph soll leicht in Text umwandelbar sein.
- Sortierung deterministisch:
  - nach Datei
  - nach Caller
  - nach Zeile
  - nach Callee
- Wichtig für stabile Tests.

7.2 – AST-basierte Funktionsaufrufe erkennen

7.2.a – PythonCallVisitor-Grundgerüst bauen
- Neuer AST-Visitor für Python-Dateien.
- Erkennt aktuelle Kontextposition:
  - Modul-Level
  - Funktion
  - Methode
  - Klasse
- Ziel: Bei jedem ast.Call wissen, wer der Caller ist.

7.2.b – Direkte Funktionsaufrufe erkennen
- Beispiele:
  - foo()
  - parse_config()
  - main()
- ast.Call mit ast.Name auswerten.
- Kante erzeugen:
  - caller -> foo
- Noch ohne perfekte Auflösung auf konkrete Definitionen.

7.2.c – Verschachtelte Calls erkennen
- Beispiele:
  - foo(bar())
  - return transform(load_data())
  - x = validate(parse(raw))
- Alle ast.Call-Knoten müssen erkannt werden.
- Ziel: Keine Calls verlieren, nur weil sie in Expressions stecken.

7.2.d – Calls auf Modulebene behandeln
- Beispiel:
  - main()
  - cli()
  - setup_logging()
- caller_name könnte dann z. B. "<module>" oder "module:<path>" sein.
- Ziel: Entry-Point-Verhalten sichtbar machen.

7.3 – Methoden- und Attributaufrufe erkennen

7.3.a – Einfache Methodenaufrufe erkennen
- Beispiele:
  - obj.save()
  - scanner.scan()
  - result.to_dict()
- ast.Call mit ast.Attribute auswerten.
- Callee mindestens als "save", "scan", "to_dict" speichern.
- Voller Ausdruck optional als "obj.save" speichern.

7.3.b – Self-Methoden genauer auflösen
- Beispiele:
  - self.scan_file()
  - self._estimate_tokens()
- Innerhalb einer Klasse kann self.method oft auf ClassName.method aufgelöst werden.
- Ziel:
  - caller: Scanner.scan
  - callee: Scanner.scan_file
- Das ist für Repo-interne Call Graphs besonders wertvoll.

7.3.c – Classmethod/staticmethod-Aufrufe innerhalb derselben Klasse erkennen
- Beispiele:
  - cls.from_path()
  - ClassName.from_path()
- Wenn ClassName im aktuellen File definiert ist, auf qualifizierten Methodennamen mappen.
- Ziel: bessere Auflösung für Factory- und Helper-Methoden.

7.3.d – Chained Calls robust, aber konservativ behandeln
- Beispiele:
  - path.read_text().splitlines()
  - scanner.scan().to_export()
- Mindestens letzte Methode erkennen.
- Nicht zu aggressiv auflösen, wenn Typ unbekannt ist.
- Confidence z. B. "unresolved_method".

7.4 – Lokale Symbolauflösung

7.4.a – Verbindung zum Symbol Index herstellen
- Bestehenden Symbol Index aus Milestone 5 verwenden.
- Alle bekannten Funktionen/Klassen/Methoden je Datei verfügbar machen.
- Ziel: Calls wie parse_config() können auf definierte Symbole gemappt werden.

7.4.b – Lokale Funktionen im selben File auflösen
- Beispiel:
  - def helper(): ...
  - def main(): helper()
- helper() soll auf current_file::helper gemappt werden.
- Confidence: local.

7.4.c – Methoden derselben Klasse auflösen
- Beispiel:
  - class Exporter:
      def export(self):
          self.render()
      def render(self):
          ...
- self.render() soll auf Exporter.render zeigen.
- Confidence: local_method.

7.4.d – Ambiguitäten bewusst markieren
- Wenn mehrere Symbole denselben Namen haben:
  - keine falsche harte Auflösung
  - stattdessen callee_name behalten
  - confidence: ambiguous oder unresolved
- Ziel: lieber ehrlich unvollständig als falsch.

7.5 – Import-basierte Auflösung vorbereiten

7.5.a – Import-Aliase aus AST erfassen
- Beispiele:
  - import pathlib as pl
  - from repo_context.scanner import scan_file
- Mapping speichern:
  - scan_file -> repo_context.scanner.scan_file
  - pl -> pathlib
- Ziel: Grundlage für bessere Auflösung über Dateien hinweg.

7.5.b – Verbindung zum Import Graph aus Milestone 6 nutzen
- Import Graph kann helfen, Modulnamen auf Dateien im Repo zu mappen.
- Beispiel:
  - from repocontext.scanner import scan_file
  - scan_file()
- Ziel: Call Graph und Import Graph arbeiten zusammen.

7.5.c – Importierte repo-interne Funktionen auflösen
- Wenn importiertes Symbol im Symbol Index existiert:
  - callee_qualified_name setzen
  - confidence: imported_local
- Externe Bibliotheken bleiben unresolved/external.

7.5.d – Externe Calls markieren
- Beispiele:
  - pathlib.Path()
  - argparse.ArgumentParser()
  - subprocess.run()
- Nicht als Fehler behandeln.
- call_type oder confidence entsprechend setzen:
  - external
  - stdlib_or_third_party
  - unresolved_external

7.6 – Export in full.txt integrieren

7.6.a – Call Graph Section im Full Export ergänzen
- Neue Sektion z. B.:
  - CALL GRAPH
  - STATIC CALL GRAPH
- Sie sollte nach Symbol Index oder nach Import Graph erscheinen.
- Sinnvoll wäre:
  - Symbol Index
  - Import Graph
  - Call Graph

7.6.b – Lesbare Gruppierung nach Caller
- Beispielausgabe:
  - repocontext/cli.py::main
    - calls parse_args at line 42
    - calls run_export at line 55
- Ziel: Für KI schnell verständlich.

7.6.c – Unresolved Calls optional begrenzen
- Nicht jeden Standardbibliotheksaufruf endlos ausgeben.
- Entweder:
  - nur repo-interne Calls prominent zeigen
  - unresolved/external Calls separat kurz zusammenfassen
- Ziel: full.txt bleibt nützlich und nicht zugemüllt.

7.6.d – Deterministische Ausgabe testen
- Gleicher Input muss gleiche Call-Graph-Ausgabe erzeugen.
- Wichtig für Snapshot-/String-Tests.

7.7 – CLI-/Pipeline-Integration

7.7.a – Scanner-/Analyzer-Pipeline erweitern
- Call Graph muss im normalen Exportlauf erzeugt werden.
- Kein separater manueller Schritt.
- Ziel:
  - repocontext full
  - repocontext export
  erzeugen automatisch Call-Graph-Daten.

7.7.b – Fehlerrobustheit sicherstellen
- Syntaxfehlerhafte Python-Dateien dürfen Export nicht abbrechen.
- Verhalten:
  - Datei überspringen
  - optional Warnung sammeln
- Bestehende Robustheit aus Scanner/Symbol Extraction übernehmen.

7.7.c – Performance beachten
- AST Parsing nicht unnötig mehrfach machen, falls schon Symbol Extraction AST nutzt.
- Wenn aktuell getrennt: erst sauber, später optimieren.
- Ziel: Milestone 7 korrekt, nicht überoptimiert.

7.8 – Tests

7.8.a – Unit-Test für direkte Funktionsaufrufe
- Input-Datei:
  - helper()
  - main() ruft helper()
- Erwartung:
  - main -> helper

7.8.b – Unit-Test für verschachtelte Calls
- Input:
  - return transform(load_data())
- Erwartung:
  - caller -> transform
  - caller -> load_data

7.8.c – Unit-Test für self.method()
- Input:
  - class Scanner:
      def scan(self):
          self.scan_file()
      def scan_file(self):
          pass
- Erwartung:
  - Scanner.scan -> Scanner.scan_file

7.8.d – Unit-Test für obj.method()
- Input:
  - result.to_dict()
- Erwartung:
  - Methode wird erkannt, aber nicht falsch lokal aufgelöst.

7.8.e – Unit-Test für importierte lokale Funktion
- Zwei Dateien:
  - a.py definiert helper()
  - b.py importiert helper und ruft helper()
- Erwartung:
  - b.main -> a.helper, falls Import Graph/Symbol Index das hergeben.

7.8.f – Unit-Test für externe Calls
- Input:
  - pathlib.Path("x").read_text()
- Erwartung:
  - erkannt, aber als external/unresolved markiert.

7.8.g – Integrationstest Full Export
- Mini-Repo mit mehreren Dateien.
- full.txt enthält Call Graph Section.
- Erwartung:
  - bekannte Kanten erscheinen
  - Reihenfolge stabil
  - keine doppelten Kanten bei gleichem Call-Ort

7.9 – Qualität und Abschluss

7.9.a – Duplikate vermeiden
- Gleicher Call in gleicher Datei, gleichem Caller, gleicher Zeile soll nicht mehrfach erscheinen.
- Falls mehrere identische Calls in verschiedenen Zeilen: beide behalten oder sauber gruppieren.

7.9.b – Ausgabegröße kontrollieren
- Bei großen Repos kann Call Graph groß werden.
- Für Milestone 7 reicht einfache Begrenzung oder Gruppierung.
- Spätere Ranking-/Limit-Logik kann in Milestone 15/16 kommen.

7.9.c – Dokumentation minimal aktualisieren
- README oder interne Beschreibung ergänzen:
  - Call Graph wird statisch aus Python-AST erzeugt.
  - Dynamische Calls werden nicht garantiert erkannt.
- Keine übertriebene Doku, nur was Nutzer verstehen müssen.

7.9.d – Gesamtprüfung
- python3 -m pytest --color=yes
- repocontext --version
- repocontext info
- repocontext full/export gegen echtes Repo testen
- ./bundle_project.sh

Definition of Done für Milestone 7:
- Python-Funktionsaufrufe werden per AST erkannt.
- Methodenaufrufe werden erkannt.
- self.method() wird lokal auf Klassenmethoden aufgelöst.
- Lokale Funktionen im selben File werden aufgelöst.
- Importierte repo-interne Funktionen werden, soweit möglich, über Symbol Index und Import Graph aufgelöst.
- Unresolved/externe Calls werden nicht falsch behauptet, sondern markiert.
- full.txt enthält eine Call-Graph-Sektion.
- Tests decken direkte Calls, verschachtelte Calls, Methoden, self.method(), Imports und Full-Export-Integration ab.
- Alle Tests sind grün.
