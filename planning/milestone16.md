# Milestone 16 – Split Exports / Multi-Part Output

## Ziel

RepoContext soll große Exportdateien optional oder automatisch in mehrere Teil-Dateien aufteilen können.

Beispiele:

- full.txt
- full.part01.txt
- full.part02.txt
- ai.txt
- ai.part01.txt
- ai.part02.txt
- docs.txt
- docs.part01.txt
- changed.txt
- changed.part01.txt

Das Ziel ist, große Repositories besser für ChatGPT/LLM-Workflows nutzbar zu machen, wenn einzelne Exportdateien zu groß werden.

---

## Grundentscheidung

Milestone 16 baut auf Milestone 15 auf.

Die Split-Konfiguration soll über `.repocontext.yml` steuerbar sein und zusätzlich per CLI überschreibbar werden.

Die erste Version soll bewusst simpel bleiben:

- Split nach Zeichen-Grenze
- stabile Dateinamen
- keine kaputten Überschriften, soweit sinnvoll möglich
- keine verlorenen Inhalte
- vollständige Hauptdatei bleibt erhalten
- zusätzliche Part-Dateien werden erzeugt
- Tests für full, ai, docs und changed

Empfohlene Grundregel:

- Ohne Split bleibt alles wie bisher.
- Mit Split bleibt die Hauptdatei vollständig erhalten.
- Zusätzlich werden Part-Dateien erzeugt.

Beispiel:

- full.txt bleibt vollständig.
- full.part01.txt, full.part02.txt usw. enthalten die gesplitteten Teile.

Vorteil:

- abwärtskompatibel
- keine kaputten bestehenden Workflows
- Parts sind nur Zusatzdateien für LLM-Uploads

---

## 16.1 – Split-Konfigurationsmodell vorbereiten

### Ziel

Die vorhandene Konfiguration aus Milestone 15 um Split-Optionen erweitern.

### Umsetzung

Neue Config-Felder, zum Beispiel:

    exports:
      split:
        enabled: false
        max_chars: 200000
        strategy: heading

Unterstützte Felder:

- enabled
- max_chars
- strategy

Unterstützte Strategien:

- plain
- heading

### Akzeptanz

- `.repocontext.yml` kann Split-Optionen enthalten.
- Defaults bleiben abwärtskompatibel.
- Ohne Split-Konfiguration ändert sich das bisherige Verhalten nicht.
- Fehlerhafte Werte werden sauber validiert.
- CLI und Exporter können später auf dieselbe Config-Struktur zugreifen.

### Tests

- Config Default ohne Split.
- Config mit Split enabled.
- Config mit custom max_chars.
- Config mit strategy plain.
- Config mit strategy heading.
- Config mit ungültigem max_chars.
- Config mit unbekannter Strategie.

### Commit

    Add split export configuration

---

## 16.2 – Gemeinsames Splitter-Modul einführen

### Ziel

Eine zentrale Split-Logik erstellen, damit nicht jeder Exporter eigene Split-Regeln bekommt.

### Neue Datei

- src/repocontext/splitter.py

### Kernfunktionen

- Text in Parts aufteilen.
- Maximale Part-Größe beachten.
- Überschriften möglichst nicht mitten im Abschnitt trennen.
- Fallback auf plain split, wenn ein Abschnitt größer ist als das Limit.
- Keine Inhalte verlieren.
- Reihenfolge stabil halten.
- Deterministische Ausgabe erzeugen.

### Vorgeschlagene API

    split_text(
        text: str,
        max_chars: int,
        strategy: str = "heading",
    ) -> list[str]

### Verhalten

- Wenn der Text kleiner als max_chars ist, entsteht ein Part.
- Wenn der Text größer ist, entstehen mehrere Parts.
- Bei strategy heading wird bevorzugt vor Markdown-Überschriften getrennt.
- Bei strategy plain wird hart nach Zeichenlimit getrennt.
- Wenn ein einzelner Abschnitt größer als max_chars ist, wird dieser Abschnitt trotzdem gesplittet.
- Der Splitter selbst fügt noch keine Part-Header ein.
- Header werden später vom Output Writer ergänzt.

### Akzeptanz

- Splitter ist unabhängig von CLI und Exportern testbar.
- Splitter verliert keine Zeichen.
- Splitter erzeugt deterministische Parts.
- Splitter kann sehr kleine Limits behandeln.
- Join aller rohen Parts ergibt wieder den Originaltext.

### Tests

