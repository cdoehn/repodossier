Milestone 18 – Release 1.0

Quelle: REPOCONTEXT_ROADMAP.md – Milestone 18 enthält:
- Documentation completion
- Smoke tests
- pipx validation
- Version 1.0.0

Ziel:
RepoContext soll nach Milestone 18 als stabile Version 1.0.0 installierbar, dokumentiert, smoke-getestet und per pipx nutzbar sein.

Keine neuen großen Features mehr.
Nur Release-Härtung, Doku, Smoke Tests, pipx-Validierung, kleinere CLI-Politur und Versionierung.


18.1 Release-Scope einfrieren und Ist-Stand prüfen

18.1.a Roadmap-Abgleich Milestone 0–17
- Prüfen, ob die bisherigen Milestones im aktuellen Code nachvollziehbar vorhanden sind.
- Nicht nach Checkboxen gehen.
- Gegen Code, Tests, README und aktuelle Exportausgaben prüfen.
- Ergebnis: offene Release-Lücken notieren oder direkt beheben.

18.1.b CLI-Hauptbefehle prüfen
- repocontext --help prüfen
- repocontext full --help prüfen
- repocontext export-ai --help prüfen
- repocontext export-docs --help prüfen
- repocontext changed --help prüfen
- Prüfen, ob argparse-Texte verständlich sind.
- Keine alten Begriffe wie Bundled Project verwenden.
- Keine toten Optionen dokumentieren.
- Keine falschen Beispiele stehen lassen.

18.1.c pyproject.toml prüfen
- Projektname prüfen.
- CLI entrypoint prüfen.
- Runtime dependencies prüfen.
- Dev dependencies prüfen.
- Python-Version prüfen.
- README-Metadaten prüfen.
- Version noch nicht final setzen, außer im späteren Version-Commit.


18.2 Dokumentation abschließen

18.2.a README finalisieren
- Kurz erklären, was RepoContext ist.
- Zielgruppe erklären: LLM-/AI-Kontext aus Repositories erzeugen.
- Installationsabschnitt ergänzen.
- Quick Start ergänzen.
- Exportarten erklären.
- Konfiguration erklären.
- Secret Detection erklären.
- Split Exports erklären.
- Bash Support erklären.
- Limitations ergänzen.

18.2.b Installation dokumentieren
- Lokale Installation dokumentieren:
  python3 -m pip install .
- Entwicklungsinstallation dokumentieren:
  python3 -m venv .venv
  source .venv/bin/activate
  python3 -m pip install -e ".[dev]"
  python3 -m pytest
- pipx-Installation dokumentieren:
  pipx install .
- Hinweis ergänzen, dass pipx für CLI-Nutzung empfohlen ist.

18.2.c Command Reference ergänzen
- repocontext full dokumentieren.
- repocontext export-ai dokumentieren.
- repocontext export-docs dokumentieren.
- repocontext changed dokumentieren.
- Je Befehl:
  - Zweck
  - typische Ausgabe
  - wichtigste Optionen
  - Beispielaufruf

18.2.d Exportdateien dokumentieren
- full.txt erklären.
- ai.txt erklären.
- docs.txt erklären.
- changed.txt erklären.
- Split-Dateien erklären, falls Exportlimits greifen.
- Erklären, dass generierte Exportdateien normalerweise nicht committed werden sollen.

18.2.e Konfiguration dokumentieren
- .repocontext.yml dokumentieren.
- Include-Filter erklären.
- Exclude-Filter erklären.
- Exportlimits erklären.
- Nur Optionen dokumentieren, die wirklich implementiert sind.
- Beispiel einbauen.

18.2.f Release-Hinweise ergänzen
- Version 1.0.0 als stabile erste Release-Version vorbereiten.
- Kurz erklären, welche Features enthalten sind.
- Bekannte Grenzen statischer Analyse nennen.
- Keine übertriebenen Versprechen machen.


18.3 Smoke Tests ergänzen

18.3.a Bestehende Teststruktur prüfen
- Prüfen, ob es bereits Smoke-/CLI-Tests gibt.
- Falls ja: dort sinnvoll erweitern.
- Falls nein: tests/test_smoke_cli.py anlegen.

18.3.b Temporäres Test-Repository erzeugen
- In tmp_path ein kleines Git-Repository erzeugen.
- Dateien anlegen:
  - README.md
  - pyproject.toml
  - src/example.py
  - scripts/example.sh
- git init ausführen.
- git add . ausführen.
- git commit -m "Initial test repo" ausführen.
- Git-User lokal im Test setzen, falls nötig.

18.3.c Full Export Smoke Test
- repocontext full ausführen.
- Prüfen:
  - full.txt wird erzeugt.
  - README-Inhalt erscheint.
  - Python-Datei erscheint.
  - Bash-Datei erscheint.
  - Repository Tree oder vergleichbare Struktur erscheint.
  - Keine offensichtlichen Fehlerausgaben.

