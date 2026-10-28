# Entscheidungen

Kurzübersicht der Architektur- und Produktentscheidungen (ADRs). Die ausführliche Fassung mit Kontext,
Konsequenzen und verworfenen Alternativen liegt im Projektdokument „StadtStimme – Architekturentscheidungen“.
Eine überholte Entscheidung wird nicht gelöscht, sondern als ersetzt markiert.

| Nr. | Entscheidung | Status |
| --- | --- | --- |
| ADR-001 | Zugang per einmaligem Aktivierungscode aus dem Brief der Stadt; 16 Zeichen Crockford-Base32 (80 Bit), gespeichert nur als Hash, Rate-Limit gegen Raten. | Akzeptiert, Gerätebindung zurückgestellt |
| ADR-002 | Punkte werden auf Maßnahmen vergeben (je genau eine Einrichtung), max. 100 pro Person, jederzeit umverteilbar. Rückfluss an die Unterstützer bei Beginn der Umsetzung oder bei Verwerfen. | Ersetzt durch ADR-011 |
| ADR-003 | Alle Punkte verfallen 6 Monate nach der letzten aktiven Nutzung. | Akzeptiert |
| ADR-004 | Benachrichtigung nur per freiwilliger E-Mail mit Double-Opt-in, getrennt vom Zugang gespeichert. | Akzeptiert |
| ADR-005 | Jede Punkteänderung als unveränderliches Ereignis; aktueller Stand als Read Model; Stichtagswerte aus dem Log. | Vorgeschlagen |
| ADR-006 | Vergleich Bürgerpriorität vs. Ausgaben als Anteile pro Einrichtung, Ausgaben des letzten abgeschlossenen Haushaltsjahres. | Akzeptiert |
| ADR-007 | Tech-Stack: Django + htmx + PostgreSQL, Start per `docker compose up`. | Akzeptiert |
| ADR-008 | Gebäude als optionale Ebene unter der Einrichtung. Eine Maßnahme kann einem Gebäude ihrer Einrichtung zugeordnet werden; Punkte und Vergleich bleiben pro Einrichtung (ADR-002, ADR-006). | Akzeptiert |
| ADR-009 | Rate-Limit für das Einlösen als eigene Tabelle mit Fehlversuchen in PostgreSQL (IP nur als Hash) statt django-ratelimit, weil django-ratelimit den Datenbank-Cache als nicht atomar ablehnt und sonst Redis nötig wäre. | Akzeptiert |
| ADR-010 | Oberfläche nach den Design-Tokens „StadtStimme v1.2“ (`static/css/tokens.css`, unverändert aus dem Design-System übernommen). Schrift Public Sans liegt selbst gehostet im Repo (OFL), damit keine Anfragen an Google Fonts gehen. | Akzeptiert |
| ADR-011 | Punkte gehen an eine Einrichtung oder an ein ganzes Thema („… allgemein“), wie in der Skizze „Punkte verteilen“. Max. 100 pro Person, jederzeit umverteilbar, gespeichert wird die ganze Verteilung auf einmal. Kein Rückfluss mehr, nur der Verfall nach ADR-003. Maßnahmen zeigen, wofür eine Einrichtung Geld braucht, tragen aber selbst keine Punkte. Gespeichert wird nur der aktuelle Stand; das Ereignis-Log aus ADR-005 bleibt vorgeschlagen. | Akzeptiert |
| ADR-012 | Übersicht „Kartenebenen“ wie in der Skizze „Dashboard 2“: Vergleich je Thema (Bürgeranteil inkl. „… allgemein“ gegen Ist-Ausgaben des letzten abgeschlossenen Haushaltsjahres, vgl. ADR-006), Karte mit Einrichtungen. Leaflet liegt selbst gehostet im Repo; die Kartenkacheln kommen direkt von OpenStreetMap (`STADTSTIMME_MAP_TILE_URL`). Dabei geht die IP-Adresse der Besucher an den Kachelserver: muss in die Datenschutzerklärung, für den Betrieb ggf. eigener Kachelserver. Die Liste unter der Karte ist die barrierefreie Alternative. | Akzeptiert |

## Zurückgestellt bis zur Teamabstimmung

- Gerätebindung nach dem Einlösen (Passkey/Passwort). Bis dahin ist der Code zugleich der Login.
- Export der Codes für den Briefdruck und Sperren von Codes.
- Admin-Login-Konzept. Bis dahin ist der Django Admin nur im Demo-Modus und nur lokal erreichbar.
