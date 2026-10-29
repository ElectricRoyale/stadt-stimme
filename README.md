# StadtStimme

Digitale Bürgerbeteiligung für Kommunen: Bürgerinnen und Bürger verteilen 100 Punkte auf
Einrichtungen und Themen, um die sich ihre Stadt als Nächstes kümmern soll. Die Ergebnisse werden öffentlich mit den
Ausgaben der Kommune verglichen.

> **Stand:** Phase 4 (Übersicht, Ergebnisse, Vorschläge). Einrichtungen, Gebäude, Maßnahmen und Ausgaben lassen sich
> im Admin pflegen und per CSV importieren. Bürgerinnen und Bürger melden sich mit dem Code aus dem
> Brief an und verteilen ihre 100 Punkte unter `/verteilen/`. Die öffentliche Übersicht unter
> `/uebersicht/` zeigt die Punkte auf einer Karte, `/ergebnisse/` den Unterschied zwischen Wunsch
> und Ausgaben je Einrichtung. Unter `/vorschlaege/` reichen sie eigene Vorschläge ein.

## Schnellstart

Voraussetzung ist nur [Docker](https://docs.docker.com/get-docker/) (Docker Desktop unter
macOS/Windows, inklusive Apple Silicon).

```bash
docker compose up
```

Beim ersten Start wird das Image gebaut; das dauert einige Minuten. Im Demo-Modus werden
die fiktiven Daten „Musterstadt“ automatisch in den leeren Katalog geladen. Danach:

| Was | Adresse | Zugang |
| --- | --- | --- |
| StadtStimme | http://localhost:8000 | – |
| Admin (nur Demo-Modus) | http://localhost:8000/admin/ | `demo` / `demo` |
| Mailpit (abgefangene E-Mails) | http://localhost:8025 | – |
| Health-Check | http://localhost:8000/healthz/ | – |

Zum Ausprobieren des Bürger-Zugangs unter http://localhost:8000/zugang/ gibt es fünf fiktive
Demo-Codes (nur im Demo-Modus angelegt):

```text
3N80-JG4V-WS61-P663
JTRP-0A7Y-CD7J-AGFR
Q4QM-6HTY-N1Y9-T9VY
DGKW-1BKK-H8BN-ZTPE
TBB1-A4YV-A4ZC-J8HR
```

Beenden mit `Strg+C`, alles inklusive Datenbank löschen mit `docker compose down -v`.

Sind Ports belegt, lassen sie sich über eine `.env`-Datei ändern (Vorlage: `.env.example`).

Das Projekt sollte nicht in einem synchronisierten Cloud-Ordner liegen (OneDrive, iCloud,
Dropbox). Docker darf solche Ordner unter macOS oft nicht lesen und bricht beim Bauen mit einer
Rechte-Abfrage ab.

> **Demo-Modus:** Die Standardwerte sind nur für die lokale Vorführung gedacht. Alle Ports sind
> an `127.0.0.1` gebunden, der Admin-Zugang ist ein Demo-Zugang. Nicht öffentlich betreiben.

## Daten pflegen und importieren

Im Admin unter **Katalog** lassen sich Kategorien, Einrichtungen, Gebäude, Maßnahmen und
Ausgaben bearbeiten. Jede Liste hat **Importieren** (CSV mit Vorschau vor dem Speichern) und
**Exportieren**. Beim Import über die Oberfläche gilt die Reihenfolge Einrichtungen,
Gebäude, Maßnahmen, Ausgaben.

Alle vier Dateien auf einmal, in einer Transaktion (bei einem Fehler wird nichts gespeichert):

```bash
docker compose exec app python manage.py import_catalog data/demo --dry-run   # nur prüfen
docker compose exec app python manage.py import_catalog data/demo             # speichern
```

Der Import ist wiederholbar: Zeilen werden über die externe ID aktualisiert statt doppelt
angelegt. Das Dateiformat beschreibt [data/demo/README.md](data/demo/README.md).

## Zugang per Code

Der Code aus dem Brief ist vorerst zugleich der Login (ADR-001; Gerätebindung, Druckexport
und Sperren sind bis zur Teamabstimmung zurückgestellt). Wer ihn auf einem zweiten Gerät
eingibt, landet im selben Zugang.

- Codes haben 16 Zeichen Crockford-Base32 (80 Bit). Gespeichert wird nur ein HMAC-Hash.
- Nach 10 Fehlversuchen pro IP-Adresse ist das Einlösen eine Stunde gesperrt. Die IP-Adresse
  wird dafür nur als Hash gespeichert.
- Test-Codes erzeugen (der Klartext erscheint nur in dieser Ausgabe):

```bash
docker compose exec app python manage.py create_access_codes 20 --batch "Test" > codes.csv
```

Für den Betrieb einen eigenen `STADTSTIMME_CODE_PEPPER` setzen und nie wieder ändern: Ein
neuer Wert macht alle ausgegebenen Codes ungültig. Ohne eigenen Wert gilt `DJANGO_SECRET_KEY`.

