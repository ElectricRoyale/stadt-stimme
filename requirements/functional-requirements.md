# Funktionale Anforderungen – StadtStimme

Dieses Dokument beschreibt, **was** StadtStimme fachlich leisten muss. Es ist aus dem
implementierten Code (Models, Services, Views, URLs, Templates), der README und den
Architekturentscheidungen in [docs/DECISIONS.md](../docs/DECISIONS.md) abgeleitet und mit dem
Anforderungskatalog des Teams („Anforderungen StadtStimme“, FA-01 bis FA-41) abgeglichen. Die
Zuordnung FA → FR steht am Ende des Dokuments.

- **Verbindlichkeit:** Akzeptierte ADRs gehen vor. Widerspricht eine Anforderung einem ADR,
  gilt das ADR, und diese Datei wird angepasst. Der ADR-Bezug steht jeweils in Klammern.
  Ein **Hinweis** unter einer Anforderung nennt einen offenen Konflikt oder eine Voraussetzung.
- **IDs sind stabil:** Neue Anforderungen bekommen die nächste freie Nummer und stehen in ihrem
  Themenbereich, auch wenn die Reihenfolge der Nummern dadurch springt.
- **Abgrenzung:** Architektur- und nicht-funktionale Anforderungen (AR-…) werden intern in
  `architecture-requirements.md` gepflegt; FR verweisen dort, wo nötig, auf AR-Nummern.
- **Konfigurierbare Werte** stehen mit ihrem Standardwert und der Einstellung, z. B.
  „183 Tage (`STADTSTIMME_POINTS_EXPIRY_DAYS`)“.

**Rollen**

| Rolle | Bedeutung |
| --- | --- |
| Besucher | Person ohne Anmeldung; sieht alle öffentlichen Seiten |
| Bürger | Person, die mit einem Aktivierungscode angemeldet ist („Zugang“) |
| Verwaltung | Mitarbeitende der Stadt mit Django-Benutzer und Mitarbeiter-Status |
| System | Automatisches Verhalten ohne direkte Aktion einer Person |

**Prioritäten:** *Muss* = Kern des Beteiligungsverfahrens, ohne den das Produkt seinen Zweck
nicht erfüllt. *Soll* = wichtig für Vertrauen und Nutzbarkeit, aber das Verfahren funktioniert
auch ohne. *Kann* = sinnvolle Ergänzung oder zurückgestellt.

---

## 1. Zugang und Authentifizierung

### FR-001: Anmeldung mit Aktivierungscode
**Beschreibung:** Bürger melden sich mit dem Code aus dem Brief der Stadt an. Ein Code ist
16 Zeichen Crockford-Base32 (80 Bit); Eingaben mit Bindestrichen, Leerzeichen oder
Kleinbuchstaben werden normalisiert. Ein QR-Code auf dem Brief füllt den Code vor; eingelöst
wird erst nach dem Absenden. Ein gültiger Code legt beim ersten Einlösen genau einen
Zugang an; jedes weitere Einlösen desselben Codes (auch auf einem anderen Gerät) führt in
denselben Zugang. Der Code ist bis zur Entscheidung über die Gerätebindung zugleich der Login
(ADR-001).
**Rolle:** Bürger
**Priorität:** Muss

### FR-002: Ein Budget je Code
**Beschreibung:** Jeder Code berechtigt zu genau einem Zugang mit einem Budget. Mehrfaches
Teilnehmen mit demselben Code ist ausgeschlossen, auch bei gleichzeitigen Anfragen.
**Rolle:** System
**Priorität:** Muss

### FR-003: Code nur als Hash speichern
**Beschreibung:** Das System speichert keinen Code im Klartext, sondern nur einen HMAC-Hash mit
einem eigenen Pepper (`STADTSTIMME_CODE_PEPPER`, sonst `DJANGO_SECRET_KEY`). Der Klartext eines
neuen Codes ist nur in der Ausgabe beim Erzeugen sichtbar (ADR-001).
**Rolle:** System
**Priorität:** Muss

### FR-004: Sperre nach Fehlversuchen
**Beschreibung:** Nach 10 fehlgeschlagenen Anmeldeversuchen (`STADTSTIMME_MAX_FAILED_ATTEMPTS`)
pro Client wird die Anmeldung für 60 Minuten (`STADTSTIMME_LOCKOUT_MINUTES`) gesperrt. Die
IP-Adresse wird dafür nur als Hash gespeichert. Die Sperre gilt für Code-Anmeldung und
Verwaltungsanmeldung gleichermaßen (ADR-001, ADR-009).
**Rolle:** System
**Priorität:** Muss

### FR-005: Verständliche Fehlermeldungen beim Einlösen
**Beschreibung:** Bei falsch formatiertem, unbekanntem oder gesperrtem Code sowie bei aktiver
Sperre nach Fehlversuchen erhält der Bürger je eine eigene, verständliche Meldung mit dem
nächsten Schritt. Eine Hilfe erklärt, wo der Code steht.
**Rolle:** Bürger
**Priorität:** Muss

### FR-006: Angemeldet bleiben und Abmelden
**Beschreibung:** Nach dem Einlösen bleibt der Bürger auf dem Gerät angemeldet
(Sitzungsdauer 183 Tage, `STADTSTIMME_SESSION_DAYS`), bis er sich abmeldet. Abmelden beendet
die Sitzung auf diesem Gerät.
**Rolle:** Bürger
**Priorität:** Muss

