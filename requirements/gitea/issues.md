# Issues – StadtStimme

Ein Issue je funktionaler Anforderung. Je Issue: Titel, Beschreibung (Markdown), Labels und Meilenstein.
Empfohlene Labels in Gitea anlegen: `Priorität/Muss`, `Priorität/Soll`, `Priorität/Kann` (exklusiv) und `Rolle/Bürger`, `Rolle/Besucher`, `Rolle/Verwaltung`, `Rolle/System`.

Sortiert nach Meilenstein, damit ihr sie der Reihe nach anlegen könnt.

---

## S1 – MVP: Prioritäten setzen und Ergebnis sehen

### FR-001: Anmeldung mit Aktivierungscode

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Anforderung:** Bürger melden sich mit dem Code aus dem Brief der Stadt an. Ein Code ist 16 Zeichen Crockford-Base32 (80 Bit); Eingaben mit Bindestrichen, Leerzeichen oder Kleinbuchstaben werden normalisiert. Ein QR-Code auf dem Brief füllt den Code vor; eingelöst wird erst nach dem Absenden. Ein gültiger Code legt beim ersten Einlösen genau einen Zugang an; jedes weitere Einlösen desselben Codes (auch auf einem anderen Gerät) führt in denselben Zugang. Der Code ist bis zur Entscheidung über die Gerätebindung zugleich der Login.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-001
```

### FR-002: Ein Budget je Code

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Anforderung:** Jeder Code berechtigt zu genau einem Zugang mit einem Budget. Mehrfaches Teilnehmen mit demselben Code ist ausgeschlossen, auch bei gleichzeitigen Anfragen.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-002
```

### FR-003: Code nur als Hash speichern

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Anforderung:** Das System speichert keinen Code im Klartext, sondern nur einen HMAC-Hash mit einem eigenen Pepper (`STADTSTIMME_CODE_PEPPER`, sonst `DJANGO_SECRET_KEY`). Der Klartext eines neuen Codes ist nur in der Ausgabe beim Erzeugen sichtbar.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-003
```

### FR-004: Sperre nach Fehlversuchen

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Anforderung:** Nach 10 fehlgeschlagenen Anmeldeversuchen (`STADTSTIMME_MAX_FAILED_ATTEMPTS`) pro Client wird die Anmeldung für 60 Minuten (`STADTSTIMME_LOCKOUT_MINUTES`) gesperrt. Die IP-Adresse wird dafür nur als Hash gespeichert. Die Sperre gilt für Code-Anmeldung und Verwaltungsanmeldung gleichermaßen.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-004
```

### FR-005: Verständliche Fehlermeldungen beim Einlösen

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Anforderung:** Bei falsch formatiertem, unbekanntem oder gesperrtem Code sowie bei aktiver Sperre nach Fehlversuchen erhält der Bürger je eine eigene, verständliche Meldung mit dem nächsten Schritt. Eine Hilfe erklärt, wo der Code steht.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-005
```

### FR-006: Angemeldet bleiben und Abmelden

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Anforderung:** Nach dem Einlösen bleibt der Bürger auf dem Gerät angemeldet (Sitzungsdauer 183 Tage, `STADTSTIMME_SESSION_DAYS`), bis er sich abmeldet. Abmelden beendet die Sitzung auf diesem Gerät.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-006
```

### FR-009: Geschützte Bürgerfunktionen

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Anforderung:** Punkte verteilen, Vorschläge einreichen und unterstützen sowie E-Mail-Hinweise verwalten sind nur mit gültigem Zugang möglich. Ohne Anmeldung werden Besucher zur Code-Eingabe geleitet. Bereits angemeldete Bürger werden von der Code-Eingabe zur Übersicht weitergeleitet.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-009
```

### FR-011: Aktivierungscodes erzeugen

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung erzeugt Codes in Chargen (z. B. je Briefversand) mit Angabe der Charge. Die Ausgabe enthält die Klartexte einmalig zur Weitergabe an den Druck.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-011
```

### FR-014: Themen pflegen

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung pflegt Themen (Kategorien) mit eindeutigem Namen. Übliche Themen erhalten automatisch Farbe und Symbol, andere reihum; die Farbe ist änderbar.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-014
```

### FR-015: Einrichtungen pflegen

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung pflegt Einrichtungen mit externer ID, Name, Thema, Adresse, Kurzbeschreibung und optionalen Koordinaten. Breiten- und Längengrad sind nur gemeinsam gültig. Eine Einrichtung ohne Koordinaten erscheint nicht auf Karten.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-015
```

