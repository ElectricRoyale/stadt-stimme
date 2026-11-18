# Architekturanforderungen – StadtStimme

Dieses Dokument beschreibt, **wie** StadtStimme gebaut sein muss: Technologie, Struktur,
Sicherheit, Datenschutz, Betrieb und Qualität. Die fachlichen Anforderungen stehen in
[functional-requirements.md](functional-requirements.md) (FR-…). Abgeleitet aus dem Code
(`config/`, `apps/`, `compose.yaml`, CI), der README und [docs/DECISIONS.md](../docs/DECISIONS.md).

- **Verbindlichkeit:** Akzeptierte ADRs gehen vor; der Bezug steht in Klammern.
- **Prüfbarkeit:** Jede Anforderung nennt, woran ihre Einhaltung erkennbar ist (**Nachweis**).
- **Prioritäten:** *Muss* = Voraussetzung für Pilot und Datenschutzfreigabe. *Soll* = wichtig für
  Wartbarkeit und Betrieb. *Kann* = Ausbaustufe oder erst bei Bedarf.

Format pro Anforderung: Beschreibung, Begründung, Nachweis, Priorität.

---

## 1. Technologie-Stack

### AR-001: Django, PostgreSQL, serverseitiges Rendering
**Beschreibung:** Die Anwendung ist ein Django-Monolith (Python ≥ 3.12) mit PostgreSQL als
einziger Datenbank. Seiten werden serverseitig mit Django-Templates gerendert; kein
Single-Page-Framework, kein Build-Schritt für das Frontend (ADR-007).
**Begründung:** Kleines Team, überschaubare Datenmenge, ein Deployment-Artefakt.
**Nachweis:** `requirements.txt`, `Dockerfile`, keine Node-Abhängigkeit im Build.
**Priorität:** Muss

### AR-002: JavaScript nur als Verbesserung
**Beschreibung:** Kernabläufe (Anmelden, Punkte verteilen und speichern, Vorschlag einreichen,
Ergebnisse lesen, Verwaltung entscheiden) funktionieren ohne JavaScript. Skripte in
`static/js/` sind kleine, seitenbezogene Module ohne Framework und ergänzen Karte, Filter und
Live-Rückmeldung (ADR-016, ADR-026, ADR-028).
**Begründung:** Barrierefreiheit, Robustheit auf alten Geräten, kein Lock-in.
**Nachweis:** View-Tests arbeiten mit normalen Formular-POSTs; Formulare haben echte `action`.
**Priorität:** Muss

### AR-003: Keine Laufzeit-Abhängigkeit von Drittanbieter-CDNs
**Beschreibung:** Schriften, Leaflet und alle Skripte liegen selbst gehostet im Repository und
werden über WhiteNoise ausgeliefert. Einzige externe Anfrage aus dem Browser sind Kartenkacheln;
der Kachelserver ist konfigurierbar und hat einen Ersatz (ADR-010, ADR-015, ADR-018).
**Begründung:** Datenschutz (keine IP-Weitergabe an Google Fonts o. Ä.), Ausfallsicherheit.
**Nachweis:** Keine externen `<script>`/`<link>`-URLs in `templates/`.
**Priorität:** Muss

### AR-004: Neue Abhängigkeiten nur mit Begründung
**Beschreibung:** Eine neue Bibliothek wird nur aufgenommen, wenn der Standard von Django oder
eine vorhandene Abhängigkeit das Problem nicht vertretbar löst; die Entscheidung steht in
DECISIONS.md (Beispiel: eigenes Rate-Limit statt django-ratelimit, ADR-009).
**Begründung:** Wartungs- und Sicherheitsaufwand pro Abhängigkeit.
**Nachweis:** Review; ADR-Eintrag bei jeder neuen Laufzeit-Abhängigkeit.
**Priorität:** Soll

---

## 2. Struktur und Schichten

