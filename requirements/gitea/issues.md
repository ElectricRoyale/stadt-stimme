# Issues – StadtStimme

Ein Issue je funktionaler Anforderung. Je Issue: Titel, Beschreibung (Markdown), Labels und Meilenstein.
Empfohlene Labels in Gitea anlegen: `Priorität/Muss`, `Priorität/Soll`, `Priorität/Kann` (exklusiv) und `Rolle/Bürger`, `Rolle/Besucher`, `Rolle/Verwaltung`, `Rolle/System`.

Sortiert nach Meilenstein, damit ihr sie der Reihe nach anlegen könnt.

**Stack:** Backend Python (Django mit REST-API), Frontend React. Die Kriterien sind markiert:
`[API]` Backend und Endpunkt, `[DB]` Datenbank, `[UI]` React-Oberfläche, `[Test]` geforderter Test.
Endpunkt-Pfade sind Vorschläge und dürfen bei der Umsetzung angepasst werden.

**Abhängigkeiten:** „Abhängig von“ nennt nur die direkten Voraussetzungen, „Blockiert“ die Issues,
die auf dieses warten. Keine Abhängigkeit zeigt auf einen späteren Meilenstein, und es gibt keine Zyklen.
In Gitea nach dem Anlegen unter „Abhängigkeiten“ mit den Issue-Nummern eintragen.

**Definition of Done für jedes Issue** (gilt zusätzlich, steht deshalb nicht in jedem Issue):
- [ ] Alle Akzeptanzkriterien erfüllt und im Browser geprüft (Handy und Desktop)
- [ ] Backend: pytest gegen PostgreSQL, Ruff und Mypy grün; neue Endpunkte prüfen Rechte
- [ ] Frontend: Komponententests (z. B. Vitest und React Testing Library), ESLint grün, per Tastatur bedienbar
- [ ] CI grün, Dokumentation (README, DECISIONS.md) bei Bedarf aktualisiert

---

## S1 – MVP: Prioritäten setzen und Ergebnis sehen

### FR-001: Anmeldung mit Aktivierungscode

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-003, FR-011
**Blockiert:** FR-002, FR-004, FR-005, FR-006, FR-022

**Anforderung:** Bürger melden sich mit dem Code aus dem Brief der Stadt an. Ein Code ist 16 Zeichen Crockford-Base32 (80 Bit); Eingaben mit Bindestrichen, Leerzeichen oder Kleinbuchstaben werden normalisiert. Ein QR-Code auf dem Brief füllt den Code vor; eingelöst wird erst nach dem Absenden. Ein gültiger Code legt beim ersten Einlösen genau einen Zugang an; jedes weitere Einlösen desselben Codes (auch auf einem anderen Gerät) führt in denselben Zugang. Der Code ist bis zur Entscheidung über die Gerätebindung zugleich der Login.

**Akzeptanzkriterien:**
- [ ] [API] `POST /api/zugang/` mit gültigem Code antwortet 200, legt beim ersten Mal genau einen Zugang an und setzt ein HttpOnly-Sitzungscookie
- [ ] [API] Eingaben wie `abcd efgh-jkmn pqrs` werden normalisiert und wie `ABCD-EFGH-JKMN-PQRS` behandelt
- [ ] [API] Zweites Einlösen desselben Codes (anderes Gerät) liefert denselben Zugang, keine neue Zeile in der Datenbank
- [ ] [UI] Aufruf über den QR-Link `#code=…` füllt das Feld vor, eingelöst wird erst nach Klick auf „Anmelden“
- [ ] [UI] Nach erfolgreicher Anmeldung landet man auf der Übersicht
- [ ] [Test] pytest für Normalisierung, Erst- und Folgeanmeldung; React-Test für Vorbefüllung aus dem QR-Link

Quelle: `requirements/functional-requirements.md` → FR-001
```

### FR-002: Ein Budget je Code

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Abhängig von:** FR-001
**Blockiert:** –

**Anforderung:** Jeder Code berechtigt zu genau einem Zugang mit einem Budget. Mehrfaches Teilnehmen mit demselben Code ist ausgeschlossen, auch bei gleichzeitigen Anfragen.

**Akzeptanzkriterien:**
- [ ] [DB] Unique-Constraint: höchstens ein Zugang je Code
- [ ] [API] Zwei gleichzeitige Einlöse-Anfragen mit demselben neuen Code erzeugen genau einen Zugang (Nebenläufigkeitstest)
- [ ] [API] Ein Zugang hat nie mehr als ein Budget von 100 Punkten, egal auf wie vielen Geräten er angemeldet ist
- [ ] [Test] pytest mit zwei parallelen Transaktionen gegen PostgreSQL

Quelle: `requirements/functional-requirements.md` → FR-002
```

### FR-003: Code nur als Hash speichern

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Abhängig von:** – (keine)
**Blockiert:** FR-001, FR-011

**Anforderung:** Das System speichert keinen Code im Klartext, sondern nur einen HMAC-Hash mit einem eigenen Pepper (`STADTSTIMME_CODE_PEPPER`, sonst `DJANGO_SECRET_KEY`). Der Klartext eines neuen Codes ist nur in der Ausgabe beim Erzeugen sichtbar.

**Akzeptanzkriterien:**
- [ ] [DB] Die Code-Tabelle enthält nur einen HMAC-Hash (64 Zeichen), keine Spalte mit Klartext
- [ ] [API] Der Hash nutzt `STADTSTIMME_CODE_PEPPER`, ohne eigenen Wert `DJANGO_SECRET_KEY`
- [ ] [API] Kein API-Endpunkt, Log-Eintrag oder Admin-Export gibt einen Code im Klartext aus
- [ ] [Test] pytest: gespeicherter Wert ≠ Klartext; gleicher Klartext mit anderem Pepper ergibt anderen Hash

Quelle: `requirements/functional-requirements.md` → FR-003
```

### FR-004: Sperre nach Fehlversuchen

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Abhängig von:** FR-001
**Blockiert:** FR-010

**Anforderung:** Nach 10 fehlgeschlagenen Anmeldeversuchen (`STADTSTIMME_MAX_FAILED_ATTEMPTS`) pro Client wird die Anmeldung für 60 Minuten (`STADTSTIMME_LOCKOUT_MINUTES`) gesperrt. Die IP-Adresse wird dafür nur als Hash gespeichert. Die Sperre gilt für Code-Anmeldung und Verwaltungsanmeldung gleichermaßen.

**Akzeptanzkriterien:**
- [ ] [API] Nach 10 Fehlversuchen (`STADTSTIMME_MAX_FAILED_ATTEMPTS`) innerhalb von 60 Minuten antwortet `POST /api/zugang/` mit 429, auch bei richtigem Code
- [ ] [API] Nach Ablauf der Sperre (`STADTSTIMME_LOCKOUT_MINUTES`) ist die Anmeldung wieder möglich
- [ ] [API] Dieselbe Sperre gilt für die Verwaltungsanmeldung
- [ ] [DB] Fehlversuche speichern die IP-Adresse nur als Hash
- [ ] [Test] pytest für Grenze 10/11, Ablauf der Sperre und Hash statt IP

Quelle: `requirements/functional-requirements.md` → FR-004
```

### FR-005: Verständliche Fehlermeldungen beim Einlösen

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-001
**Blockiert:** –

**Anforderung:** Bei falsch formatiertem, unbekanntem oder gesperrtem Code sowie bei aktiver Sperre nach Fehlversuchen erhält der Bürger je eine eigene, verständliche Meldung mit dem nächsten Schritt. Eine Hilfe erklärt, wo der Code steht.

**Akzeptanzkriterien:**
- [ ] [API] Fehlerantworten unterscheiden per Code-Feld: `format`, `unbekannt`, `gesperrt`, `zu_viele_versuche`
- [ ] [UI] Jede Fehlerart zeigt einen eigenen deutschen Text mit nächstem Schritt (z. B. „16 Zeichen, z. B. ABCD-EFGH-JKMN-PQRS“)
- [ ] [UI] Die Meldung ist mit dem Eingabefeld verknüpft (`aria-describedby`) und wird vom Screenreader vorgelesen
- [ ] [UI] Eine aufklappbare Hilfe zeigt, wo der Code auf dem Brief steht

Quelle: `requirements/functional-requirements.md` → FR-005
```

### FR-006: Angemeldet bleiben und Abmelden

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-001
**Blockiert:** FR-007, FR-009, FR-034

**Anforderung:** Nach dem Einlösen bleibt der Bürger auf dem Gerät angemeldet (Sitzungsdauer 183 Tage, `STADTSTIMME_SESSION_DAYS`), bis er sich abmeldet. Abmelden beendet die Sitzung auf diesem Gerät.

**Akzeptanzkriterien:**
- [ ] [API] Das Sitzungscookie ist 183 Tage gültig (`STADTSTIMME_SESSION_DAYS`), HttpOnly, im Betrieb Secure
- [ ] [API] `POST /api/abmelden/` beendet nur die Sitzung dieses Geräts; andere Geräte bleiben angemeldet
- [ ] [UI] Nach Neuladen des Browsers ist man weiterhin angemeldet
- [ ] [UI] „Abmelden“ ist in der Navigation erreichbar und führt zur Anmeldeseite

Quelle: `requirements/functional-requirements.md` → FR-006
```

### FR-009: Geschützte Bürgerfunktionen

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Abhängig von:** FR-006
**Blockiert:** FR-024, FR-044

**Anforderung:** Punkte verteilen, Vorschläge einreichen und unterstützen sowie E-Mail-Hinweise verwalten sind nur mit gültigem Zugang möglich. Ohne Anmeldung werden Besucher zur Code-Eingabe geleitet. Bereits angemeldete Bürger werden von der Code-Eingabe zur Übersicht weitergeleitet.

**Akzeptanzkriterien:**
- [ ] [API] Alle schreibenden Bürger-Endpunkte (Verteilen, Vorschlag, Unterstützen, E-Mail) antworten ohne gültige Sitzung mit 401
- [ ] [UI] Geschützte Seiten leiten ohne Anmeldung auf die Code-Eingabe weiter
- [ ] [UI] Angemeldete, die die Code-Eingabe aufrufen, werden zur Übersicht weitergeleitet
- [ ] [Test] pytest-Rechte-Matrix: jeder Bürger-Endpunkt ohne Sitzung → 401