### FR-007: Mein Bereich
**Beschreibung:** Angemeldete Bürger haben einen Bereich „Mein Bereich“ mit Anmeldestatus,
ihrem Punktestand (vergeben und frei), ihren eigenen Vorschlägen mit Schritt und ihren
Einstellungen für E-Mail-Hinweise, jeweils mit Link zu „Punkte verteilen“, „Vorschläge“ und den
Hinweis-Einstellungen.
**Rolle:** Bürger
**Priorität:** Soll

### FR-008: Geschützte Bürgerfunktionen
**Beschreibung:** Punkte verteilen, Vorschläge einreichen und unterstützen sowie E-Mail-Hinweise
verwalten sind nur mit gültigem Zugang möglich. Ohne Anmeldung werden Besucher zur
Code-Eingabe geleitet. Bereits angemeldete Bürger werden von der Code-Eingabe zur Übersicht
weitergeleitet.
**Rolle:** System
**Priorität:** Muss

### FR-009: Anmeldung der Verwaltung
**Beschreibung:** Auf der Anmeldeseite wählt man zwischen „Bürgerin oder Bürger“ (Code) und
„Stadtverwaltung“ (Benutzername und Passwort). Nur Benutzer mit Mitarbeiter-Status gelangen
auf die Verwaltungsseite. Jede Verwaltungsfunktion prüft ihr eigenes Recht (z. B.
„Vorschlag ändern“, „Einrichtung ändern“, Datenpflege je Katalogliste), sodass sich
Mitarbeitende über Gruppen unterschiedliche Rechte-Kategorien zuweisen lassen. Bis zum
Admin-Login-Konzept ist das nur im Demo-Modus verfügbar;
sonst zeigt die Seite einen Hinweis (DECISIONS.md, „Zurückgestellt“).
**Rolle:** Verwaltung
**Priorität:** Muss

### FR-010: Aktivierungscodes erzeugen
**Beschreibung:** Die Verwaltung erzeugt Codes in Chargen (z. B. je Briefversand) mit Angabe
der Charge. Die Ausgabe enthält die Klartexte einmalig zur Weitergabe an den Druck.
**Rolle:** Verwaltung
**Priorität:** Muss

### FR-073: Spitzname
**Beschreibung:** Bürger können in „Mein Bereich“ freiwillig einen Spitznamen wählen, der bei
ihren Vorschlägen angezeigt wird. Bei der Eingabe weist die Anwendung darauf hin, keinen echten
Namen zu verwenden. Ohne Spitzname bleibt der Zugang anonym.
**Rolle:** Bürger
**Priorität:** Kann
**Hinweis:** ADR-014 stellt „Vornamen zeigen“ zurück; vor der Umsetzung braucht es ein ADR zu
Moderation und Datenschutz (AR-020).

---

## 2. Katalog: Themen, Einrichtungen, Maßnahmen, Ausgaben

### FR-011: Themen pflegen
**Beschreibung:** Die Verwaltung pflegt Themen (Kategorien) mit eindeutigem Namen. Übliche
Themen erhalten automatisch Farbe und Symbol, andere reihum; die Farbe ist änderbar (ADR-017,
ADR-018).
**Rolle:** Verwaltung
**Priorität:** Muss

### FR-012: Einrichtungen pflegen
**Beschreibung:** Die Verwaltung pflegt Einrichtungen mit externer ID, Name, Thema, Adresse,
Kurzbeschreibung und optionalen Koordinaten. Breiten- und Längengrad sind nur gemeinsam
gültig. Eine Einrichtung ohne Koordinaten erscheint nicht auf Karten.
**Rolle:** Verwaltung
**Priorität:** Muss

### FR-013: Gebäude als optionale Ebene
**Beschreibung:** Eine Einrichtung kann Gebäude haben. Maßnahmen lassen sich einem Gebäude
ihrer Einrichtung zuordnen; Punkte und Vergleiche bleiben pro Einrichtung (ADR-008).
**Rolle:** Verwaltung
**Priorität:** Kann

### FR-014: Maßnahmen pflegen
**Beschreibung:** Die Verwaltung pflegt Maßnahmen je Einrichtung mit Status (offen,
beschlossen, in Umsetzung, abgeschlossen, verworfen). Maßnahmen zeigen, wofür eine Einrichtung
Geld braucht, tragen aber selbst keine Punkte (ADR-011).
**Rolle:** Verwaltung
**Priorität:** Muss

### FR-015: Ausgaben pflegen
**Beschreibung:** Die Verwaltung pflegt Ist-Ausgaben je Einrichtung und Haushaltsjahr. Diese
Werte sind die Grundlage für den Vergleich mit den Bürgerpunkten (ADR-006).
**Rolle:** Verwaltung
**Priorität:** Muss

### FR-016: CSV-Import mit Vorschau
**Beschreibung:** Einrichtungen, Gebäude, Maßnahmen und Ausgaben lassen sich per CSV
importieren, einzeln über die Oberfläche mit Vorschau vor dem Speichern oder alle vier auf
einmal per Befehl. Der Gesamtimport läuft in einer Transaktion (bei einem Fehler wird nichts
gespeichert), bietet einen Probelauf und ist wiederholbar: Zeilen werden über die externe ID
aktualisiert statt doppelt angelegt.
**Rolle:** Verwaltung
**Priorität:** Muss

### FR-017: CSV-Export des Katalogs
**Beschreibung:** Jede Katalogliste lässt sich als CSV exportieren.
**Rolle:** Verwaltung
**Priorität:** Soll