## Punkte verteilen

Jede Person hat 100 Punkte und gibt sie an Einrichtungen oder an ein ganzes Thema
(„Sport allgemein“, ADR-011). Sie kann jederzeit umverteilen. Punkte verfallen nach
183 Tagen ohne Aktivität (ADR-003, `STADTSTIMME_POINTS_EXPIRY_DAYS`). Ergebnisse zählen
verfallene Punkte sofort nicht mehr mit. Gelöscht werden sie, sobald die Person zurückkommt,
oder mit diesem Befehl (z. B. täglich per Cron):

```bash
docker compose exec app python manage.py expire_points
```

## Übersicht, Ergebnisse und Karte

`/uebersicht/` und `/ergebnisse/` sind ohne Code erreichbar. Pro Thema steht der Anteil der Punkte neben dem Anteil
an den Ist-Ausgaben des letzten abgeschlossenen Haushaltsjahres (ADR-006, ADR-012). Die Karte
zeigt Einrichtungen mit Koordinaten (Spalten `latitude`, `longitude` im CSV, optional).
`/ergebnisse/` zeigt je Einrichtung und je Thema die Lücke in Prozentpunkten: Anteil der
Bürgerpunkte minus Anteil der Ist-Ausgaben (ADR-013).

Leaflet liegt im Repo, die Kartenkacheln lädt der Browser direkt von OpenStreetMap. Dabei geht
die IP-Adresse an den Kachelserver; das gehört in die Datenschutzerklärung. Ein anderer
Kachelserver lässt sich über `STADTSTIMME_MAP_TILE_URL` und `STADTSTIMME_MAP_ATTRIBUTION` setzen.

## Vorschläge

Unter `/vorschlaege/` reicht man mit Code einen Vorschlag in drei Schritten ein: Anliegen,
Einordnen (Thema, optional ein bekannter Ort), Prüfen. Die Verwaltung schaltet Vorschläge im
Admin unter **Vorschläge** frei oder lehnt sie ab. Erst freigegebene Vorschläge erscheinen beim
Schreiben als „Gibt es schon ähnlich“ und können unterstützt werden (ADR-014).

| Einstellung | Standard |
| --- | --- |
| `STADTSTIMME_PROPOSAL_REVIEW_DAYS` (Prüffrist, wird angezeigt) | 14 |
| `STADTSTIMME_PROPOSAL_SUPPORT_THRESHOLD` (Schwelle, wird angezeigt) | 50 |
| `STADTSTIMME_PROPOSALS_PER_DAY` (Limit je Zugang) | 5 |

## Entwicklung

Python 3.12+ und Docker.

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

docker compose up -d db mailpit      # nur Datenbank und Mailpit starten
export DJANGO_DEBUG=true             # Windows: set DJANGO_DEBUG=true
python manage.py migrate
python manage.py import_catalog data/demo
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
apps/core/       Einstieg (Weiterleitung), Health-Check, Demo-Admin-Befehl
apps/catalog/    Einrichtungen, Gebäude, Maßnahmen, Ausgaben; CSV-Import und Admin
apps/access/     Aktivierungscodes, Code-Login, Sperre nach Fehlversuchen
apps/points/     Punkte verteilen, Verfall
apps/reporting/  Öffentliche Übersicht und Ergebnisse: Vergleich, Karte
apps/proposals/  Vorschläge einreichen, freigeben, unterstützen
templates/       Basis-Template (mobile-first, deutsch)
static/          CSS, Schrift und kleine Skripte ohne Build-Schritt
data/demo/       Fiktive Demo-Daten „Musterstadt“
docker/          Entrypoint: Migrationen, Demo-Admin, Start
docs/            Entscheidungen (ADRs)
```

Fachliche Module kommen phasenweise als eigene Django-Apps dazu, als Nächstes
`notifications`. Fachlogik liegt jeweils in `services.py`, Views bleiben dünn.

## Fahrplan

| Phase | Inhalt | Gate |
| --- | --- | --- |
| 0 | Fundament | CI grün, Start mit `docker compose up` |
| 1 | Katalog: Einrichtungen, Gebäude, Maßnahmen, Ausgaben, CSV-Import | Demo-Daten vollständig importiert |
| 2 | Code-Login (Zwischenlösung) | Rate-Limit greift, kein Code im Klartext |
| 3 | Punktevergabe | 5 Testpersonen in unter 5 Minuten |
| 4 | Transparenz: Ergebnisse, Vergleich, Stichtags-Export | Stichtagswerte reproduzierbar |
| 5 | Benachrichtigungen (Verfall bereits in Phase 3, Rückfluss entfällt laut ADR-011) | Job-Tests grün |
| 6 | Zugang final, Barrierefreiheit, Datenschutz, Pilot | Freigabe Datenschutz |

Entscheidungen: [docs/DECISIONS.md](docs/DECISIONS.md)