Quelle: `requirements/functional-requirements.md` → FR-009
```

### FR-011: Aktivierungscodes erzeugen

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-003
**Blockiert:** FR-001, FR-012, FR-059, FR-065, FR-068, FR-078

**Anforderung:** Die Verwaltung erzeugt Codes in Chargen (z. B. je Briefversand) mit Angabe der Charge. Die Ausgabe enthält die Klartexte einmalig zur Weitergabe an den Druck.

**Akzeptanzkriterien:**
- [ ] [API] Befehl `create_access_codes <Anzahl> --batch <Charge>` erzeugt die Codes und gibt die Klartexte genau einmal als CSV aus
- [ ] [DB] Jeder Code ist einer Charge zugeordnet und hat den Status „ausgegeben“
- [ ] [API] Codes sind eindeutig; Kollisionen werden neu erzeugt
- [ ] [Test] pytest: 20 Codes → 20 Hashes, Ausgabe enthält 20 gültige Klartexte

Quelle: `requirements/functional-requirements.md` → FR-011
```

### FR-014: Themen pflegen

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** – (keine)
**Blockiert:** FR-015, FR-023, FR-044

**Anforderung:** Die Verwaltung pflegt Themen (Kategorien) mit eindeutigem Namen. Übliche Themen erhalten automatisch Farbe und Symbol, andere reihum; die Farbe ist änderbar.

**Akzeptanzkriterien:**
- [ ] [API] Themen haben einen eindeutigen Namen; doppelte Namen werden abgewiesen
- [ ] [API] Übliche Themen (z. B. „Bildung“, „Sport“) erhalten automatisch Farbe und Symbol, andere reihum
- [ ] [UI] Die Verwaltung kann Name und Farbe eines Themas in der Datenpflege ändern
- [ ] [UI] Farbe und Symbol erscheinen einheitlich in Listen, Filtern und Karten

Quelle: `requirements/functional-requirements.md` → FR-014
```

### FR-015: Einrichtungen pflegen

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-014
**Blockiert:** FR-016, FR-017, FR-018, FR-019, FR-021, FR-023, FR-043

**Anforderung:** Die Verwaltung pflegt Einrichtungen mit externer ID, Name, Thema, Adresse, Kurzbeschreibung und optionalen Koordinaten. Breiten- und Längengrad sind nur gemeinsam gültig. Eine Einrichtung ohne Koordinaten erscheint nicht auf Karten.

**Akzeptanzkriterien:**
- [ ] [API] Einrichtungen haben externe ID (eindeutig), Name, Thema, Adresse, Beschreibung, optional Koordinaten
- [ ] [API] Nur Breitengrad ohne Längengrad (oder umgekehrt) wird mit Fehlermeldung abgewiesen
- [ ] [UI] Einrichtungen ohne Koordinaten fehlen auf Karten, erscheinen aber in Listen
- [ ] [Test] pytest für Koordinaten-Validierung (−90…90, −180…180, beide oder keine)

Quelle: `requirements/functional-requirements.md` → FR-015
```

### FR-018: Ausgaben pflegen

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-015
**Blockiert:** FR-019, FR-036, FR-038

**Anforderung:** Die Verwaltung pflegt Ist-Ausgaben je Einrichtung und Haushaltsjahr. Diese Werte sind die Grundlage für den Vergleich mit den Bürgerpunkten.

**Akzeptanzkriterien:**
- [ ] [API] Ausgaben haben Einrichtung, Haushaltsjahr und Betrag (≥ 0, zwei Nachkommastellen)
- [ ] [API] Je Einrichtung und Jahr gibt es höchstens einen Eintrag je Ausgabenart
- [ ] [UI] Die Datenpflege zeigt Ausgaben je Einrichtung und Jahr

Quelle: `requirements/functional-requirements.md` → FR-018
```

### FR-019: CSV-Import mit Vorschau

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-015, FR-018
**Blockiert:** FR-016, FR-017, FR-020, FR-078

**Anforderung:** Einrichtungen, Gebäude, Maßnahmen und Ausgaben lassen sich per CSV importieren, einzeln über die Oberfläche mit Vorschau vor dem Speichern oder alle vier auf einmal per Befehl. Der Gesamtimport läuft in einer Transaktion (bei einem Fehler wird nichts gespeichert), bietet einen Probelauf und ist wiederholbar: Zeilen werden über die externe ID aktualisiert statt doppelt angelegt.

**Akzeptanzkriterien:**
- [ ] [UI] Einzelimport mit Vorschau: neue, geänderte und fehlerhafte Zeilen werden vor dem Speichern angezeigt
- [ ] [API] `import_catalog <Ordner>` importiert alle vier Dateien in einer Transaktion; ein Fehler speichert nichts
- [ ] [API] `--dry-run` prüft ohne zu speichern
- [ ] [API] Ein zweiter Import derselben Dateien ändert nichts (Abgleich über externe ID)
- [ ] [Test] pytest mit den Demo-Daten: zweimal importieren → gleiche Anzahl Zeilen

Quelle: `requirements/functional-requirements.md` → FR-019
```

### FR-022: Budget von 100 Punkten

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Abhängig von:** FR-001
**Blockiert:** FR-024

**Anforderung:** Jeder Zugang hat ein Budget von 100 Punkten. Die Summe der vergebenen Punkte darf 100 nie überschreiten; ein Speichern darüber wird abgewiesen.

**Akzeptanzkriterien:**
- [ ] [API] `PUT /api/verteilung/` mit mehr als 100 Punkten antwortet 400 und speichert nichts
- [ ] [DB] Punkte je Vergabe sind ganze Zahlen ≥ 0
- [ ] [UI] Die Plus-Knöpfe sind gesperrt, wenn keine Punkte mehr frei sind
- [ ] [Test] pytest für 100 (gültig) und 101 (abgewiesen), auch bei parallelen Anfragen

Quelle: `requirements/functional-requirements.md` → FR-022
```

### FR-023: Punkte an Einrichtung oder ganzes Thema

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-014, FR-015
**Blockiert:** FR-024, FR-036

**Anforderung:** Bürger vergeben Punkte an einzelne Einrichtungen oder an ein ganzes Thema („… allgemein“). Je Ziel gibt es höchstens eine Vergabe pro Zugang.

**Akzeptanzkriterien:**
- [ ] [API] Ein Ziel ist entweder eine Einrichtung oder ein Thema, nie beides (DB-Constraint)
- [ ] [API] Je Zugang und Ziel gibt es höchstens eine Vergabe
- [ ] [UI] Jedes Thema hat eine Zeile „… allgemein“ neben seinen Einrichtungen

Quelle: `requirements/functional-requirements.md` → FR-023
```

### FR-024: Verteilung bearbeiten und speichern

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-009, FR-022, FR-023
**Blockiert:** FR-007, FR-025, FR-026, FR-027, FR-028, FR-029, FR-031, FR-032, FR-037, FR-074

**Anforderung:** Bürger ändern Punkte je Ziel per Plus/Minus in Einerschritten oder per direkter Zahleneingabe; zulässig sind nur ganze, nicht negative Zahlen. Vergebene und freie Punkte sowie die Summe je Thema aktualisieren sich bei jeder Änderung sofort, als Zahl und als Raster aus 100 Feldern, in dem Punkte an ein ganzes Thema erkennbar sind. Gespeichert wird die ganze Verteilung auf einmal; ein Teil des Budgets darf frei bleiben. Bürger können jederzeit umverteilen. Für die Auswertung zählt je Zugang nur die zuletzt erfolgreich gespeicherte Verteilung.

**Akzeptanzkriterien:**
- [ ] [UI] Plus/Minus ändern um genau einen Punkt; die Zahleneingabe akzeptiert nur ganze, nicht negative Zahlen
- [ ] [UI] Vergebene und freie Punkte, Summe je Thema und das Raster aus 100 Feldern aktualisieren sich sofort ohne Server-Anfrage
- [ ] [UI] Punkte an ganze Themen sind im Raster unterscheidbar (nicht nur über Farbe)
- [ ] [API] Gespeichert wird die ganze Verteilung in einer Anfrage; ein Teil des Budgets darf frei bleiben
- [ ] [UI] Nach dem Speichern erscheint eine Bestätigung; ungespeicherte Änderungen sind erkennbar

Quelle: `requirements/functional-requirements.md` → FR-024
```

### FR-036: Öffentliche Übersicht

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Besucher`

```markdown
**Abhängig von:** FR-018, FR-023, FR-038
**Blockiert:** FR-026, FR-037, FR-039, FR-041

**Anforderung:** Die Übersicht ist ohne Anmeldung erreichbar und zeigt den Vergleich je Thema (Anteil Bürgerpunkte gegen Anteil Ist-Ausgaben), eine Karte mit Liste der Einrichtungen, den Datenstand, die Zahl der Teilnehmenden, die meistunterstützten Vorschläge mit Link und Neuigkeiten.

**Akzeptanzkriterien:**
- [ ] [API] `GET /api/uebersicht/` ist ohne Anmeldung erreichbar
- [ ] [UI] Die Übersicht zeigt je Thema Anteil Bürgerpunkte neben Anteil Ist-Ausgaben, Datenstand und Zahl der Teilnehmenden
- [ ] [UI] Sie zeigt eine Karte mit Liste, die meistunterstützten Vorschläge mit Link und Neuigkeiten
- [ ] [UI] Layout funktioniert von 320 px bis Desktop

Quelle: `requirements/functional-requirements.md` → FR-036
```

### FR-038: Vergleich mit dem letzten abgeschlossenen Haushaltsjahr

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Abhängig von:** FR-018
**Blockiert:** FR-036

**Anforderung:** Alle Vergleiche verwenden die Ist-Ausgaben des letzten abgeschlossenen Haushaltsjahres. Fehlen solche Ausgaben, zeigt die Seite das ausdrücklich an.

**Akzeptanzkriterien:**
- [ ] [API] Vergleiche nutzen das letzte abgeschlossene Haushaltsjahr (Vorjahr des aktuellen Jahres oder früher)
- [ ] [UI] Das verwendete Jahr steht an jedem Vergleich
- [ ] [UI] Ohne Ausgaben eines abgeschlossenen Jahres erscheint der Hinweis „Noch keine Ist-Ausgaben“ statt 0 %

Quelle: `requirements/functional-requirements.md` → FR-038
```

### FR-078: Demo-Modus

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Abhängig von:** FR-011, FR-019
**Blockiert:** –

**Anforderung:** Im Demo-Modus lädt das System fiktive Testdaten (Mannheim) in einen leeren Katalog, legt Demo-Codes und einen Demo-Admin an und macht Admin und Verwaltungsseite erreichbar. Ohne Demo-Modus sind beide nicht erreichbar.

**Akzeptanzkriterien:**
- [ ] [API] Im Demo-Modus lädt der Start Testdaten (Mannheim) nur in einen leeren Katalog und legt Demo-Codes und Demo-Admin an
- [ ] [API] Ohne Demo-Modus sind Datenpflege und Verwaltungsseite nicht erreichbar (404)
- [ ] [Test] CI-Job startet mit `docker compose up` und prüft beide Modi

Quelle: `requirements/functional-requirements.md` → FR-078
```