- Text kleiner als Limit ergibt 1 Part.
- Text größer als Limit ergibt mehrere Parts.
- Plain Split verliert keine Inhalte.
- Heading Split trennt bevorzugt an Überschriften.
- Sehr großer Abschnitt wird trotzdem gesplittet.
- Sehr kleines Limit funktioniert.
- Leerer Text funktioniert sauber.
- Join aller Parts ergibt den Originaltext.

### Commit

    Add reusable export splitter

---

## 16.3 – Output Writer abstrahieren

### Ziel

Das Schreiben von Exportdateien zentralisieren.

Bisher schreiben Export-Kommandos vermutlich direkt full.txt, ai.txt, docs.txt oder changed.txt.

Stattdessen soll ein gemeinsamer Writer entscheiden:

- normale Einzeldatei schreiben
- oder vollständige Einzeldatei plus Multi-Part-Dateien schreiben

### Neue Datei

- src/repocontext/output_writer.py

### Verhalten ohne Split

- full.txt wird wie bisher geschrieben.
- ai.txt wird wie bisher geschrieben.
- docs.txt wird wie bisher geschrieben.
- changed.txt wird wie bisher geschrieben.
- Keine zusätzlichen Dateien.

### Verhalten mit Split

Bei Split enabled:

- Hauptdatei bleibt vollständig erhalten.
- Zusätzlich werden Part-Dateien erzeugt.

Beispiel:

- full.txt
- full.part01.txt
- full.part02.txt

### Part-Header

Jeder Part bekommt einen kurzen Kopf:

    # RepoContext Export Part 1/3

    Source export: full.txt
    Part: 1 of 3

Danach folgt der jeweilige Inhaltsteil.

### Alte Parts bereinigen

Vor neuem Export sollen alte passende Part-Dateien entfernt werden.

Beispiel:

- alter Export hatte full.part01.txt bis full.part05.txt
- neuer Export braucht nur full.part01.txt bis full.part02.txt
- full.part03.txt bis full.part05.txt müssen gelöscht werden

Andere Dateien dürfen nicht angefasst werden.

### Akzeptanz

- Writer kann Einzeldatei schreiben.
- Writer kann zusätzliche Part-Dateien schreiben.
- Alte name.partXX.txt werden vor neuem Export bereinigt.
- Andere Dateien bleiben unangetastet.
- Dateinamen sind stabil und sortierbar.
- Hauptdatei bleibt vollständig.

### Tests

- Einzeldatei ohne Split.
- Split erzeugt name.part01.txt und name.part02.txt.
- Hauptdatei bleibt vollständig.
- Part-Dateien enthalten Header.
- Alte name.partXX.txt werden entfernt.
- Andere Dateien bleiben unangetastet.
- Dateinamen sind korrekt nullgepadded.

### Commit

    Add split-aware output writer

---

## 16.4 – CLI-Optionen für Split ergänzen

### Ziel

Split soll nicht nur über `.repocontext.yml`, sondern auch direkt per CLI nutzbar sein.

### Relevante Commands

- repocontext full
- repocontext export-ai
- repocontext export-docs
- repocontext changed

### Neue Optionen

- --split
- --no-split
- --split-max-chars <N>
- --split-strategy plain|heading

### Priorität

CLI überschreibt Config.

Reihenfolge:

1. CLI-Option
2. .repocontext.yml
3. Default

### Verhalten

- --split aktiviert Split.
- --no-split deaktiviert Split auch bei Config enabled.
- --split-max-chars überschreibt Config-Wert.
- --split-strategy überschreibt Config-Wert.
- Ohne CLI-Flags bleibt das bisherige Verhalten erhalten.

### Akzeptanz

- Bestehende Commands funktionieren unverändert.
- --split aktiviert Split ohne Config.
- --no-split deaktiviert Split trotz Config.
- --split-max-chars setzt das Limit.
- --split-strategy setzt die Strategie.
- Fehlerhafte Werte werden verständlich gemeldet.

### Tests

- CLI aktiviert Split ohne Config.
- Config aktiviert Split.
- CLI --no-split überschreibt Config.
- CLI Limit überschreibt Config Limit.
- CLI Strategy überschreibt Config Strategy.
- Ungültiges Limit erzeugt Fehler.
- Ungültige Strategy erzeugt Fehler.

### Commit

    Add split CLI options

---

## 16.5 – Full Export splitten

### Ziel

repocontext full unterstützt Multi-Part-Ausgabe.

### Beispiel

    repocontext full --split --split-max-chars 50000

Erzeugt:

- full.txt
- full.part01.txt
- full.part02.txt
- full.part03.txt

### Verhalten

- full.txt bleibt vollständig.
- Parts enthalten zusammen den Exportinhalt.
- Parts enthalten jeweils kurzen Header.
- Alte full.partXX.txt werden entfernt.
- Split-Konfiguration aus Config und CLI wird beachtet.