### FR-018: Ausgaben pflegen

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung pflegt Ist-Ausgaben je Einrichtung und Haushaltsjahr. Diese Werte sind die Grundlage für den Vergleich mit den Bürgerpunkten.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-018
```

### FR-019: CSV-Import mit Vorschau

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Einrichtungen, Gebäude, Maßnahmen und Ausgaben lassen sich per CSV importieren, einzeln über die Oberfläche mit Vorschau vor dem Speichern oder alle vier auf einmal per Befehl. Der Gesamtimport läuft in einer Transaktion (bei einem Fehler wird nichts gespeichert), bietet einen Probelauf und ist wiederholbar: Zeilen werden über die externe ID aktualisiert statt doppelt angelegt.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-019
```

### FR-022: Budget von 100 Punkten

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Anforderung:** Jeder Zugang hat ein Budget von 100 Punkten. Die Summe der vergebenen Punkte darf 100 nie überschreiten; ein Speichern darüber wird abgewiesen.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-022
```

### FR-023: Punkte an Einrichtung oder ganzes Thema

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Anforderung:** Bürger vergeben Punkte an einzelne Einrichtungen oder an ein ganzes Thema („… allgemein“). Je Ziel gibt es höchstens eine Vergabe pro Zugang.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-023
```

### FR-024: Verteilung bearbeiten und speichern

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Anforderung:** Bürger ändern Punkte je Ziel per Plus/Minus in Einerschritten oder per direkter Zahleneingabe; zulässig sind nur ganze, nicht negative Zahlen. Vergebene und freie Punkte sowie die Summe je Thema aktualisieren sich bei jeder Änderung sofort, als Zahl und als Raster aus 100 Feldern, in dem Punkte an ein ganzes Thema erkennbar sind. Gespeichert wird die ganze Verteilung auf einmal; ein Teil des Budgets darf frei bleiben. Bürger können jederzeit umverteilen. Für die Auswertung zählt je Zugang nur die zuletzt erfolgreich gespeicherte Verteilung.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-024
```

### FR-036: Öffentliche Übersicht

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/Besucher`

```markdown
**Anforderung:** Die Übersicht ist ohne Anmeldung erreichbar und zeigt den Vergleich je Thema (Anteil Bürgerpunkte gegen Anteil Ist-Ausgaben), eine Karte mit Liste der Einrichtungen, den Datenstand, die Zahl der Teilnehmenden, die meistunterstützten Vorschläge mit Link und Neuigkeiten.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-036
```

### FR-038: Vergleich mit dem letzten abgeschlossenen Haushaltsjahr

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Anforderung:** Alle Vergleiche verwenden die Ist-Ausgaben des letzten abgeschlossenen Haushaltsjahres. Fehlen solche Ausgaben, zeigt die Seite das ausdrücklich an.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-038
```

### FR-078: Demo-Modus

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Anforderung:** Im Demo-Modus lädt das System fiktive Testdaten (Mannheim) in einen leeren Katalog, legt Demo-Codes und einen Demo-Admin an und macht Admin und Verwaltungsseite erreichbar. Ohne Demo-Modus sind beide nicht erreichbar.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-078
```

### FR-079: Health-Check

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Soll`, `Rolle/System`

```markdown
**Anforderung:** Ein öffentlicher Endpunkt meldet, ob die Anwendung läuft und die Datenbank erreichbar ist.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-079
```

### FR-080: Stadtname konfigurierbar

Meilenstein: **S1 – MVP: Prioritäten setzen und Ergebnis sehen** · Labels: `Priorität/Soll`, `Rolle/System`

```markdown
**Anforderung:** Der Stadtname in Logo und Texten kommt aus `STADTSTIMME_CITY_NAME`, damit andere Kommunen die Anwendung ohne Codeänderung nutzen können.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-080
```

---

## S2 – Wunsch und Haushalt im Detail vergleichen

### FR-016: Gebäude als optionale Ebene

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Kann`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Eine Einrichtung kann Gebäude haben. Maßnahmen lassen sich einem Gebäude ihrer Einrichtung zuordnen; Punkte und Vergleiche bleiben pro Einrichtung.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-016
```

### FR-017: Maßnahmen pflegen

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung pflegt Maßnahmen je Einrichtung mit Status (offen, beschlossen, in Umsetzung, abgeschlossen, verworfen). Maßnahmen zeigen, wofür eine Einrichtung Geld braucht, tragen aber selbst keine Punkte.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-017
```

### FR-020: CSV-Export des Katalogs

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Soll`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Jede Katalogliste lässt sich als CSV exportieren.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-020
```