### FR-079: Health-Check

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Soll`, `Rolle/System`

```markdown
**Abhängig von:** – (keine)
**Blockiert:** –

**Anforderung:** Ein öffentlicher Endpunkt meldet, ob die Anwendung läuft und die Datenbank erreichbar ist.

**Akzeptanzkriterien:**
- [ ] [API] `GET /healthz/` antwortet 200 nur, wenn die Datenbank erreichbar ist, sonst 503
- [ ] [API] Der Endpunkt gibt keine internen Details aus

Quelle: `requirements/functional-requirements.md` → FR-079
```

### FR-080: Stadtname konfigurierbar

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Soll`, `Rolle/System`

```markdown
**Abhängig von:** – (keine)
**Blockiert:** –

**Anforderung:** Der Stadtname in Logo und Texten kommt aus `STADTSTIMME_CITY_NAME`, damit andere Kommunen die Anwendung ohne Codeänderung nutzen können.

**Akzeptanzkriterien:**
- [ ] [UI] Logo, Seitentitel und Texte zeigen den Wert aus `STADTSTIMME_CITY_NAME`
- [ ] [API] Der Name kommt über einen Konfigurations-Endpunkt ins Frontend, kein Neubau nötig

Quelle: `requirements/functional-requirements.md` → FR-080
```

---

## S2 – Wunsch und Haushalt im Detail vergleichen

### FR-016: Gebäude als optionale Ebene

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Kann`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-015, FR-019
**Blockiert:** –

**Anforderung:** Eine Einrichtung kann Gebäude haben. Maßnahmen lassen sich einem Gebäude ihrer Einrichtung zuordnen; Punkte und Vergleiche bleiben pro Einrichtung.

**Akzeptanzkriterien:**
- [ ] [DB] Gebäude gehören zu genau einer Einrichtung
- [ ] [API] Eine Maßnahme kann nur einem Gebäude ihrer eigenen Einrichtung zugeordnet werden
- [ ] [UI] Das Detail einer Einrichtung zeigt ihre Gebäude mit Maßnahmen
- [ ] [API] Punkte und Vergleiche bleiben je Einrichtung; Gebäude haben keine eigenen Punkte

Quelle: `requirements/functional-requirements.md` → FR-016
```

### FR-017: Maßnahmen pflegen

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-015, FR-019
**Blockiert:** FR-021, FR-033, FR-040, FR-047

**Anforderung:** Die Verwaltung pflegt Maßnahmen je Einrichtung mit Status (offen, beschlossen, in Umsetzung, abgeschlossen, verworfen). Maßnahmen zeigen, wofür eine Einrichtung Geld braucht, tragen aber selbst keine Punkte.

**Akzeptanzkriterien:**
- [ ] [API] Maßnahmen haben einen der Status offen, beschlossen, in Umsetzung, abgeschlossen, verworfen
- [ ] [UI] Das Detail einer Einrichtung listet ihre Maßnahmen mit Status
- [ ] [API] Maßnahmen lassen sich nicht als Ziel von Punkten speichern

Quelle: `requirements/functional-requirements.md` → FR-017
```

### FR-020: CSV-Export des Katalogs

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Soll`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-019
**Blockiert:** –

**Anforderung:** Jede Katalogliste lässt sich als CSV exportieren.

**Akzeptanzkriterien:**
- [ ] [UI] Jede Katalogliste in der Datenpflege hat „Exportieren“
- [ ] [API] Der Export ist eine CSV im selben Format wie der Import
- [ ] [Test] Export → Import ergibt keine Änderungen

Quelle: `requirements/functional-requirements.md` → FR-020
```

### FR-025: Ziele filtern und auf der Karte finden

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Soll`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-024, FR-043
**Blockiert:** –

**Anforderung:** In „Punkte verteilen“ lassen sich Ziele nach Thema filtern und Einrichtungen auf einer Karte finden. Eine Liste ist die gleichwertige Alternative zur Karte.

**Akzeptanzkriterien:**
- [ ] [UI] Ein Filter nach Thema blendet die übrigen Ziele in Liste und Karte aus
- [ ] [UI] Klick auf einen Kartenpunkt springt zur Zeile der Einrichtung in der Liste
- [ ] [UI] Die Liste ist ohne Karte vollständig bedienbar (Tastatur, Screenreader)

Quelle: `requirements/functional-requirements.md` → FR-025
```

### FR-026: Eigene Verteilung mit dem Gesamtbild vergleichen

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Kann`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-024, FR-036
**Blockiert:** –

**Anforderung:** Bürger sehen ihre eigene Verteilung neben der Verteilung aller Teilnehmenden.

**Akzeptanzkriterien:**
- [ ] [API] `GET /api/verteilung/vergleich/` liefert je Thema eigenen Anteil und Anteil aller Teilnehmenden
- [ ] [UI] „Punkte verteilen“ zeigt beide Anteile nebeneinander je Thema
- [ ] [UI] Ohne eigene Punkte erscheint nur der Anteil aller

Quelle: `requirements/functional-requirements.md` → FR-026
```

### FR-037: Eigene Punkte in der Übersicht

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Soll`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-024, FR-036
**Blockiert:** –

**Anforderung:** Angemeldete Bürger sehen in der Übersicht zusätzlich ihre eigene Verteilung im Vergleich zum Anteil aller Bürgerpunkte und zu den Ausgaben, ihre vergebenen und freien Punkte als Zahl und Raster aus 100 Feldern mit Link zu „Punkte verteilen“, ihre eigenen Vorschläge und bis wann ihre Punkte gültig sind.

**Akzeptanzkriterien:**
- [ ] [UI] Angemeldete sehen zusätzlich ihre Verteilung neben dem Anteil aller und den Ausgaben
- [ ] [UI] Vergebene und freie Punkte als Zahl und Raster aus 100 Feldern, mit Link zu „Punkte verteilen“
- [ ] [UI] Eigene Vorschläge und „gültig bis“ (Datum des Verfalls)
- [ ] [API] Für Besucher enthält die Antwort keine persönlichen Daten

Quelle: `requirements/functional-requirements.md` → FR-037
```

### FR-039: Lücke je Einrichtung und je Thema

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Muss`, `Rolle/Besucher`

```markdown
**Abhängig von:** FR-036
**Blockiert:** FR-040, FR-042, FR-061

**Anforderung:** Die Ergebnisseite zeigt je Einrichtung und je ganzem Thema die Lücke in Prozentpunkten: Anteil Bürgerpunkte minus Anteil Ist-Ausgaben. Der Themenvergleich enthält alle Punkte des Themas inkl. „… allgemein“ und alle Ausgaben des Themas.

**Akzeptanzkriterien:**
- [ ] [API] Lücke je Einrichtung = Anteil Bürgerpunkte − Anteil Ist-Ausgaben in Prozentpunkten (ganzzahlig)
- [ ] [API] Der Themenvergleich enthält alle Punkte des Themas inkl. „… allgemein“ und alle Ausgaben des Themas
- [ ] [UI] Listen „Einrichtungen“ und „Ganze Themen“ sind nach Lücke sortiert; Plus und Minus sind nicht nur farblich unterscheidbar
- [ ] [Test] pytest mit festen Daten prüft die Rechnung

Quelle: `requirements/functional-requirements.md` → FR-039
```

### FR-040: Detail je Einrichtung

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Soll`, `Rolle/Besucher`

```markdown
**Abhängig von:** FR-017, FR-039
**Blockiert:** –

**Anforderung:** Zu jeder Einrichtung lassen sich in den Ergebnissen Punkte, Ausgaben und zugehörige Maßnahmen im Detail ansehen. Die Auswahl erfolgt über die Liste oder die Markierung auf der Ergebniskarte.

**Akzeptanzkriterien:**
- [ ] [UI] Klick auf eine Einrichtung in Liste oder Ergebniskarte öffnet das Detail
- [ ] [UI] Das Detail zeigt Punkte, Anteil, Ausgaben, Lücke und Maßnahmen mit Status
- [ ] [UI] Das Detail ist per URL direkt aufrufbar und per Tastatur schließbar

Quelle: `requirements/functional-requirements.md` → FR-040
```

### FR-041: Einordnung der Belastbarkeit

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Soll`, `Rolle/Besucher`

```markdown
**Abhängig von:** FR-036
**Blockiert:** –

**Anforderung:** Die Ergebnisse nennen Stand, Zahl der Mitmachenden, vergebene Punkte, durchschnittliche Punkte je Person, Anteil an ganze Themen und Summe der Ausgaben sowie den Hinweis, dass die Zahlen nicht repräsentativ sind.

**Akzeptanzkriterien:**
- [ ] [UI] Die Ergebnisse nennen Stand (Datum, Uhrzeit), Mitmachende, vergebene Punkte, Durchschnitt je Person, Anteil an ganzen Themen und Summe der Ausgaben
- [ ] [UI] Der Hinweis „nicht repräsentativ“ ist immer sichtbar
- [ ] [API] Die Werte stimmen mit Übersicht und CSV-Export überein

Quelle: `requirements/functional-requirements.md` → FR-041
```

### FR-042: Ergebnisse als CSV

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Soll`, `Rolle/Besucher`

```markdown
**Abhängig von:** FR-039
**Blockiert:** –

**Anforderung:** Die Ergebnistabelle lässt sich als CSV herunterladen (Semikolon, Dezimalkomma, BOM für deutsche Tabellenprogramme). Texte werden gegen Formel-Injektion geschützt.

**Akzeptanzkriterien:**
- [ ] [UI] „Als CSV herunterladen“ auf der Ergebnisseite, ohne Anmeldung
- [ ] [API] Die Datei hat Semikolon, Dezimalkomma und BOM und öffnet sich in Excel und LibreOffice direkt in Spalten
- [ ] [API] Texte, die mit `=`, `+`, `-` oder `@` beginnen, erhalten ein vorangestelltes Apostroph
- [ ] [API] Die CSV enthält keine personenbezogenen Daten

Quelle: `requirements/functional-requirements.md` → FR-042
```

### FR-043: Karten der Einrichtungen

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Soll`, `Rolle/Besucher`