### FR-018: Öffentliche Suche
**Beschreibung:** Besucher durchsuchen Einrichtungen und passende Maßnahmen über eine
Suchleiste. Treffer verlinken auf die Ergebnisse und auf „Punkte verteilen“. Die Suche ist
ohne Anmeldung und ohne JavaScript nutzbar (ADR-018).
**Rolle:** Besucher
**Priorität:** Soll

---

## 3. Punkte verteilen

### FR-019: Budget von 100 Punkten
**Beschreibung:** Jeder Zugang hat ein Budget von 100 Punkten. Die Summe der vergebenen Punkte
darf 100 nie überschreiten; ein Speichern darüber wird abgewiesen (ADR-011).
**Rolle:** System
**Priorität:** Muss

### FR-020: Punkte an Einrichtung oder ganzes Thema
**Beschreibung:** Bürger vergeben Punkte an einzelne Einrichtungen oder an ein ganzes Thema
(„… allgemein“). Je Ziel gibt es höchstens eine Vergabe pro Zugang (ADR-011).
**Rolle:** Bürger
**Priorität:** Muss

### FR-021: Verteilung bearbeiten und speichern
**Beschreibung:** Bürger ändern Punkte je Ziel per Plus/Minus in Einerschritten (ADR-019) oder
per direkter Zahleneingabe; zulässig sind nur ganze, nicht negative Zahlen. Vergebene und freie
Punkte sowie die Summe je Thema aktualisieren sich bei jeder Änderung sofort, als Zahl und als
Raster aus 100 Feldern, in dem Punkte an ein ganzes Thema erkennbar sind. Gespeichert wird die
ganze Verteilung auf einmal; ein Teil des Budgets darf frei bleiben. Bürger können jederzeit
umverteilen. Für die Auswertung zählt je Zugang nur die zuletzt erfolgreich gespeicherte
Verteilung.
**Rolle:** Bürger
**Priorität:** Muss

### FR-022: Ziele filtern und auf der Karte finden
**Beschreibung:** In „Punkte verteilen“ lassen sich Ziele nach Thema filtern und
Einrichtungen auf einer Karte finden. Eine Liste ist die gleichwertige Alternative zur Karte.
**Rolle:** Bürger
**Priorität:** Soll

### FR-023: Eigene Verteilung mit dem Gesamtbild vergleichen
**Beschreibung:** Bürger sehen ihre eigene Verteilung neben der Verteilung aller Teilnehmenden.
**Rolle:** Bürger
**Priorität:** Kann

### FR-024: Erledigte Einrichtungen nicht wählbar
**Beschreibung:** Als erledigt markierte Einrichtungen fehlen in „Punkte verteilen“ (Liste und
Karte). Ein Speichern mit Punkten an einer erledigten Einrichtung wird mit Hinweis abgewiesen
(ADR-029).
**Rolle:** System
**Priorität:** Muss

### FR-025: Hinweis auf angenommene Vorschläge
**Beschreibung:** Angenommene Vorschläge erscheinen in „Punkte verteilen“ als Hinweis an ihrer
Einrichtung oder, ohne Einrichtung, beim Thema („… allgemein“), mit Link zum Vorschlag. Sie
sind kein eigenes Punkteziel (ADR-023).
**Rolle:** Bürger
**Priorität:** Soll

### FR-078: Ziele per QR-Code verlinken
**Beschreibung:** Für jede Einrichtung und jedes Thema gibt es einen direkten Link auf das Ziel in
„Punkte verteilen“, den die Verwaltung als QR-Code ausgeben kann (z. B. als Aushang vor Ort).
Der QR-Code enthält keinen Zugangscode.
**Rolle:** Verwaltung
**Priorität:** Kann

### FR-076: Abstimmungszeitraum
**Beschreibung:** Die Verwaltung legt Abstimmungszeiträume (Runden) mit Beginn und Ende fest.
Übersicht und Ergebnisse zeigen den laufenden Zeitraum; Snapshots und Entscheidungen beziehen
sich auf ihn.
**Rolle:** Verwaltung
**Priorität:** Kann
**Hinweis:** Das heutige Modell ist eine fortlaufende Beteiligung mit Verfall nach Inaktivität
(ADR-003). Runden sind eine Produktentscheidung mit Folgen für Verfall, Ergebnisse und
Vorschläge und brauchen ein eigenes ADR.

### FR-026: Verlauf zurückgekommener und verfallener Punkte
**Beschreibung:** „Punkte verteilen“ zeigt Punkte, die in den letzten 30 Tagen zurückgekommen
oder verfallen sind, mit Anlass (ADR-027).
**Rolle:** Bürger
**Priorität:** Soll

### FR-027: Unveränderliches Ereignis-Log
**Beschreibung:** Jede Punkteänderung (vergeben, entzogen, zurückgegeben, verfallen) wird in
derselben Transaktion als unveränderliches Ereignis mit Delta, Zeitpunkt und optional der
auslösenden Maßnahme gespeichert. Ändern und Löschen von Ereignissen ist ausgeschlossen. Beim
Löschen eines Zugangs bleibt das Log pseudonym erhalten (ADR-005, ADR-027).
**Rolle:** System
**Priorität:** Muss