### FR-025: Ziele filtern und auf der Karte finden

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Soll`, `Rolle/Bürger`

```markdown
**Anforderung:** In „Punkte verteilen“ lassen sich Ziele nach Thema filtern und Einrichtungen auf einer Karte finden. Eine Liste ist die gleichwertige Alternative zur Karte.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-025
```

### FR-026: Eigene Verteilung mit dem Gesamtbild vergleichen

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Kann`, `Rolle/Bürger`

```markdown
**Anforderung:** Bürger sehen ihre eigene Verteilung neben der Verteilung aller Teilnehmenden.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-026
```

### FR-037: Eigene Punkte in der Übersicht

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Soll`, `Rolle/Bürger`

```markdown
**Anforderung:** Angemeldete Bürger sehen in der Übersicht zusätzlich ihre eigene Verteilung im Vergleich zum Anteil aller Bürgerpunkte und zu den Ausgaben, ihre vergebenen und freien Punkte als Zahl und Raster aus 100 Feldern mit Link zu „Punkte verteilen“, ihre eigenen Vorschläge und bis wann ihre Punkte gültig sind.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-037
```

### FR-039: Lücke je Einrichtung und je Thema

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Muss`, `Rolle/Besucher`

```markdown
**Anforderung:** Die Ergebnisseite zeigt je Einrichtung und je ganzem Thema die Lücke in Prozentpunkten: Anteil Bürgerpunkte minus Anteil Ist-Ausgaben. Der Themenvergleich enthält alle Punkte des Themas inkl. „… allgemein“ und alle Ausgaben des Themas.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-039
```

### FR-040: Detail je Einrichtung

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Soll`, `Rolle/Besucher`

```markdown
**Anforderung:** Zu jeder Einrichtung lassen sich in den Ergebnissen Punkte, Ausgaben und zugehörige Maßnahmen im Detail ansehen. Die Auswahl erfolgt über die Liste oder die Markierung auf der Ergebniskarte.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-040
```

### FR-041: Einordnung der Belastbarkeit

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Soll`, `Rolle/Besucher`

```markdown
**Anforderung:** Die Ergebnisse nennen Stand, Zahl der Mitmachenden, vergebene Punkte, durchschnittliche Punkte je Person, Anteil an ganze Themen und Summe der Ausgaben sowie den Hinweis, dass die Zahlen nicht repräsentativ sind.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-041
```

### FR-042: Ergebnisse als CSV

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Soll`, `Rolle/Besucher`

```markdown
**Anforderung:** Die Ergebnistabelle lässt sich als CSV herunterladen (Semikolon, Dezimalkomma, BOM für deutsche Tabellenprogramme). Texte werden gegen Formel-Injektion geschützt.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-042
```

### FR-043: Karten der Einrichtungen

Meilenstein: **S2 – Wunsch und Haushalt im Detail vergleichen** · Labels: `Priorität/Soll`, `Rolle/Besucher`

```markdown
**Anforderung:** Übersicht, „Punkte verteilen“, Ergebnisse und Vorschläge zeigen Einrichtungen mit Koordinaten auf einer zoombaren Karte, immer zusammen mit einer gleichwertigen Liste. Markierungen zeigen das Thema (Farbe und Symbol) und mit ihrer Größe den Anteil an den Bürgerpunkten. Ein Klick auf eine Markierung führt zum zugehörigen Ziel bzw. zu seinen Details. Angemeldete Bürger können zwischen allen Einrichtungen und den von ihnen gewichteten umschalten. Fällt der Kachelserver aus, wechselt die Karte auf einen Ersatz und zeigt danach mindestens die Marker.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-043
```

---

## S3 – Ereignis-Log, Verfall und Stichtag

### FR-010: Anmeldung der Verwaltung

Meilenstein: **S3 – Ereignis-Log, Verfall und Stichtag** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Auf der Anmeldeseite wählt man zwischen „Bürgerin oder Bürger“ (Code) und „Stadtverwaltung“ (Benutzername und Passwort). Nur Benutzer mit Mitarbeiter-Status gelangen auf die Verwaltungsseite. Jede Verwaltungsfunktion prüft ihr eigenes Recht (z. B. „Vorschlag ändern“, „Einrichtung ändern“, Datenpflege je Katalogliste), sodass sich Mitarbeitende über Gruppen unterschiedliche Rechte-Kategorien zuweisen lassen. Bis zum Admin-Login-Konzept ist das nur im Demo-Modus verfügbar; sonst zeigt die Seite einen Hinweis.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-010
```

### FR-030: Snapshot als Abstimmungszeitpunkt