```markdown
**Abhängig von:** FR-015
**Blockiert:** FR-025, FR-045

**Anforderung:** Übersicht, „Punkte verteilen“, Ergebnisse und Vorschläge zeigen Einrichtungen mit Koordinaten auf einer zoombaren Karte, immer zusammen mit einer gleichwertigen Liste. Markierungen zeigen das Thema (Farbe und Symbol) und mit ihrer Größe den Anteil an den Bürgerpunkten. Ein Klick auf eine Markierung führt zum zugehörigen Ziel bzw. zu seinen Details. Angemeldete Bürger können zwischen allen Einrichtungen und den von ihnen gewichteten umschalten. Fällt der Kachelserver aus, wechselt die Karte auf einen Ersatz und zeigt danach mindestens die Marker.

**Akzeptanzkriterien:**
- [ ] [UI] Karten auf Übersicht, Verteilen, Ergebnissen und Vorschlägen zeigen Einrichtungen mit Koordinaten als Kreise in Themenfarbe; die Größe entspricht dem Anteil
- [ ] [UI] Zoomen mit Plus/Minus, Strg/⌘ + Mausrad und Pinch; Mausrad ohne Taste scrollt die Seite
- [ ] [UI] Klick auf einen Kreis führt zum Ziel bzw. Detail; angemeldete Bürger können auf „nur meine“ umschalten
- [ ] [UI] Fällt der Kachelserver aus, wechselt die Karte auf den Ersatz, danach bleiben die Marker sichtbar
- [ ] [UI] Jede Karte hat eine gleichwertige Liste daneben oder darunter

Quelle: `requirements/functional-requirements.md` → FR-043
```

---

## S3 – Ereignis-Log, Verfall und Stichtag

### FR-010: Anmeldung der Verwaltung

Meilenstein: **S3 – Ereignis-Log, Verfall und Stichtag** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-004
**Blockiert:** FR-012, FR-029, FR-057, FR-059, FR-060, FR-061, FR-064, FR-065, FR-068

**Anforderung:** Auf der Anmeldeseite wählt man zwischen „Bürgerin oder Bürger“ (Code) und „Stadtverwaltung“ (Benutzername und Passwort). Nur Benutzer mit Mitarbeiter-Status gelangen auf die Verwaltungsseite. Jede Verwaltungsfunktion prüft ihr eigenes Recht (z. B. „Vorschlag ändern“, „Einrichtung ändern“, Datenpflege je Katalogliste), sodass sich Mitarbeitende über Gruppen unterschiedliche Rechte-Kategorien zuweisen lassen. Bis zum Admin-Login-Konzept ist das nur im Demo-Modus verfügbar; sonst zeigt die Seite einen Hinweis.

**Akzeptanzkriterien:**
- [ ] [UI] Die Anmeldeseite bietet „Bürgerin oder Bürger“ und „Stadtverwaltung“ als Auswahl
- [ ] [API] `POST /api/verwaltung/anmelden/` mit Benutzername und Passwort lässt nur Benutzer mit Mitarbeiter-Status zu
- [ ] [API] Jeder Verwaltungs-Endpunkt prüft sein eigenes Django-Recht (z. B. `change_proposal`); ohne Recht 403
- [ ] [API] Ohne Demo-Modus antwortet die Verwaltungsanmeldung mit einem Hinweis statt einer Anmeldung
- [ ] [Test] pytest-Rechte-Matrix für Mitarbeitende ohne und mit jedem Recht

Quelle: `requirements/functional-requirements.md` → FR-010
```

### FR-030: Snapshot als Abstimmungszeitpunkt

Meilenstein: **S3 – Ereignis-Log, Verfall und Stichtag** · Labels: `Priorität/Soll`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-064
**Blockiert:** FR-067

**Anforderung:** Die Beteiligung bleibt fortlaufend ohne feste Runden. Die Verwaltung hält zu einem beliebigen Zeitpunkt einen benannten, datierten Snapshot fest (aggregierte Punkte je Ziel, Teilnehmende, Ziele, Ist-Ausgaben). Snapshots sind unveränderlich, werden aus dem Ereignis-Log berechnet (FR-032, FR-064), lassen sich in der Anwendung einsehen, als CSV herunterladen und miteinander vergleichen. So kann sich die Stadt, z. B. für eine Gemeinderatssitzung, auf einen festen Abstimmungsstand beziehen.

**Akzeptanzkriterien:**
- [ ] [UI] Die Verwaltung legt einen Snapshot mit Namen an; Datum und Uhrzeit werden automatisch gesetzt
- [ ] [API] Der Snapshot enthält aggregierte Punkte je Ziel, Teilnehmende, Ziele und Ist-Ausgaben, berechnet aus dem Ereignis-Log
- [ ] [DB] Snapshots sind unveränderlich (keine Änderung oder Löschung über die API)
- [ ] [UI] Snapshots lassen sich ansehen, als CSV laden und zu zweit vergleichen (Differenz je Thema)

Quelle: `requirements/functional-requirements.md` → FR-030
```

### FR-032: Unveränderliches Ereignis-Log

Meilenstein: **S3 – Ereignis-Log, Verfall und Stichtag** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Abhängig von:** FR-024
**Blockiert:** FR-008, FR-031, FR-033, FR-034, FR-062, FR-064, FR-069

**Anforderung:** Jede Punkteänderung (vergeben, entzogen, zurückgegeben, verfallen) wird in derselben Transaktion als unveränderliches Ereignis mit Delta, Zeitpunkt und optional der auslösenden Maßnahme gespeichert. Ändern und Löschen von Ereignissen ist ausgeschlossen. Beim Löschen eines Zugangs bleibt das Log pseudonym erhalten.

**Akzeptanzkriterien:**
- [ ] [DB] Jede Punkteänderung schreibt in derselben Transaktion ein Ereignis (vergeben, entzogen, zurückgegeben, verfallen) mit Delta ≠ 0 und Zeitpunkt
- [ ] [DB] Ein Datenbank-Trigger verhindert UPDATE und DELETE auf dem Log
- [ ] [DB] Beim Löschen eines Zugangs bleiben seine Ereignisse erhalten
- [ ] [Test] pytest: Summe der Deltas je Zugang = aktueller Stand; UPDATE auf das Log schlägt fehl

Quelle: `requirements/functional-requirements.md` → FR-032
```

### FR-034: Verfall nach Inaktivität

Meilenstein: **S3 – Ereignis-Log, Verfall und Stichtag** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Abhängig von:** FR-006, FR-032
**Blockiert:** FR-035, FR-072

**Anforderung:** Alle Punkte eines Zugangs verfallen nach 183 Tagen ohne Aktivität (`STADTSTIMME_POINTS_EXPIRY_DAYS`). Ergebnisse zählen verfallene Punkte sofort nicht mehr mit. Entzogen werden sie, sobald die Person zurückkommt, oder durch den täglichen Lauf. Jede Nutzung mit dem Zugang verlängert die Frist.

**Akzeptanzkriterien:**
- [ ] [API] Zugänge ohne Aktivität seit 183 Tagen (`STADTSTIMME_POINTS_EXPIRY_DAYS`) zählen in Ergebnissen sofort nicht mehr
- [ ] [API] Ihre Punkte werden beim nächsten Besuch oder im täglichen Lauf als „verfallen“ entzogen
- [ ] [API] Jede Anfrage mit gültiger Sitzung setzt die letzte Aktivität neu
- [ ] [Test] pytest mit Zeitreise: 182 Tage → zählt, 184 Tage → zählt nicht

Quelle: `requirements/functional-requirements.md` → FR-034
```

### FR-035: Tägliche Aufgaben

Meilenstein: **S3 – Ereignis-Log, Verfall und Stichtag** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Abhängig von:** FR-034
**Blockiert:** –

**Anforderung:** Ein täglicher Lauf (Standard 02:00 UTC, `DAILY_TASKS_AT`) verschickt zuerst Verfallswarnungen und lässt danach Punkte verfallen. Beide Schritte sind idempotent, jederzeit manuell startbar, und ein Fehler im einen hält den anderen nicht auf.

**Akzeptanzkriterien:**
- [ ] [API] `run_daily_tasks` sendet erst Verfallswarnungen und lässt dann Punkte verfallen
- [ ] [API] Zweimal am selben Tag ausgeführt, ändert der zweite Lauf nichts
- [ ] [API] Ein Fehler in einem Schritt verhindert den anderen nicht und wird geloggt
- [ ] [API] Der Dienst `scheduler` startet den Lauf um `DAILY_TASKS_AT` (Standard 02:00 UTC)

Quelle: `requirements/functional-requirements.md` → FR-035
```

### FR-059: Beteiligung beobachten

Meilenstein: **S3 – Ereignis-Log, Verfall und Stichtag** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-010, FR-011
**Blockiert:** –

**Anforderung:** Die Verwaltung sieht die Beteiligung nur als Summen: eingelöste Codes je Woche, eingelöste Codes und Zugänge mit vergebenen Punkten. Rückschlüsse auf einzelne Personen sind nicht möglich.

**Akzeptanzkriterien:**
- [ ] [UI] Beteiligung zeigt eingelöste Codes je Kalenderwoche, Summe eingelöster Codes und Zugänge mit Punkten
- [ ] [API] Die Antwort enthält nur Summen, keine Daten einzelner Zugänge

Quelle: `requirements/functional-requirements.md` → FR-059
```

### FR-064: Stichtags-Export

Meilenstein: **S3 – Ereignis-Log, Verfall und Stichtag** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-010, FR-032
**Blockiert:** FR-030

**Anforderung:** Die Verwaltung lädt für einen Stichtag eine CSV mit Punkten und Unterstützern je Ziel zum Tagesende herunter, ergänzt um die Zahl der Teilnehmenden und die Ist-Ausgaben je Ziel. Die Werte werden aus dem Ereignis-Log berechnet und sind für denselben Stichtag reproduzierbar.

**Akzeptanzkriterien:**
- [ ] [UI] Auswahl eines Stichtags und Download als CSV
- [ ] [API] Werte je Ziel zum Tagesende: Punkte, Unterstützer, Teilnehmende, Ist-Ausgaben, berechnet aus dem Log
- [ ] [Test] Zweimaliger Export für denselben vergangenen Stichtag ist byte-gleich

Quelle: `requirements/functional-requirements.md` → FR-064
```

### FR-065: Zugänge je Charge

Meilenstein: **S3 – Ereignis-Log, Verfall und Stichtag** · Labels: `Priorität/Soll`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-010, FR-011
**Blockiert:** –

**Anforderung:** Die Verwaltung sieht je Charge, wie viele Codes ausgegeben und eingelöst sind.

**Akzeptanzkriterien:**
- [ ] [UI] Tabelle je Charge: ausgegeben, eingelöst, Quote
- [ ] [API] Nur Summen, keine Codes

Quelle: `requirements/functional-requirements.md` → FR-065
```