### FR-028: Rückfluss bei Umsetzung einer Maßnahme
**Beschreibung:** Geht eine Maßnahme auf „in Umsetzung“ (über Admin, Verwaltungsseite oder
CSV-Import, auch bei Neuanlage), erhalten alle Unterstützer ihre Punkte auf der zugehörigen
Einrichtung zurück. Punkte an ein ganzes Thema bleiben. „Verworfen“ löst keinen Rückfluss aus.
Parallel neu vergebene Punkte bleiben erhalten (ADR-027).
**Rolle:** System
**Priorität:** Muss

### FR-029: Verfall nach Inaktivität
**Beschreibung:** Alle Punkte eines Zugangs verfallen nach 183 Tagen ohne Aktivität
(`STADTSTIMME_POINTS_EXPIRY_DAYS`). Ergebnisse zählen verfallene Punkte sofort nicht mehr mit.
Entzogen werden sie, sobald die Person zurückkommt, oder durch den täglichen Lauf. Jede
Nutzung mit dem Zugang verlängert die Frist (ADR-003).
**Rolle:** System
**Priorität:** Muss

### FR-030: Tägliche Aufgaben
**Beschreibung:** Ein täglicher Lauf (Standard 02:00 UTC, `DAILY_TASKS_AT`) verschickt zuerst
Verfallswarnungen und lässt danach Punkte verfallen. Beide Schritte sind idempotent, jederzeit
manuell startbar, und ein Fehler im einen hält den anderen nicht auf (ADR-028).
**Rolle:** System
**Priorität:** Muss

---

## 4. Öffentliche Übersicht und Ergebnisse

### FR-031: Öffentliche Übersicht
**Beschreibung:** Die Übersicht ist ohne Anmeldung erreichbar und zeigt den Vergleich je Thema
(Anteil Bürgerpunkte gegen Anteil Ist-Ausgaben), eine Karte mit Liste der Einrichtungen, den
Datenstand, die Zahl der Teilnehmenden, die meistunterstützten Vorschläge mit Link und
Neuigkeiten (ADR-012, ADR-017).
**Rolle:** Besucher
**Priorität:** Muss

### FR-032: Eigene Punkte in der Übersicht
**Beschreibung:** Angemeldete Bürger sehen in der Übersicht zusätzlich ihre eigene Verteilung
im Vergleich zum Anteil aller Bürgerpunkte und zu den Ausgaben, ihre vergebenen und freien
Punkte als Zahl und Raster aus 100 Feldern mit Link zu „Punkte verteilen“, ihre eigenen
Vorschläge und bis wann ihre Punkte gültig sind.
**Rolle:** Bürger
**Priorität:** Soll

### FR-033: Vergleich mit dem letzten abgeschlossenen Haushaltsjahr
**Beschreibung:** Alle Vergleiche verwenden die Ist-Ausgaben des letzten abgeschlossenen
Haushaltsjahres. Fehlen solche Ausgaben, zeigt die Seite das ausdrücklich an (ADR-006).
**Rolle:** System
**Priorität:** Muss

### FR-034: Lücke je Einrichtung und je Thema
**Beschreibung:** Die Ergebnisseite zeigt je Einrichtung und je ganzem Thema die Lücke in
Prozentpunkten: Anteil Bürgerpunkte minus Anteil Ist-Ausgaben. Der Themenvergleich enthält alle
Punkte des Themas inkl. „… allgemein“ und alle Ausgaben des Themas (ADR-013).
**Rolle:** Besucher
**Priorität:** Muss

### FR-035: Detail je Einrichtung
**Beschreibung:** Zu jeder Einrichtung lassen sich in den Ergebnissen Punkte, Ausgaben und
zugehörige Maßnahmen im Detail ansehen. Die Auswahl erfolgt über die Liste oder die
Markierung auf der Ergebniskarte.
**Rolle:** Besucher
**Priorität:** Soll

### FR-036: Einordnung der Belastbarkeit
**Beschreibung:** Die Ergebnisse nennen Stand, Zahl der Mitmachenden, vergebene Punkte,
durchschnittliche Punkte je Person, Anteil an ganze Themen und Summe der Ausgaben sowie den
Hinweis, dass die Zahlen nicht repräsentativ sind.
**Rolle:** Besucher
**Priorität:** Soll

### FR-037: Ergebnisse als CSV
**Beschreibung:** Die Ergebnistabelle lässt sich als CSV herunterladen (Semikolon,
Dezimalkomma, BOM für deutsche Tabellenprogramme). Texte werden gegen Formel-Injektion
geschützt.
**Rolle:** Besucher
**Priorität:** Soll

### FR-038: Karten der Einrichtungen
**Beschreibung:** Übersicht, „Punkte verteilen“, Ergebnisse und Vorschläge zeigen Einrichtungen
mit Koordinaten auf einer zoombaren Karte, immer zusammen mit einer gleichwertigen Liste.
Markierungen zeigen das Thema (Farbe und Symbol) und mit ihrer Größe den Anteil an den
Bürgerpunkten. Ein Klick auf eine Markierung führt zum zugehörigen Ziel bzw. zu seinen Details.
Angemeldete Bürger können zwischen allen Einrichtungen und den von ihnen gewichteten
umschalten. Fällt der Kachelserver aus, wechselt die Karte auf einen
Ersatz und zeigt danach mindestens die Marker (ADR-018, ADR-020, ADR-030).
**Rolle:** Besucher
**Priorität:** Soll

---

## 5. Vorschläge