Meilenstein: **S3 – Ereignis-Log, Verfall und Stichtag** · Labels: `Priorität/Soll`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Beteiligung bleibt fortlaufend ohne feste Runden. Die Verwaltung hält zu einem beliebigen Zeitpunkt einen benannten, datierten Snapshot fest (aggregierte Punkte je Ziel, Teilnehmende, Ziele, Ist-Ausgaben). Snapshots sind unveränderlich, werden aus dem Ereignis-Log berechnet (FR-032, FR-064), lassen sich in der Anwendung einsehen, als CSV herunterladen und miteinander vergleichen. So kann sich die Stadt, z. B. für eine Gemeinderatssitzung, auf einen festen Abstimmungsstand beziehen.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-030
```

### FR-032: Unveränderliches Ereignis-Log

Meilenstein: **S3 – Ereignis-Log, Verfall und Stichtag** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Anforderung:** Jede Punkteänderung (vergeben, entzogen, zurückgegeben, verfallen) wird in derselben Transaktion als unveränderliches Ereignis mit Delta, Zeitpunkt und optional der auslösenden Maßnahme gespeichert. Ändern und Löschen von Ereignissen ist ausgeschlossen. Beim Löschen eines Zugangs bleibt das Log pseudonym erhalten.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-032
```

### FR-034: Verfall nach Inaktivität

Meilenstein: **S3 – Ereignis-Log, Verfall und Stichtag** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Anforderung:** Alle Punkte eines Zugangs verfallen nach 183 Tagen ohne Aktivität (`STADTSTIMME_POINTS_EXPIRY_DAYS`). Ergebnisse zählen verfallene Punkte sofort nicht mehr mit. Entzogen werden sie, sobald die Person zurückkommt, oder durch den täglichen Lauf. Jede Nutzung mit dem Zugang verlängert die Frist.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-034
```

### FR-035: Tägliche Aufgaben

Meilenstein: **S3 – Ereignis-Log, Verfall und Stichtag** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Anforderung:** Ein täglicher Lauf (Standard 02:00 UTC, `DAILY_TASKS_AT`) verschickt zuerst Verfallswarnungen und lässt danach Punkte verfallen. Beide Schritte sind idempotent, jederzeit manuell startbar, und ein Fehler im einen hält den anderen nicht auf.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-035
```

### FR-059: Beteiligung beobachten

Meilenstein: **S3 – Ereignis-Log, Verfall und Stichtag** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung sieht die Beteiligung nur als Summen: eingelöste Codes je Woche, eingelöste Codes und Zugänge mit vergebenen Punkten. Rückschlüsse auf einzelne Personen sind nicht möglich.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-059
```

### FR-064: Stichtags-Export

Meilenstein: **S3 – Ereignis-Log, Verfall und Stichtag** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung lädt für einen Stichtag eine CSV mit Punkten und Unterstützern je Ziel zum Tagesende herunter, ergänzt um die Zahl der Teilnehmenden und die Ist-Ausgaben je Ziel. Die Werte werden aus dem Ereignis-Log berechnet und sind für denselben Stichtag reproduzierbar.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-064
```

### FR-065: Zugänge je Charge

Meilenstein: **S3 – Ereignis-Log, Verfall und Stichtag** · Labels: `Priorität/Soll`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung sieht je Charge, wie viele Codes ausgegeben und eingelöst sind.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-065
```

---

## S4 – Vorschläge einreichen und unterstützen

### FR-007: Mein Bereich

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Soll`, `Rolle/Bürger`

```markdown
**Anforderung:** Angemeldete Bürger haben einen Bereich „Mein Bereich“ mit Anmeldestatus, ihrem Punktestand (vergeben und frei), ihren eigenen Vorschlägen mit Schritt und ihren Einstellungen für E-Mail-Hinweise, jeweils mit Link zu „Punkte verteilen“, „Vorschläge“ und den Hinweis-Einstellungen.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-007
```

### FR-044: Vorschlag einreichen

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Anforderung:** Angemeldete Bürger reichen einen Vorschlag in drei Schritten ein: Anliegen (Titel 8–80 Zeichen, Beschreibung optional bis 600 Zeichen), Einordnen, Prüfen. Vor dem Einreichen können sie zu jedem vorherigen Schritt zurückkehren und korrigieren, ohne Eingaben zu verlieren.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-044
```

### FR-045: Thema und Ort eines Vorschlags

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Anforderung:** Ein Vorschlag hat immer ein Thema. Der Ort ist „allgemein“, eine bekannte Einrichtung passend zum Thema oder ein neuer Punkt auf der Karte (per Klick oder Kartenmitte für Tastaturnutzung). Einrichtung und Punkt sind nie gleichzeitig gesetzt. Ohne JavaScript stehen „allgemein“ und „bekannter Ort“ zur Verfügung.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-045
```