### AR-005: Fachliche Module als Django-Apps
**Beschreibung:** Jede fachliche Domäne ist eine eigene App unter `apps/`: `access` (Zugang),
`catalog` (Katalog), `points` (Punkte, Ereignis-Log), `proposals` (Vorschläge), `reporting`
(öffentliche Auswertung), `notifications` (E-Mail), `cityadmin` (Verwaltungsseite), `core`
(Einstieg, Health-Check). Neue Domänen kommen als neue App hinzu.
**Begründung:** Hohe Kohäsion, klare Zuständigkeit, getrennt testbar.
**Nachweis:** `INSTALLED_APPS`, Ordnerstruktur.
**Priorität:** Muss

### AR-006: Fachlogik in Services, dünne Views
**Beschreibung:** Geschäftsregeln (Budget, Rückfluss, Verfall, Entscheiden, Einlösen) liegen in
Service-Modulen (`services.py`, `ledger.py`, `returns.py` …). Views lesen Eingaben, rufen
Services und rendern; Templates enthalten keine Fachlogik. Fachfehler werden als eigene
Exceptions signalisiert (z. B. `BudgetExceededError`, `DecisionError`).
**Begründung:** Testbarkeit ohne HTTP, Wiederverwendung aus Admin, Befehlen und Signalen.
**Nachweis:** Service-Tests je App; keine ORM-Schreibzugriffe mit Fachregeln in `views.py`.
**Priorität:** Muss

### AR-007: Gerichtete Abhängigkeiten zwischen Apps
**Beschreibung:** Abhängigkeiten zeigen von außen nach innen: `catalog` und `access` hängen von
keiner anderen Fach-App ab; `points` und `proposals` nutzen nur diese beiden; `reporting`,
`notifications` und `cityadmin` dürfen lesen, was sie darstellen. Zyklen sind unzulässig.
Reaktionen über App-Grenzen (z. B. Rückfluss → E-Mail) laufen über Django-Signale statt
direkte Aufrufe.
**Begründung:** Geringe Kopplung, Änderungen bleiben lokal.
**Nachweis:** Import-Analyse im Review; keine Imports aus `reporting`/`cityadmin` in Kern-Apps.
**Priorität:** Soll

### AR-008: Eine Quelle je abgeleitetem Wert
**Beschreibung:** Jede Kennzahl hat genau eine Berechnung, die alle Seiten nutzen (z. B.
Ist-Ausgaben je Einrichtung nur aus `apps/catalog/spending.py`, Anteile und Lücken aus
`apps/reporting/statistics.py`) (ADR-015).
**Begründung:** Übersicht, Ergebnisse, Export und Verwaltung dürfen sich nie widersprechen.
**Nachweis:** Keine doppelte Aggregation in Views oder Templates.
**Priorität:** Muss

### AR-009: Konfiguration über Umgebungsvariablen
**Beschreibung:** Alle umgebungs- und kommunenabhängigen Werte (Secrets, Datenbank, Mail,
Kachelserver, Stadtname, Fristen, Schwellen, Limits) kommen aus Umgebungsvariablen mit
sicherem Standardwert (`config/env.py`). Fachliche Konstanten mit Produktbedeutung sind
benannt und dokumentiert, nicht im Code verstreut.
**Begründung:** Eine Codebasis für mehrere Kommunen und Umgebungen (12-Factor).
**Nachweis:** `.env.example`, README-Tabellen.
**Priorität:** Muss

---

## 3. Daten und Konsistenz

### AR-010: Integrität in der Datenbank absichern
**Beschreibung:** Invarianten werden zusätzlich zur Anwendungslogik als Datenbank-Constraints
erzwungen, z. B. genau ein Ziel je Vergabe, eine Vergabe je Ziel und Zugang, eine
Unterstützung je Vorschlag und Zugang, nie Einrichtung und Punkt zugleich am Vorschlag,
Delta ≠ 0 im Ereignis-Log.
**Begründung:** Schutz vor Fehlern in Admin, Import und parallelen Anfragen.
**Nachweis:** `CheckConstraint`/`UniqueConstraint` in den Models, Tests auf Verletzung.
**Priorität:** Muss