### Akzeptanz

- Kleines Repo erzeugt bei großem Limit höchstens einen Part.
- Künstlich kleines Limit erzwingt mehrere Parts.
- full.txt bleibt vorhanden.
- full.txt bleibt vollständig.
- Part-Dateien sind sortierbar.
- Keine alten full.partXX.txt bleiben zurück.

### Tests

- Full Export ohne Split bleibt unverändert.
- Full Export mit Split erzeugt Part-Dateien.
- Full Export mit kleinem Limit erzeugt mehrere Parts.
- full.txt enthält weiterhin den vollständigen Export.
- Alte full.partXX.txt werden bereinigt.

### Commit

    Support split full exports

---

## 16.6 – AI Export splitten

### Ziel

repocontext export-ai unterstützt Multi-Part-Ausgabe.

### Beispiel

    repocontext export-ai --split --split-max-chars 50000

Erzeugt:

- ai.txt
- ai.part01.txt
- ai.part02.txt
- ai.part03.txt

### Besonderheit

ai.txt ist besonders LLM-orientiert.

Darum soll der Split möglichst an großen Abschnitten erfolgen, zum Beispiel:

- Architecture Summary
- Symbol Index
- Import Graph
- Call Graph
- Important Files
- Source Snippets

Die konkrete Abschnittserkennung muss nicht perfekt sein. Es reicht, wenn die gemeinsame heading-Strategie Markdown-Überschriften sinnvoll berücksichtigt.

### Akzeptanz

- ai.txt bleibt vollständig.
- ai.partXX.txt wird erzeugt.
- Wichtige AI-Abschnitte werden nicht unnötig mitten in Überschriften getrennt.
- Part-Header sagen klar, welcher Export gesplittet wurde.
- Keine alten ai.partXX.txt bleiben zurück.

### Tests

- AI Export ohne Split bleibt unverändert.
- AI Export mit Split erzeugt Part-Dateien.
- Kleines Limit erzeugt mehrere Parts.
- ai.txt bleibt vollständig.
- Inhalte aus Symbol Index / Import Graph / Source Snippets gehen nicht verloren.
- Alte ai.partXX.txt werden bereinigt.

### Commit

    Support split AI exports

---

## 16.7 – Docs Export splitten

### Ziel

repocontext export-docs unterstützt Multi-Part-Ausgabe.

### Beispiel

    repocontext export-docs --split --split-max-chars 50000

Erzeugt:

- docs.txt
- docs.part01.txt
- docs.part02.txt

### Verhalten

- docs.txt bleibt vollständig.
- docs.partXX.txt wird zusätzlich erzeugt.
- Markdown-/Dokumentabschnitte werden möglichst sauber getrennt.
- Alte docs.partXX.txt werden entfernt.

### Akzeptanz

- Docs Export bleibt vollständig.
- Parts sind stabil benannt.
- Markdown-Überschriften bleiben möglichst lesbar.
- Keine alten docs.partXX.txt bleiben zurück.

### Tests

- Docs Export ohne Split bleibt unverändert.
- Docs Export mit Split erzeugt Parts.
- Kleines Limit erzeugt mehrere Parts.
- docs.txt bleibt vollständig.
- Alte docs.partXX.txt werden bereinigt.

### Commit

    Support split docs exports

---

## 16.8 – Changed Export splitten

### Ziel

repocontext changed unterstützt Multi-Part-Ausgabe.

### Beispiel

    repocontext changed --split --split-max-chars 50000

Erzeugt:

- changed.txt
- changed.part01.txt
- changed.part02.txt

### Besonderheit

Changed Export enthält potenziell große Diffs.

Split sollte möglichst an Datei- oder Diff-Grenzen erfolgen.

Die erste Version darf dafür ebenfalls die heading-Strategie nutzen, sofern der Changed Export Dateigrenzen als Überschriften oder erkennbare Abschnitte ausgibt.

Falls ein einzelner Diff sehr groß ist, wird notfalls plain gesplittet.

### Akzeptanz

- changed.txt bleibt vollständig.
- changed.partXX.txt wird erzeugt.
- Große Diffs werden notfalls plain gesplittet.
- Git-Kontext bleibt erhalten.
- Keine alten changed.partXX.txt bleiben zurück.

### Tests

- Changed Export ohne Split bleibt unverändert.
- Changed Export mit Split erzeugt Parts.
- Große künstliche Änderung erzeugt mehrere Parts.
- changed.txt bleibt vollständig.
- Datei-/Diff-Überschriften bleiben möglichst sauber.
- Alte changed.partXX.txt werden bereinigt.