### FR-046: Tageslimit für Vorschläge

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Anforderung:** Ein Zugang darf höchstens 5 Vorschläge pro Tag einreichen (`STADTSTIMME_PROPOSALS_PER_DAY`); darüber wird mit Hinweis abgewiesen.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-046
```

### FR-047: Ähnliche Einträge vorschlagen

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Soll`, `Rolle/Bürger`

```markdown
**Anforderung:** Beim Schreiben zeigt „Gibt es das schon?“ ähnliche Vorschläge und offene Maßnahmen (Abgleich über Wortstämme), damit Doppelungen vermieden werden.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-047
```

### FR-048: Vorschläge sofort öffentlich

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Anforderung:** Ein eingereichter Vorschlag ist ohne Freigabe sofort öffentlich sichtbar und unterstützbar.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-048
```

### FR-049: Vorschlag unterstützen

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Anforderung:** Angemeldete Bürger unterstützen beliebig viele offene Vorschläge anderer, jeden höchstens einmal, und können die Unterstützung zurückziehen. Unterstützungen sind unabhängig vom Budget der 100 Punkte. Eigene sowie entschiedene Vorschläge sind nicht unterstützbar; abgelehnte Vorschläge erscheinen nicht mehr unter den eigenen unterstützten.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-049
```

### FR-050: Weg eines Vorschlags

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Muss`, `Rolle/Besucher`

```markdown
**Anforderung:** Jeder Vorschlag zeigt seinen Schritt: „Sammelt“ (unter der Schwelle von 50 Unterstützungen, `STADTSTIMME_PROPOSAL_SUPPORT_THRESHOLD`), „In Prüfung“ (Schwelle erreicht, seit dem Zeitpunkt der N-ten Unterstützung) und „Entschieden“ (angenommen oder abgelehnt). Solange ein Vorschlag sammelt, zeigt er die noch benötigten Unterstützungen. Die Liste lässt sich nach Schritt filtern, auch ohne JavaScript.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-050
```

### FR-055: Vorschlagsliste durchsuchen, filtern und sortieren

Meilenstein: **S4 – Vorschläge einreichen und unterstützen** · Labels: `Priorität/Soll`, `Rolle/Besucher`

```markdown
**Anforderung:** Die Vorschlagsliste ist nach Titel und Ort durchsuchbar, nach Thema und Schritt filterbar und nach Zahl der Unterstützungen sortierbar. Angemeldete Bürger wählen zwischen allen und nur ihren eigenen Vorschlägen. Filter und Sortierung funktionieren ohne JavaScript.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-055
```

---

## S5 – Stadt antwortet auf Vorschläge

### FR-028: Hinweis auf angenommene Vorschläge

Meilenstein: **S5 – Stadt antwortet auf Vorschläge** · Labels: `Priorität/Soll`, `Rolle/Bürger`

```markdown
**Anforderung:** Angenommene Vorschläge erscheinen in „Punkte verteilen“ als Hinweis an ihrer Einrichtung oder, ohne Einrichtung, beim Thema („… allgemein“), mit Link zum Vorschlag. Sie sind kein eigenes Punkteziel.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-028
```

### FR-051: Öffentliche Antwort der Stadt

Meilenstein: **S5 – Stadt antwortet auf Vorschläge** · Labels: `Priorität/Muss`, `Rolle/Besucher`

```markdown
**Anforderung:** Entschiedene Vorschläge zeigen die öffentliche Begründung der Stadt, das Entscheidungsdatum und gegebenenfalls die daraus entstandene Maßnahme. Angenommene und abgelehnte Vorschläge bleiben dauerhaft sichtbar, weil es keine abgeschlossenen Runden gibt.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-051
```

### FR-052: Neuer Ort wird Einrichtung

Meilenstein: **S5 – Stadt antwortet auf Vorschläge** · Labels: `Priorität/Soll`, `Rolle/System`

```markdown
**Anforderung:** Wird ein Vorschlag mit neuem Ort angenommen, legt das System daraus eine Einrichtung an (Name = Titel, Thema und Koordinaten vom Vorschlag, externe ID `VORSCHLAG-<Nr>`) und verknüpft den Vorschlag mit ihr. Sie ist danach wählbar und in Karten und Ergebnissen enthalten.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-052
```

### FR-057: Wartet auf Sie

Meilenstein: **S5 – Stadt antwortet auf Vorschläge** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltungsseite listet Vorschläge in Prüfung mit ihrer Antwortfrist von 14 Tagen ab Erreichen der Schwelle (`STADTSTIMME_PROPOSAL_REVIEW_DAYS`), früheste Frist zuerst.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-057
```