### FR-039: Vorschlag einreichen
**Beschreibung:** Angemeldete Bürger reichen einen Vorschlag in drei Schritten ein: Anliegen
(Titel 8–80 Zeichen, Beschreibung optional bis 600 Zeichen), Einordnen, Prüfen (ADR-014). Vor
dem Einreichen können sie zu jedem vorherigen Schritt zurückkehren und korrigieren, ohne
Eingaben zu verlieren.
**Rolle:** Bürger
**Priorität:** Muss

### FR-040: Thema und Ort eines Vorschlags
**Beschreibung:** Ein Vorschlag hat immer ein Thema. Der Ort ist „allgemein“, eine bekannte
Einrichtung passend zum Thema oder ein neuer Punkt auf der Karte (per Klick oder Kartenmitte
für Tastaturnutzung). Einrichtung und Punkt sind nie gleichzeitig gesetzt. Ohne JavaScript
stehen „allgemein“ und „bekannter Ort“ zur Verfügung (ADR-022).
**Rolle:** Bürger
**Priorität:** Muss

### FR-041: Tageslimit für Vorschläge
**Beschreibung:** Ein Zugang darf höchstens 5 Vorschläge pro Tag einreichen
(`STADTSTIMME_PROPOSALS_PER_DAY`); darüber wird mit Hinweis abgewiesen (ADR-014, ADR-025).
**Rolle:** System
**Priorität:** Muss

### FR-042: Ähnliche Einträge vorschlagen
**Beschreibung:** Beim Schreiben zeigt „Gibt es das schon?“ ähnliche Vorschläge und offene
Maßnahmen (Abgleich über Wortstämme), damit Doppelungen vermieden werden (ADR-016).
**Rolle:** Bürger
**Priorität:** Soll

### FR-043: Vorschläge sofort öffentlich
**Beschreibung:** Ein eingereichter Vorschlag ist ohne Freigabe sofort öffentlich sichtbar und
unterstützbar (ADR-025).
**Rolle:** System
**Priorität:** Muss

### FR-044: Vorschlag unterstützen
**Beschreibung:** Angemeldete Bürger unterstützen beliebig viele offene Vorschläge anderer,
jeden höchstens einmal, und können die Unterstützung zurückziehen. Unterstützungen sind
unabhängig vom Budget der 100 Punkte. Eigene sowie entschiedene Vorschläge sind nicht
unterstützbar; abgelehnte Vorschläge erscheinen nicht mehr unter den eigenen unterstützten
(ADR-016, ADR-025).
**Rolle:** Bürger
**Priorität:** Muss

### FR-045: Weg eines Vorschlags
**Beschreibung:** Jeder Vorschlag zeigt seinen Schritt: „Sammelt“ (unter der Schwelle von
50 Unterstützungen, `STADTSTIMME_PROPOSAL_SUPPORT_THRESHOLD`), „In Prüfung“ (Schwelle erreicht,
seit dem Zeitpunkt der N-ten Unterstützung) und „Entschieden“ (angenommen oder abgelehnt).
Solange ein Vorschlag sammelt, zeigt er die noch benötigten Unterstützungen. Die
Liste lässt sich nach Schritt filtern, auch ohne JavaScript (ADR-016, ADR-025).
**Rolle:** Besucher
**Priorität:** Muss

### FR-046: Öffentliche Antwort der Stadt
**Beschreibung:** Entschiedene Vorschläge zeigen die öffentliche Begründung der Stadt, das
Entscheidungsdatum und gegebenenfalls die daraus entstandene Maßnahme (ADR-016).
**Rolle:** Besucher
**Priorität:** Muss

### FR-047: Neuer Ort wird Einrichtung
**Beschreibung:** Wird ein Vorschlag mit neuem Ort angenommen, legt das System daraus eine
Einrichtung an (Name = Titel, Thema und Koordinaten vom Vorschlag, externe ID
`VORSCHLAG-<Nr>`) und verknüpft den Vorschlag mit ihr. Sie ist danach wählbar und in Karten
und Ergebnissen enthalten (ADR-024).
**Rolle:** System
**Priorität:** Soll

### FR-079: Vorschlagsliste durchsuchen, filtern und sortieren
**Beschreibung:** Die Vorschlagsliste ist nach Titel und Ort durchsuchbar, nach Thema und Schritt
filterbar und nach Zahl der Unterstützungen sortierbar. Angemeldete Bürger wählen zwischen allen
und nur ihren eigenen Vorschlägen. Filter und Sortierung funktionieren ohne JavaScript.
**Rolle:** Besucher
**Priorität:** Soll

### FR-077: Vorschlag teilen
**Beschreibung:** Jeder Vorschlag hat einen dauerhaften, öffentlichen Link, den Ersteller und
andere teilen können. Der Link enthält keinen Zugangscode und keine Angabe zum Ersteller.
**Rolle:** Bürger
**Priorität:** Kann

---

## 6. Verwaltungsseite

### FR-048: Wartet auf Sie
**Beschreibung:** Die Verwaltungsseite listet Vorschläge in Prüfung mit ihrer Antwortfrist von
14 Tagen ab Erreichen der Schwelle (`STADTSTIMME_PROPOSAL_REVIEW_DAYS`), früheste Frist zuerst
(ADR-025, ADR-026).
**Rolle:** Verwaltung
**Priorität:** Muss

### FR-049: Vorschlag entscheiden
**Beschreibung:** Die Verwaltung nimmt einen Vorschlag an oder lehnt ihn ab, jederzeit, auch
vor Erreichen der Schwelle. Pflicht ist eine öffentliche Antwort mit mindestens 20 Zeichen,
optional eine verknüpfte Maßnahme. Ein bereits entschiedener Vorschlag kann nicht erneut
entschieden werden. Entscheiden erfordert das Recht „Vorschlag ändern“ (ADR-025, ADR-026).
**Rolle:** Verwaltung
**Priorität:** Muss

