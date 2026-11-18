# Funktionale Anforderungen – StadtStimme
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
<a id="fr-001"></a>
### FR-001: Anmeldung mit Aktivierungscode
**Beschreibung:** Bürger melden sich mit dem Code aus dem Brief der Stadt an. Ein Code ist
16 Zeichen Crockford-Base32 (80 Bit); Eingaben mit Bindestrichen, Leerzeichen oder
Kleinbuchstaben werden normalisiert. Ein QR-Code auf dem Brief füllt den Code vor; eingelöst
wird erst nach dem Absenden. Ein gültiger Code legt beim ersten Einlösen genau einen
Zugang an; jedes weitere Einlösen desselben Codes (auch auf einem anderen Gerät) führt in
denselben Zugang. Der Code ist bis zur Entscheidung über die Gerätebindung zugleich der Login.
**Rolle:** Bürger
**Priorität:** Muss
<a id="fr-002"></a>
### FR-002: Ein Budget je Code
**Beschreibung:** Jeder Code berechtigt zu genau einem Zugang mit einem Budget. Mehrfaches
Teilnehmen mit demselben Code ist ausgeschlossen, auch bei gleichzeitigen Anfragen.
**Rolle:** System
**Priorität:** Muss
<a id="fr-003"></a>
### FR-003: Code nur als Hash speichern
**Beschreibung:** Das System speichert keinen Code im Klartext, sondern nur einen HMAC-Hash mit
einem eigenen Pepper (`STADTSTIMME_CODE_PEPPER`, sonst `DJANGO_SECRET_KEY`). Der Klartext eines
neuen Codes ist nur in der Ausgabe beim Erzeugen sichtbar.
**Rolle:** System
**Priorität:** Muss
<a id="fr-004"></a>
### FR-004: Sperre nach Fehlversuchen
**Beschreibung:** Nach 10 fehlgeschlagenen Anmeldeversuchen (`STADTSTIMME_MAX_FAILED_ATTEMPTS`)
pro Client wird die Anmeldung für 60 Minuten (`STADTSTIMME_LOCKOUT_MINUTES`) gesperrt. Die
IP-Adresse wird dafür nur als Hash gespeichert. Die Sperre gilt für Code-Anmeldung und
Verwaltungsanmeldung gleichermaßen.
**Rolle:** System
**Priorität:** Muss
<a id="fr-005"></a>
### FR-005: Verständliche Fehlermeldungen beim Einlösen
**Beschreibung:** Bei falsch formatiertem, unbekanntem oder gesperrtem Code sowie bei aktiver
Sperre nach Fehlversuchen erhält der Bürger je eine eigene, verständliche Meldung mit dem
nächsten Schritt. Eine Hilfe erklärt, wo der Code steht.
**Rolle:** Bürger
**Priorität:** Muss
<a id="fr-006"></a>
### FR-006: Angemeldet bleiben und Abmelden
**Beschreibung:** Nach dem Einlösen bleibt der Bürger auf dem Gerät angemeldet
(Sitzungsdauer 183 Tage, `STADTSTIMME_SESSION_DAYS`), bis er sich abmeldet. Abmelden beendet
die Sitzung auf diesem Gerät.
**Rolle:** Bürger
**Priorität:** Muss
<a id="fr-007"></a>
### FR-007: Mein Bereich
**Beschreibung:** Angemeldete Bürger haben einen Bereich „Mein Bereich“ mit Anmeldestatus,
ihrem Punktestand (vergeben und frei), ihren eigenen Vorschlägen mit Schritt und ihren
Einstellungen für E-Mail-Hinweise, jeweils mit Link zu „Punkte verteilen“, „Vorschläge“ und den
Hinweis-Einstellungen.
**Rolle:** Bürger
**Priorität:** Soll
<a id="fr-008"></a>
### FR-008: Geschützte Bürgerfunktionen
**Beschreibung:** Punkte verteilen, Vorschläge einreichen und unterstützen sowie E-Mail-Hinweise
verwalten sind nur mit gültigem Zugang möglich. Ohne Anmeldung werden Besucher zur
Code-Eingabe geleitet. Bereits angemeldete Bürger werden von der Code-Eingabe zur Übersicht
weitergeleitet.
**Rolle:** System
**Priorität:** Muss
<a id="fr-009"></a>
### FR-009: Anmeldung der Verwaltung
**Beschreibung:** Auf der Anmeldeseite wählt man zwischen „Bürgerin oder Bürger“ (Code) und
„Stadtverwaltung“ (Benutzername und Passwort). Nur Benutzer mit Mitarbeiter-Status gelangen
auf die Verwaltungsseite. Jede Verwaltungsfunktion prüft ihr eigenes Recht (z. B.
„Vorschlag ändern“, „Einrichtung ändern“, Datenpflege je Katalogliste), sodass sich
Mitarbeitende über Gruppen unterschiedliche Rechte-Kategorien zuweisen lassen. Bis zum
Admin-Login-Konzept ist das nur im Demo-Modus verfügbar;
sonst zeigt die Seite einen Hinweis.
**Rolle:** Verwaltung
**Priorität:** Muss
<a id="fr-010"></a>
### FR-010: Aktivierungscodes erzeugen
**Beschreibung:** Die Verwaltung erzeugt Codes in Chargen (z. B. je Briefversand) mit Angabe
der Charge. Die Ausgabe enthält die Klartexte einmalig zur Weitergabe an den Druck.
**Rolle:** Verwaltung
**Priorität:** Muss
<a id="fr-011"></a>
### FR-011: Codes für den Briefdruck exportieren
**Beschreibung:** Die Verwaltung exportiert Codes für den Druck (DECISIONS.md, zurückgestellt).
Sperren und Wiederöffnen eines Zugangs regelt [FR-068](#fr-068).
**Rolle:** Verwaltung
**Priorität:** Kann
<a id="fr-012"></a>
### FR-012: Spitzname
**Beschreibung:** Bürger können in „Mein Bereich“ freiwillig einen Spitznamen wählen, der bei
ihren Vorschlägen angezeigt wird. Bei der Eingabe weist die Anwendung darauf hin, keinen echten
Namen zu verwenden. Ohne Spitzname bleibt der Zugang anonym.
**Rolle:** Bürger
**Priorität:** Kann

---

## 2. Katalog: Themen, Einrichtungen, Maßnahmen, Ausgaben
<a id="fr-013"></a>
### FR-013: Themen pflegen
**Beschreibung:** Die Verwaltung pflegt Themen (Kategorien) mit eindeutigem Namen. Übliche
Themen erhalten automatisch Farbe und Symbol, andere reihum; die Farbe ist änderbar.
**Rolle:** Verwaltung
**Priorität:** Muss
<a id="fr-014"></a>
### FR-014: Einrichtungen pflegen
**Beschreibung:** Die Verwaltung pflegt Einrichtungen mit externer ID, Name, Thema, Adresse,
Kurzbeschreibung und optionalen Koordinaten. Breiten- und Längengrad sind nur gemeinsam
gültig. Eine Einrichtung ohne Koordinaten erscheint nicht auf Karten.
**Rolle:** Verwaltung
**Priorität:** Muss
<a id="fr-015"></a>
### FR-015: Gebäude als optionale Ebene
**Beschreibung:** Eine Einrichtung kann Gebäude haben. Maßnahmen lassen sich einem Gebäude
ihrer Einrichtung zuordnen; Punkte und Vergleiche bleiben pro Einrichtung.
**Rolle:** Verwaltung
**Priorität:** Kann
<a id="fr-016"></a>
### FR-016: Maßnahmen pflegen
**Beschreibung:** Die Verwaltung pflegt Maßnahmen je Einrichtung mit Status (offen,
beschlossen, in Umsetzung, abgeschlossen, verworfen). Maßnahmen zeigen, wofür eine Einrichtung
Geld braucht, tragen aber selbst keine Punkte.
**Rolle:** Verwaltung
**Priorität:** Muss
<a id="fr-017"></a>
### FR-017: Ausgaben pflegen
**Beschreibung:** Die Verwaltung pflegt Ist-Ausgaben je Einrichtung und Haushaltsjahr. Diese
Werte sind die Grundlage für den Vergleich mit den Bürgerpunkten.
**Rolle:** Verwaltung
**Priorität:** Muss
<a id="fr-018"></a>
### FR-018: CSV-Import mit Vorschau
**Beschreibung:** Einrichtungen, Gebäude, Maßnahmen und Ausgaben lassen sich per CSV
importieren, einzeln über die Oberfläche mit Vorschau vor dem Speichern oder alle vier auf
einmal per Befehl. Der Gesamtimport läuft in einer Transaktion (bei einem Fehler wird nichts
gespeichert), bietet einen Probelauf und ist wiederholbar: Zeilen werden über die externe ID
aktualisiert statt doppelt angelegt.
**Rolle:** Verwaltung
**Priorität:** Muss
<a id="fr-019"></a>
### FR-019: CSV-Export des Katalogs
**Beschreibung:** Jede Katalogliste lässt sich als CSV exportieren.
**Rolle:** Verwaltung
**Priorität:** Soll
<a id="fr-020"></a>
### FR-020: Öffentliche Suche
**Beschreibung:** Besucher durchsuchen Einrichtungen und passende Maßnahmen über eine
Suchleiste. Treffer verlinken auf die Ergebnisse und auf „Punkte verteilen“. Die Suche ist
ohne Anmeldung und ohne JavaScript nutzbar.
**Rolle:** Besucher
**Priorität:** Soll

---
## 3. Punkte verteilen
<a id="fr-021"></a>
### FR-021: Budget von 100 Punkten
**Beschreibung:** Jeder Zugang hat ein Budget von 100 Punkten. Die Summe der vergebenen Punkte
darf 100 nie überschreiten; ein Speichern darüber wird abgewiesen.
**Rolle:** System
**Priorität:** Muss
<a id="fr-022"></a>
### FR-022: Punkte an Einrichtung oder ganzes Thema
**Beschreibung:** Bürger vergeben Punkte an einzelne Einrichtungen oder an ein ganzes Thema
(„… allgemein“). Je Ziel gibt es höchstens eine Vergabe pro Zugang.
**Rolle:** Bürger
**Priorität:** Muss
<a id="fr-023"></a>
### FR-023: Verteilung bearbeiten und speichern
**Beschreibung:** Bürger ändern Punkte je Ziel per Plus/Minus in Einerschritten oder
per direkter Zahleneingabe; zulässig sind nur ganze, nicht negative Zahlen. Vergebene und freie
Punkte sowie die Summe je Thema aktualisieren sich bei jeder Änderung sofort, als Zahl und als
Raster aus 100 Feldern, in dem Punkte an ein ganzes Thema erkennbar sind. Gespeichert wird die
ganze Verteilung auf einmal; ein Teil des Budgets darf frei bleiben. Bürger können jederzeit
umverteilen. Für die Auswertung zählt je Zugang nur die zuletzt erfolgreich gespeicherte
Verteilung.
**Rolle:** Bürger
**Priorität:** Muss
<a id="fr-024"></a>
### FR-024: Ziele filtern und auf der Karte finden
**Beschreibung:** In „Punkte verteilen“ lassen sich Ziele nach Thema filtern und
Einrichtungen auf einer Karte finden. Eine Liste ist die gleichwertige Alternative zur Karte.
**Rolle:** Bürger
**Priorität:** Soll

<a id="fr-025"></a>
### FR-025: Eigene Verteilung mit dem Gesamtbild vergleichen
**Beschreibung:** Bürger sehen ihre eigene Verteilung neben der Verteilung aller Teilnehmenden.
**Rolle:** Bürger
**Priorität:** Kann
<a id="fr-026"></a>
### FR-026: Erledigte Einrichtungen nicht wählbar
**Beschreibung:** Als erledigt markierte Einrichtungen fehlen in „Punkte verteilen“ (Liste und
Karte). Ein Speichern mit Punkten an einer erledigten Einrichtung wird mit Hinweis abgewiesen.
**Rolle:** System
**Priorität:** Muss
<a id="fr-027"></a>
### FR-027: Hinweis auf angenommene Vorschläge
**Beschreibung:** Angenommene Vorschläge erscheinen in „Punkte verteilen“ als Hinweis an ihrer
Einrichtung oder, ohne Einrichtung, beim Thema („… allgemein“), mit Link zum Vorschlag. Sie
sind kein eigenes Punkteziel.
**Rolle:** Bürger
**Priorität:** Soll
<a id="fr-028"></a>
### FR-028: Ziele per QR-Code verlinken
**Beschreibung:** Für jede Einrichtung und jedes Thema gibt es einen direkten Link auf das Ziel in
„Punkte verteilen“, den die Verwaltung als QR-Code ausgeben kann (z. B. als Aushang vor Ort).
Der QR-Code enthält keinen Zugangscode.
**Rolle:** Verwaltung
**Priorität:** Kann
<a id="fr-029"></a>
### FR-029: Snapshot als Abstimmungszeitpunkt
**Beschreibung:** Die Beteiligung bleibt fortlaufend ohne feste Runden. Die Verwaltung
hält zu einem beliebigen Zeitpunkt einen benannten, datierten Snapshot fest (aggregierte Punkte
je Ziel, Teilnehmende, Ziele, Ist-Ausgaben). Snapshots sind unveränderlich, werden aus dem
Ereignis-Log berechnet ([FR-031](#fr-031), [FR-063](#fr-063)), lassen sich in der Anwendung einsehen, als CSV
herunterladen und miteinander vergleichen. So kann sich die Stadt, z. B. für eine
Gemeinderatssitzung, auf einen festen Abstimmungsstand beziehen.
**Rolle:** Verwaltung
**Priorität:** Soll
<a id="fr-030"></a>
### FR-030: Verlauf zurückgekommener und verfallener Punkte
**Beschreibung:** „Punkte verteilen“ zeigt Punkte, die in den letzten 30 Tagen zurückgekommen
oder verfallen sind, mit Anlass.
**Rolle:** Bürger
**Priorität:** Soll
<a id="fr-031"></a>
### FR-031: Unveränderliches Ereignis-Log
**Beschreibung:** Jede Punkteänderung (vergeben, entzogen, zurückgegeben, verfallen) wird in
derselben Transaktion als unveränderliches Ereignis mit Delta, Zeitpunkt und optional der
auslösenden Maßnahme gespeichert. Ändern und Löschen von Ereignissen ist ausgeschlossen. Beim
Löschen eines Zugangs bleibt das Log pseudonym erhalten.
**Rolle:** System
**Priorität:** Muss
<a id="fr-032"></a>
### FR-032: Rückfluss bei Umsetzung einer Maßnahme
**Beschreibung:** Geht eine Maßnahme auf „in Umsetzung“ (über Admin, Verwaltungsseite oder
CSV-Import, auch bei Neuanlage), erhalten alle Unterstützer ihre Punkte auf der zugehörigen
Einrichtung zurück. Punkte an ein ganzes Thema bleiben. „Verworfen“ löst keinen Rückfluss aus.
Parallel neu vergebene Punkte bleiben erhalten.
**Rolle:** System
**Priorität:** Muss
<a id="fr-033"></a>
### FR-033: Verfall nach Inaktivität
**Beschreibung:** Alle Punkte eines Zugangs verfallen nach 183 Tagen ohne Aktivität
(`STADTSTIMME_POINTS_EXPIRY_DAYS`). Ergebnisse zählen verfallene Punkte sofort nicht mehr mit.
Entzogen werden sie, sobald die Person zurückkommt, oder durch den täglichen Lauf. Jede
Nutzung mit dem Zugang verlängert die Frist.
**Rolle:** System
**Priorität:** Muss
<a id="fr-034"></a>
### FR-034: Tägliche Aufgaben
**Beschreibung:** Ein täglicher Lauf (Standard 02:00 UTC, `DAILY_TASKS_AT`) verschickt zuerst
Verfallswarnungen und lässt danach Punkte verfallen. Beide Schritte sind idempotent, jederzeit
manuell startbar, und ein Fehler im einen hält den anderen nicht auf.
**Rolle:** System
**Priorität:** Muss

---
## 4. Öffentliche Übersicht und Ergebnisse
<a id="fr-035"></a>
### FR-035: Öffentliche Übersicht
**Beschreibung:** Die Übersicht ist ohne Anmeldung erreichbar und zeigt den Vergleich je Thema
(Anteil Bürgerpunkte gegen Anteil Ist-Ausgaben), eine Karte mit Liste der Einrichtungen, den
Datenstand, die Zahl der Teilnehmenden, die meistunterstützten Vorschläge mit Link und
Neuigkeiten.
**Rolle:** Besucher
**Priorität:** Muss
<a id="fr-036"></a>
### FR-036: Eigene Punkte in der Übersicht
**Beschreibung:** Angemeldete Bürger sehen in der Übersicht zusätzlich ihre eigene Verteilung
im Vergleich zum Anteil aller Bürgerpunkte und zu den Ausgaben, ihre vergebenen und freien
Punkte als Zahl und Raster aus 100 Feldern mit Link zu „Punkte verteilen“, ihre eigenen
Vorschläge und bis wann ihre Punkte gültig sind.
**Rolle:** Bürger
**Priorität:** Soll
<a id="fr-037"></a>
### FR-037: Vergleich mit dem letzten abgeschlossenen Haushaltsjahr
**Beschreibung:** Alle Vergleiche verwenden die Ist-Ausgaben des letzten abgeschlossenen
Haushaltsjahres. Fehlen solche Ausgaben, zeigt die Seite das ausdrücklich an.
**Rolle:** System
**Priorität:** Muss
<a id="fr-038"></a>
### FR-038: Lücke je Einrichtung und je Thema
**Beschreibung:** Die Ergebnisseite zeigt je Einrichtung und je ganzem Thema die Lücke in
Prozentpunkten: Anteil Bürgerpunkte minus Anteil Ist-Ausgaben. Der Themenvergleich enthält alle
Punkte des Themas inkl. „… allgemein“ und alle Ausgaben des Themas.
**Rolle:** Besucher
**Priorität:** Muss
<a id="fr-039"></a>
### FR-039: Detail je Einrichtung
**Beschreibung:** Zu jeder Einrichtung lassen sich in den Ergebnissen Punkte, Ausgaben und
zugehörige Maßnahmen im Detail ansehen. Die Auswahl erfolgt über die Liste oder die
Markierung auf der Ergebniskarte.
**Rolle:** Besucher
**Priorität:** Soll
<a id="fr-040"></a>
### FR-040: Einordnung der Belastbarkeit
**Beschreibung:** Die Ergebnisse nennen Stand, Zahl der Mitmachenden, vergebene Punkte,
durchschnittliche Punkte je Person, Anteil an ganze Themen und Summe der Ausgaben sowie den
Hinweis, dass die Zahlen nicht repräsentativ sind.
**Rolle:** Besucher
**Priorität:** Soll
<a id="fr-041"></a>
### FR-041: Ergebnisse als CSV
**Beschreibung:** Die Ergebnistabelle lässt sich als CSV herunterladen (Semikolon,
Dezimalkomma, BOM für deutsche Tabellenprogramme). Texte werden gegen Formel-Injektion
geschützt.
**Rolle:** Besucher
**Priorität:** Soll
<a id="fr-042"></a>
### FR-042: Karten der Einrichtungen
**Beschreibung:** Übersicht, „Punkte verteilen“, Ergebnisse und Vorschläge zeigen Einrichtungen
mit Koordinaten auf einer zoombaren Karte, immer zusammen mit einer gleichwertigen Liste.
Markierungen zeigen das Thema (Farbe und Symbol) und mit ihrer Größe den Anteil an den
Bürgerpunkten. Ein Klick auf eine Markierung führt zum zugehörigen Ziel bzw. zu seinen Details.
Angemeldete Bürger können zwischen allen Einrichtungen und den von ihnen gewichteten
umschalten. Fällt der Kachelserver aus, wechselt die Karte auf einen
Ersatz und zeigt danach mindestens die Marker.
**Rolle:** Besucher
**Priorität:** Soll

---
## 5. Vorschläge
<a id="fr-043"></a>
### FR-043: Vorschlag einreichen
**Beschreibung:** Angemeldete Bürger reichen einen Vorschlag in drei Schritten ein: Anliegen
(Titel 8–80 Zeichen, Beschreibung optional bis 600 Zeichen), Einordnen, Prüfen. Vor
dem Einreichen können sie zu jedem vorherigen Schritt zurückkehren und korrigieren, ohne
Eingaben zu verlieren.
**Rolle:** Bürger
**Priorität:** Muss
<a id="fr-044"></a>
### FR-044: Thema und Ort eines Vorschlags
**Beschreibung:** Ein Vorschlag hat immer ein Thema. Der Ort ist „allgemein“, eine bekannte
Einrichtung passend zum Thema oder ein neuer Punkt auf der Karte (per Klick oder Kartenmitte
für Tastaturnutzung). Einrichtung und Punkt sind nie gleichzeitig gesetzt. Ohne JavaScript
stehen „allgemein“ und „bekannter Ort“ zur Verfügung.
**Rolle:** Bürger
**Priorität:** Muss
<a id="fr-045"></a>
### FR-045: Tageslimit für Vorschläge
**Beschreibung:** Ein Zugang darf höchstens 5 Vorschläge pro Tag einreichen
(`STADTSTIMME_PROPOSALS_PER_DAY`); darüber wird mit Hinweis abgewiesen.
**Rolle:** System
**Priorität:** Muss
<a id="fr-046"></a>
### FR-046: Ähnliche Einträge vorschlagen
**Beschreibung:** Beim Schreiben zeigt „Gibt es das schon?“ ähnliche Vorschläge und offene
Maßnahmen (Abgleich über Wortstämme), damit Doppelungen vermieden werden.
**Rolle:** Bürger
**Priorität:** Soll
<a id="fr-047"></a>
### FR-047: Vorschläge sofort öffentlich
**Beschreibung:** Ein eingereichter Vorschlag ist ohne Freigabe sofort öffentlich sichtbar und
unterstützbar.
**Rolle:** System
**Priorität:** Muss
<a id="fr-048"></a>
### FR-048: Vorschlag unterstützen
**Beschreibung:** Angemeldete Bürger unterstützen beliebig viele offene Vorschläge anderer,
jeden höchstens einmal, und können die Unterstützung zurückziehen. Unterstützungen sind
unabhängig vom Budget der 100 Punkte. Eigene sowie entschiedene Vorschläge sind nicht
unterstützbar; abgelehnte Vorschläge erscheinen nicht mehr unter den eigenen unterstützten.
**Rolle:** Bürger
**Priorität:** Muss
<a id="fr-049"></a>
### FR-049: Weg eines Vorschlags
**Beschreibung:** Jeder Vorschlag zeigt seinen Schritt: „Sammelt“ (unter der Schwelle von
50 Unterstützungen, `STADTSTIMME_PROPOSAL_SUPPORT_THRESHOLD`), „In Prüfung“ (Schwelle erreicht,
seit dem Zeitpunkt der N-ten Unterstützung) und „Entschieden“ (angenommen oder abgelehnt).
Solange ein Vorschlag sammelt, zeigt er die noch benötigten Unterstützungen. Die
Liste lässt sich nach Schritt filtern, auch ohne JavaScript.
**Rolle:** Besucher
**Priorität:** Muss
<a id="fr-050"></a>
### FR-050: Öffentliche Antwort der Stadt
**Beschreibung:** Entschiedene Vorschläge zeigen die öffentliche Begründung der Stadt, das
Entscheidungsdatum und gegebenenfalls die daraus entstandene Maßnahme. Angenommene
und abgelehnte Vorschläge bleiben dauerhaft sichtbar, weil es keine abgeschlossenen Runden gibt.
**Rolle:** Besucher
**Priorität:** Muss
<a id="fr-051"></a>
### FR-051: Neuer Ort wird Einrichtung
**Beschreibung:** Wird ein Vorschlag mit neuem Ort angenommen, legt das System daraus eine
Einrichtung an (Name = Titel, Thema und Koordinaten vom Vorschlag, externe ID
`VORSCHLAG-<Nr>`) und verknüpft den Vorschlag mit ihr. Sie ist danach wählbar und in Karten
und Ergebnissen enthalten.
**Rolle:** System
**Priorität:** Soll
<a id="fr-052"></a>
### FR-052: Vorschläge melden
**Beschreibung:** Bürger melden unpassende Vorschläge an die Verwaltung.
**Rolle:** Bürger
**Priorität:** Kann
<a id="fr-053"></a>
### FR-053: Foto zum Vorschlag
**Beschreibung:** Bürger fügen einem Vorschlag ein Foto bei.
**Rolle:** Bürger
**Priorität:** Kann
<a id="fr-054"></a>
### FR-054: Vorschlagsliste durchsuchen, filtern und sortieren
**Beschreibung:** Die Vorschlagsliste ist nach Titel und Ort durchsuchbar, nach Thema und Schritt
filterbar und nach Zahl der Unterstützungen sortierbar. Angemeldete Bürger wählen zwischen allen
und nur ihren eigenen Vorschlägen. Filter und Sortierung funktionieren ohne JavaScript.
**Rolle:** Besucher
**Priorität:** Soll
<a id="fr-055"></a>
### FR-055: Vorschlag teilen
**Beschreibung:** Jeder Vorschlag hat einen dauerhaften, öffentlichen Link, den Ersteller und
andere teilen können. Der Link enthält keinen Zugangscode und keine Angabe zum Ersteller.
**Rolle:** Bürger
**Priorität:** Kann

---
## 6. Verwaltungsseite
<a id="fr-056"></a>
### FR-056: Wartet auf Sie
**Beschreibung:** Die Verwaltungsseite listet Vorschläge in Prüfung mit ihrer Antwortfrist von
14 Tagen ab Erreichen der Schwelle (`STADTSTIMME_PROPOSAL_REVIEW_DAYS`), früheste Frist zuerst.
**Rolle:** Verwaltung
**Priorität:** Muss
<a id="fr-057"></a>
### FR-057: Vorschlag entscheiden
**Beschreibung:** Die Verwaltung nimmt einen Vorschlag an oder lehnt ihn ab, jederzeit, auch
vor Erreichen der Schwelle. Pflicht ist eine öffentliche Antwort mit mindestens 20 Zeichen,
optional eine verknüpfte Maßnahme. Ein bereits entschiedener Vorschlag kann nicht erneut
entschieden werden. Entscheiden erfordert das Recht „Vorschlag ändern“.
**Rolle:** Verwaltung
**Priorität:** Muss
<a id="fr-058"></a>
### FR-058: Beteiligung beobachten
**Beschreibung:** Die Verwaltung sieht die Beteiligung nur als Summen: eingelöste Codes je
Woche, eingelöste Codes und Zugänge mit vergebenen Punkten. Rückschlüsse auf einzelne Personen
sind nicht möglich.
**Rolle:** Verwaltung
**Priorität:** Muss
<a id="fr-059"></a>
### FR-059: Vorschläge nach Schritt
**Beschreibung:** Die Verwaltung sieht alle Vorschläge gruppiert nach Schritt mit Zugang zur
Entscheidungsseite.
**Rolle:** Verwaltung
**Priorität:** Muss
<a id="fr-060"></a>
### FR-060: Einrichtungen nach Lücke
**Beschreibung:** Die Verwaltung sieht Einrichtungen sortiert nach Lücke mit ihren Maßnahmen und
einem Link zur Datenpflege.
**Rolle:** Verwaltung
**Priorität:** Soll
<a id="fr-061"></a>
### FR-061: Einrichtung als erledigt markieren
**Beschreibung:** Die Verwaltung markiert eine Einrichtung als erledigt, auch ohne passende
Maßnahme. Vorher bestätigt sie eine Rückfrage mit Zahl der Unterstützer und Punkte. Danach
gehen alle Punkte an dieser Einrichtung an die Unterstützer zurück, und Betroffene mit
E-Mail-Hinweis werden benachrichtigt; Themenpunkte bleiben. Dasselbe gilt, wenn eine Einrichtung
dauerhaft aus dem Katalog genommen wird: Sie wird dann als erledigt archiviert statt gelöscht,
weil das Ereignis-Log auf sie verweist. Erfordert das Recht „Einrichtung ändern“.
**Rolle:** Verwaltung
**Priorität:** Muss
<a id="fr-062"></a>
### FR-062: Einrichtung wieder öffnen
**Beschreibung:** Eine erledigte Einrichtung wird wieder wählbar über „Wieder öffnen“ oder
automatisch, sobald die Stadt einen Vorschlag an diesem Ort annimmt. In Ergebnissen, Suche und
als bekannter Ort bei Vorschlägen bleibt sie immer sichtbar.
**Rolle:** Verwaltung
**Priorität:** Muss
<a id="fr-063"></a>
### FR-063: Stichtags-Export
**Beschreibung:** Die Verwaltung lädt für einen Stichtag eine CSV mit Punkten und Unterstützern
je Ziel zum Tagesende herunter, ergänzt um die Zahl der Teilnehmenden und die Ist-Ausgaben je
Ziel. Die Werte werden aus dem Ereignis-Log berechnet und sind für
denselben Stichtag reproduzierbar.
**Rolle:** Verwaltung
**Priorität:** Muss
<a id="fr-064"></a>
### FR-064: Zugänge je Charge
**Beschreibung:** Die Verwaltung sieht je Charge, wie viele Codes ausgegeben und eingelöst sind.
**Rolle:** Verwaltung
**Priorität:** Soll
<a id="fr-065"></a>
### FR-065: Inhalte moderieren
**Beschreibung:** Die Verwaltung kann unpassende Vorschläge mit Begründung ablehnen ([FR-057](#fr-057))
oder doppelte und unzulässige Vorschläge mit Begründung entfernen. Ein entfernter
Vorschlag ist öffentlich nicht mehr sichtbar; sein Ersteller sieht in „Mein Bereich“, dass und
warum er entfernt wurde.
**Rolle:** Verwaltung
**Priorität:** Muss
<a id="fr-066"></a>
### FR-066: Berichte auf der Verwaltungsseite
**Beschreibung:** Die Verwaltung erstellt aus Snapshots ([FR-029](#fr-029)) aufbereitete Berichte für den
Gemeinderat und wählt den Zeitraum der Auswertung. Das Protokoll der
Verwaltungsaktionen regelt.
**Rolle:** Verwaltung
**Priorität:** Kann
<a id="fr-067"></a>
### FR-067: Zugang finden und einsehen
**Beschreibung:** Die Verwaltung findet einen Zugang über die letzten 8 Zeichen seines Codes
(z. B. bei einer Anfrage per Telefon) und sieht Status, Charge, Zeitpunkt des Einlösens,
letzte Aktivität und die Vorschläge des Zugangs. Die Punkteverteilung des Zugangs sieht sie
nicht. Von dort kann sie den Zugang schließen und wieder öffnen ([FR-068](#fr-068)), aber nichts
im Namen des Bürgers ändern.
**Rolle:** Verwaltung
**Priorität:** Soll
**Hinweis:** Codes liegen nur als Hash vor; für die Suche braucht es einen eigenen
Hash der letzten 8 Zeichen.
<a id="fr-068"></a>
### FR-068: Zugang schließen und wieder öffnen
**Beschreibung:** Die Verwaltung schließt einen Zugang (z. B. bei Wegzug) und öffnet ihn bei
Bedarf wieder. Das Schließen wirkt sofort, auch auf bestehende Anmeldungen. Alle Punkte des
Zugangs werden entzogen (Ereignis „entzogen“); seine Vorschläge und Unterstützungen bleiben
erhalten. Erfordert ein eigenes Recht.
**Rolle:** Verwaltung
**Priorität:** Soll

---
## 7. E-Mail-Hinweise
<a id="fr-069"></a>
### FR-069: E-Mail freiwillig hinterlegen
**Beschreibung:** Bürger hinterlegen freiwillig eine E-Mail-Adresse für Hinweise, ändern oder
entfernen sie und wählen, welche Arten von Hinweisen sie erhalten. Die Adresse wird verschlüsselt und getrennt von den Punkten gespeichert und mit
dem Zugang gelöscht.
**Rolle:** Bürger
**Priorität:** Soll
<a id="fr-070"></a>
### FR-070: Double-Opt-in
**Beschreibung:** Hinweise gehen erst nach Bestätigung über einen Link raus. Der Link ist
72 Stunden gültig, das Token wird nur als Hash gespeichert, und das Öffnen des Links bestätigt
erst nach Klick auf einen Knopf. Eine neue Bestätigungsmail ist frühestens nach 10 Minuten
möglich.
**Rolle:** System
**Priorität:** Soll
<a id="fr-071"></a>
### FR-071: Verfallswarnung
**Beschreibung:** Bestätigte Empfänger erhalten 14 Tage vor dem Verfall
(`STADTSTIMME_POINTS_EXPIRY_WARNING_DAYS`) eine Warnung, einmal je Inaktivitätsphase.
**Rolle:** System
**Priorität:** Soll
<a id="fr-072"></a>
### FR-072: Hinweis bei Rückfluss
**Beschreibung:** Bestätigte Empfänger erhalten eine E-Mail, wenn Punkte zu ihnen
zurückkommen (Maßnahme in Umsetzung oder Einrichtung erledigt).
**Rolle:** System
**Priorität:** Soll
<a id="fr-073"></a>
### FR-073: Erinnerung an freie Punkte
**Beschreibung:** Bestätigte Empfänger mit freien Punkten erhalten eine Erinnerung, ihre Punkte
zu verteilen. Die Erinnerung wiederholt sich in einem konfigurierbaren Abstand, solange Punkte
frei sind, und lässt sich einzeln abbestellen.
**Rolle:** System
**Priorität:** Kann
<a id="fr-074"></a>
### FR-074: Hinweis zu eigenen und unterstützten Vorschlägen
**Beschreibung:** Bestätigte Empfänger erhalten einen Hinweis, wenn ein eigener oder unterstützter
Vorschlag die Schwelle erreicht, angenommen, abgelehnt oder von der Stadt beantwortet wird.
**Rolle:** System
**Priorität:** Sol
<a id="fr-075"></a>
### FR-075: Abmelden mit einem Klick
**Beschreibung:** Jede Hinweis-Mail enthält einen Abmeldelink und `List-Unsubscribe`
(Ein-Klick nach RFC 8058). Abmelden löscht die Adresse.
**Rolle:** Bürger
**Priorität:** Soll
<a id="fr-076"></a>
### FR-076: Robust bei Mailausfall
**Beschreibung:** Ist der Mailserver nicht erreichbar, schlägt keine fachliche Aktion fehl
(z. B. Speichern einer Maßnahme); es wird lediglich keine Mail versendet.
**Rolle:** System
**Priorität:** Soll

---
## 8. Systemfunktionen
<a id="fr-077"></a>
### FR-077: Demo-Modus
**Beschreibung:** Im Demo-Modus lädt das System fiktive Testdaten (Mannheim) in einen leeren
Katalog, legt Demo-Codes und einen Demo-Admin an und macht Admin und Verwaltungsseite
erreichbar. Ohne Demo-Modus sind beide nicht erreichbar.
**Rolle:** System
**Priorität:** Muss
<a id="fr-078"></a>
### FR-078: Health-Check
**Beschreibung:** Ein öffentlicher Endpunkt meldet, ob die Anwendung läuft und die Datenbank
erreichbar ist.
**Rolle:** System
**Priorität:** Soll
<a id="fr-079"></a>
### FR-079: Stadtname konfigurierbar
**Beschreibung:** Der Stadtname in Logo und Texten kommt aus `STADTSTIMME_CITY_NAME`, damit
andere Kommunen die Anwendung ohne Codeänderung nutzen können.
**Rolle:** System
**Priorität:** Soll

---
## Offene Punkte

- **Löschen eines Zugangs durch den Bürger:** Das Datenmodell sieht das Löschen vor (Ereignis
  „entzogen“, E-Mail wird mitgelöscht), eine Funktion für Bürger gibt es aber nicht. Für die
  Datenschutzfreigabe (Phase 6) zu klären.
- **Personas und Akzeptanzkriterien** sind nicht dokumentiert. Prioritäten oben sind aus dem
  Produktziel und den ADRs abgeleitet und sollten im Team bestätigt werden.