---

## S4 – Vorschläge einreichen und unterstützen

### FR-007: Mein Bereich

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Soll`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-006, FR-024, FR-044
**Blockiert:** FR-008, FR-013, FR-070

**Anforderung:** Angemeldete Bürger haben einen Bereich „Mein Bereich“ mit Anmeldestatus, ihrem Punktestand (vergeben und frei), ihren eigenen Vorschlägen mit Schritt und ihren Einstellungen für E-Mail-Hinweise, jeweils mit Link zu „Punkte verteilen“, „Vorschläge“ und den Hinweis-Einstellungen.

**Akzeptanzkriterien:**
- [ ] [API] `GET /api/mein-bereich/` liefert Punkte (vergeben/frei), eigene Vorschläge mit Schritt und den Status der E-Mail-Hinweise
- [ ] [UI] „Mein Bereich“ zeigt diese drei Blöcke mit Links zu „Punkte verteilen“, „Vorschläge“ und Hinweis-Einstellungen
- [ ] [UI] Ohne eigene Vorschläge erscheint ein leerer Zustand mit Link „Vorschlag einreichen“
- [ ] [API] Ohne Anmeldung antwortet der Endpunkt 401

Quelle: `requirements/functional-requirements.md` → FR-007
```

### FR-044: Vorschlag einreichen

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-009, FR-014
**Blockiert:** FR-007, FR-045, FR-046, FR-047, FR-048, FR-054

**Anforderung:** Angemeldete Bürger reichen einen Vorschlag in drei Schritten ein: Anliegen (Titel 8–80 Zeichen, Beschreibung optional bis 600 Zeichen), Einordnen, Prüfen. Vor dem Einreichen können sie zu jedem vorherigen Schritt zurückkehren und korrigieren, ohne Eingaben zu verlieren.

**Akzeptanzkriterien:**
- [ ] [UI] Das Formular hat drei Schritte: Anliegen, Einordnen, Prüfen; man kann jederzeit zurück, ohne Eingaben zu verlieren
- [ ] [API] `POST /api/vorschlaege/` akzeptiert Titel 8–80 Zeichen und Beschreibung bis 600 Zeichen, sonst 400 mit Feldfehler
- [ ] [UI] Nach dem Einreichen erscheint der Vorschlag oben in der Liste mit Bestätigung
- [ ] [API] Ohne Anmeldung 401

Quelle: `requirements/functional-requirements.md` → FR-044
```

### FR-045: Thema und Ort eines Vorschlags

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-043, FR-044
**Blockiert:** FR-052

**Anforderung:** Ein Vorschlag hat immer ein Thema. Der Ort ist „allgemein“, eine bekannte Einrichtung passend zum Thema oder ein neuer Punkt auf der Karte (per Klick oder Kartenmitte für Tastaturnutzung). Einrichtung und Punkt sind nie gleichzeitig gesetzt. Ohne JavaScript stehen „allgemein“ und „bekannter Ort“ zur Verfügung.

**Akzeptanzkriterien:**
- [ ] [UI] Thema ist Pflicht; Ort: „allgemein“, „bekannter Ort“ (nur Einrichtungen des Themas) oder „neuer Ort“ per Karte
- [ ] [UI] „Kartenmitte setzen“ erlaubt einen neuen Ort ohne Maus
- [ ] [API] Einrichtung und Koordinaten gleichzeitig werden mit 400 abgewiesen (zusätzlich DB-Constraint)
- [ ] [API] Koordinaten außerhalb des Stadtgebiets werden abgewiesen

Quelle: `requirements/functional-requirements.md` → FR-045
```

### FR-046: Tageslimit für Vorschläge

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Abhängig von:** FR-044
**Blockiert:** –

**Anforderung:** Ein Zugang darf höchstens 5 Vorschläge pro Tag einreichen (`STADTSTIMME_PROPOSALS_PER_DAY`); darüber wird mit Hinweis abgewiesen.

**Akzeptanzkriterien:**
- [ ] [API] Der sechste Vorschlag eines Zugangs innerhalb eines Kalendertags wird mit 429 abgewiesen (`STADTSTIMME_PROPOSALS_PER_DAY`)
- [ ] [UI] Der Hinweis nennt, ab wann wieder eingereicht werden kann
- [ ] [Test] pytest für 5 (erlaubt) und 6 (abgewiesen)

Quelle: `requirements/functional-requirements.md` → FR-046
```

### FR-047: Ähnliche Einträge vorschlagen

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Soll`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-017, FR-044
**Blockiert:** –

**Anforderung:** Beim Schreiben zeigt „Gibt es das schon?“ ähnliche Vorschläge und offene Maßnahmen (Abgleich über Wortstämme), damit Doppelungen vermieden werden.

**Akzeptanzkriterien:**
- [ ] [API] `GET /api/vorschlaege/aehnlich/?q=` liefert ab 8 Zeichen bis zu 5 ähnliche Vorschläge und offene Maßnahmen (Wortstämme)
- [ ] [UI] „Gibt es das schon?“ erscheint während der Eingabe des Titels, verzögert (Debounce), mit Link und Unterstützen-Knopf
- [ ] [UI] Der Hinweis blockiert das Einreichen nicht

Quelle: `requirements/functional-requirements.md` → FR-047
```

### FR-048: Vorschläge sofort öffentlich

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Abhängig von:** FR-044
**Blockiert:** FR-049, FR-053, FR-056

**Anforderung:** Ein eingereichter Vorschlag ist ohne Freigabe sofort öffentlich sichtbar und unterstützbar.

**Akzeptanzkriterien:**
- [ ] [API] Ein neuer Vorschlag hat den Status „offen“ und ist sofort in `GET /api/vorschlaege/` enthalten
- [ ] [UI] Er ist sofort für andere sichtbar und unterstützbar, ohne Freigabe

Quelle: `requirements/functional-requirements.md` → FR-048
```

### FR-049: Vorschlag unterstützen

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-048
**Blockiert:** FR-050

**Anforderung:** Angemeldete Bürger unterstützen beliebig viele offene Vorschläge anderer, jeden höchstens einmal, und können die Unterstützung zurückziehen. Unterstützungen sind unabhängig vom Budget der 100 Punkte. Eigene sowie entschiedene Vorschläge sind nicht unterstützbar; abgelehnte Vorschläge erscheinen nicht mehr unter den eigenen unterstützten.

**Akzeptanzkriterien:**
- [ ] [API] `POST /api/vorschlaege/<id>/unterstuetzen/` schaltet die Unterstützung an und aus; höchstens eine je Zugang (DB-Constraint)
- [ ] [API] Eigene und entschiedene Vorschläge → 400 mit Meldung
- [ ] [UI] Zahl und Fortschritt aktualisieren sich sofort nach dem Klick
- [ ] [API] Unterstützungen ändern das Punktebudget nicht

Quelle: `requirements/functional-requirements.md` → FR-049
```

### FR-050: Weg eines Vorschlags

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Muss`, `Rolle/Besucher`

```markdown
**Abhängig von:** FR-049
**Blockiert:** FR-055, FR-057, FR-060, FR-075

**Anforderung:** Jeder Vorschlag zeigt seinen Schritt: „Sammelt“ (unter der Schwelle von 50 Unterstützungen, `STADTSTIMME_PROPOSAL_SUPPORT_THRESHOLD`), „In Prüfung“ (Schwelle erreicht, seit dem Zeitpunkt der N-ten Unterstützung) und „Entschieden“ (angenommen oder abgelehnt). Solange ein Vorschlag sammelt, zeigt er die noch benötigten Unterstützungen. Die Liste lässt sich nach Schritt filtern, auch ohne JavaScript.

**Akzeptanzkriterien:**
- [ ] [UI] Jeder Vorschlag zeigt „Sammelt“, „In Prüfung“ oder „Entschieden“ als Text, nicht nur als Farbe
- [ ] [UI] Beim Sammeln steht „noch N Unterstützungen“ bis zur Schwelle (`STADTSTIMME_PROPOSAL_SUPPORT_THRESHOLD`)
- [ ] [API] „In Prüfung seit“ ist der Zeitpunkt der N-ten Unterstützung
- [ ] [UI] Die Liste lässt sich nach Schritt filtern; der Filter steht in der URL

Quelle: `requirements/functional-requirements.md` → FR-050
```

### FR-055: Vorschlagsliste durchsuchen, filtern und sortieren

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Soll`, `Rolle/Besucher`

```markdown
**Abhängig von:** FR-050
**Blockiert:** –

**Anforderung:** Die Vorschlagsliste ist nach Titel und Ort durchsuchbar, nach Thema und Schritt filterbar und nach Zahl der Unterstützungen sortierbar. Angemeldete Bürger wählen zwischen allen und nur ihren eigenen Vorschlägen. Filter und Sortierung funktionieren ohne JavaScript.

**Akzeptanzkriterien:**
- [ ] [UI] Suche nach Titel und Ort, Filter nach Thema und Schritt, Sortierung nach Unterstützungen
- [ ] [UI] Angemeldete wählen „Alle“ oder „Meine“
- [ ] [API] Filter, Suche und Sortierung erfolgen serverseitig per Query-Parameter
- [ ] [UI] Der Zustand steht in der URL, sodass eine gefilterte Liste teilbar ist

Quelle: `requirements/functional-requirements.md` → FR-055
```

---

## S5 – Stadt antwortet auf Vorschläge

### FR-028: Hinweis auf angenommene Vorschläge

Meilenstein: **S5 – Stadt antwortet auf Vorschläge** · Labels: `Priorität/Soll`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-024, FR-058
**Blockiert:** –

**Anforderung:** Angenommene Vorschläge erscheinen in „Punkte verteilen“ als Hinweis an ihrer Einrichtung oder, ohne Einrichtung, beim Thema („… allgemein“), mit Link zum Vorschlag. Sie sind kein eigenes Punkteziel.

**Akzeptanzkriterien:**
- [ ] [UI] Angenommene Vorschläge erscheinen als Hinweis unter ihrer Einrichtung oder bei „… allgemein“ ihres Themas
- [ ] [UI] Der Hinweis verlinkt auf den Vorschlag
- [ ] [API] Angenommene Vorschläge sind kein eigenes Ziel in `GET /api/ziele/`

Quelle: `requirements/functional-requirements.md` → FR-028
```

### FR-051: Öffentliche Antwort der Stadt

Meilenstein: **S5 – Stadt antwortet auf Vorschläge** · Labels: `Priorität/Muss`, `Rolle/Besucher`