### AR-011: Ereignis-Log als Quelle, Read Model für den Alltag
**Beschreibung:** Punkteänderungen werden als unveränderliche Ereignisse in derselben
Transaktion wie das Read Model (`Allocation`) geschrieben. UPDATE und DELETE auf dem Log
verbietet ein Datenbank-Trigger. Stichtagswerte werden aus dem Log berechnet. Weitere
abgeleitete Tabellen erst, wenn Messungen sie nötig machen (ADR-005, ADR-027).
**Begründung:** Nachvollziehbarkeit gegenüber Gemeinderat, reproduzierbare Stichtage.
**Nachweis:** Migration mit Trigger, `test_ledger.py`, `test_snapshot.py`.
**Priorität:** Muss

### AR-012: Nebenläufigkeit kontrolliert behandeln
**Beschreibung:** Operationen, die Budget oder Codes betreffen, laufen in Transaktionen mit
Zeilensperren in fester Reihenfolge (`select_for_update`), damit weder Doppel-Einlösen noch
Budgetüberschreitung noch Deadlocks entstehen (ADR-027).
**Begründung:** Gleichzeitige Nutzung desselben Codes auf mehreren Geräten ist vorgesehen.
**Nachweis:** `test_concurrency.py`.
**Priorität:** Muss

### AR-013: Schemaänderungen nur über Migrationen
**Beschreibung:** Jede Model-Änderung hat eine Migration; Datenmigrationen überführen
bestehende Daten (z. B. Statuswechsel ADR-025). Fehlende Migrationen brechen die CI.
**Begründung:** Reproduzierbare Datenbankstände, sichere Updates im Betrieb.
**Nachweis:** `makemigrations --check` in der CI.
**Priorität:** Muss

### AR-014: Idempotente Importe und Hintergrundaufgaben
**Beschreibung:** CSV-Import (über externe ID), tägliche Aufgaben und Demo-Daten-Laden lassen
sich beliebig oft ausführen, ohne Daten zu verdoppeln oder Ereignisse doppelt zu erzeugen
(ADR-028).
**Begründung:** Wiederholung nach Abbruch muss gefahrlos sein.
**Nachweis:** `test_import.py`, `test_expiry.py`, `test_commands.py`.
**Priorität:** Muss

---

## 4. Sicherheit

### AR-015: Geheimnisse nie im Klartext speichern
**Beschreibung:** Codes und Bestätigungs-Tokens nur als Hash (HMAC mit Pepper), IP-Adressen
nur als Hash, E-Mail-Adressen verschlüsselt (Fernet). Schlüssel kommen aus der Umgebung und
werden im Betrieb nie geändert; ohne eigenen Wert gilt `DJANGO_SECRET_KEY` (ADR-001, ADR-028).
**Begründung:** Ein Datenbank-Leak darf keine Zugänge und keine Kontaktdaten offenlegen.
**Nachweis:** Model-Felder, Tests auf Hash-/Chiffrat-Speicherung.
**Priorität:** Muss

### AR-016: Sichere HTTP-Standards
**Beschreibung:** CSRF-Schutz für alle zustandsändernden Anfragen, nur POST für Änderungen,
`HttpOnly`-Cookies, `Secure`-Cookies im Betrieb (`DJANGO_SECURE_COOKIES`), `X-Frame-Options:
DENY`, `nosniff`, `Referrer-Policy: same-origin`. Im Betrieb zusätzlich HTTPS-Weiterleitung,
HSTS und eine Content-Security-Policy.
**Begründung:** Schutz gegen CSRF, Clickjacking, Session-Diebstahl, XSS.
**Nachweis:** `config/settings.py`, `manage.py check --deploy` ohne Warnungen im Betrieb.
**Priorität:** Muss