### FR-058: Vorschlag entscheiden

Meilenstein: **S5 – Stadt antwortet auf Vorschläge** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung nimmt einen Vorschlag an oder lehnt ihn ab, jederzeit, auch vor Erreichen der Schwelle. Pflicht ist eine öffentliche Antwort mit mindestens 20 Zeichen, optional eine verknüpfte Maßnahme. Ein bereits entschiedener Vorschlag kann nicht erneut entschieden werden. Entscheiden erfordert das Recht „Vorschlag ändern“.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-058
```

### FR-060: Vorschläge nach Schritt

Meilenstein: **S5 – Stadt antwortet auf Vorschläge** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung sieht alle Vorschläge gruppiert nach Schritt mit Zugang zur Entscheidungsseite.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-060
```

### FR-066: Inhalte moderieren

Meilenstein: **S5 – Stadt antwortet auf Vorschläge** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung kann unpassende Vorschläge mit Begründung ablehnen (FR-058) oder doppelte und unzulässige Vorschläge mit Begründung entfernen. Ein entfernter Vorschlag ist öffentlich nicht mehr sichtbar; sein Ersteller sieht in „Mein Bereich“, dass und warum er entfernt wurde.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-066
```

---

## S6 – Rückfluss: Erledigtes gibt Punkte frei

### FR-027: Erledigte Einrichtungen nicht wählbar

Meilenstein: **S6 – Rückfluss: Erledigtes gibt Punkte frei** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Anforderung:** Als erledigt markierte Einrichtungen fehlen in „Punkte verteilen“ (Liste und Karte). Ein Speichern mit Punkten an einer erledigten Einrichtung wird mit Hinweis abgewiesen.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-027
```

### FR-031: Verlauf zurückgekommener und verfallener Punkte

Meilenstein: **S6 – Rückfluss: Erledigtes gibt Punkte frei** · Labels: `Priorität/Soll`, `Rolle/Bürger`

```markdown
**Anforderung:** „Punkte verteilen“ zeigt Punkte, die in den letzten 30 Tagen zurückgekommen oder verfallen sind, mit Anlass.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-031
```

### FR-033: Rückfluss bei Umsetzung einer Maßnahme

Meilenstein: **S6 – Rückfluss: Erledigtes gibt Punkte frei** · Labels: `Priorität/Muss`, `Rolle/System`

```markdown
**Anforderung:** Geht eine Maßnahme auf „in Umsetzung“ (über Admin, Verwaltungsseite oder CSV-Import, auch bei Neuanlage), erhalten alle Unterstützer ihre Punkte auf der zugehörigen Einrichtung zurück. Punkte an ein ganzes Thema bleiben. „Verworfen“ löst keinen Rückfluss aus. Parallel neu vergebene Punkte bleiben erhalten.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-033
```

### FR-061: Einrichtungen nach Lücke

Meilenstein: **S6 – Rückfluss: Erledigtes gibt Punkte frei** · Labels: `Priorität/Soll`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung sieht Einrichtungen sortiert nach Lücke mit ihren Maßnahmen und einem Link zur Datenpflege.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-061
```

### FR-062: Einrichtung als erledigt markieren

Meilenstein: **S6 – Rückfluss: Erledigtes gibt Punkte frei** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung markiert eine Einrichtung als erledigt, auch ohne passende Maßnahme. Vorher bestätigt sie eine Rückfrage mit Zahl der Unterstützer und Punkte. Danach gehen alle Punkte an dieser Einrichtung an die Unterstützer zurück, und Betroffene mit E-Mail-Hinweis werden benachrichtigt; Themenpunkte bleiben. Dasselbe gilt, wenn eine Einrichtung dauerhaft aus dem Katalog genommen wird: Sie wird dann als erledigt archiviert statt gelöscht, weil das Ereignis-Log auf sie verweist. Erfordert das Recht „Einrichtung ändern“.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-062
```

### FR-063: Einrichtung wieder öffnen