```markdown
**Abhängig von:** FR-058
**Blockiert:** –

**Anforderung:** Entschiedene Vorschläge zeigen die öffentliche Begründung der Stadt, das Entscheidungsdatum und gegebenenfalls die daraus entstandene Maßnahme. Angenommene und abgelehnte Vorschläge bleiben dauerhaft sichtbar, weil es keine abgeschlossenen Runden gibt.

**Akzeptanzkriterien:**
- [ ] [UI] Entschiedene Vorschläge zeigen Antwort der Stadt, Entscheidungsdatum und ggf. die Maßnahme
- [ ] [UI] Angenommene und abgelehnte Vorschläge bleiben dauerhaft in der Liste (Filter „Entschieden“)

Quelle: `requirements/functional-requirements.md` → FR-051
```

### FR-052: Neuer Ort wird Einrichtung

Meilenstein: **S5 – Stadt antwortet auf Vorschläge** · Labels: `Priorität/Soll`, `Rolle/System`

```markdown
**Abhängig von:** FR-045, FR-058
**Blockiert:** –

**Anforderung:** Wird ein Vorschlag mit neuem Ort angenommen, legt das System daraus eine Einrichtung an (Name = Titel, Thema und Koordinaten vom Vorschlag, externe ID `VORSCHLAG-<Nr>`) und verknüpft den Vorschlag mit ihr. Sie ist danach wählbar und in Karten und Ergebnissen enthalten.

**Akzeptanzkriterien:**
- [ ] [API] Annehmen eines Vorschlags mit neuem Ort legt eine Einrichtung an (Name = Titel, Thema und Koordinaten vom Vorschlag, externe ID `VORSCHLAG-<Nr>`)
- [ ] [API] Der Vorschlag verweist danach auf diese Einrichtung
- [ ] [UI] Die Einrichtung ist sofort in „Punkte verteilen“, Karten und Ergebnissen sichtbar
- [ ] [API] Zweimaliges Annehmen ist nicht möglich, es entsteht keine doppelte Einrichtung

Quelle: `requirements/functional-requirements.md` → FR-052
```

### FR-057: Wartet auf Sie

Meilenstein: **S5 – Stadt antwortet auf Vorschläge** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-010, FR-050
**Blockiert:** FR-058

**Anforderung:** Die Verwaltungsseite listet Vorschläge in Prüfung mit ihrer Antwortfrist von 14 Tagen ab Erreichen der Schwelle (`STADTSTIMME_PROPOSAL_REVIEW_DAYS`), früheste Frist zuerst.

**Akzeptanzkriterien:**
- [ ] [UI] „Wartet auf Sie“ listet Vorschläge in Prüfung mit Antwortfrist (14 Tage ab Schwelle, `STADTSTIMME_PROPOSAL_REVIEW_DAYS`), früheste zuerst
- [ ] [UI] Überfällige Fristen sind hervorgehoben (Text, nicht nur Farbe)
- [ ] [API] Nur für Mitarbeitende, sonst 403

Quelle: `requirements/functional-requirements.md` → FR-057
```

### FR-058: Vorschlag entscheiden

Meilenstein: **S5 – Stadt antwortet auf Vorschläge** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-057
**Blockiert:** FR-028, FR-051, FR-052, FR-063, FR-066, FR-075

**Anforderung:** Die Verwaltung nimmt einen Vorschlag an oder lehnt ihn ab, jederzeit, auch vor Erreichen der Schwelle. Pflicht ist eine öffentliche Antwort mit mindestens 20 Zeichen, optional eine verknüpfte Maßnahme. Ein bereits entschiedener Vorschlag kann nicht erneut entschieden werden. Entscheiden erfordert das Recht „Vorschlag ändern“.

**Akzeptanzkriterien:**
- [ ] [UI] Entscheidungsseite mit „Annehmen“/„Ablehnen“, öffentlicher Antwort und optionaler Maßnahme
- [ ] [API] Antwort unter 20 Zeichen → 400; bereits entschiedene Vorschläge → 409
- [ ] [API] Ohne Recht „Vorschlag ändern“ → 403
- [ ] [DB] Entscheidungsdatum und verantwortliches Konto werden gespeichert

Quelle: `requirements/functional-requirements.md` → FR-058
```

### FR-060: Vorschläge nach Schritt

Meilenstein: **S5 – Stadt antwortet auf Vorschläge** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-010, FR-050
**Blockiert:** –

**Anforderung:** Die Verwaltung sieht alle Vorschläge gruppiert nach Schritt mit Zugang zur Entscheidungsseite.

**Akzeptanzkriterien:**
- [ ] [UI] Alle Vorschläge gruppiert nach Sammelt, In Prüfung, Entschieden, jeweils mit Anzahl
- [ ] [UI] Jeder Eintrag verlinkt zur Entscheidungsseite

Quelle: `requirements/functional-requirements.md` → FR-060
```

### FR-066: Inhalte moderieren

Meilenstein: **S5 – Stadt antwortet auf Vorschläge** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-058
**Blockiert:** FR-053

**Anforderung:** Die Verwaltung kann unpassende Vorschläge mit Begründung ablehnen (FR-058) oder doppelte und unzulässige Vorschläge mit Begründung entfernen. Ein entfernter Vorschlag ist öffentlich nicht mehr sichtbar; sein Ersteller sieht in „Mein Bereich“, dass und warum er entfernt wurde.

**Akzeptanzkriterien:**
- [ ] [UI] Ablehnen mit Begründung (wie FR-058) oder „Entfernen“ mit Begründung für doppelte oder unzulässige Vorschläge
- [ ] [API] Entfernte Vorschläge fehlen in allen öffentlichen Listen und Links (404)
- [ ] [UI] Der Ersteller sieht in „Mein Bereich“, dass und warum sein Vorschlag entfernt wurde
- [ ] [DB] Entfernen wird mit Zeitpunkt, Konto und Begründung gespeichert

Quelle: `requirements/functional-requirements.md` → FR-066
```

---

## S6 – Rückfluss: Erledigtes gibt Punkte frei

### FR-027: Erledigte Einrichtungen nicht wählbar

Meilenstein: **S6 – Rückfluss: Erledigtes gibt Punkte frei** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Abhängig von:** FR-024, FR-062
**Blockiert:** –

**Anforderung:** Als erledigt markierte Einrichtungen fehlen in „Punkte verteilen“ (Liste und Karte). Ein Speichern mit Punkten an einer erledigten Einrichtung wird mit Hinweis abgewiesen.

**Akzeptanzkriterien:**
- [ ] [API] Erledigte Einrichtungen fehlen in `GET /api/ziele/`
- [ ] [UI] Sie erscheinen weder in der Liste noch auf der Karte von „Punkte verteilen“
- [ ] [API] Eine Verteilung mit Punkten an einer erledigten Einrichtung wird mit 400 und dem Namen der Einrichtung abgewiesen
- [ ] [UI] Die Ablehnung erscheint als verständlicher Hinweis, die übrige Verteilung bleibt erhalten

Quelle: `requirements/functional-requirements.md` → FR-027
```

### FR-031: Verlauf zurückgekommener und verfallener Punkte

Meilenstein: **S6 – Rückfluss: Erledigtes gibt Punkte frei** · Labels: `Priorität/Soll`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-024, FR-032
**Blockiert:** –

**Anforderung:** „Punkte verteilen“ zeigt Punkte, die in den letzten 30 Tagen zurückgekommen oder verfallen sind, mit Anlass.

**Akzeptanzkriterien:**
- [ ] [API] `GET /api/verteilung/verlauf/` liefert zurückgekommene und verfallene Punkte der letzten 30 Tage mit Anlass
- [ ] [UI] „Punkte verteilen“ zeigt den Verlauf mit Datum, Punkten und Anlass (z. B. Maßnahme in Umsetzung)
- [ ] [UI] Ohne Einträge wird der Bereich nicht angezeigt

Quelle: `requirements/functional-requirements.md` → FR-031
```

### FR-033: Rückfluss bei Umsetzung einer Maßnahme

Meilenstein: **S6 – Rückfluss: Erledigtes gibt Punkte frei** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Abhängig von:** FR-017, FR-032
**Blockiert:** FR-073

**Anforderung:** Geht eine Maßnahme auf „in Umsetzung“ (über Admin, Verwaltungsseite oder CSV-Import, auch bei Neuanlage), erhalten alle Unterstützer ihre Punkte auf der zugehörigen Einrichtung zurück. Punkte an ein ganzes Thema bleiben. „Verworfen“ löst keinen Rückfluss aus. Parallel neu vergebene Punkte bleiben erhalten.

**Akzeptanzkriterien:**
- [ ] [API] Wechselt eine Maßnahme auf „in Umsetzung“ (Datenpflege, Import, Neuanlage), gehen alle Punkte an ihrer Einrichtung an die Unterstützer zurück
- [ ] [API] Punkte an ganze Themen bleiben; „verworfen“ löst nichts aus
- [ ] [DB] Je Rückgabe ein Ereignis „zurückgegeben“ mit Verweis auf die Maßnahme
- [ ] [Test] pytest inkl. paralleler Neuvergabe: neu vergebene Punkte bleiben erhalten

Quelle: `requirements/functional-requirements.md` → FR-033
```

### FR-061: Einrichtungen nach Lücke

Meilenstein: **S6 – Rückfluss: Erledigtes gibt Punkte frei** · Labels: `Priorität/Soll`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-010, FR-039
**Blockiert:** FR-062

**Anforderung:** Die Verwaltung sieht Einrichtungen sortiert nach Lücke mit ihren Maßnahmen und einem Link zur Datenpflege.

**Akzeptanzkriterien:**
- [ ] [UI] Einrichtungen sortiert nach Lücke (größte zuerst) mit Maßnahmen und Link zur Datenpflege
- [ ] [UI] Je Einrichtung gibt es „Erledigt“ bzw. „Wieder öffnen“
- [ ] [API] Die Werte stimmen mit der öffentlichen Ergebnisseite überein

Quelle: `requirements/functional-requirements.md` → FR-061
```

### FR-062: Einrichtung als erledigt markieren

Meilenstein: **S6 – Rückfluss: Erledigtes gibt Punkte frei** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-032, FR-061
**Blockiert:** FR-027, FR-063, FR-073

**Anforderung:** Die Verwaltung markiert eine Einrichtung als erledigt, auch ohne passende Maßnahme. Vorher bestätigt sie eine Rückfrage mit Zahl der Unterstützer und Punkte. Danach gehen alle Punkte an dieser Einrichtung an die Unterstützer zurück, und Betroffene mit E-Mail-Hinweis werden benachrichtigt; Themenpunkte bleiben. Dasselbe gilt, wenn eine Einrichtung dauerhaft aus dem Katalog genommen wird: Sie wird dann als erledigt archiviert statt gelöscht, weil das Ereignis-Log auf sie verweist. Erfordert das Recht „Einrichtung ändern“.