### FR-050: Beteiligung beobachten
**Beschreibung:** Die Verwaltung sieht die Beteiligung nur als Summen: eingelöste Codes je
Woche, eingelöste Codes und Zugänge mit vergebenen Punkten. Rückschlüsse auf einzelne Personen
sind nicht möglich (ADR-026).
**Rolle:** Verwaltung
**Priorität:** Muss

### FR-051: Vorschläge nach Schritt
**Beschreibung:** Die Verwaltung sieht alle Vorschläge gruppiert nach Schritt mit Zugang zur
Entscheidungsseite (ADR-026).
**Rolle:** Verwaltung
**Priorität:** Muss

### FR-052: Einrichtungen nach Lücke
**Beschreibung:** Die Verwaltung sieht Einrichtungen sortiert nach Lücke mit ihren Maßnahmen und
einem Link zur Datenpflege (ADR-026).
**Rolle:** Verwaltung
**Priorität:** Soll

### FR-053: Einrichtung als erledigt markieren
**Beschreibung:** Die Verwaltung markiert eine Einrichtung als erledigt, auch ohne passende
Maßnahme. Vorher bestätigt sie eine Rückfrage mit Zahl der Unterstützer und Punkte. Danach
gehen alle Punkte an dieser Einrichtung an die Unterstützer zurück, und Betroffene mit
E-Mail-Hinweis werden benachrichtigt; Themenpunkte bleiben. Dasselbe gilt, wenn eine Einrichtung
dauerhaft aus dem Katalog genommen wird: Sie wird dann als erledigt archiviert statt gelöscht,
weil das Ereignis-Log auf sie verweist (AR-011). Erfordert das Recht „Einrichtung ändern“
(ADR-029).
**Rolle:** Verwaltung
**Priorität:** Muss

### FR-054: Einrichtung wieder öffnen
**Beschreibung:** Eine erledigte Einrichtung wird wieder wählbar über „Wieder öffnen“ oder
automatisch, sobald die Stadt einen Vorschlag an diesem Ort annimmt. In Ergebnissen, Suche und
als bekannter Ort bei Vorschlägen bleibt sie immer sichtbar (ADR-029).
**Rolle:** Verwaltung
**Priorität:** Muss

### FR-055: Stichtags-Export
**Beschreibung:** Die Verwaltung lädt für einen Stichtag eine CSV mit Punkten und Unterstützern
je Ziel zum Tagesende herunter, ergänzt um die Zahl der Teilnehmenden und die Ist-Ausgaben je
Ziel. Die Werte werden aus dem Ereignis-Log berechnet und sind für
denselben Stichtag reproduzierbar (ADR-027).
**Rolle:** Verwaltung
**Priorität:** Muss

### FR-056: Zugänge je Charge
**Beschreibung:** Die Verwaltung sieht je Charge, wie viele Codes ausgegeben und eingelöst sind
(ADR-026).
**Rolle:** Verwaltung
**Priorität:** Soll

### FR-057: Inhalte moderieren
**Beschreibung:** Die Verwaltung kann unpassende Vorschläge mit Begründung ablehnen (FR-049)
oder doppelte und unzulässige Vorschläge mit Begründung entfernen (ADR-025). Ein entfernter
Vorschlag ist öffentlich nicht mehr sichtbar; sein Ersteller sieht in „Mein Bereich“, dass und
warum er entfernt wurde.
**Rolle:** Verwaltung
**Priorität:** Muss

### FR-074: Zugang finden und einsehen
**Beschreibung:** Die Verwaltung findet einen Zugang über die letzten 8 Zeichen seines Codes
(z. B. bei einer Anfrage per Telefon) und sieht Status, Charge, Zeitpunkt des Einlösens und
letzte Aktivität. Sie kann dort nichts im Namen des Bürgers ändern.
**Rolle:** Verwaltung
**Priorität:** Soll
**Hinweis:** Codes liegen nur als Hash vor (AR-015); für die Suche braucht es einen eigenen
Hash der letzten 8 Zeichen. Die im Katalog gewünschte Einsicht in Verteilung und Vorschläge des
Zugangs widerspricht AR-022 und ist deshalb nicht übernommen (siehe Abgleich).

### FR-075: Zugang schließen und wieder öffnen
**Beschreibung:** Die Verwaltung schließt einen Zugang (z. B. bei Wegzug) und öffnet ihn bei
Bedarf wieder. Das Schließen wirkt sofort, auch auf bestehende Anmeldungen. Alle Punkte des
Zugangs werden entzogen (Ereignis „entzogen“); seine Vorschläge und Unterstützungen bleiben
erhalten. Erfordert ein eigenes Recht.
**Rolle:** Verwaltung
**Priorität:** Soll

---

## 7. E-Mail-Hinweise

### FR-058: E-Mail freiwillig hinterlegen
**Beschreibung:** Bürger hinterlegen freiwillig eine E-Mail-Adresse für Hinweise, ändern oder
entfernen sie und wählen, welche Arten von Hinweisen sie erhalten. Die Adresse wird verschlüsselt und getrennt von den Punkten gespeichert und mit
dem Zugang gelöscht (ADR-004, ADR-028).
**Rolle:** Bürger
**Priorität:** Soll

