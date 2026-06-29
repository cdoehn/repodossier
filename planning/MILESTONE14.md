Milestone 14 – Secret Detection

Ziel:
RepoContext soll potenziell sensible Secrets in exportierten Dateien erkennen, klassifizieren und sicher maskieren, bevor sie in full.txt, ai.txt, docs.txt oder changed.txt landen. Die Erkennung soll konservativ genug sein, um typische API Keys, Tokens, Secrets und Passwörter zu finden, aber so umgesetzt werden, dass False Positives nachvollziehbar bleiben und Tests stabil sind.

Quelle: REPOCONTEXT_ROADMAP.md, Milestone 14 – Secret Detection :contentReference[oaicite:0]{index=0}


14.1 – Secret-Detection-Grundmodell

14.1.a – SecretFinding-Datenmodell einführen
Ziel:
Eine zentrale Datenstruktur für erkannte Secrets schaffen.

Umsetzung:
- Neues Modul anlegen:
  - src/repocontext/secrets.py
- Dataclass SecretFinding hinzufügen mit:
  - file_path: str
  - line_number: int
  - secret_type: str
  - matched_text: str
  - masked_text: str
  - variable_name: str | None
  - confidence: str
- Optional helper:
  - has_secret: bool
  - display_label oder summary_line

Tests:
- tests/test_secrets.py anlegen
- Test für Dataclass-Initialisierung
- Test, dass alle Felder korrekt gesetzt werden

Akzeptanz:
- SecretFinding ist importierbar
- Tests laufen grün
- Noch keine Integration in Exporte


14.1.b – SecretPattern-Datenmodell und Pattern Registry einführen
Ziel:
Secret-Erkennung konfigurierbar und testbar machen.

Umsetzung:
- In src/repocontext/secrets.py ergänzen:
  - Dataclass SecretPattern
    - name: str
    - regex: Pattern[str]
    - secret_type: str
    - confidence: str
    - value_group: str | int | None
- Funktion default_secret_patterns() hinzufügen
- Erste Pattern-Namen vorbereiten:
  - api_key_assignment
  - token_assignment
  - secret_assignment
  - password_assignment

Tests:
- Test, dass default_secret_patterns() nicht leer ist
- Test, dass alle Pattern eindeutige Namen haben
- Test, dass alle Pattern einen secret_type setzen

Akzeptanz:
- Pattern sind zentral definiert
- Noch keine Maskierung erforderlich


14.2 – Masking Core

14.2.a – mask_secret_value() implementieren
Ziel:
Secret-Werte zuverlässig maskieren, ohne Kontext komplett zu verlieren.

Umsetzung:
- Funktion mask_secret_value(value: str) -> str hinzufügen
- Verhalten:
  - Leere Werte bleiben leer
  - Sehr kurze Werte vollständig maskieren
  - Werte ab sinnvoller Länge teilweise sichtbar lassen:
    - Anfang 3–4 Zeichen sichtbar
    - Ende 3–4 Zeichen sichtbar
    - Mitte durch ***REDACTED*** ersetzen
- Beispiele:
  - "abc" -> "***REDACTED***"
  - "sk_live_1234567890abcdef" -> "sk_l***REDACTED***cdef"

Tests:
- Kurzer Secret-Wert wird vollständig maskiert
- Langer Secret-Wert wird teilweise maskiert
- Maskierter Wert enthält nicht den vollständigen Originalwert
- Maskierung ist deterministisch

Akzeptanz:
- Keine Secret-Erkennung ohne Masking
- Masking-Funktion separat testbar


14.2.b – mask_secret_in_line() implementieren
Ziel:
Nur den sensiblen Wert in einer Zeile ersetzen, nicht die ganze Zeile zerstören.

Umsetzung:
- Funktion mask_secret_in_line(line: str, secret_value: str) -> str
- Ersetzt nur das erste passende Secret-Vorkommen oder alle identischen Vorkommen, je nach einfacher stabiler Implementierung
- Kommentar/Code-Struktur der Zeile bleibt erhalten