**Akzeptanzkriterien:**
- [ ] [UI] „Erledigt“ öffnet eine Rückfrage mit Zahl der Unterstützer und Punkte
- [ ] [API] Nach Bestätigung gehen alle Punkte an dieser Einrichtung zurück (Ereignis „zurückgegeben“), Themenpunkte bleiben
- [ ] [API] Betroffene mit bestätigter E-Mail erhalten einen Hinweis
- [ ] [API] Ohne Recht „Einrichtung ändern“ → 403
- [ ] [API] „Aus dem Katalog nehmen“ archiviert eine Einrichtung auf dieselbe Weise statt sie zu löschen

Quelle: `requirements/functional-requirements.md` → FR-062
```

### FR-063: Einrichtung wieder öffnen

Meilenstein: **S6 – Rückfluss: Erledigtes gibt Punkte frei** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-058, FR-062
**Blockiert:** –

**Anforderung:** Eine erledigte Einrichtung wird wieder wählbar über „Wieder öffnen“ oder automatisch, sobald die Stadt einen Vorschlag an diesem Ort annimmt. In Ergebnissen, Suche und als bekannter Ort bei Vorschlägen bleibt sie immer sichtbar.

**Akzeptanzkriterien:**
- [ ] [UI] „Wieder öffnen“ macht eine erledigte Einrichtung sofort wieder wählbar
- [ ] [API] Annehmen eines Vorschlags an einer erledigten Einrichtung öffnet sie automatisch
- [ ] [UI] Erledigte Einrichtungen bleiben in Ergebnissen, Suche und als bekannter Ort bei Vorschlägen sichtbar

Quelle: `requirements/functional-requirements.md` → FR-063
```

---

## S7 – Hinweise per E-Mail

### FR-070: E-Mail freiwillig hinterlegen

Meilenstein: **S7 – Hinweise per E-Mail** · Labels: `Priorität/Soll`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-007
**Blockiert:** FR-008, FR-071

**Anforderung:** Bürger hinterlegen freiwillig eine E-Mail-Adresse für Hinweise, ändern oder entfernen sie und wählen, welche Arten von Hinweisen sie erhalten. Die Adresse wird verschlüsselt und getrennt von den Punkten gespeichert und mit dem Zugang gelöscht.

**Akzeptanzkriterien:**
- [ ] [UI] In „Mein Bereich“ E-Mail eintragen, ändern, entfernen und Hinweisarten (Verfall, Rückfluss, Vorschläge, Erinnerung) wählen
- [ ] [DB] Die Adresse liegt verschlüsselt in einer eigenen Tabelle
- [ ] [API] Beim Löschen des Zugangs wird sie mitgelöscht
- [ ] [API] Ungültige Adressen → 400

Quelle: `requirements/functional-requirements.md` → FR-070
```

### FR-071: Double-Opt-in

Meilenstein: **S7 – Hinweise per E-Mail** · Labels: `Priorität/Soll`, `Rolle/System`

```markdown
**Abhängig von:** FR-070
**Blockiert:** FR-072, FR-073, FR-074, FR-075, FR-076, FR-077

**Anforderung:** Hinweise gehen erst nach Bestätigung über einen Link raus. Der Link ist 72 Stunden gültig, das Token wird nur als Hash gespeichert, und das Öffnen des Links bestätigt erst nach Klick auf einen Knopf. Eine neue Bestätigungsmail ist frühestens nach 10 Minuten möglich.

**Akzeptanzkriterien:**
- [ ] [API] Nach dem Eintragen geht eine Bestätigungsmail raus; der Link ist 72 Stunden gültig
- [ ] [UI] Der Link öffnet eine Seite mit Knopf „Bestätigen“; erst der Klick bestätigt
- [ ] [DB] Das Token wird nur als Hash gespeichert
- [ ] [API] Eine neue Bestätigungsmail ist frühestens nach 10 Minuten möglich (429)

Quelle: `requirements/functional-requirements.md` → FR-071
```

### FR-072: Verfallswarnung

Meilenstein: **S7 – Hinweise per E-Mail** · Labels: `Priorität/Soll`, `Rolle/System`

```markdown
**Abhängig von:** FR-034, FR-071
**Blockiert:** –

**Anforderung:** Bestätigte Empfänger erhalten 14 Tage vor dem Verfall (`STADTSTIMME_POINTS_EXPIRY_WARNING_DAYS`) eine Warnung, einmal je Inaktivitätsphase.

**Akzeptanzkriterien:**
- [ ] [API] 14 Tage vor dem Verfall (`STADTSTIMME_POINTS_EXPIRY_WARNING_DAYS`) geht eine Warnung an bestätigte Adressen
- [ ] [API] Je Inaktivitätsphase höchstens eine Warnung; nach neuer Aktivität wieder möglich
- [ ] [Test] pytest mit Zeitreise; Mail in Mailpit prüfbar

Quelle: `requirements/functional-requirements.md` → FR-072
```

### FR-073: Hinweis bei Rückfluss

Meilenstein: **S7 – Hinweise per E-Mail** · Labels: `Priorität/Soll`, `Rolle/System`

```markdown
**Abhängig von:** FR-033, FR-062, FR-071
**Blockiert:** –

**Anforderung:** Bestätigte Empfänger erhalten eine E-Mail, wenn Punkte zu ihnen zurückkommen (Maßnahme in Umsetzung oder Einrichtung erledigt).

**Akzeptanzkriterien:**
- [ ] [API] Kommen Punkte zurück (Maßnahme in Umsetzung, Einrichtung erledigt), erhalten bestätigte Betroffene eine Mail mit Punkten und Grund
- [ ] [API] Mehrere Rückflüsse in einem Vorgang ergeben eine Mail je Person
- [ ] [UI] Die Mail verlinkt auf „Punkte verteilen“

Quelle: `requirements/functional-requirements.md` → FR-073
```

### FR-075: Hinweis zu eigenen und unterstützten Vorschlägen

Meilenstein: **S7 – Hinweise per E-Mail** · Labels: `Priorität/Soll`, `Rolle/System`

```markdown
**Abhängig von:** FR-050, FR-058, FR-071
**Blockiert:** –

**Anforderung:** Bestätigte Empfänger erhalten einen Hinweis, wenn ein eigener oder unterstützter Vorschlag die Schwelle erreicht, angenommen, abgelehnt oder von der Stadt beantwortet wird.

**Akzeptanzkriterien:**
- [ ] [API] Hinweis an Ersteller und Unterstützer, wenn ein Vorschlag die Schwelle erreicht, angenommen, abgelehnt oder beantwortet wird
- [ ] [API] Höchstens eine Mail je Ereignis und Person
- [ ] [UI] Die Mail verlinkt auf den Vorschlag

Quelle: `requirements/functional-requirements.md` → FR-075
```

### FR-076: Abmelden mit einem Klick

Meilenstein: **S7 – Hinweise per E-Mail** · Labels: `Priorität/Soll`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-071
**Blockiert:** –

**Anforderung:** Jede Hinweis-Mail enthält einen Abmeldelink und `List-Unsubscribe` (Ein-Klick nach RFC 8058). Abmelden löscht die Adresse.

**Akzeptanzkriterien:**
- [ ] [API] Jede Hinweis-Mail hat einen Abmeldelink und `List-Unsubscribe` mit Ein-Klick (RFC 8058)
- [ ] [API] Abmelden löscht die Adresse sofort
- [ ] [UI] Die Abmeldeseite bestätigt das Abmelden

Quelle: `requirements/functional-requirements.md` → FR-076
```

### FR-077: Robust bei Mailausfall

Meilenstein: **S7 – Hinweise per E-Mail** · Labels: `Priorität/Soll`, `Rolle/System`

```markdown
**Abhängig von:** FR-071
**Blockiert:** –

**Anforderung:** Ist der Mailserver nicht erreichbar, schlägt keine fachliche Aktion fehl (z. B. Speichern einer Maßnahme); es wird lediglich keine Mail versendet.

**Akzeptanzkriterien:**
- [ ] [API] Ist der Mailserver nicht erreichbar, gelingt die auslösende Aktion trotzdem (z. B. Maßnahme speichern)
- [ ] [API] Der Fehler wird ohne E-Mail-Adresse geloggt
- [ ] [Test] pytest mit simuliertem SMTP-Ausfall

Quelle: `requirements/functional-requirements.md` → FR-077
```

---

## S8 – Zugänge verwalten und löschen

### FR-008: Zugang selbst löschen

Meilenstein: **S8 – Zugänge verwalten und löschen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-007, FR-032, FR-070
**Blockiert:** –

**Anforderung:** Bürger löschen ihren Zugang in „Mein Bereich“ nach einer Rückfrage, die die Folgen nennt. Alle Punkte werden entzogen (Ereignis „entzogen“), die E-Mail-Adresse für Hinweise wird gelöscht, und eigene Vorschläge und Unterstützungen werden entfernt. Das Ereignis-Log bleibt pseudonym erhalten (FR-032). Der Code ist danach gesperrt; neu teilnehmen kann die Person nur mit einem neuen Code der Stadt.

**Akzeptanzkriterien:**
- [ ] [UI] „Zugang löschen“ in „Mein Bereich“ öffnet eine Rückfrage, die Folgen nennt (Punkte, E-Mail, Vorschläge, Code gesperrt)
- [ ] [API] `DELETE /api/mein-bereich/` schreibt für alle Punkte Ereignisse „entzogen“, löscht E-Mail, Vorschläge und Unterstützungen und beendet alle Sitzungen des Zugangs
- [ ] [DB] Das Ereignis-Log bleibt erhalten, ohne Verweis auf eine Person
- [ ] [API] Ein erneutes Einlösen des Codes wird mit „gesperrt“ abgewiesen
- [ ] [Test] pytest: Übersicht zählt die Punkte danach nicht mehr; Log-Einträge bleiben

