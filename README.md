# StadtStimme

Digitale Bürgerbeteiligung für Kommunen: Bürgerinnen und Bürger verteilen 100 Punkte auf Vorhaben,
um die sich ihre Stadt als Nächstes kümmern soll. Die Ergebnisse werden öffentlich mit den
Ausgaben der Kommune verglichen.

> **Stand:** Phase 0 (Fundament). Projektgerüst, Start per Docker, CI und Demo-Daten.
> Fachfunktionen folgen ab Phase 1.

## Schnellstart

Voraussetzung ist nur [Docker](https://docs.docker.com/get-docker/) (Docker Desktop unter
macOS/Windows, inklusive Apple Silicon).

```bash
docker compose up
```

Beim ersten Start wird das Image gebaut; das dauert einige Minuten. Danach:

| Was | Adresse | Zugang |
| --- | --- | --- |
| StadtStimme | http://localhost:8000 | – |
| Admin (nur Demo-Modus) | http://localhost:8000/admin/ | `demo` / `demo` |
| Mailpit (abgefangene E-Mails) | http://localhost:8025 | – |
| Health-Check | http://localhost:8000/healthz/ | – |

Beenden mit `Strg+C`, alles inklusive Datenbank löschen mit `docker compose down -v`.

Sind Ports belegt, lassen sie sich über eine `.env`-Datei ändern (Vorlage: `.env.example`).

> **Demo-Modus:** Die Standardwerte sind nur für die lokale Vorführung gedacht. Alle Ports sind
> an `127.0.0.1` gebunden, der Admin-Zugang ist ein Demo-Zugang. Nicht öffentlich betreiben.

## Entwicklung

Python 3.12+ und Docker.

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

docker compose up -d db mailpit      # nur Datenbank und Mailpit starten
export DJANGO_DEBUG=true             # Windows: set DJANGO_DEBUG=true
python manage.py migrate
python manage.py runserver
```

Qualitätsprüfungen (laufen auch in der CI):

```bash
ruff check . && ruff format --check .   # Lint und Formatierung
mypy .                                  # Typprüfung
pytest                                  # Tests gegen PostgreSQL
```

## Projektstruktur

```
config/          Einstellungen (alles über Umgebungsvariablen), URLs, WSGI
apps/core/       Startseite, Health-Check, Demo-Admin-Befehl
templates/       Basis-Template (mobile-first, deutsch)
static/          CSS ohne Build-Schritt
data/demo/       Fiktive Demo-Daten „Musterstadt“
docker/          Entrypoint: Migrationen, Demo-Admin, Start
docs/            Entscheidungen (ADRs)
```

Fachliche Module kommen phasenweise als eigene Django-Apps dazu: `catalog`, `access`, `voting`,
`reporting`, `notifications`. Fachlogik liegt jeweils in `services.py`, Views bleiben dünn.

## Fahrplan

| Phase | Inhalt | Gate |
| --- | --- | --- |
| 0 | Fundament | CI grün, Start mit `docker compose up` |
| 1 | Katalog: Einrichtungen, Maßnahmen, Ausgaben, CSV-Import | Demo-Daten vollständig importiert |
| 2 | Code-Login (Zwischenlösung) | Rate-Limit greift, kein Code im Klartext |
| 3 | Punktevergabe | 5 Testpersonen in unter 5 Minuten |
| 4 | Transparenz: Ergebnisse, Vergleich, Stichtags-Export | Stichtagswerte reproduzierbar |
| 5 | Rückfluss, Verfall, Benachrichtigungen | Job-Tests grün |
| 6 | Zugang final, Barrierefreiheit, Datenschutz, Pilot | Freigabe Datenschutz |

Entscheidungen: [docs/DECISIONS.md](docs/DECISIONS.md)