Tests:
- "API_KEY='abcd1234secret'" wird zu "API_KEY='abc***REDACTED***cret'"
- Variable, Gleichheitszeichen und Quotes bleiben erhalten
- Nicht betroffene Teile der Zeile bleiben unverändert

Akzeptanz:
- Maskierung erhält Lesbarkeit des Codes


14.3 – Assignment-basierte Erkennung

14.3.a – API_KEY-Erkennung implementieren
Ziel:
Typische API-Key-Zuweisungen erkennen.

Erkennung:
- Variablennamen mit:
  - API_KEY
  - api_key
  - apiKey
  - GOOGLE_API_KEY
  - OPENAI_API_KEY
  - *_API_KEY
- Formen:
  - API_KEY = "..."
  - API_KEY='...'
  - API_KEY: "..."
  - export API_KEY="..."
  - os.environ["API_KEY"] = "..."

Umsetzung:
- detect_secrets_in_text(text: str, file_path: str) -> list[SecretFinding]
- Zeilenweise prüfen
- line_number 1-basiert
- SecretFinding.secret_type = "API_KEY"
- confidence = "high" bei klarer Zuweisung

Tests:
- Python-Zuweisung wird erkannt
- dotenv-Zuweisung wird erkannt
- YAML-artige Zuweisung wird erkannt
- export-Zuweisung wird erkannt
- Zeilennummer stimmt
- Masked Text enthält Original-Secret nicht vollständig

Akzeptanz:
- API_KEY laut Roadmap abgedeckt


14.3.b – TOKEN-Erkennung implementieren
Ziel:
Typische Token-Zuweisungen erkennen.

Erkennung:
- Variablennamen mit:
  - TOKEN
  - token
  - access_token
  - refresh_token
  - github_token
  - bearer_token
  - auth_token
- Formen wie bei API_KEY

Umsetzung:
- Pattern für tokenartige Variablennamen ergänzen
- SecretFinding.secret_type = "TOKEN"

Tests:
- ACCESS_TOKEN wird erkannt
- refresh_token wird erkannt
- GITHUB_TOKEN wird erkannt
- Normale Wörter mit "token" ohne Zuweisung werden nicht erkannt

Akzeptanz:
- TOKEN laut Roadmap abgedeckt


14.3.c – SECRET-Erkennung implementieren
Ziel:
Generische Secret-Zuweisungen erkennen.

Erkennung:
- Variablennamen mit:
  - SECRET
  - secret
  - client_secret
  - jwt_secret
  - signing_secret
  - webhook_secret
  - app_secret

Umsetzung:
- Pattern für secretartige Variablennamen ergänzen
- SecretFinding.secret_type = "SECRET"

Tests:
- CLIENT_SECRET wird erkannt
- jwt_secret wird erkannt
- WEBHOOK_SECRET wird erkannt
- Kommentar mit Wort "secret" ohne Wert wird nicht erkannt

Akzeptanz:
- SECRET laut Roadmap abgedeckt


14.3.d – PASSWORD-Erkennung implementieren
Ziel:
Passwortartige Zuweisungen erkennen.

Erkennung:
- Variablennamen mit:
  - PASSWORD
  - password
  - passwd
  - pwd
  - db_password
  - database_password

Umsetzung:
- Pattern für passwortartige Variablennamen ergänzen
- SecretFinding.secret_type = "PASSWORD"

Tests:
- DB_PASSWORD wird erkannt
- password = "..." wird erkannt
- passwd='...' wird erkannt
- pwd: "..." wird erkannt
- Begriffe wie "password_required = True" werden nicht als Secret gewertet, wenn Wert boolesch ist

Akzeptanz:
- PASSWORD laut Roadmap abgedeckt


14.4 – False-Positive-Schutz

14.4.a – Placeholder-Werte ignorieren
Ziel:
Beispielwerte und offensichtliche Platzhalter nicht als echte Secrets melden.

Ignorieren:
- ""
- "changeme"
- "change-me"
- "example"
- "example-token"
- "your-api-key"
- "your_api_key"
- "insert-key-here"
- "todo"
- "none"
- "null"
- "dummy"
- "test"
- "password"
- "secret"