### AR-017: Missbrauch begrenzen
**Beschreibung:** Öffentliche Eingänge mit Missbrauchspotenzial sind begrenzt: Fehlversuche beim
Anmelden (atomar in PostgreSQL, ADR-009), Vorschläge je Tag und Zugang, Bestätigungsmails je
10 Minuten. Neue öffentliche Schreibfunktionen brauchen ein vergleichbares Limit.
**Begründung:** Brute Force auf Codes, Spam, Mail-Bombing.
**Nachweis:** Tests je Limit.
**Priorität:** Muss

### AR-018: Rechte nach dem Minimalprinzip
**Beschreibung:** Verwaltungsfunktionen prüfen Mitarbeiter-Status und das konkrete Django-Recht
der Aktion („Vorschlag ändern“, „Einrichtung ändern“). Admin und Verwaltungsseite sind ohne
Demo-Modus nicht geroutet, bis das Admin-Login-Konzept steht (ADR-026).
**Begründung:** Trennung von Lesen und Entscheiden im Team der Stadt.
**Nachweis:** `config/urls.py`, View-Tests mit und ohne Recht.
**Priorität:** Muss

### AR-019: Ausgaben gegen Injektion schützen
**Beschreibung:** Templates escapen automatisch; `|safe` nur für selbst erzeugtes Markup. CSV-
Exporte schützen Texte gegen Formel-Injektion.
**Begründung:** Vorschlagstexte sind ungeprüfte Bürgereingaben und sofort öffentlich (ADR-025).
**Nachweis:** `apps/reporting/export.py`, Tests mit `=`-Präfix.
**Priorität:** Muss

---

## 5. Datenschutz (DSGVO)

### AR-020: Datensparsamkeit und Pseudonymität
**Beschreibung:** Ein Zugang kennt keinen Namen, keine Adresse und keine Klartext-IP. Die
Verbindung zur Person besteht nur über den Brief der Stadt. Neue personenbezogene Felder
brauchen einen dokumentierten Zweck.
**Begründung:** Art. 5 DSGVO (Datenminimierung); Vertrauen in die Beteiligung.
**Nachweis:** Models in `apps/access`, Review neuer Felder.
**Priorität:** Muss

### AR-021: Trennung von Kontaktdaten und Beteiligung
**Beschreibung:** E-Mail-Adressen liegen in einer eigenen Tabelle, verschlüsselt, nur nach
Double-Opt-in genutzt und werden beim Abmelden oder Löschen des Zugangs entfernt. Das
Ereignis-Log bleibt beim Löschen eines Zugangs pseudonym erhalten (ADR-004, ADR-027, ADR-028).
**Begründung:** Zweckbindung; Auswertung ohne Personenbezug.
**Nachweis:** `apps/notifications/models.py`, Löschtests.
**Priorität:** Muss

### AR-022: Nur aggregierte Auswertung für die Verwaltung
**Beschreibung:** Verwaltung und Öffentlichkeit sehen Beteiligung und Punkte nur als Summen.
Keine Ansicht zeigt, wie ein einzelner Zugang verteilt hat (ADR-026).
**Begründung:** Schutz vor Rückschlüssen auf Einzelne, insbesondere bei kleinen Chargen.
**Nachweis:** Templates und Querysets in `cityadmin` und `reporting`.
**Priorität:** Muss

### AR-023: Datenflüsse an Dritte dokumentieren
**Beschreibung:** Jede Übermittlung an Dritte (derzeit: IP an den Kachelserver, E-Mails an den
SMTP-Dienst) ist in README und Datenschutzerklärung benannt und konfigurierbar. Für den
Regelbetrieb: eigener Kachelserver oder Vertrag (ADR-012, ADR-018).
**Begründung:** Informationspflicht Art. 13 DSGVO, Auftragsverarbeitung.
**Nachweis:** README-Abschnitt „Karte“, Datenschutzerklärung (Phase 6).
**Priorität:** Muss

---

## 6. Performance und Skalierung