Meilenstein: **S6 – Rückfluss: Erledigtes gibt Punkte frei** · Labels: `Priorität/Muss`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Eine erledigte Einrichtung wird wieder wählbar über „Wieder öffnen“ oder automatisch, sobald die Stadt einen Vorschlag an diesem Ort annimmt. In Ergebnissen, Suche und als bekannter Ort bei Vorschlägen bleibt sie immer sichtbar.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-063
```

---

## S7 – Hinweise per E-Mail

### FR-070: E-Mail freiwillig hinterlegen

Meilenstein: **S7 – Hinweise per E-Mail** · Labels: `Priorität/Soll`, `Rolle/Bürger`

```markdown
**Anforderung:** Bürger hinterlegen freiwillig eine E-Mail-Adresse für Hinweise, ändern oder entfernen sie und wählen, welche Arten von Hinweisen sie erhalten. Die Adresse wird verschlüsselt und getrennt von den Punkten gespeichert und mit dem Zugang gelöscht.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-070
```

### FR-071: Double-Opt-in

Meilenstein: **S7 – Hinweise per E-Mail** · Labels: `Priorität/Soll`, `Rolle/System`

```markdown
**Anforderung:** Hinweise gehen erst nach Bestätigung über einen Link raus. Der Link ist 72 Stunden gültig, das Token wird nur als Hash gespeichert, und das Öffnen des Links bestätigt erst nach Klick auf einen Knopf. Eine neue Bestätigungsmail ist frühestens nach 10 Minuten möglich.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-071
```

### FR-072: Verfallswarnung

Meilenstein: **S7 – Hinweise per E-Mail** · Labels: `Priorität/Soll`, `Rolle/System`

```markdown
**Anforderung:** Bestätigte Empfänger erhalten 14 Tage vor dem Verfall (`STADTSTIMME_POINTS_EXPIRY_WARNING_DAYS`) eine Warnung, einmal je Inaktivitätsphase.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-072
```

### FR-073: Hinweis bei Rückfluss

Meilenstein: **S7 – Hinweise per E-Mail** · Labels: `Priorität/Soll`, `Rolle/System`

```markdown
**Anforderung:** Bestätigte Empfänger erhalten eine E-Mail, wenn Punkte zu ihnen zurückkommen (Maßnahme in Umsetzung oder Einrichtung erledigt).

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-073
```

### FR-075: Hinweis zu eigenen und unterstützten Vorschlägen

Meilenstein: **S7 – Hinweise per E-Mail** · Labels: `Priorität/Soll`, `Rolle/System`

```markdown
**Anforderung:** Bestätigte Empfänger erhalten einen Hinweis, wenn ein eigener oder unterstützter Vorschlag die Schwelle erreicht, angenommen, abgelehnt oder von der Stadt beantwortet wird.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-075
```

### FR-076: Abmelden mit einem Klick

Meilenstein: **S7 – Hinweise per E-Mail** · Labels: `Priorität/Soll`, `Rolle/Bürger`

```markdown
**Anforderung:** Jede Hinweis-Mail enthält einen Abmeldelink und `List-Unsubscribe` (Ein-Klick nach RFC 8058). Abmelden löscht die Adresse.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-076
```

### FR-077: Robust bei Mailausfall

Meilenstein: **S7 – Hinweise per E-Mail** · Labels: `Priorität/Soll`, `Rolle/System`

```markdown
**Anforderung:** Ist der Mailserver nicht erreichbar, schlägt keine fachliche Aktion fehl (z. B. Speichern einer Maßnahme); es wird lediglich keine Mail versendet.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-077
```

---

## S8 – Zugänge verwalten und löschen

### FR-008: Zugang selbst löschen

Meilenstein: **S8 – Zugänge verwalten und löschen** · Labels: `Priorität/Muss`, `Rolle/Bürger`

```markdown
**Anforderung:** Bürger löschen ihren Zugang in „Mein Bereich“ nach einer Rückfrage, die die Folgen nennt. Alle Punkte werden entzogen (Ereignis „entzogen“), die E-Mail-Adresse für Hinweise wird gelöscht, und eigene Vorschläge und Unterstützungen werden entfernt. Das Ereignis-Log bleibt pseudonym erhalten (FR-032). Der Code ist danach gesperrt; neu teilnehmen kann die Person nur mit einem neuen Code der Stadt.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-008
```

### FR-068: Zugang finden und einsehen

Meilenstein: **S8 – Zugänge verwalten und löschen** · Labels: `Priorität/Soll`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung findet einen Zugang über die letzten 8 Zeichen seines Codes (z. B. bei einer Anfrage per Telefon) und sieht Status, Charge, Zeitpunkt des Einlösens, letzte Aktivität und die Vorschläge des Zugangs. Die Punkteverteilung des Zugangs sieht sie nicht. Von dort kann sie den Zugang schließen und wieder öffnen (FR-069), aber nichts im Namen des Bürgers ändern.

**Hinweis:** Codes liegen nur als Hash vor; für die Suche braucht es einen eigenen Hash der letzten 8 Zeichen.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-068
```