Umsetzung:
- Funktion is_placeholder_secret(value: str) -> bool
- Case-insensitive
- Trim Quotes/Whitespace

Tests:
- Platzhalter werden ignoriert
- Echte längere Werte werden nicht ignoriert
- "test" wird ignoriert
- "test_very_long_realistic_token_123456" wird nicht pauschal ignoriert, sofern Pattern es erkennt

Akzeptanz:
- Dokumentationsbeispiele lösen keine unnötigen Treffer aus


14.4.b – Nicht-sensitive Zuweisungen ignorieren
Ziel:
Häufige False Positives vermeiden.

Ignorieren:
- Boolean-Werte:
  - true
  - false
  - True
  - False
- Zahlenwerte:
  - 0
  - 1
  - 123
- None/null
- Sehr kurze Werte unter Mindestlänge, außer explizit später anders entschieden

Umsetzung:
- Funktion is_probably_secret_value(value: str) -> bool
- detect_secrets_in_text nutzt diese Funktion

Tests:
- password_required = True wird nicht erkannt
- token_count = 123 wird nicht erkannt
- secret_enabled = false wird nicht erkannt
- API_KEY = "sk-123456789abcdef" wird erkannt

Akzeptanz:
- Erkennung ist brauchbar konservativ


14.4.c – Kommentare separat behandeln
Ziel:
Kommentare mit Begriffen wie "password" oder "token" sollen nicht unnötig maskiert werden.

Umsetzung:
- Für vollständige Kommentarzeilen keine Assignment-Erkennung ausführen:
  - Python "# ..."
  - Bash "# ..."
  - YAML "# ..."
- Inline-Kommentare nach erkannter Zuweisung bleiben erhalten

Tests:
- "# API_KEY = ..." wird nicht erkannt
- "API_KEY = 'realvalue'  # comment" wird erkannt und Kommentar bleibt erhalten

Akzeptanz:
- Dokumentationskommentare bleiben lesbar


14.5 – Dateiweite Maskierung

14.5.a – mask_secrets_in_text() implementieren
Ziel:
Einen kompletten Dateiinhalt maskieren und Findings zurückgeben.

Umsetzung:
- Funktion:
  - mask_secrets_in_text(text: str, file_path: str) -> tuple[str, list[SecretFinding]]
- Verhalten:
  - Erkennt alle Secrets
  - Ersetzt sie im Text durch maskierte Varianten
  - Gibt maskierten Text und Findings zurück
- Reihenfolge der Findings:
  - Datei-Reihenfolge
  - Zeilen-Reihenfolge

Tests:
- Datei mit mehreren Secrets wird vollständig maskiert
- Findings enthalten alle Treffer
- Maskierter Text enthält keine vollständigen Secret-Werte
- Nicht betroffene Zeilen bleiben identisch

Akzeptanz:
- Zentrale Funktion für Exportintegration vorhanden


14.5.b – SecretScanResult einführen
Ziel:
Für spätere Export-Summaries eine strukturierte Zusammenfassung bereitstellen.

Umsetzung:
- Dataclass SecretScanResult:
  - masked_text: str
  - findings: list[SecretFinding]
  - total_findings: int property
  - findings_by_type: dict[str, int] property oder Funktion
- Optional:
  - scan_and_mask_text(text, file_path) -> SecretScanResult

Tests:
- total_findings stimmt
- findings_by_type zählt API_KEY, TOKEN, SECRET, PASSWORD korrekt

Akzeptanz:
- Exporter müssen nicht selbst zählen


14.6 – Integration in Full Export

14.6.a – Full Export maskiert Source Dump
Ziel:
full.txt darf erkannte Secrets nicht im Klartext enthalten.

Umsetzung:
- Full-Exporter an der Stelle integrieren, an der Dateiinhalt in den Export geschrieben wird
- Vor dem Schreiben:
  - scan_and_mask_text(content, relative_path)
- Nur maskierten Inhalt ausgeben
- Bestehende Exportstruktur nicht verändern