### AR-024: Antwortzeiten bei kommunaler Last
**Beschreibung:** Öffentliche Seiten und „Punkte verteilen“ antworten bei einer Großstadt im
Pilot (Größenordnung 10⁴ Zugänge, 10² Einrichtungen) serverseitig in unter 500 ms (p95). Listen
werden ohne N+1-Abfragen geladen (`select_related`/`prefetch_related`, Aggregation in SQL).
**Begründung:** Mobile Nutzung über schwache Verbindungen; Ergebnisse werden live berechnet.
**Nachweis:** Abfragezahl in Tests (`django_assert_num_queries`), Lasttest vor dem Pilot.
**Priorität:** Soll

### AR-025: Zuerst messen, dann cachen
**Beschreibung:** Ergebnisse werden live aus dem Read Model berechnet. Caches oder zusätzliche
Summentabellen werden erst eingeführt, wenn Messungen das belegen, und dann mit klarer
Invalidierung (ADR-027).
**Begründung:** Abgeleitete Daten können auseinanderlaufen; YAGNI.
**Nachweis:** ADR bei Einführung eines Caches.
**Priorität:** Soll

### AR-026: Horizontal skalierbarer App-Prozess
**Beschreibung:** Der App-Prozess ist zustandslos: Sitzungen, Rate-Limits und Sperren liegen in
PostgreSQL, nicht im Arbeitsspeicher. Mehrere App-Instanzen hinter einem Proxy sind ohne
Codeänderung möglich; der Scheduler läuft genau einmal.
**Begründung:** Lastspitzen nach dem Briefversand.
**Nachweis:** Keine prozesslokalen Caches mit Fachzustand.
**Priorität:** Kann

---

## 7. Deployment und Betrieb

### AR-027: Start mit einem Befehl
**Beschreibung:** `docker compose up` startet App, Datenbank, Scheduler und Mailpit vollständig;
der Entrypoint migriert und lädt im Demo-Modus Testdaten. Alle Ports sind lokal an `127.0.0.1`
gebunden. Die CI prüft diesen Start (ADR-007).
**Begründung:** Gate von Phase 0; einfache Vorführung in Kommunen.
**Nachweis:** CI-Job „Plug and Play“.
**Priorität:** Muss

### AR-028: Demo-Modus strikt vom Betrieb getrennt
**Beschreibung:** Demo-Zugänge, Demo-Daten, Admin und Verwaltungsseite sind nur bei gesetztem
Demo-Modus aktiv. Ohne ihn startet die Anwendung nur mit eigenen Secrets.
**Begründung:** Demo-Zugang `demo`/`demo` darf nie öffentlich erreichbar sein.
**Nachweis:** `config/urls.py`, Tests ohne Demo-Modus.
**Priorität:** Muss

### AR-029: Beobachtbarkeit
**Beschreibung:** Ein Health-Check prüft App und Datenbank. Logs gehen strukturiert auf stdout
(Level über `DJANGO_LOG_LEVEL`) und enthalten keine Codes, Tokens, E-Mail-Adressen oder IPs.
Fehler externer Dienste (SMTP, Kacheln) werden geloggt, brechen aber keine fachliche Aktion ab.
**Begründung:** Betrieb ohne Zugriff auf personenbezogene Daten.
**Nachweis:** `/healthz/`, Review der Log-Aufrufe.
**Priorität:** Soll

### AR-030: Hintergrundaufgaben ohne zusätzliche Infrastruktur
**Beschreibung:** Zeitgesteuerte Aufgaben laufen als Management-Befehle im Compose-Dienst
`scheduler`, ohne cron und ohne Message-Broker. Eine Warteschlange kommt erst, wenn der
Mailversand das nötig macht (ADR-028).
**Begründung:** Wenige, tägliche Aufgaben rechtfertigen keinen Broker.
**Nachweis:** `docker/daily.sh`, `run_daily_tasks`.
**Priorität:** Soll

---

## 8. Qualität, Tests und Wartbarkeit