18.3.d AI Export Smoke Test
- repocontext export-ai ausführen.
- Prüfen:
  - ai.txt wird erzeugt.
  - Important Files erscheinen.
  - Symbol Index erscheint.
  - Import Graph erscheint.
  - Call Graph erscheint.
  - Bash-Symbole erscheinen, falls Bash-Datei vorhanden.

18.3.e Docs Export Smoke Test
- repocontext export-docs ausführen.
- Prüfen:
  - docs.txt wird erzeugt.
  - README-Inhalt erscheint.
  - Doku-Inhalt erscheint.
  - Kein vollständiger Source-Dump wie in full.txt.

18.3.f Changed Export Smoke Test
- Nach Initial Commit eine Datei ändern.
- repocontext changed ausführen.
- Prüfen:
  - changed.txt wird erzeugt.
  - geänderte Datei erscheint.
  - Diff-/Änderungskontext erscheint.
  - keine ignorierten Exportdateien versehentlich als relevante Änderung erscheinen.


18.4 pipx Validation

18.4.a pipx lokal testen
- pipx uninstall repocontext || true
- pipx install .
- repocontext --help ausführen.
- repocontext full --help ausführen.
- Prüfen:
  - CLI ist verfügbar.
  - Keine Importfehler.
  - Keine Pfadabhängigkeit auf Entwicklungsumgebung.
  - Paketdaten fehlen nicht.

18.4.b pipx Smoke Flow testen
- Nach pipx install in ein temporäres Beispielrepo wechseln.
- repocontext full ausführen.
- repocontext export-ai ausführen.
- repocontext export-docs ausführen.
- repocontext changed ausführen.
- Prüfen:
  - full.txt wird erzeugt.
  - ai.txt wird erzeugt.
  - docs.txt wird erzeugt.
  - changed.txt wird erzeugt.

18.4.c pipx Reinstall prüfen
- pipx uninstall repocontext ausführen.
- pipx install . erneut ausführen.
- repocontext --version ausführen.
- Falls --version noch fehlt, als kleinen Release-Fix ergänzen.


18.5 Version 1.0.0 setzen

18.5.a Version zentral setzen
- In pyproject.toml Version auf 1.0.0 setzen.
- Falls zusätzlich src/repocontext/__init__.py oder ähnliche Datei eine __version__ enthält:
  - ebenfalls auf 1.0.0 setzen
  - oder besser aus einer zentralen Quelle lesen, falls das Projekt das schon tut.

18.5.b repocontext --version prüfen oder ergänzen
- repocontext --version soll funktionieren.
- Erwartete Ausgabe ungefähr:
  repocontext 1.0.0

18.5.c Versionstest ergänzen
- Test ergänzen:
  - CLI --version gibt 1.0.0 aus.
  - Ausgabe enthält repocontext.
  - Test soll robust sein und nicht unnötig abhängig von Formatdetails werden.


18.6 Release-Finalcheck

18.6.a Komplette Testsuite ausführen
- python3 -m pytest --color=yes
- Erwartung:
  - alle Tests grün

18.6.b RepoContext-Exports mit RepoContext selbst erzeugen
- Kein bundle_project.sh verwenden.
- Stattdessen:
  repocontext full
  repocontext export-ai
  repocontext export-docs
  repocontext changed
- Prüfen:
  - full.txt plausibel
  - ai.txt plausibel
  - docs.txt plausibel
  - changed.txt plausibel
  - keine Secrets sichtbar
  - keine alten Begriffe wie Bundled Project
  - keine unnötigen riesigen Artefakte

18.6.c Git-Status prüfen
- git status --short
- Prüfen:
  - nur gewünschte Release-Dateien geändert
  - generierte Exportdateien nicht versehentlich zum Commit vorgemerkt
  - keine temporären Test-/pipx-Artefakte enthalten


18.7 Sinnvolle Commit-Reihenfolge

18.7.a Commit 1: Document release usage
- README finalisieren.
- Installation, pipx, Quick Start und Commands dokumentieren.
- Config und Exportarten dokumentieren.
- alte Begriffe entfernen.

18.7.b Commit 2: Add release smoke tests
- CLI-Smoke-Tests für full, ai, docs und changed ergänzen.
- Temporäres Git-Testrepo im Test erzeugen.
- Exportdateien prüfen.

18.7.c Commit 3: Validate pipx release install
- pipx-Anleitung finalisieren.
- ggf. lokale pipx-Validation als manuelles Release-Check-Kommando dokumentieren.
- Paketdaten und Entrypoint prüfen.

18.7.d Commit 4: Release version 1.0.0
- Version auf 1.0.0 setzen.
- --version prüfen oder ergänzen.
- Versionstest ergänzen.

18.7.e Commit 5: Finalize release 1.0
- letzte Doku-Korrekturen.
- Abschlussprüfung.
- alle Tests grün.
- finaler Release-Commit.


Empfohlener nächster Schritt:
Mit 18.1 und 18.2 beginnen.

Erster Implementierungsblock:
- README releasefähig machen.
- CLI-Hilfetexte prüfen und ggf. verbessern.
- Keine Version auf 1.0.0 setzen.
- Keine neuen großen Features einbauen.
- Danach Tests laufen lassen und Commit erzeugen.