Tests:
- Neuer Test in tests/test_full_exporter.py
- Repository-Fixture mit Datei:
  - config.py mit API_KEY
  - .env-artige Datei, falls Scanner sie bereits berücksichtigt
- full.txt enthält:
  - "***REDACTED***"
  - nicht den vollständigen Secret-Wert
- Nicht-secret Code bleibt enthalten

Akzeptanz:
- Full Export ist secret-safe


14.6.b – Secret Summary im Full Export ergänzen
Ziel:
full.txt soll transparent zeigen, dass Secrets erkannt und maskiert wurden.

Umsetzung:
- Abschnitt ergänzen:
  - "# Secret Detection"
- Inhalt:
  - "Total findings: X"
  - Tabelle oder Liste nach Typ:
    - API_KEY: n
    - TOKEN: n
    - SECRET: n
    - PASSWORD: n
  - Optional betroffene Dateien mit Anzahl
- Keine echten Secret-Werte anzeigen
- Nur maskierte Werte oder gar keine Werte anzeigen

Tests:
- Full Export enthält "# Secret Detection"
- Counts stimmen
- Secret-Wert erscheint nicht im Summary
- Datei mit Secret wird genannt

Akzeptanz:
- Nutzer sieht, dass Masking aktiv war


14.7 – Integration in AI Export

14.7.a – AI Export maskiert Inhalte
Ziel:
ai.txt darf keine erkannten Secrets im Klartext enthalten.

Umsetzung:
- AI-Exporter beim Einfügen relevanter Codeausschnitte oder wichtiger Dateien ebenfalls maskieren
- Falls AI Export keine vollständigen Inhalte schreibt, trotzdem alle enthaltenen Inhalte maskieren
- Gemeinsame Utility nutzen, nicht doppelt implementieren

Tests:
- tests/test_ai_exporter.py ergänzen
- ai.txt enthält nicht den vollständigen Secret-Wert
- ai.txt enthält Maskierungsmarker
- Symbol Index / Architekturteile bleiben unverändert

Akzeptanz:
- AI Export ist secret-safe


14.7.b – Secret-Warnhinweis im AI Export ergänzen
Ziel:
ai.txt soll knapp signalisieren, dass Secrets maskiert wurden.

Umsetzung:
- Abschnitt oder Hinweis ergänzen:
  - "Secret Detection"
  - "Potential secrets were masked before export."
- Keine sensiblen Werte zeigen
- Summary kurz halten, da ai.txt kompakt bleiben soll

Tests:
- Hinweis erscheint, wenn Secrets gefunden wurden
- Hinweis erscheint nicht oder zeigt "0", wenn keine Secrets gefunden wurden
- Keine echten Werte im Hinweis

Akzeptanz:
- AI Export bleibt knapp und sicher


14.8 – Integration in Documentation Export

14.8.a – Docs Export maskiert Dokumentationsinhalte
Ziel:
docs.txt darf keine Secrets enthalten, auch wenn README, SPEC oder TASKS Beispiele mit echten Werten enthalten.

Umsetzung:
- Docs-Exporter beim Schreiben extrahierter Dokumentationsdateien maskieren
- Placeholder-Filter verhindert unnötige Meldungen bei normalen Beispielen

Tests:
- tests/test_docs_exporter.py ergänzen
- README mit echtem TOKEN wird maskiert
- README mit "your-api-key" wird nicht als echter Fund gezählt
- docs.txt enthält keinen Klartext-Token

Akzeptanz:
- Documentation Export ist secret-safe


14.8.b – Docs Secret Summary optional ergänzen
Ziel:
Auch docs.txt kann zeigen, dass maskiert wurde, ohne zu viel Raum einzunehmen.

Umsetzung:
- Kurzer Abschnitt:
  - "# Secret Detection"
  - "Potential secrets masked: X"
- Nur bei Funden oder immer mit 0, je nachdem was besser zur bestehenden Exportstruktur passt

Tests:
- Summary bei Fund vorhanden
- Kein Klartext-Secret in Summary

Akzeptanz:
- Verhalten konsistent mit Full Export


14.9 – Integration in Changed Export