### AR-031: Qualitätsprüfungen als Merge-Voraussetzung
**Beschreibung:** Jeder Pull Request besteht Ruff (Lint und Format), Mypy im Strict-Modus,
`manage.py check`, die Migrationsprüfung und die Tests gegen PostgreSQL (nicht SQLite).
**Begründung:** Constraints und Trigger lassen sich nur gegen PostgreSQL verlässlich testen.
**Nachweis:** `.github/workflows/ci.yml`, `pyproject.toml`.
**Priorität:** Muss

### AR-032: Testabdeckung nach Risiko
**Beschreibung:** Jede Geschäftsregel aus FR-… hat mindestens einen Service-Test; sicherheits-
und integritätskritische Teile (Einlösen, Budget, Rückfluss, Verfall, Log, Entscheiden) haben
zusätzlich Tests für Fehlerfälle und Nebenläufigkeit. Views werden auf Rechte und Statuscodes
getestet.
**Begründung:** Fehler hier verfälschen das Beteiligungsergebnis.
**Nachweis:** `apps/*/tests/`.
**Priorität:** Muss

### AR-033: Überschaubare Module
**Beschreibung:** Dateien bleiben unter etwa 400 Zeilen; Templates werden in Partials
(`_*.html`) zerlegt. Namen im Code sind englisch, Texte für Nutzer deutsch und in Templates.
**Begründung:** Lesbarkeit und Review-Aufwand.
**Nachweis:** Review.
**Priorität:** Soll

### AR-034: Entscheidungen dokumentieren
**Beschreibung:** Architektur- und Produktentscheidungen stehen als ADR in `docs/DECISIONS.md`.
Überholte Entscheidungen werden als ersetzt markiert, nicht gelöscht. Änderungen an
Schnittstellen, Datenmodell oder Regeln aktualisieren README und Anforderungen im selben PR.
**Begründung:** Projekt wächst über Phasen und Bearbeiter hinweg.
**Nachweis:** DECISIONS.md, PR-Review.
**Priorität:** Muss

### AR-035: Designsystem als einzige Stilquelle
**Beschreibung:** Farben, Abstände und Schriften kommen aus den Design-Tokens
(`static/css/tokens*.css`); keine fest codierten Werte in Komponenten-CSS. Themenfarben werden
aus `Category.color` abgeleitet (ADR-010, ADR-015, ADR-017).
**Begründung:** Konsistente Oberfläche, Anpassbarkeit für andere Kommunen.
**Nachweis:** Review des CSS auf fest codierte Werte.
**Priorität:** Soll

### AR-036: Barrierefreiheit nach WCAG 2.1 AA
**Beschreibung:** Alle Seiten erfüllen WCAG 2.1 AA (Pflicht für öffentliche Stellen nach BITV
2.0): semantisches HTML, Tastaturbedienung, sichtbarer Fokus, ausreichende Kontraste, Karten
mit gleichwertiger Liste (ADR-012), responsives Layout ab 320 px.
**Begründung:** Gesetzliche Pflicht für kommunale Angebote; alle Bürger sollen teilnehmen.
**Nachweis:** Accessibility-Audit vor dem Pilot (Phase 6).
**Priorität:** Muss

---

## Offene Punkte und erkannte Abweichungen

- **CSP und HSTS fehlen** (AR-016): In `config/settings.py` sind weder Content-Security-Policy
  noch HSTS/HTTPS-Weiterleitung gesetzt. *Relevant* vor dem öffentlichen Betrieb.
- **htmx aus ADR-007 ist nicht eingebunden:** Die Oberfläche nutzt kleine eigene Skripte
  (ADR-028 nennt das). ADR-007 sollte neu bewertet und angepasst werden. *Optional.*
- **Kopplung über `access.views`** (AR-007): `points` und `notifications` importieren den
  Decorator `participant_required` aus `apps/access/views.py`. Sauberer wäre ein eigenes Modul
  (z. B. `apps/access/decorators.py`). *Optional.*
- **Leistungsziel AR-024** ist ein Vorschlag ohne Messung. Vor dem Pilot mit einem Lasttest
  bestätigen oder anpassen.