### FR-069: Zugang schließen und wieder öffnen

Meilenstein: **S8 – Zugänge verwalten und löschen** · Labels: `Priorität/Soll`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung schließt einen Zugang (z. B. bei Wegzug) und öffnet ihn bei Bedarf wieder. Das Schließen wirkt sofort, auch auf bestehende Anmeldungen. Alle Punkte des Zugangs werden entzogen (Ereignis „entzogen“); seine Vorschläge und Unterstützungen bleiben erhalten. Erfordert ein eigenes Recht.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-069
```

---

## S9 – Finden und teilen

### FR-021: Öffentliche Suche

Meilenstein: **S9 – Finden und teilen** · Labels: `Priorität/Soll`, `Rolle/Besucher`

```markdown
**Anforderung:** Besucher durchsuchen Einrichtungen und passende Maßnahmen über eine Suchleiste. Treffer verlinken auf die Ergebnisse und auf „Punkte verteilen“. Die Suche ist ohne Anmeldung und ohne JavaScript nutzbar.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-021
```

### FR-029: Ziele per QR-Code verlinken

Meilenstein: **S9 – Finden und teilen** · Labels: `Priorität/Kann`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Für jede Einrichtung und jedes Thema gibt es einen direkten Link auf das Ziel in „Punkte verteilen“, den die Verwaltung als QR-Code ausgeben kann (z. B. als Aushang vor Ort). Der QR-Code enthält keinen Zugangscode.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-029
```

### FR-056: Vorschlag teilen

Meilenstein: **S9 – Finden und teilen** · Labels: `Priorität/Kann`, `Rolle/Bürger`

```markdown
**Anforderung:** Jeder Vorschlag hat einen dauerhaften, öffentlichen Link, den Ersteller und andere teilen können. Der Link enthält keinen Zugangscode und keine Angabe zum Ersteller.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-056
```

---

## S10 – Briefdruck und Gemeinderatsberichte

### FR-012: Codes für den Briefdruck exportieren

Meilenstein: **S10 – Briefdruck und Gemeinderatsberichte** · Labels: `Priorität/Kann`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung exportiert Codes für den Druck (DECISIONS.md, zurückgestellt). Sperren und Wiederöffnen eines Zugangs regelt FR-069.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-012
```

### FR-067: Berichte auf der Verwaltungsseite

Meilenstein: **S10 – Briefdruck und Gemeinderatsberichte** · Labels: `Priorität/Kann`, `Rolle/Verwaltung`

```markdown
**Anforderung:** Die Verwaltung erstellt aus Snapshots (FR-030) aufbereitete Berichte für den Gemeinderat und wählt den Zeitraum der Auswertung. Das Protokoll der Verwaltungsaktionen regelt.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-067
```

---

## S11 – Mitwirkung erweitern

### FR-013: Spitzname

Meilenstein: **S11 – Mitwirkung erweitern** · Labels: `Priorität/Kann`, `Rolle/Bürger`

```markdown
**Anforderung:** Bürger können in „Mein Bereich“ freiwillig einen Spitznamen wählen, der bei ihren Vorschlägen angezeigt wird. Bei der Eingabe weist die Anwendung darauf hin, keinen echten Namen zu verwenden. Ohne Spitzname bleibt der Zugang anonym.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-013
```

### FR-053: Vorschläge melden

Meilenstein: **S11 – Mitwirkung erweitern** · Labels: `Priorität/Kann`, `Rolle/Bürger`

```markdown
**Anforderung:** Bürger melden unpassende Vorschläge an die Verwaltung.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-053
```

### FR-054: Foto zum Vorschlag

Meilenstein: **S11 – Mitwirkung erweitern** · Labels: `Priorität/Kann`, `Rolle/Bürger`

```markdown
**Anforderung:** Bürger fügen einem Vorschlag ein Foto bei.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-054
```

### FR-074: Erinnerung an freie Punkte

Meilenstein: **S11 – Mitwirkung erweitern** · Labels: `Priorität/Kann`, `Rolle/System`

```markdown
**Anforderung:** Bestätigte Empfänger mit freien Punkten erhalten eine Erinnerung, ihre Punkte zu verteilen. Die Erinnerung wiederholt sich in einem konfigurierbaren Abstand, solange Punkte frei sind, und lässt sich einzeln abbestellen.

**Akzeptanzkriterien:**
- [ ] Verhalten wie beschrieben, im Browser geprüft
- [ ] Tests ergänzt (Service, bei Views auch Rechte)
- [ ] Ruff, Mypy und CI grün

Quelle: `requirements/functional-requirements.md` → FR-074
```