14.9.a – Changed Export maskiert Diff-Inhalte
Ziel:
changed.txt darf keine Secrets enthalten, auch wenn sie in Git-Diffs auftauchen.

Umsetzung:
- Changed-Exporter an der Stelle integrieren, an der Diff oder geänderte Datei-Inhalte geschrieben werden
- Maskierung muss auch bei Zeilen mit Diff-Präfix funktionieren:
  - +API_KEY="..."
  - -API_KEY="..."
- Pattern müssen optional führende Diff-Zeichen erlauben oder vor Prüfung temporär entfernen

Tests:
- tests/test_changed_cli.py oder tests/test_changed_exporter.py ergänzen
- Diff mit neuem Secret wird maskiert
- Diff mit entferntem Secret wird maskiert
- Vollständiger Secret-Wert erscheint nicht in changed.txt

Akzeptanz:
- Changed Export ist secret-safe


14.9.b – Changed Secret Summary ergänzen
Ziel:
changed.txt soll anzeigen, ob Secrets im Diff maskiert wurden.

Umsetzung:
- Kurzer Abschnitt:
  - "# Secret Detection"
  - "Potential secrets masked in changed export: X"
- Keine Secret-Werte anzeigen

Tests:
- Summary bei Diff-Secret vorhanden
- Count stimmt
- Kein Klartext-Secret

Akzeptanz:
- Changed Export erfüllt Milestone 14 vollständig für Diffs


14.10 – CLI- und Pipeline-Konsistenz

14.10.a – Gemeinsame Secret-Scan-Pipeline verwenden
Ziel:
Alle Exporter verwenden denselben Codepfad für Secret Detection.

Umsetzung:
- Keine doppelten Regex-Implementierungen in einzelnen Exportern
- Zentrale Funktionen aus src/repocontext/secrets.py nutzen
- Bei Bedarf kleine Adapter-Funktion:
  - mask_export_content(content, path)

Tests:
- Ein parametrischer Test über full/ai/docs/changed, soweit praktikabel
- Gleicher Secret-Wert wird in allen Exporten maskiert

Akzeptanz:
- Wartbarer, zentraler Milestone


14.10.b – Export-Reihenfolge und bestehende Abschnitte stabil halten
Ziel:
Milestone 14 darf bestehende Exporte nicht unnötig umbauen.

Umsetzung:
- Bestehende Snapshot-/Regressionserwartungen prüfen
- Secret Detection Sections an sinnvollen Stellen einfügen:
  - nach Dependency/Database/Graph Summaries oder vor Source Dump
- Bestehende Überschriften möglichst nicht umbenennen

Tests:
- Bestehende Tests bleiben grün
- Neue Tests prüfen nur relevante Ergänzungen

Akzeptanz:
- Minimal-invasive Integration


14.11 – README-Dokumentation

14.11.a – README Secret Detection dokumentieren
Ziel:
Nutzer verstehen, dass RepoContext Secrets maskiert, aber kein vollwertiger Security Scanner ist.

Umsetzung:
- README Abschnitt ergänzen:
  - Secret Detection
  - erkannte Klassen:
    - API_KEY
    - TOKEN
    - SECRET
    - PASSWORD
  - Masking-Verhalten
  - Hinweis:
    - Best-effort Schutz
    - keine Garantie, alle Secrets zu finden
    - vor Veröffentlichung trotzdem prüfen
- Beispiele mit Platzhalterwerten, nicht mit echten Secrets

Tests:
- README-Dokumentationstest ergänzen oder bestehenden README-Test erweitern
- Prüfen auf:
  - "Secret Detection"
  - "API_KEY"
  - "TOKEN"
  - "PASSWORD"
  - "masked"

Akzeptanz:
- Feature ist dokumentiert


14.11.b – CLI-Hilfe prüfen
Ziel:
Falls argparse-Beschreibungen schon existieren, Secret Detection angemessen erwähnen.

Umsetzung:
- Prüfen, ob CLI-Hilfe Exportbefehle beschreibt
- Optional Beschreibung ergänzen:
  - "exports mask potential secrets by default"
- Kein neuer CLI-Schalter nötig, außer Architektur verlangt es