### Commit

    Support split changed exports

---

## 16.9 – README und Dokumentation aktualisieren

### Ziel

Split Export wird dokumentiert.

### README-Inhalte

- Zweck von Split Exports.
- Beispiel `.repocontext.yml`.
- Beispiel CLI-Aufrufe.
- Erklärung der Dateinamen.
- Hinweis: Originaldatei bleibt vollständig erhalten.
- Hinweis: Part-Dateien sind Zusatzdateien für LLM-Uploads.
- Hinweis: CLI überschreibt Config.
- Keine Erwähnung von bundle_project.sh.

### Beispiel Config

    exports:
      split:
        enabled: true
        max_chars: 100000
        strategy: heading

### Beispiel CLI-Aufrufe

    repocontext full --split --split-max-chars 100000
    repocontext export-ai --split
    repocontext export-docs --split
    repocontext changed --split
    repocontext full --no-split

### Akzeptanz

- README beschreibt Config.
- README beschreibt CLI.
- README beschreibt Dateinamen.
- README erklärt, dass Hauptdateien vollständig bleiben.
- Keine alten Bundle-Begriffe.
- Beispiele nutzen nur RepoContext-Kommandos.

### Commit

    Document split exports

---

## 16.10 – Finale Acceptance Tests

### Ziel

End-to-End prüfen, dass Split Exports in allen Exporttypen funktionieren.

### Testdatei

- tests/test_split_exports_acceptance.py

### Prüfumfang

- repocontext full --split --split-max-chars ...
- repocontext export-ai --split --split-max-chars ...
- repocontext export-docs --split --split-max-chars ...
- repocontext changed --split --split-max-chars ...

### Akzeptanz

- Alle Commands laufen erfolgreich.
- Hauptdateien existieren weiterhin.
- Part-Dateien existieren bei erzwungen kleinem Limit.
- Part-Dateien enthalten Header.
- Alte Part-Dateien werden nicht stehen gelassen.
- Full pytest ist grün.

### Abschlussprüfung

    python3 -m pytest --color=yes

    repocontext full --split --split-max-chars 50000
    repocontext export-ai --split --split-max-chars 50000
    repocontext export-docs --split --split-max-chars 50000
    repocontext changed --split --split-max-chars 50000

    ls -1 full.txt full.part*.txt ai.txt ai.part*.txt docs.txt docs.part*.txt changed.txt changed.part*.txt

### Commit

    Add split export acceptance tests

---

## Nicht Teil von Milestone 16

Diese Punkte bleiben spätere Erweiterungen:

- Token-genaue Splits nach Modell-Kontextfenster.
- Automatische ZIP-Ausgabe.
- Remote Git URL Input.
- Recent Commit Context.
- Code Compression / Token Saving Mode.
- Projekt-/CLI-Renaming.
- Cloud Upload.
- Interaktive Auswahl einzelner Parts.
- Semantisches Splitten nach AST.
- Automatische Zusammenfassungen pro Part.
- Split nach konkretem Modell wie GPT, Claude oder Gemini.

---

## Empfohlene Commit-Reihenfolge

1. Add split export configuration
2. Add reusable export splitter
3. Add split-aware output writer
4. Add split CLI options
5. Support split full exports
6. Support split AI exports
7. Support split docs exports
8. Support split changed exports
9. Document split exports
10. Add split export acceptance tests

---

## Definition of Done

Milestone 16 ist abgeschlossen, wenn:

- Split-Konfiguration über `.repocontext.yml` funktioniert.
- CLI-Flags Split aktivieren/deaktivieren können.
- CLI-Flags Config-Werte überschreiben können.
- full unterstützt Split-Ausgaben.
- export-ai unterstützt Split-Ausgaben.
- export-docs unterstützt Split-Ausgaben.
- changed unterstützt Split-Ausgaben.
- Hauptdateien weiterhin wie bisher vollständig existieren.
- Part-Dateien stabil und sortierbar benannt werden.
- Alte Part-Dateien vor neuer Ausgabe entfernt werden.
- Andere Dateien nicht versehentlich gelöscht werden.
- Tests für Config vorhanden sind.
- Tests für Splitter vorhanden sind.
- Tests für Writer vorhanden sind.
- Tests für CLI vorhanden sind.
- Acceptance Tests für alle Exporttypen vorhanden sind.
- README dokumentiert die Funktion.
- README enthält keine alten Bundle-Begriffe.
- python3 -m pytest --color=yes vollständig grün ist.

---

## Startpunkt

Der erste sinnvolle Umsetzungsschritt ist:

16.1 – Split-Konfigurationsmodell vorbereiten
