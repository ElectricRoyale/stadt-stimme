# Entscheidungen

Kurzübersicht der Architektur- und Produktentscheidungen (ADRs). Die ausführliche Fassung mit Kontext,
Konsequenzen und verworfenen Alternativen liegt im Projektdokument „StadtStimme – Architekturentscheidungen“.
Eine überholte Entscheidung wird nicht gelöscht, sondern als ersetzt markiert.

| Nr. | Entscheidung | Status |
| --- | --- | --- |
| ADR-001 | Zugang per einmaligem Aktivierungscode aus dem Brief der Stadt; 16 Zeichen Crockford-Base32 (80 Bit), gespeichert nur als Hash, Rate-Limit gegen Raten. | Akzeptiert, Gerätebindung zurückgestellt |
| ADR-002 | Punkte werden auf Maßnahmen vergeben (je genau eine Einrichtung), max. 100 pro Person, jederzeit umverteilbar. Rückfluss an die Unterstützer bei Beginn der Umsetzung oder bei Verwerfen. | Akzeptiert |
| ADR-003 | Alle Punkte verfallen 6 Monate nach der letzten aktiven Nutzung. | Akzeptiert |
| ADR-004 | Benachrichtigung nur per freiwilliger E-Mail mit Double-Opt-in, getrennt vom Zugang gespeichert. | Akzeptiert |
| ADR-005 | Jede Punkteänderung als unveränderliches Ereignis; aktueller Stand als Read Model; Stichtagswerte aus dem Log. | Vorgeschlagen |
| ADR-006 | Vergleich Bürgerpriorität vs. Ausgaben als Anteile pro Einrichtung, Ausgaben des letzten abgeschlossenen Haushaltsjahres. | Akzeptiert |
| ADR-007 | Tech-Stack: Django + htmx + PostgreSQL, Start per `docker compose up`. | Akzeptiert |
| ADR-008 | Gebäude als optionale Ebene unter der Einrichtung. Eine Maßnahme kann einem Gebäude ihrer Einrichtung zugeordnet werden; Punkte und Vergleich bleiben pro Einrichtung (ADR-002, ADR-006). | Akzeptiert |
| ADR-009 | Rate-Limit für das Einlösen als eigene Tabelle mit Fehlversuchen in PostgreSQL (IP nur als Hash) statt django-ratelimit, weil django-ratelimit den Datenbank-Cache als nicht atomar ablehnt und sonst Redis nötig wäre. | Akzeptiert |
| ADR-010 | Oberfläche nach den Design-Tokens „StadtStimme v1.2“ (`static/css/tokens.css`, unverändert aus dem Design-System übernommen). Schrift Public Sans liegt selbst gehostet im Repo (OFL), damit keine Anfragen an Google Fonts gehen. | Akzeptiert |

## Zurückgestellt bis zur Teamabstimmung

- Gerätebindung nach dem Einlösen (Passkey/Passwort). Bis dahin ist der Code zugleich der Login.
- Export der Codes für den Briefdruck und Sperren von Codes.
- Admin-Login-Konzept. Bis dahin ist der Django Admin nur im Demo-Modus und nur lokal erreichbar.