Tests:
- CLI help test nur ergänzen, falls bestehende Tests dafür vorhanden sind

Akzeptanz:
- Nutzer sieht Sicherheitsverhalten auch in CLI/README


14.12 – Abschlussprüfung Milestone 14

14.12.a – Vollständige Test-Suite laufen lassen
Ziel:
Sicherstellen, dass Secret Detection keine bestehenden Funktionen beschädigt.

Prüfbefehl:
- python3 -m pytest --color=yes

Zusätzlich prüfen:
- repocontext full
- repocontext export-ai
- repocontext export-docs
- repocontext changed, falls Git-Diff vorhanden/testbar

Akzeptanz:
- Alle Tests grün
- Keine Klartext-Secrets in erzeugten Exporten


14.12.b – Manuelle Exportprüfung mit Testsecret
Ziel:
Echte End-to-End-Sicherheit prüfen.

Vorgehen:
- Temporäre Testdatei mit eindeutigem Fake-Secret erzeugen:
  - OPENAI_API_KEY="sk-test-1234567890abcdefSECRET"
- repocontext full ausführen
- repocontext export-ai ausführen
- repocontext export-docs ausführen, falls Datei dokumentationsrelevant ist
- repocontext changed ausführen, falls Datei uncommitted geändert ist
- grep prüfen:
  - Fake-Secret darf nirgends vollständig erscheinen
  - REDACTED Marker soll erscheinen

Akzeptanz:
- Klartext-Secret erscheint in keinem Export


14.12.c – Milestone-Review
Ziel:
Abgleichen, ob Roadmap-Punkte vollständig erfüllt sind.

Roadmap-Punkte:
- API_KEY detection
- TOKEN detection
- SECRET detection
- PASSWORD detection
- Masking support

Erwartetes Ergebnis:
- Alle fünf Punkte umgesetzt
- Tests vorhanden
- README dokumentiert
- full.txt, ai.txt, docs.txt und changed.txt secret-safe
- Keine echten Secret-Werte in Summaries


Empfohlene Commit-Reihenfolge:

Commit 1:
Add secret detection core models and masking helpers

Enthält:
- src/repocontext/secrets.py
- SecretFinding
- SecretPattern
- mask_secret_value
- mask_secret_in_line
- erste Unit Tests

Commit 2:
Detect common API keys tokens secrets and passwords

Enthält:
- detect_secrets_in_text
- API_KEY/TOKEN/SECRET/PASSWORD Pattern
- Placeholder-/False-Positive-Schutz
- Unit Tests

Commit 3:
Mask secrets in full export

Enthält:
- Full Export Integration
- Full Secret Detection Summary
- Full Export Tests

Commit 4:
Mask secrets in AI and docs exports

Enthält:
- AI Export Integration
- Docs Export Integration
- Hinweise/Summaries
- Tests

Commit 5:
Mask secrets in changed export

Enthält:
- Changed Export Integration
- Diff-Zeilen-Masking
- Changed Export Tests

Commit 6:
Document secret detection

Enthält:
- README Update
- CLI-Hilfe falls sinnvoll
- Dokumentationstests

Commit 7:
Finalize milestone 14 secret detection

Enthält:
- kleinere Konsistenzfixes
- Abschlussprüfung
- ggf. Teststabilisierung


Definition of Done für Milestone 14:

- API_KEY-Zuweisungen werden erkannt
- TOKEN-Zuweisungen werden erkannt
- SECRET-Zuweisungen werden erkannt
- PASSWORD-Zuweisungen werden erkannt
- Erkannte Werte werden maskiert
- Vollständige Original-Secrets erscheinen nicht in:
  - full.txt
  - ai.txt
  - docs.txt
  - changed.txt
- Placeholder und offensichtliche Beispiele werden nicht unnötig als echte Secrets gezählt
- Summaries zeigen nur Typen, Counts und Dateien, keine Klartextwerte
- README dokumentiert das Feature und die Best-effort-Grenzen
- Tests für Core, Full Export, AI Export, Docs Export und Changed Export sind vorhanden
- python3 -m pytest --color=yes läuft grün
