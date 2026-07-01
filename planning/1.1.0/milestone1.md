# MILESTONE 1 – Pipx Installation Hardening

Release-Linie: 1.1.0  
Empfohlener Zielpfad im Repository: `planning/1.1.0/milestone1.md`  
Roadmap-Punkt: `1. Pipx Installation Hardening`  
Projektname: RepoDossier  
Legacy-Alias: RepoContext / `repocontext`

---

## Ziel

RepoDossier soll zuverlässig lokal aus dem Repository per `pipx` installierbar sein.

Nach diesem Milestone muss ein normaler Nutzer aus einem lokalen Checkout heraus installieren können:

```bash
python3 -m pipx install "$PWD"
```

Danach müssen beide CLI-Kommandos verfügbar sein:

```bash
repodossier --help
repocontext --help
repodossier --version
repocontext --version
```

Die README soll genau diesen robusten Installationsweg dokumentieren. Alte oder lokal problematische Installationsvarianten wie `pipx install -e .` sollen nicht mehr als Standardweg empfohlen werden.

---

## Warum Release 1.1.0 und nicht 1.0.1?

Empfehlung: `1.1.0`

Begründung:

- Die neue Roadmap enthält mehrere neue Features und strukturelle Erweiterungen.
- Pipx Installation Hardening ist zwar klein, startet aber eine neue Entwicklungsreihe nach Release 1.0.0.
- Die folgenden Roadmap-Punkte gehen klar über reine Patch-/Bugfix-Arbeit hinaus.
- `1.0.1` wäre eher passend, wenn ausschließlich kleine Bugfixes für die bestehende 1.0.0-Linie gemacht würden.
- `1.1.0` signalisiert sauber: stabile 1.0.0-Basis plus neue Verbesserungsrunde.

Empfohlene Ordnerstruktur:

```text
planning/
├── 1.1.0/
│   ├── milestone1.md
│   ├── milestone2.md
│   ├── milestone3.md
│   └── ...
├── archive/
│   └── 1.0.0/
└── roadmap_next.md
```

Hinweis:

- `planning/archive/1.0.0/` bleibt historisch.
- Die neue aktive Planung liegt zuerst in `planning/1.1.0/`.
- Nach Abschluss von Release 1.1.0 kann die Planung optional nach `planning/archive/1.1.0/` verschoben werden.

---

## Ausgangslage

Die Roadmap fordert für diesen Milestone:

- robuste lokale pipx-Installation
- README-Dokumentation des funktionierenden Installationswegs
- keine primäre Empfehlung von `pipx install -e .`
- Bereinigung doppelter package-include-Regeln in `pyproject.toml`
- Prüfung von Build und Twine Check
- pipx-Smoke-Test für beide CLI-Kommandos
- Erweiterung von `scripts/validate_pipx_release.sh`
- Sicherstellung, dass `repodossier` und `repocontext` nach Installation verfügbar sind

Bekannte konkrete Problemstelle:

```toml
include = ["repodossier*", "repodossier*"]
```

Ziel:

```toml
include = ["repodossier*"]
```

Bekannter funktionierender Installationsweg:

```bash
cd ~/market_research/repo_dossier || {
  echo "Fehler: Projektverzeichnis nicht gefunden."
}

python3 -m pipx uninstall repodossier 2>/dev/null || true
python3 -m pipx install "$PWD"

export PATH="$HOME/.local/bin:$PATH"

repodossier --help
repocontext --help
```

---

# 1.1 Bestandsaufnahme der aktuellen Installation und Paket-Metadaten

## 1.1.a Aktuelle Projektstruktur prüfen

Ziel:

Vor Änderungen prüfen, wie Paket, CLI-Entrypoints, README und Validierungsskript aktuell aufgebaut sind.

Zu prüfen:

- `pyproject.toml`
- `README.md`
- `scripts/validate_pipx_release.sh`
- `tests/test_pipx_release_validation_script.py`
- `tests/test_release_smoke_cli.py`
- `tests/test_repodossier_cli_alias.py`
- `tests/test_version_cli.py`
- `src/repodossier/__main__.py`
- `src/repodossier/cli.py`
- `src/repocontext/__main__.py`
- `src/repocontext/cli.py`

Akzeptanzkriterien:

- Klar ist, wo die CLI-Entrypoints definiert sind.
- Klar ist, ob `repodossier` und `repocontext` beide in `pyproject.toml` registriert sind.
- Klar ist, welche README-Abschnitte geändert werden müssen.
- Klar ist, wie das pipx-Validierungsskript aktuell arbeitet.
- Klar ist, welche Tests bereits existieren und welche ergänzt werden müssen.

---

## 1.1.b CLI-Entrypoints in pyproject.toml prüfen

Ziel:

Sicherstellen, dass beide Kommandos als Script-Entrypoints paketiert werden.

Zu prüfen:

```toml
[project.scripts]
repodossier = "repodossier.__main__:main"
repocontext = "repocontext.__main__:main"
```

oder die aktuell passende Projektstruktur.

Anforderungen:

- `repodossier` muss der primäre aktuelle CLI-Name bleiben.
- `repocontext` bleibt als Legacy-Kompatibilitätsalias erhalten.
- Beide müssen nach pipx-Installation direkt im PATH verfügbar sein.
- Es darf keine harte Abhängigkeit von einer aktivierten `.venv` geben.

Akzeptanzkriterien:

- `pyproject.toml` enthält beide CLI-Scripts.
- Beide Script-Ziele sind importierbar.
- Tests prüfen mindestens indirekt, dass beide CLI-Namen funktionieren.

---

## 1.1.c Aktuelle README-Installationsabschnitte markieren

Ziel:

Alle Stellen finden, an denen Installation oder pipx erwähnt wird.

Zu prüfen:

- Abschnitt `## Installation`
- Abschnitt `## Development`
- Abschnitt `## Development workflow`
- Release Usage Guide
- Pipx Validation Note
- alte Beispiele mit `pipx install .`
- alte Beispiele mit `pipx install -e .`
- alte Beispiele mit `python3 -m pipx install -e .`

Anforderungen:

- Nicht nur den ersten Installationsabschnitt prüfen.
- Auch später eingefügte Release-Blöcke prüfen.
- Doppelte oder widersprüchliche Installationshinweise vermeiden.

Akzeptanzkriterien:

- Alle install-relevanten README-Stellen sind bekannt.
- Es gibt eine klare Entscheidung, welche Stellen geändert werden.
- Keine widersprüchliche Standardempfehlung bleibt stehen.

---

## 1.1.d Vorhandenes pipx-Validierungsskript verstehen

Ziel:

Prüfen, ob `scripts/validate_pipx_release.sh` bereits isoliert testet und welche Lücken es noch gibt.

Zu prüfen:

- Wird `PIPX_HOME` temporär gesetzt?
- Wird `PIPX_BIN_DIR` temporär gesetzt?
- Wird der lokale Checkout installiert?
- Wird `python3 -m pipx install "$PWD"` genutzt?
- Wird noch `pipx install -e .` genutzt?
- Werden beide CLIs geprüft?
- Werden `--help` und `--version` geprüft?
- Werden Export-Smoke-Tests gemacht?
- Wird ein temporäres Git-Repository verwendet?
- Wird am Ende sauber aufgeräumt?

Akzeptanzkriterien:

- Lücken sind dokumentiert.
- Das Skript kann gezielt erweitert werden.
- Es gibt keine unnötige Vermischung mit der lokalen Entwicklungs-`.venv`.

---

## 1.1.e Bestehende Tests lesen und Zieltests festlegen

Ziel:

Verhindern, dass neue Tests blind oder doppelt an falschen Stellen eingefügt werden.

Zu prüfen:

- `tests/test_pipx_release_validation_script.py`
- `tests/test_release_smoke_cli.py`
- `tests/test_repodossier_cli_alias.py`
- `tests/test_version_cli.py`
- `tests/test_readme_documentation.py`
- `tests/test_public_release_metadata.py`

Akzeptanzkriterien:

- Neue Tests werden semantisch passend einsortiert.
- README-Tests werden dort ergänzt, wo bereits README-Inhalte geprüft werden.
- Script-Tests werden dort ergänzt, wo bereits das Validierungsskript geprüft wird.
- CLI-Tests werden nur ergänzt, wenn sie echten Mehrwert bringen.

---

# 1.2 pyproject.toml bereinigen und Paket-Metadaten härten

## 1.2.a Doppelte package-include-Regel entfernen

Ziel:

Die doppelte Include-Regel in `pyproject.toml` bereinigen.

Aktuell zu prüfen:

```toml
include = ["repodossier*", "repodossier*"]
```

Ziel:

```toml
include = ["repodossier*"]
```

Anforderungen:

- Nur die doppelte Angabe entfernen.
- Keine Paketstruktur unnötig umbauen.
- Keine Umbenennung von Packages.
- Legacy-Package `repocontext` darf nicht versehentlich aus der Distribution fallen, falls es noch gebraucht wird.

Wichtig:

Wenn die Paketfindung aktuell `repocontext` nur wegen anderer Konfiguration einschließt, darf die Bereinigung `repocontext` nicht aus der installierten Distribution entfernen.

Akzeptanzkriterien:

- `pyproject.toml` enthält keine doppelte Include-Regel.
- `repodossier` bleibt paketiert.
- `repocontext` bleibt als Legacy-Alias paketiert.
- `python3 -m build` funktioniert nach der Änderung.

---

## 1.2.b Paketfindung für repodossier und repocontext prüfen

Ziel:

Sicherstellen, dass beide Packages in Wheel und sdist landen.

Zu prüfen:

- Ist `src/repodossier` im Wheel enthalten?
- Ist `src/repocontext` im Wheel enthalten?
- Sind beide `__main__.py` Dateien enthalten?
- Sind beide CLI-Script-Ziele im Wheel-Metadata sichtbar?

Mögliche Prüfung:

```bash
rm -rf dist build *.egg-info src/*.egg-info
python3 -m build
python3 -m zipfile -l dist/*.whl | grep -E 'repodossier|repocontext'
```

Akzeptanzkriterien:

- Wheel enthält `repodossier`.
- Wheel enthält `repocontext`.
- Wheel enthält die benötigten Entry-Module.
- Keine unnötigen generierten Dateien werden paketiert.

---

## 1.2.c Build-Backend und Projektmetadaten nicht unnötig ändern

Ziel:

Milestone 1 bleibt fokussiert auf Installationshärtung.

Nicht ändern, außer zwingend nötig:

- Projektname
- Versioning-Logik
- License
- Python-Requires
- Dependency-Liste
- Konsolenbefehle außer zur Korrektur
- Paketstruktur

Akzeptanzkriterien:

- Keine unnötige pyproject-Umstrukturierung.
- Diffs bleiben klein und nachvollziehbar.
- Bestehende Release-Metadaten-Tests bleiben grün.

---

# 1.3 Robusten pipx-Installationsweg festlegen

## 1.3.a Offiziellen lokalen pipx-Installationsweg definieren

Ziel:

Ein einziger offizieller Standardweg für lokale Installation aus einem Checkout.

Offiziell:

```bash
python3 -m pipx uninstall repodossier 2>/dev/null || true
python3 -m pipx install "$PWD"
export PATH="$HOME/.local/bin:$PATH"
repodossier --help
repocontext --help
```

Anforderungen:

- `python3 -m pipx` statt bloß `pipx`, damit klar ist, welcher Python-Kontext verwendet wird.
- `"$PWD"` statt `.` verwenden, weil es robuster und eindeutiger ist.
- `pipx install -e .` nicht als normalen Standard empfehlen.
- `repodossier` vor `repocontext` nennen.
- `repocontext` klar als Legacy-Alias kennzeichnen.

Akzeptanzkriterien:

- Dieser Installationsweg ist im Milestone dokumentiert.
- README wird später auf diesen Weg umgestellt.
- Validierungsskript nutzt ebenfalls diesen Ansatz oder eine isolierte Variante davon.

---

## 1.3.b Nicht mehr empfohlenen Standardweg explizit entfernen

Ziel:

Problematische oder verwirrende Standardempfehlungen aus der README entfernen oder herabstufen.

Nicht mehr als Standard empfehlen:

```bash
pipx install -e .
python3 -m pipx install -e .
```

Auch zu prüfen:

```bash
pipx install .
```

Diese Variante kann funktionieren, ist aber weniger eindeutig als:

```bash
python3 -m pipx install "$PWD"
```

Anforderungen:

- `pipx install -e .` darf nicht mehr als normaler Nutzerweg erscheinen.
- Falls Editable-Install überhaupt erwähnt wird, dann nur unter Development und mit `pip install -e ".[dev]"` in einer `.venv`.
- Die normale pipx-Installation soll nicht mit Developer Editable Install vermischt werden.

Akzeptanzkriterien:

- README empfiehlt nicht mehr primär `pipx install -e .`.
- README enthält keine widersprüchliche pipx-Standardempfehlung.
- Development-Install bleibt separat und verständlich.

---

## 1.3.c Entscheidung zu Editable Development Install dokumentieren

Ziel:

Entwickler sollen weiterhin schnell lokal entwickeln können, aber nicht über pipx editable als Standard.

Empfohlener Development-Weg:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 -m pytest --color=yes
```

Anforderungen:

- Development-Install ist klar getrennt von normaler pipx-Installation.
- Keine Empfehlung von `pipx install -e .` als Hauptweg.
- Keine Aussage, dass pipx editable grundsätzlich verboten ist; nur nicht Standard.

Akzeptanzkriterien:

- README trennt Installation und Development sauber.
- Nutzer wissen, wann sie pipx und wann sie `.venv` verwenden sollen.

---

# 1.4 README-Installationsdokumentation aktualisieren

## 1.4.a README Installation Abschnitt ersetzen

Ziel:

Der Hauptabschnitt `## Installation` soll den robusten pipx-Weg zeigen.

Neuer Inhalt soll ungefähr abdecken:

```markdown
## Installation

### Install from a local checkout with pipx

From the repository root:

    python3 -m pipx uninstall repodossier 2>/dev/null || true
    python3 -m pipx install "$PWD"
    export PATH="$HOME/.local/bin:$PATH"

Verify both CLI names:

    repodossier --help
    repodossier --version
    repocontext --help
    repocontext --version

`repodossier` is the current command. `repocontext` is kept as a temporary legacy compatibility alias.
```

Anforderungen:

- `repodossier` ist der primäre Name.
- `repocontext` wird als Legacy-Alias erklärt.
- Die Befehle sind copy-paste-fähig.
- Kein Verweis auf nicht vorhandene Veröffentlichung auf PyPI, falls noch nicht veröffentlicht.
- Keine falsche Aussage, dass `pipx install repodossier` bereits der Standard ist, solange das Paket lokal installiert wird.

Akzeptanzkriterien:

- README enthält den robusten pipx-Weg.
- README nennt beide CLI-Namen.
- README erklärt Legacy-Alias klar.
- README ist nicht widersprüchlich.

---

## 1.4.b README Development Abschnitt sauber halten

Ziel:

Development Setup bleibt als `.venv`-Workflow dokumentiert.