### FR-059: Double-Opt-in
**Beschreibung:** Hinweise gehen erst nach Bestätigung über einen Link raus. Der Link ist
72 Stunden gültig, das Token wird nur als Hash gespeichert, und das Öffnen des Links bestätigt
erst nach Klick auf einen Knopf. Eine neue Bestätigungsmail ist frühestens nach 10 Minuten
möglich (ADR-028).
**Rolle:** System
**Priorität:** Soll

### FR-060: Verfallswarnung
**Beschreibung:** Bestätigte Empfänger erhalten 14 Tage vor dem Verfall
(`STADTSTIMME_POINTS_EXPIRY_WARNING_DAYS`) eine Warnung, einmal je Inaktivitätsphase
(ADR-028).
**Rolle:** System
**Priorität:** Soll

### FR-061: Hinweis bei Rückfluss
**Beschreibung:** Bestätigte Empfänger erhalten eine E-Mail, wenn Punkte zu ihnen
zurückkommen (Maßnahme in Umsetzung oder Einrichtung erledigt) (ADR-027, ADR-028, ADR-029).
**Rolle:** System
**Priorität:** Soll

### FR-080: Erinnerung an freie Punkte
**Beschreibung:** Bestätigte Empfänger mit freien Punkten erhalten eine Erinnerung, ihre Punkte
zu verteilen. Die Erinnerung wiederholt sich in einem konfigurierbaren Abstand, solange Punkte
frei sind, und lässt sich einzeln abbestellen.
**Rolle:** System
**Priorität:** Kann

### FR-081: Hinweis zu eigenen und unterstützten Vorschlägen
**Beschreibung:** Bestätigte Empfänger erhalten einen Hinweis, wenn ein eigener oder unterstützter
Vorschlag die Schwelle erreicht, angenommen, abgelehnt oder von der Stadt beantwortet wird.
**Rolle:** System
**Priorität:** Soll

### FR-062: Abmelden mit einem Klick
**Beschreibung:** Jede Hinweis-Mail enthält einen Abmeldelink und `List-Unsubscribe`
(Ein-Klick nach RFC 8058). Abmelden löscht die Adresse (ADR-028).
**Rolle:** Bürger
**Priorität:** Soll

### FR-063: Robust bei Mailausfall
**Beschreibung:** Ist der Mailserver nicht erreichbar, schlägt keine fachliche Aktion fehl
(z. B. Speichern einer Maßnahme); es wird lediglich keine Mail versendet (ADR-028).
**Rolle:** System
**Priorität:** Soll

---

## 8. Systemfunktionen

### FR-064: Demo-Modus
**Beschreibung:** Im Demo-Modus lädt das System fiktive Testdaten (Mannheim) in einen leeren
Katalog, legt Demo-Codes und einen Demo-Admin an und macht Admin und Verwaltungsseite
erreichbar. Ohne Demo-Modus sind beide nicht erreichbar (ADR-019).
**Rolle:** System
**Priorität:** Muss

### FR-065: Health-Check
**Beschreibung:** Ein öffentlicher Endpunkt meldet, ob die Anwendung läuft und die Datenbank
erreichbar ist.
**Rolle:** System
**Priorität:** Soll

### FR-066: Stadtname konfigurierbar
**Beschreibung:** Der Stadtname in Logo und Texten kommt aus `STADTSTIMME_CITY_NAME`, damit
andere Kommunen die Anwendung ohne Codeänderung nutzen können (ADR-015).
**Rolle:** System
**Priorität:** Soll

---

## 9. Zurückgestellt (nicht im aktuellen Umfang)

Diese Anforderungen sind bekannt, aber bis zur Teamabstimmung oder einem fehlenden Datenmodell
zurückgestellt. Sie werden erst umgesetzt, wenn die zugehörige Entscheidung getroffen ist.

### FR-067: Gerätebindung nach dem Einlösen
**Beschreibung:** Nach dem ersten Einlösen bindet der Bürger seinen Zugang an Passkey oder
Passwort; der Code ist danach nicht mehr allein der Login (ADR-001, zurückgestellt).
**Rolle:** Bürger
**Priorität:** Kann

### FR-068: Codes für den Briefdruck exportieren
**Beschreibung:** Die Verwaltung exportiert Codes für den Druck (DECISIONS.md, zurückgestellt).
Sperren und Wiederöffnen eines Zugangs regelt FR-075.
**Rolle:** Verwaltung
**Priorität:** Kann

### FR-069: Admin-Login für den Regelbetrieb
**Beschreibung:** Verwaltung und Admin sind außerhalb des Demo-Modus mit einem eigenen
Login-Konzept inkl. Team-Verwaltung und zweitem Faktor nutzbar (ADR-026, zurückgestellt).
**Rolle:** Verwaltung
**Priorität:** Kann

### FR-070: Vorschläge melden
**Beschreibung:** Bürger melden unpassende Vorschläge an die Verwaltung (ADR-025,
zurückgestellt).
**Rolle:** Bürger
**Priorität:** Kann

### FR-071: Foto zum Vorschlag
**Beschreibung:** Bürger fügen einem Vorschlag ein Foto bei (ADR-014, zurückgestellt wegen
Speicher, Datenschutz und Moderation).
**Rolle:** Bürger
**Priorität:** Kann