Quelle: `requirements/functional-requirements.md` → FR-008
```

### FR-068: Zugang finden und einsehen

Meilenstein: **S8 – Zugänge verwalten und löschen** · Labels: `Priorität/Soll`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-010, FR-011
**Blockiert:** FR-069

**Anforderung:** Die Verwaltung findet einen Zugang über die letzten 8 Zeichen seines Codes (z. B. bei einer Anfrage per Telefon) und sieht Status, Charge, Zeitpunkt des Einlösens, letzte Aktivität und die Vorschläge des Zugangs. Die Punkteverteilung des Zugangs sieht sie nicht. Von dort kann sie den Zugang schließen und wieder öffnen (FR-069), aber nichts im Namen des Bürgers ändern.

**Hinweis:** Codes liegen nur als Hash vor; für die Suche braucht es einen eigenen Hash der letzten 8 Zeichen.

**Akzeptanzkriterien:**
- [ ] [UI] Suche über die letzten 8 Zeichen eines Codes
- [ ] [API] Antwort: Status, Charge, Einlösezeitpunkt, letzte Aktivität, Vorschläge; keine Punkteverteilung
- [ ] [DB] Für die Suche wird ein eigener Hash der letzten 8 Zeichen gespeichert, kein Klartext
- [ ] [UI] Von dort führt „Schließen“/„Wieder öffnen“ zu FR-069

Quelle: `requirements/functional-requirements.md` → FR-068
```

### FR-069: Zugang schließen und wieder öffnen

Meilenstein: **S8 – Zugänge verwalten und löschen** · Labels: `Priorität/Soll`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-032, FR-068
**Blockiert:** –

**Anforderung:** Die Verwaltung schließt einen Zugang (z. B. bei Wegzug) und öffnet ihn bei Bedarf wieder. Das Schließen wirkt sofort, auch auf bestehende Anmeldungen. Alle Punkte des Zugangs werden entzogen (Ereignis „entzogen“); seine Vorschläge und Unterstützungen bleiben erhalten. Erfordert ein eigenes Recht.

**Akzeptanzkriterien:**
- [ ] [UI] „Zugang schließen“ mit Rückfrage; „Wieder öffnen“ für geschlossene Zugänge
- [ ] [API] Schließen entzieht alle Punkte (Ereignis „entzogen“) und beendet sofort alle Sitzungen des Zugangs
- [ ] [API] Vorschläge und Unterstützungen bleiben erhalten
- [ ] [API] Erfordert ein eigenes Recht, sonst 403

Quelle: `requirements/functional-requirements.md` → FR-069
```

---

## S9 – Finden und teilen

### FR-021: Öffentliche Suche

Meilenstein: **S9 – Finden und teilen** · Labels: `Priorität/Soll`, `Rolle/Besucher`

```markdown
**Abhängig von:** FR-015, FR-017
**Blockiert:** –

**Anforderung:** Besucher durchsuchen Einrichtungen und passende Maßnahmen über eine Suchleiste. Treffer verlinken auf die Ergebnisse und auf „Punkte verteilen“. Die Suche ist ohne Anmeldung und ohne JavaScript nutzbar.

**Akzeptanzkriterien:**
- [ ] [API] `GET /api/suche/?q=` findet Einrichtungen und Maßnahmen ab 2 Zeichen, ohne Anmeldung
- [ ] [UI] Die Suchleiste ist ab 768 px als Feld, am Telefon als Symbol sichtbar; „/“ setzt den Fokus
- [ ] [UI] Treffer verlinken auf Ergebnis-Detail und „Punkte verteilen“
- [ ] [UI] Ohne Treffer erscheint ein Hinweis mit Vorschlag „Vorschlag einreichen“

Quelle: `requirements/functional-requirements.md` → FR-021
```

### FR-029: Ziele per QR-Code verlinken

Meilenstein: **S9 – Finden und teilen** · Labels: `Priorität/Kann`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-010, FR-024
**Blockiert:** –

**Anforderung:** Für jede Einrichtung und jedes Thema gibt es einen direkten Link auf das Ziel in „Punkte verteilen“, den die Verwaltung als QR-Code ausgeben kann (z. B. als Aushang vor Ort). Der QR-Code enthält keinen Zugangscode.

**Akzeptanzkriterien:**
- [ ] [API] Jede Einrichtung und jedes Thema hat einen festen Link auf „Punkte verteilen“ mit diesem Ziel vorausgewählt
- [ ] [UI] Die Verwaltung kann den QR-Code dazu als PNG/SVG herunterladen
- [ ] [API] Der Link enthält keinen Zugangscode
- [ ] [UI] Aufruf des Links ohne Anmeldung führt erst zur Code-Eingabe und danach zum Ziel

Quelle: `requirements/functional-requirements.md` → FR-029
```

### FR-056: Vorschlag teilen

Meilenstein: **S9 – Finden und teilen** · Labels: `Priorität/Kann`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-048
**Blockiert:** –

**Anforderung:** Jeder Vorschlag hat einen dauerhaften, öffentlichen Link, den Ersteller und andere teilen können. Der Link enthält keinen Zugangscode und keine Angabe zum Ersteller.

**Akzeptanzkriterien:**
- [ ] [API] Jeder Vorschlag hat eine dauerhafte URL `/vorschlaege/<id>`
- [ ] [UI] „Teilen“ nutzt die Web-Share-API, sonst „Link kopieren“
- [ ] [API] Die Seite ist ohne Anmeldung aufrufbar und enthält keine Angaben zum Ersteller außer dem Spitznamen

Quelle: `requirements/functional-requirements.md` → FR-056
```

---

## S10 – Briefdruck und Gemeinderatsberichte

### FR-012: Codes für den Briefdruck exportieren

Meilenstein: **S10 – Briefdruck und Gemeinderatsberichte** · Labels: `Priorität/Kann`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-010, FR-011
**Blockiert:** –

**Anforderung:** Die Verwaltung exportiert Codes für den Druck (DECISIONS.md, zurückgestellt). Sperren und Wiederöffnen eines Zugangs regelt FR-069.

**Akzeptanzkriterien:**
- [ ] [UI] Auf der Verwaltungsseite gibt es je Charge „Für den Druck exportieren“
- [ ] [API] Der Export liefert eine Druckdatei (CSV) mit Code und QR-Link und ist je Charge nur einmal möglich
- [ ] [DB] Zeitpunkt und verantwortliches Konto des Exports werden gespeichert
- [ ] [API] Ein zweiter Export derselben Charge antwortet 409 mit Hinweis

Quelle: `requirements/functional-requirements.md` → FR-012
```

### FR-067: Berichte auf der Verwaltungsseite

Meilenstein: **S10 – Briefdruck und Gemeinderatsberichte** · Labels: `Priorität/Kann`, `Rolle/Verwaltung`

```markdown
**Abhängig von:** FR-030
**Blockiert:** –

**Anforderung:** Die Verwaltung erstellt aus Snapshots (FR-030) aufbereitete Berichte für den Gemeinderat und wählt den Zeitraum der Auswertung. Das Protokoll der Verwaltungsaktionen regelt.

**Akzeptanzkriterien:**
- [ ] [UI] Bericht aus einem Snapshot oder dem Vergleich zweier Snapshots für einen gewählten Zeitraum
- [ ] [UI] Druckansicht und Download (PDF über den Browser)
- [ ] [API] Der Bericht enthält nur aggregierte Werte

Quelle: `requirements/functional-requirements.md` → FR-067
```

---

## S11 – Mitwirkung erweitern

### FR-013: Spitzname

Meilenstein: **S11 – Mitwirkung erweitern** · Labels: `Priorität/Kann`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-007
**Blockiert:** –

**Anforderung:** Bürger können in „Mein Bereich“ freiwillig einen Spitznamen wählen, der bei ihren Vorschlägen angezeigt wird. Bei der Eingabe weist die Anwendung darauf hin, keinen echten Namen zu verwenden. Ohne Spitzname bleibt der Zugang anonym.

**Akzeptanzkriterien:**
- [ ] [UI] In „Mein Bereich“ lässt sich ein Spitzname (3–30 Zeichen) setzen, ändern und entfernen
- [ ] [UI] Beim Eingeben erscheint der Hinweis, keinen echten Namen zu verwenden
- [ ] [API] Spitznamen mit Links oder nur Leerzeichen werden abgewiesen (400)
- [ ] [UI] Der Spitzname erscheint bei eigenen Vorschlägen; ohne Spitznamen steht dort nichts

Quelle: `requirements/functional-requirements.md` → FR-013
```

### FR-053: Vorschläge melden

Meilenstein: **S11 – Mitwirkung erweitern** · Labels: `Priorität/Kann`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-048, FR-066
**Blockiert:** –

**Anforderung:** Bürger melden unpassende Vorschläge an die Verwaltung.

**Akzeptanzkriterien:**
- [ ] [UI] Angemeldete Bürger können einen Vorschlag mit einem Grund melden
- [ ] [API] Je Zugang und Vorschlag höchstens eine Meldung
- [ ] [UI] Die Verwaltung sieht gemeldete Vorschläge mit Anzahl der Meldungen bei „Inhalte moderieren“

Quelle: `requirements/functional-requirements.md` → FR-053
```

### FR-054: Foto zum Vorschlag

Meilenstein: **S11 – Mitwirkung erweitern** · Labels: `Priorität/Kann`, `Rolle/Bürger`

```markdown
**Abhängig von:** FR-044
**Blockiert:** –

**Anforderung:** Bürger fügen einem Vorschlag ein Foto bei.

**Akzeptanzkriterien:**
- [ ] [UI] Im Schritt „Anliegen“ lässt sich ein Foto (JPEG/PNG, max. 5 MB) hinzufügen und entfernen
- [ ] [API] Metadaten (z. B. GPS) werden beim Hochladen entfernt; andere Dateitypen → 400
- [ ] [UI] Das Foto erscheint am Vorschlag mit Pflicht-Alternativtext
- [ ] [API] Beim Entfernen oder Löschen des Vorschlags wird das Foto gelöscht

Quelle: `requirements/functional-requirements.md` → FR-054
```

### FR-074: Erinnerung an freie Punkte

Meilenstein: **S11 – Mitwirkung erweitern** · Labels: `Priorität/Kann`, `Rolle/System`

```markdown
**Abhängig von:** FR-024, FR-071
**Blockiert:** –

**Anforderung:** Bestätigte Empfänger mit freien Punkten erhalten eine Erinnerung, ihre Punkte zu verteilen. Die Erinnerung wiederholt sich in einem konfigurierbaren Abstand, solange Punkte frei sind, und lässt sich einzeln abbestellen.

**Akzeptanzkriterien:**
- [ ] [API] Bestätigte Empfänger mit freien Punkten erhalten im konfigurierbaren Abstand eine Erinnerung
- [ ] [API] Sind alle Punkte vergeben, endet die Erinnerung
- [ ] [UI] Die Erinnerung lässt sich einzeln in den Einstellungen und per Link in der Mail abbestellen

Quelle: `requirements/functional-requirements.md` → FR-074
```