Soll enthalten:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 -m pytest --color=yes
```

Anforderungen:

- Development Setup soll nicht entfernt werden.
- Development Setup soll nicht mit pipx verwechselt werden.
- Die Tests sollen mit `python3 -m pytest --color=yes` dokumentiert bleiben.
- Keine Empfehlung, generierte Exportdateien zu committen.

Akzeptanzkriterien:

- Development-Dokumentation bleibt nutzbar.
- Normalnutzer-Installation und Entwickler-Installation sind klar getrennt.

---

## 1.4.c Release Usage Guide aktualisieren

Ziel:

Falls im README ein Release-Usage-Block vorhanden ist, muss auch dort der Installationshinweis konsistent sein.

Zu ändern:

- Abschnitt `Release 1.0 usage guide`, falls noch vorhanden
- Unterabschnitt `Installation`
- Pipx Validation Note
- Local pipx testing Beispiele

Anforderungen:

- Keine alten Beispiele stehen lassen, die dem neuen Hauptweg widersprechen.
- Falls die alte Release-1.0-Doku historisch bleiben soll, trotzdem keine problematische aktuelle Empfehlung prominent stehen lassen.
- Bei aktuellen Anleitungen `python3 -m pipx install "$PWD"` verwenden.

Akzeptanzkriterien:

- README enthält keinen Widerspruch zwischen Hauptinstallation und Release-Guide.
- README-Tests können die neuen Strings prüfen.
- Nutzer sehen überall denselben empfohlenen lokalen pipx-Weg.

---

## 1.4.d README-Sprache zu Legacy RepoContext präzisieren

Ziel:

Klarheit über `repodossier` und `repocontext`.

Anforderungen:

- `repodossier` ist der aktuelle Name.
- `repocontext` bleibt temporärer Kompatibilitätsalias.
- Neue Dokumentation bevorzugt `repodossier`.
- pipx-Smoke-Tests prüfen aber beide.

Akzeptanzkriterien:

- README vermeidet den Eindruck, dass beide Namen gleichwertige neue Produktnamen sind.
- Der Alias bleibt für Nutzer alter Workflows auffindbar.
- Keine alte Dokumentation empfiehlt primär `repocontext`.

---

# 1.5 README-Regressionstests ergänzen

## 1.5.a Test für robusten pipx-Installationsweg ergänzen

Ziel:

README-Test sichert, dass der neue offizielle Installationsweg dokumentiert ist.

Möglicher Test in `tests/test_readme_documentation.py` oder passender README-Testdatei:

Erwartete Strings:

```text
python3 -m pipx install "$PWD"
python3 -m pipx uninstall repodossier
repodossier --help
repocontext --help
repodossier --version
repocontext --version
```

Akzeptanzkriterien:

- Test schlägt fehl, wenn der robuste Installationsweg wieder entfernt wird.
- Test prüft beide CLI-Namen.
- Test ist nicht unnötig fragil gegenüber Markdown-Formatierung.

---

## 1.5.b Test gegen primäre editable-pipx-Empfehlung ergänzen

Ziel:

Verhindern, dass `pipx install -e .` wieder als Standard auftaucht.

Mögliche Prüfung:

- README darf `pipx install -e .` nicht enthalten.
- README darf `python3 -m pipx install -e .` nicht enthalten.

Falls eine Entwickler-Notiz zu pipx editable bewusst behalten wird:

- Test muss prüfen, dass es nicht im Hauptinstallationsabschnitt steht.
- Einfacher und robuster für diesen Milestone: komplett aus README entfernen.

Akzeptanzkriterien:

- Problematischer Standardweg ist aus README verschwunden.
- Test verhindert Rückfall.

---

## 1.5.c Test für klare Legacy-Alias-Sprache ergänzen

Ziel:

README soll deutlich machen, dass `repocontext` Legacy-Kompatibilität ist.

Erwartete Strings sinngemäß:

```text
repodossier is the current command
repocontext is kept as a temporary legacy compatibility alias
```

oder vorhandene README-Formulierung.

Akzeptanzkriterien:

- README erklärt Alias-Verhalten.
- Neue Nutzer werden zum aktuellen Namen geführt.
- Alte Nutzer finden den Kompatibilitätsbefehl.

---

## 1.5.d Test für Development-Install beibehalten

Ziel:

Sicherstellen, dass die Entwicklerinstallation weiterhin dokumentiert ist.

Erwartete Strings:

```text
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 -m pytest --color=yes
```

Akzeptanzkriterien:

- Development-Workflow bleibt dokumentiert.
- Entfernen des `.venv`-Workflows wird erkannt.
- Normaler pipx-Weg und Development-Weg bleiben beide sichtbar.

---

# 1.6 validate_pipx_release.sh härten

## 1.6.a Skript auf isolierte pipx-Umgebung prüfen

Ziel:

Das Validierungsskript soll nicht vom globalen Nutzer-pipx-Zustand abhängen.

Anforderungen:

- Temporäres Arbeitsverzeichnis verwenden.
- `PIPX_HOME` temporär setzen.
- `PIPX_BIN_DIR` temporär setzen.
- `PATH` um temporäres `PIPX_BIN_DIR` erweitern.
- Am Ende temporäre Umgebung löschen.

Beispielprinzip:

```bash
TMP_DIR="$(mktemp -d)"
export PIPX_HOME="$TMP_DIR/pipx_home"
export PIPX_BIN_DIR="$TMP_DIR/pipx_bin"
export PATH="$PIPX_BIN_DIR:$PATH"
```

Akzeptanzkriterien:

- Skript nutzt isolierten pipx-Kontext.
- Lokale globale pipx-Installationen beeinflussen das Ergebnis nicht.
- Skript räumt temporäre Dateien auf.

---

## 1.6.b Robuste lokale Installation im Skript nutzen

Ziel:

Das Skript soll denselben installierbaren lokalen Checkout testen wie die README.

Anforderung:

```bash
python3 -m pipx install "$REPO_ROOT"
```

Nicht verwenden:

```bash
pipx install -e .
python3 -m pipx install -e .
```

Anforderungen:

- `REPO_ROOT` absolut bestimmen.
- Skript darf aus beliebigem Startverzeichnis funktionieren.
- Installation muss aus dem aktuellen Checkout erfolgen.
- Nach Installation müssen CLI-Scripts im temporären `PIPX_BIN_DIR` liegen.

Akzeptanzkriterien:

- Skript nutzt `python3 -m pipx install "$REPO_ROOT"`.
- Kein `pipx install -e .` im Skript.
- Skript funktioniert vom Repository-Root und aus Unterordnern.

---

## 1.6.c Beide CLI-Namen mit --help prüfen

Ziel:

Nach pipx-Installation müssen beide CLI-Kommandos Hilfe anzeigen.

Checks:

```bash
repodossier --help
repocontext --help
```

Anforderungen:

- Exitcode muss 0 sein.
- Ausgabe sollte Grundtext oder bekannte Subcommands enthalten.
- Fehlerausgabe muss bei Fehlern sichtbar bleiben.

Akzeptanzkriterien:

- Skript bricht ab, wenn `repodossier --help` fehlschlägt.
- Skript bricht ab, wenn `repocontext --help` fehlschlägt.
- Test deckt ab, dass beide Checks im Skript stehen.

---

## 1.6.d Beide CLI-Namen mit --version prüfen

Ziel:

Nach pipx-Installation müssen beide CLI-Kommandos Version anzeigen.

Checks:

```bash
repodossier --version
repocontext --version
```

Anforderungen:

- Exitcode muss 0 sein.
- Ausgabe muss eine Versionsinformation enthalten.
- `repocontext --version` darf nicht kaputtgehen, obwohl es Legacy ist.

Akzeptanzkriterien:

- Skript prüft `repodossier --version`.
- Skript prüft `repocontext --version`.
- Tests sichern beide Strings im Skript ab.

---

## 1.6.e Temporäres Git-Testrepository erzeugen

Ziel:

Export-Smoke-Tests sollen nicht auf dem echten Repo-Dossier-Repository laufen, sondern auf einem kleinen temporären Git-Repository.

Anforderungen:

- `git init`
- minimaler `README.md`
- minimaler Python-Sourcefile, z. B. `src/demo.py`
- mindestens ein Commit, damit Git-Befehle stabil funktionieren
- optional eine Änderung für `changed`

Beispiel:

```bash
mkdir -p "$TMP_DIR/sample_repo/src"
cd "$TMP_DIR/sample_repo"
git init
git config user.email "test@example.invalid"
git config user.name "RepoDossier Test"
printf '# Sample\n' > README.md
printf 'def main():\n    return 0\n' > src/demo.py
git add .
git commit -m "Initial sample project"
```

Akzeptanzkriterien:

- Sample-Repo ist unabhängig vom echten Repo.
- Export-Kommandos laufen in diesem Sample-Repo.
- Keine erzeugten Exportdateien verschmutzen das echte Arbeitsverzeichnis.

---

## 1.6.f Full Export Smoke prüfen

Ziel:

Validierungsskript muss prüfen, dass installierte CLI `full.txt` erzeugen kann.

Check:

```bash
repodossier full
test -s full.txt
grep -q "AI Quick Start" full.txt
grep -q "Repository Statistics" full.txt
```

Akzeptanzkriterien:

- `repodossier full` läuft im Sample-Repo.
- `full.txt` wird erzeugt.
- `full.txt` ist nicht leer.
- Der Export enthält erwartete Grundabschnitte.

---

## 1.6.g AI Export Smoke prüfen

Ziel:

Validierungsskript muss prüfen, dass `ai.txt` erzeugt werden kann.

Check:

```bash
repodossier export-ai
test -s ai.txt
grep -q "Project summary" ai.txt
```

oder passend zu aktueller Ausgabe.

Akzeptanzkriterien:

- `repodossier export-ai` läuft.
- `ai.txt` wird erzeugt.
- `ai.txt` ist nicht leer.
- Ein stabiler AI-Grundabschnitt wird geprüft.

---

## 1.6.h Docs Export Smoke prüfen

Ziel:

Validierungsskript muss prüfen, dass `docs.txt` erzeugt werden kann.

Check:

```bash
repodossier export-docs
test -s docs.txt
grep -q "Documentation" docs.txt
```

Akzeptanzkriterien:

- `repodossier export-docs` läuft.
- `docs.txt` wird erzeugt.
- `docs.txt` ist nicht leer.
- Ein stabiler Dokumentationsabschnitt wird geprüft.

---

## 1.6.i Changed Export Smoke prüfen

Ziel:

Validierungsskript muss prüfen, dass `changed.txt` erzeugt werden kann.

Vorgehen:

- Nach Initial Commit eine Datei ändern.
- Dann `repodossier changed` ausführen.

Beispiel:

```bash
printf '\n# changed\n' >> README.md
repodossier changed
test -s changed.txt
grep -q "Changed" changed.txt
```

Akzeptanzkriterien:

- `changed.txt` wird im Sample-Repo erzeugt.
- Changed Export crasht nicht.
- Changed Export enthält die geänderte Datei oder eine stabile Changed-Überschrift.

---

## 1.6.j Legacy-Alias für mindestens einen Export prüfen

Ziel:

Nicht nur Help/Version, sondern auch echte Legacy-CLI-Ausführung prüfen.

Empfehlung:

```bash
repocontext export-ai --output legacy-ai.txt
test -s legacy-ai.txt
```

Falls `--output` für `export-ai` nicht unterstützt wird:

- Dann nur `repocontext export-ai` in separatem temporären Verzeichnis verwenden.
- Oder Legacy-Alias über `repocontext info` prüfen, falls stabiler.

Akzeptanzkriterien:

- Mindestens ein echter `repocontext`-Subcommand läuft nach pipx-Installation.
- Legacy-Alias ist nicht nur importierbar, sondern praktisch nutzbar.
- Test bleibt klein und robust.

---

## 1.6.k Skript-Ausgabe verständlich machen

Ziel:

Bei Fehlern soll Christian sofort sehen, welcher Schritt gescheitert ist.

Anforderungen:

- Klare Abschnittsausgaben mit `echo`.
- Keine unnötig stillen Fehler.
- `set -euo pipefail` verwenden.
- Bei Cleanup trotzdem temporäre Dateien löschen.
- Keine interaktiven Prompts.
- Keine Befehle, die in einem Pager hängen bleiben.

Beispielausgaben:

```text
== Build checkout path ==
== Install with isolated pipx ==
== Check repodossier CLI ==
== Check repocontext legacy CLI ==
== Create sample git repository ==
== Smoke full export ==
== Smoke AI export ==
== Smoke docs export ==
== Smoke changed export ==
```

Akzeptanzkriterien:

- Skript ist gut lesbar.
- Fehlerstelle ist erkennbar.
- Keine Pager-Ausgaben.
- Keine manuelle Interaktion nötig.

---

# 1.7 Tests für validate_pipx_release.sh ergänzen

## 1.7.a Test für Installationskommando im Skript

Ziel:

Sicherstellen, dass das Skript den robusten Installationsweg nutzt.

Erwartete Strings:

```text
python3 -m pipx install
"$REPO_ROOT"
```

oder genaue Skriptstruktur.

Nicht erlaubt:

```text
pipx install -e
python3 -m pipx install -e
```

Akzeptanzkriterien:

- Test schlägt fehl, wenn editable pipx wieder genutzt wird.
- Test erlaubt robuste absolute Pfadinstallation.
- Test ist nicht unnötig abhängig von Whitespace.

---

## 1.7.b Test für isolierte pipx-Umgebung

Ziel:

Skript muss `PIPX_HOME` und `PIPX_BIN_DIR` verwenden.

Erwartete Strings:

```text
PIPX_HOME
PIPX_BIN_DIR
PATH=
mktemp -d
```

Akzeptanzkriterien:

- Test stellt sicher, dass isolierte pipx-Umgebung erhalten bleibt.
- Globale Nutzerinstallation wird nicht versehentlich genutzt.
- Test ist einfach und wartbar.

---

## 1.7.c Test für beide CLI Help Checks

Ziel:

Beide CLI-Namen müssen im Skript geprüft werden.

Erwartete Strings:

```text
repodossier --help
repocontext --help
```

Akzeptanzkriterien:

- Beide Help Checks sind vorhanden.
- Entfernen des Legacy-Checks fällt auf.
- Entfernen des primären Checks fällt auf.

---

## 1.7.d Test für beide CLI Version Checks

Ziel:

Beide CLI-Namen müssen mit `--version` geprüft werden.

Erwartete Strings:

```text
repodossier --version
repocontext --version
```

Akzeptanzkriterien:

- Beide Version Checks sind vorhanden.
- Legacy-Version bleibt abgesichert.
- Primäre CLI-Version bleibt abgesichert.

---

## 1.7.e Test für Export-Smoke-Checks

Ziel:

Skript soll alle vier Exportmodi prüfen.

Erwartete Strings:

```text
repodossier full
repodossier export-ai
repodossier export-docs
repodossier changed
full.txt
ai.txt
docs.txt
changed.txt
```

Akzeptanzkriterien:

- Full, AI, Docs und Changed werden im Skript geprüft.
- Erzeugte Dateien werden geprüft.
- Smoke-Test bleibt breit genug für Release-Validierung.

---

## 1.7.f Test gegen echte Repository-Verschmutzung

Ziel:

Das Skript soll Export-Smoke-Tests in einem temporären Sample-Repo ausführen.

Erwartete Hinweise:

```text
git init
sample_repo
```

oder die konkret gewählte temporäre Repo-Erstellung.

Akzeptanzkriterien:

- Skript erzeugt Testexporte nicht direkt im RepoDossier-Arbeitsverzeichnis.
- Echte Arbeitskopie bleibt sauber.
- Test ist robust gegenüber internen Pfadnamen.

---

# 1.8 Build- und Twine-Checks integrieren

## 1.8.a Build-Dependency-Verfügbarkeit prüfen

Ziel:

`python3 -m build` und `python3 -m twine check dist/*` sollen ausführbar sein.

Möglichkeiten:

1. Build/Twine als Developer-Dokumentation voraussetzen.
2. Build/Twine in optionalen dev dependencies ergänzen.
3. Validierungsskript prüft verständlich, ob Module fehlen, und gibt klare Anleitung.

Empfehlung für diesen Milestone:

- Wenn `build` und `twine` noch nicht in dev dependencies sind, ergänzen:
  - `build`
  - `twine`
- Dann kann der Release-Check reproduzierbar aus der Development-Umgebung laufen.

Akzeptanzkriterien:

- Entscheidung ist im Code/Doku sichtbar.
- Build/Twine-Check ist reproduzierbar.
- Fehlende Tools führen zu verständlicher Meldung.

---

## 1.8.b Build im Validierungsskript ausführen

Ziel:

Vor pipx-Smoke-Test sicherstellen, dass Paketbau grundsätzlich funktioniert.

Befehle:

```bash
rm -rf dist build src/*.egg-info
python3 -m build
```

Anforderungen:

- Aus Repository-Root ausführen.
- Alte Build-Artefakte vorher löschen.
- Build-Artefakte nicht committen.
- Skript darf nicht stillschweigend alte dist-Dateien prüfen.

Akzeptanzkriterien:

- `dist/*.whl` entsteht frisch.
- `dist/*.tar.gz` entsteht frisch.
- Buildfehler brechen das Skript ab.

---

## 1.8.c Twine Check im Validierungsskript ausführen

Ziel:

Metadatenqualität der Distribution prüfen.

Befehl:

```bash
python3 -m twine check dist/*
```

Akzeptanzkriterien:

- Twine Check läuft nach frischem Build.
- Fehler in Paketmetadaten brechen das Skript ab.
- Keine Veröffentlichung wird ausgelöst.
- Kein Upload zu PyPI.

---

## 1.8.d Tests für Build-/Twine-Check im Skript ergänzen

Ziel:

Sicherstellen, dass Release-Validierung diese Checks enthält.

Erwartete Strings:

```text
python3 -m build
python3 -m twine check dist/*
```

Akzeptanzkriterien:

- Test erkennt Entfernen der Build-Prüfung.
- Test erkennt Entfernen der Twine-Prüfung.
- Test erzwingt keinen echten Build im Unit-Test, sondern prüft Skriptinhalt.

---

# 1.9 Lokale manuelle pipx-Prüfung dokumentieren

## 1.9.a Kurzen manuellen Check in README aufnehmen

Ziel:

Neben dem Vollskript soll es einen kleinen manuellen Check geben.

Empfohlener Abschnitt:

```bash
python3 -m pipx uninstall repodossier 2>/dev/null || true
python3 -m pipx install "$PWD"
export PATH="$HOME/.local/bin:$PATH"

repodossier --version
repodossier --help
repocontext --version
repocontext --help
```

Akzeptanzkriterien:

- Nutzer können Installation schnell manuell testen.
- Beide CLI-Namen sind abgedeckt.
- Der Check entspricht dem offiziellen Weg.

---

## 1.9.b Vollständige Release-Validierung dokumentieren

Ziel:

README soll klar auf das Skript verweisen.

Empfohlener Abschnitt:

```bash
scripts/validate_pipx_release.sh
```

Erklären:

- baut Distribution
- prüft Paketmetadaten
- installiert mit isoliertem pipx
- prüft beide CLI-Namen
- erzeugt full, ai, docs und changed in einem temporären Testrepo

Akzeptanzkriterien:

- README beschreibt Zweck des Skripts.
- Nutzer wissen, wann sie das Skript verwenden.
- Keine Verwechslung mit normaler Installation.

---

# 1.10 CLI-Smoke-Tests prüfen und ggf. ergänzen

## 1.10.a Bestehende Release Smoke CLI Tests prüfen

Ziel:

Sicherstellen, dass installierte CLI-Verhalten nicht nur im Skript, sondern auch in Tests grundlegend abgedeckt ist.

Zu prüfen:

- `tests/test_release_smoke_cli.py`
- `tests/test_repodossier_cli_alias.py`
- `tests/test_version_cli.py`

Mögliche Anforderungen:

- `repodossier --version` funktioniert.
- `repocontext --version` funktioniert.
- `repodossier --help` funktioniert.
- `repocontext --help` funktioniert.
- `python -m repodossier --help` funktioniert.
- `python -m repocontext --help` funktioniert, falls unterstützt.

Akzeptanzkriterien:

- Bestehende Tests decken das ausreichend ab oder werden minimal ergänzt.
- Keine schweren pipx-Integrationstests in normaler Unit-Test-Suite, wenn das zu langsam oder fragil ist.
- Echte pipx-Installation bleibt Aufgabe des Validierungsskripts.

---

## 1.10.b Keine Netzwerkabhängigkeit in Tests einführen

Ziel:

Tests und Validierung bleiben lokal.

Nicht erlaubt:

- PyPI Upload
- PyPI Download als Pflicht
- Netzwerkzugriff
- externe Paket-Repositories
- externe Git-Repositories

Akzeptanzkriterien:

- Tests laufen offline.
- Validierung installiert lokalen Checkout.
- Keine CI-Abhängigkeit von externen Diensten außer normalen Python-Tool-Installationen, falls CI sie vorher installiert.

---

## 1.10.c CI-Relevanz prüfen

Ziel:

Entscheiden, ob das vollständige pipx-Validierungsskript in CI laufen soll oder nur lokal dokumentiert bleibt.

Empfehlung für diesen Milestone:

- Normale CI bleibt bei Tests und CLI-Smoke.
- Vollständiges pipx-Validierungsskript wird lokal dokumentiert.
- Optional später eigener CI-Job für Release-Validation.

Begründung:

- pipx-Isolation und Build/Twine können CI verlängern.
- Milestone 1 soll stabilisieren, nicht CI unnötig komplex machen.

Akzeptanzkriterien:

- CI wird nicht unnötig aufgebläht.
- README dokumentiert lokalen Release-Check.
- Bestehende CI-Smoke-Tests bleiben grün.

---

# 1.11 Abschlussprüfung für Milestone 1

## 1.11.a Syntax- und Importprüfung

Ziel:

Schnell prüfen, ob Python-Dateien syntaktisch korrekt sind.

Befehl:

```bash
python3 -m compileall src tests
```

Akzeptanzkriterien:

- Keine Syntaxfehler.
- Keine kaputten Importpfade durch pyproject-/Package-Änderungen.

---

## 1.11.b Vollständige Testsuite ausführen

Befehl:

```bash
python3 -m pytest --color=yes
```

Akzeptanzkriterien:

- Alle Tests grün.
- Neue README-/Script-Tests grün.
- Bestehende Exporttests grün.

---

## 1.11.c Build und Twine Check ausführen

Befehle:

```bash
rm -rf dist build src/*.egg-info
python3 -m build
python3 -m twine check dist/*
```

Akzeptanzkriterien:

- Wheel wird gebaut.
- sdist wird gebaut.
- Twine Check ist grün.
- Keine Build-Artefakte werden versehentlich committed.

---

## 1.11.d Isoliertes pipx-Validierungsskript ausführen

Befehl:

```bash
scripts/validate_pipx_release.sh
```

Akzeptanzkriterien:

- Skript installiert RepoDossier aus lokalem Checkout.
- `repodossier --help` funktioniert.
- `repodossier --version` funktioniert.
- `repocontext --help` funktioniert.
- `repocontext --version` funktioniert.
- `full.txt` wird im temporären Sample-Repo erzeugt.
- `ai.txt` wird im temporären Sample-Repo erzeugt.
- `docs.txt` wird im temporären Sample-Repo erzeugt.
- `changed.txt` wird im temporären Sample-Repo erzeugt.
- Temporäre Umgebung wird aufgeräumt.

---

## 1.11.e RepoDossier Selbstexport erzeugen

Ziel:

Nach erfolgreicher Implementierung den aktuellen Projektstand mit RepoDossier selbst prüfen.

Befehle:

```bash
repodossier full
repodossier export-ai
repodossier export-docs
repodossier changed
```

Akzeptanzkriterien:

- `full.txt` wird erzeugt.
- `ai.txt` wird erzeugt.
- `docs.txt` wird erzeugt.
- `changed.txt` wird erzeugt.
- README-Änderungen sind in `docs.txt` sichtbar.
- Keine alten `pipx install -e .` Standardempfehlungen tauchen in den Exports auf.

---

## 1.11.f Git-Status prüfen

Befehle:

```bash
git status --short
git --no-pager diff -- README.md pyproject.toml scripts/validate_pipx_release.sh tests
```

Akzeptanzkriterien:

- Nur erwartete Dateien geändert.
- Keine `dist/`, `build/`, `*.egg-info`, `full.txt`, `ai.txt`, `docs.txt`, `changed.txt` staged.
- Diff ist nachvollziehbar.
- Kein Pager hängt im Terminal.

---

# 1.12 Empfohlene Patch-Reihenfolge

## Patch 1.1 – pyproject cleanup and package sanity

Umfang:

- `pyproject.toml` doppelte Include-Regel bereinigen
- prüfen, dass beide Packages weiterhin paketiert werden
- ggf. Tests für Release-Metadaten minimal ergänzen

Tests:

```bash
python3 -m pytest --color=yes tests/test_public_release_metadata.py tests/test_repodossier_cli_alias.py tests/test_version_cli.py
```

Commit-Vorschlag:

```text
Clean up package include metadata
```

---

## Patch 1.2 – README pipx installation update

Umfang:

- README Hauptinstallation aktualisieren
- Release Usage Guide konsistent machen
- Development install getrennt halten
- `repodossier` als primär und `repocontext` als Legacy erklären
- alte `pipx install -e .` Standardempfehlung entfernen

Tests:

```bash
python3 -m pytest --color=yes tests/test_readme_documentation.py tests/test_readme_configuration_status.py
```

Commit-Vorschlag:

```text
Document robust pipx installation
```

---

## Patch 1.3 – README regression tests

Umfang:

- Tests für `python3 -m pipx install "$PWD"`
- Tests für beide CLI Help/Version Hinweise
- Tests gegen `pipx install -e .`
- Tests für Development Install beibehalten

Tests:

```bash
python3 -m pytest --color=yes tests/test_readme_documentation.py
```

Commit-Vorschlag:

```text
Test documented pipx installation flow
```

---

## Patch 1.4 – Harden pipx release validation script

Umfang:

- isoliertes `PIPX_HOME`
- isoliertes `PIPX_BIN_DIR`
- `python3 -m pipx install "$REPO_ROOT"`
- beide CLI-Namen mit `--help`
- beide CLI-Namen mit `--version`
- temporäres Git-Sample-Repo
- full/ai/docs/changed Smoke-Exports
- klare Script-Ausgaben
- Cleanup

Tests:

```bash
python3 -m pytest --color=yes tests/test_pipx_release_validation_script.py
```

Commit-Vorschlag:

```text
Harden pipx release validation
```

---

## Patch 1.5 – Build and twine release checks

Umfang:

- `python3 -m build`
- `python3 -m twine check dist/*`
- ggf. `build` und `twine` in dev dependencies ergänzen
- Tests für Skriptinhalt ergänzen

Tests:

```bash
python3 -m pytest --color=yes tests/test_pipx_release_validation_script.py tests/test_public_release_metadata.py
```

Commit-Vorschlag:

```text
Add build metadata checks to pipx validation
```

---

## Patch 1.6 – Final milestone documentation and smoke pass

Umfang:

- letzte README-Konsistenz
- ggf. `planning/1.1.0/milestone1.md` hinzufügen
- vollständige Test- und Smoke-Prüfung
- keine generierten Exportdateien committen

Tests:

```bash
python3 -m compileall src tests
python3 -m pytest --color=yes
scripts/validate_pipx_release.sh
```

Commit-Vorschlag:

```text
Finalize pipx installation hardening
```

---

# 1.13 Definition of Done

Milestone 1 gilt als fertig, wenn alle folgenden Punkte erfüllt sind:

1. Die neue Release-Linie wird als `1.1.0` geplant.
2. Die aktive Milestone-Datei liegt unter `planning/1.1.0/milestone1.md`.
3. `pyproject.toml` enthält keine doppelte Include-Regel mehr.
4. `repodossier` bleibt als aktueller CLI-Name paketiert.
5. `repocontext` bleibt als Legacy-CLI-Alias paketiert.
6. README dokumentiert den robusten lokalen pipx-Weg mit `python3 -m pipx install "$PWD"`.
7. README empfiehlt `pipx install -e .` nicht mehr als Standard.
8. README trennt normale pipx-Installation und Development-Install klar.
9. README erklärt `repodossier` als aktuellen Befehl.
10. README erklärt `repocontext` als temporären Legacy-Kompatibilitätsalias.
11. README zeigt Checks für `repodossier --help`.
12. README zeigt Checks für `repodossier --version`.
13. README zeigt Checks für `repocontext --help`.
14. README zeigt Checks für `repocontext --version`.
15. README verweist auf `scripts/validate_pipx_release.sh` als vollständige lokale Release-Validierung.
16. README-Regressionstests sichern den neuen Installationsweg ab.
17. Tests verhindern eine erneute Standardempfehlung von `pipx install -e .`.
18. `scripts/validate_pipx_release.sh` nutzt eine isolierte pipx-Umgebung.
19. Das Validierungsskript setzt `PIPX_HOME`.
20. Das Validierungsskript setzt `PIPX_BIN_DIR`.
21. Das Validierungsskript installiert aus dem lokalen Checkout.
22. Das Validierungsskript nutzt `python3 -m pipx install "$REPO_ROOT"`.
23. Das Validierungsskript nutzt nicht `pipx install -e .`.
24. Das Validierungsskript prüft `repodossier --help`.
25. Das Validierungsskript prüft `repodossier --version`.
26. Das Validierungsskript prüft `repocontext --help`.
27. Das Validierungsskript prüft `repocontext --version`.
28. Das Validierungsskript erzeugt ein temporäres Git-Testrepository.
29. Das Validierungsskript prüft `repodossier full`.
30. Das Validierungsskript prüft `repodossier export-ai`.
31. Das Validierungsskript prüft `repodossier export-docs`.
32. Das Validierungsskript prüft `repodossier changed`.
33. Das Validierungsskript prüft, dass `full.txt` erzeugt wird.
34. Das Validierungsskript prüft, dass `ai.txt` erzeugt wird.
35. Das Validierungsskript prüft, dass `docs.txt` erzeugt wird.
36. Das Validierungsskript prüft, dass `changed.txt` erzeugt wird.
37. Das Validierungsskript prüft optional mindestens einen echten `repocontext`-Subcommand.
38. Das Validierungsskript baut eine frische Distribution mit `python3 -m build`.
39. Das Validierungsskript prüft Paketmetadaten mit `python3 -m twine check dist/*`.
40. Build- und Twine-Abhängigkeiten sind für Entwickler nachvollziehbar verfügbar.
41. Unit-Tests für README-Dokumentation sind grün.
42. Unit-Tests für das pipx-Validierungsskript sind grün.
43. CLI-Smoke-Tests sind grün.
44. `python3 -m compileall src tests` ist grün.
45. `python3 -m pytest --color=yes` ist grün.
46. `scripts/validate_pipx_release.sh` läuft lokal erfolgreich durch.
47. `python3 -m build` läuft erfolgreich durch.
48. `python3 -m twine check dist/*` läuft erfolgreich durch.
49. Keine generierten Exportdateien werden committed.
50. Keine Build-Artefakte werden committed.
51. Keine alten Bundle-/Snapshot-Skripte werden für die Abschlussprüfung verwendet.
52. Abschlussprüfung nutzt RepoDossier CLI selbst.
53. Git-Diff ist klein, nachvollziehbar und auf diesen Milestone fokussiert.
54. Es gibt einen finalen Commit für Milestone 1.

---

# 1.14 Nicht-Ziele für Milestone 1

Folgende Dinge gehören nicht zu Milestone 1:

- Veröffentlichung auf PyPI
- GitHub Release erstellen
- Git Tag erstellen
- Version in `_version.py` erhöhen
- Umstellung auf XML-Exports
- Umbau des internen Export-Modells
- neue Language Detection
- neue Analysefeatures
- Entfernung des Legacy-Alias `repocontext`
- Umbenennung von Paketen
- große CI-Umstrukturierung
- neues Packaging-Backend
- neue Projektstruktur
- Änderungen an Exportformaten außer Smoke-Test-Relevanz
- Änderungen an Secret Detection
- Änderungen an Split Export Logik
- neue Konfigurationsfeatures

Diese Themen bleiben späteren Milestones oder Release-Schritten vorbehalten.

---

# 1.15 Risiken und Gegenmaßnahmen

## Risiko: repocontext fällt aus der Distribution

Gegenmaßnahme:

- Wheel-Inhalt prüfen.
- CLI-Alias-Tests laufen lassen.
- `repocontext --help` und `repocontext --version` im pipx-Skript prüfen.

## Risiko: README enthält widersprüchliche Installationswege

Gegenmaßnahme:

- Alle pipx-Stellen in README prüfen.
- README-Tests für erlaubte und unerlaubte Strings ergänzen.
- Release Usage Guide nicht vergessen.

## Risiko: pipx-Test verschmutzt echte Nutzerumgebung

Gegenmaßnahme:

- Temporäres `PIPX_HOME`.
- Temporäres `PIPX_BIN_DIR`.
- Cleanup per trap.
- Kein globales `pipx uninstall`, außer in der manuellen README-Anleitung.

## Risiko: Export-Smoke-Test verschmutzt echtes Repo

Gegenmaßnahme:

- Temporäres Git-Sample-Repo.
- Export-Kommandos nur dort ausführen.
- Keine Testexporte im RepoDossier-Root.

## Risiko: Build/Twine fehlen in Entwicklungsumgebung

Gegenmaßnahme:

- Dev Dependencies ergänzen oder klare Fehlermeldung dokumentieren.
- README erklärt vollständige Release-Validierung.
- Validierungsskript prüft verständlich.

---

# 1.16 Abschlussnotiz

Dieser Milestone ist absichtlich klein und stabilisierend.

Er soll keine neue Export-Architektur einführen, sondern sicherstellen, dass RepoDossier als lokales CLI-Tool robust installiert, geprüft und dokumentiert werden kann.

Nach Abschluss dieses Milestones ist die Grundlage gelegt, damit die folgenden 1.1.0-Milestones auf einer sauber installierbaren CLI aufbauen können.