### FR-072: Berichte und Protokoll auf der Verwaltungsseite
**Beschreibung:** Die Verwaltung erstellt datierte Snapshots einer Abstimmung (Punkte,
Teilnehmende, Ziele, Ausgaben), sieht sie in der Anwendung ein, vergleicht Snapshots
miteinander und wählt den Zeitraum der Auswertung (ADR-026, zurückgestellt). Das Protokoll der
Verwaltungsaktionen regelt AR-040.
**Rolle:** Verwaltung
**Priorität:** Kann

---

## Abgleich mit dem Anforderungskatalog des Teams

Jede FA ist einer FR zugeordnet. „Gleich“ heißt: Die FR beschreibt dasselbe und blieb unverändert.
„Ergänzt“ heißt: Die FR wurde um Details aus der FA erweitert. „Neu“ heißt: Die FR ist neu.

| FA | FR | Art |
| --- | --- | --- |
| FA-01 | FR-001 | gleich |
| FA-02 | FR-009 | gleich |
| FA-03 | FR-009 | ergänzt |
| FA-04 | FR-007, FR-073 | ergänzt, neu (Spitzname) |
| FA-05 | FR-074 | neu, teilweise (siehe Konflikte) |
| FA-06 | FR-075 | neu |
| FA-07 | FR-032 | ergänzt |
| FA-08 | FR-031, FR-076 | ergänzt, neu (Zeitraum) |
| FA-09 | FR-050 | gleich |
| FA-10 | FR-038 | ergänzt |
| FA-11 | FR-021, FR-032 | ergänzt |
| FA-12 | FR-031, FR-032 | ergänzt |
| FA-13 | FR-001, FR-002 | gleich |
| FA-14 | FR-020 | nicht übernommen (siehe Konflikte) |
| FA-15 | FR-021 | ergänzt |
| FA-16 | FR-021 | ergänzt |
| FA-17 | FR-021 | ergänzt |
| FA-18 | FR-038 | ergänzt |
| FA-19 | FR-024, FR-028, FR-053 | gleich |
| FA-20 | FR-031, FR-032, FR-034 | gleich |
| FA-21 | FR-035, FR-038 | ergänzt |
| FA-22 | FR-037 | gleich |
| FA-23 | FR-039 | ergänzt |
| FA-24 | FR-045 | gleich |
| FA-25 | FR-076 | neu (hängt am Zeitraum) |
| FA-26 | FR-077 | neu |
| FA-27 | FR-078 | neu |
| FA-28 | FR-079 | neu |
| FA-29 | FR-044 | ergänzt |
| FA-30 | FR-045, FR-047 | ergänzt (siehe Konflikte) |
| FA-31 | FR-049, FR-057 | ergänzt |
| FA-32 | FR-015, FR-016 | gleich |
| FA-33 | FR-012, FR-014 | gleich |
| FA-34 | FR-053 | ergänzt |
| FA-35 | FR-055 | ergänzt |
| FA-36 | FR-072 | ergänzt |
| FA-37 | FR-047, FR-049 | gleich |
| FA-38 | FR-044 | ergänzt |
| FA-39 | FR-058 | ergänzt |
| FA-40 | FR-061, FR-080 | neu (Erinnerung an freie Punkte) |
| FA-41 | FR-081 | neu |

### Konflikte mit akzeptierten Entscheidungen

Diese Punkte aus dem Katalog widersprechen einem akzeptierten ADR und sind deshalb nicht oder nur
teilweise übernommen. Sie brauchen eine bewusste Entscheidung im Team.

| FA | Widerspruch | Empfehlung |
| --- | --- | --- |
| FA-14 | Maßnahmen und Projekte als eigenes Punkteziel. ADR-011 und ADR-023 legen fest: Punkte gehen nur an Einrichtung oder Thema; ein eigenes Ziel je Maßnahme wurde verworfen (Migration, Ergebnisse ohne Ausgaben je Maßnahme). | Bei ADR-011 bleiben. Maßnahmen sind über ihre Einrichtung erreichbar. |
| FA-30, FA-37 | „Angenommener Vorschlag wird Ziel.“ Nach ADR-023/024 wird nur ein Vorschlag mit neuem Ort eine Einrichtung; sonst erscheint er als Hinweis an Einrichtung oder Thema. | Bei ADR-023/024 bleiben; FR-047 und FR-025 decken den Zweck. |
| FA-05 | Verwaltung sieht die Auswahl eines einzelnen Zugangs. Widerspricht AR-022 und ADR-026 („nur Summen“) und schwächt das Vertrauen in die anonyme Beteiligung. | Nicht übernehmen; nur Status und Aktivität zeigen (FR-074). |
| FA-08, FA-25 | Voting-Zeitraum. Das heutige Modell ist fortlaufend mit Verfall (ADR-003). | Als FR-076 (Kann) aufgenommen; vor Umsetzung ADR. |
| FA-31, FA-41 | Mehrere Kommentare der Stadt je Vorschlag. Heute gibt es genau eine öffentliche Antwort (ADR-016). | Eine Antwort beibehalten, bis ein Bedarf für Verläufe belegt ist. |

## Offene Punkte

- **Löschen eines Zugangs durch den Bürger:** Das Datenmodell sieht das Löschen vor (Ereignis
  „entzogen“, E-Mail wird mitgelöscht), eine Funktion für Bürger gibt es aber nicht. Für die
  Datenschutzfreigabe (Phase 6) zu klären.
- **Personas und Akzeptanzkriterien** sind nicht dokumentiert. Prioritäten oben sind aus dem
  Produktziel und den ADRs abgeleitet und sollten im Team bestätigt werden.
