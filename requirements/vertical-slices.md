# Vertical Slices – StadtStimme

Dieses Dokument teilt die funktionalen Anforderungen aus
[functional-requirements.md](functional-requirements.md) in **Vertical Slices** und legt die
Reihenfolge ihrer Umsetzung fest. Erstellt mit KI-Unterstützung (Claude) auf Basis der
Anforderungen, der Architekturanforderungen und der Entscheidungen in
[docs/DECISIONS.md](../docs/DECISIONS.md).

## Vorgehen

**Was ein Slice hier ist:** Ein Slice liefert für eine Rolle (Bürger, Besucher, Verwaltung)
einen eigenständig nutzbaren Mehrwert und geht dafür durch alle Schichten: Oberfläche
(Templates, CSS, kleine Skripte), Backend (Views, Services, Befehle) und Datenbank (Models,
Migrationen, Constraints), jeweils mit Tests. Nach jedem Slice ist die Anwendung lauffähig
(`docker compose up`) und vorführbar.

**Regeln für den Schnitt**

1. Jede FR gehört zu genau einem Slice. Erweitert ein späterer Slice eine Seite aus einem
   früheren, steht das beim späteren Slice unter „Baut auf“.
2. Ein Slice ist erst fertig, wenn sein Abnahme-Szenario von Anfang bis Ende im Browser
   funktioniert (Definition of Done aus den Projektregeln: Tests, Lint, Typprüfung grün).
3. Querschnitts-Anforderungen (Sicherheit, Datenschutz, Barrierefreiheit,
   [AR-001](architecture-requirements.md#ar-001) bis
   [AR-040](architecture-requirements.md#ar-040)) gelten für jeden Slice ab dem ersten. Pro
   Slice sind nur die ARs genannt, die dort zum ersten Mal eine Rolle spielen.

**Regeln für die Reihenfolge**

1. **Abhängigkeiten zuerst:** Ein Slice kommt erst, wenn alles, worauf er fachlich aufbaut,
   fertig ist (z. B. Rückfluss braucht das Ereignis-Log).
2. **Kernnutzen vor Erweiterung:** Muss vor Soll vor Kann. Das Beteiligungsverfahren selbst (Punkte
   geben, Ergebnis sehen) kommt vor Komfort und Kommunikation.
3. **Risiko früh:** Teile mit hohem Risiko für Datenintegrität (Budget, Log, Rückfluss) kommen
   früh, solange die Datenmenge klein ist und Migrationen billig sind.

## Übersicht

| Nr. | Slice | Mehrwert für | FRs | Baut auf |
| --- | --- | --- | --- | --- |
| S1 | **MVP:** Mit Code Prioritäten setzen und Ergebnis sehen | Bürger, Besucher | 20 | – |
| S2 | Wunsch und Haushalt im Detail vergleichen | Besucher, Bürger | 11 | S1 |
| S3 | Nachvollziehbare Punkte: Ereignis-Log, Verfall, Stichtag | Verwaltung | 8 | S1 |
| S4 | Vorschläge einreichen und unterstützen | Bürger | 9 | S1, S2 |
| S5 | Stadt antwortet auf Vorschläge | Verwaltung, Bürger | 7 | S3, S4 |
| S6 | Rückfluss: Erledigtes gibt Punkte frei | Verwaltung, Bürger | 6 | S3, S5 |
| S7 | Hinweise per E-Mail | Bürger | 7 | S3, S6 |
| S8 | Zugänge verwalten und löschen | Bürger, Verwaltung | 3 | S3, S4, S7 |
| S9 | Finden und teilen | Besucher, Bürger | 3 | S2, S4 |
| S10 | Briefdruck und Berichte für den Gemeinderat | Verwaltung | 2 | S3 |
| S11 | Mitwirkung erweitern | Bürger | 4 | S4, S5, S7 |

Summe: 80 FRs. S1 bis S8 enthalten alle Muss-Anforderungen; danach ist StadtStimme reif für
den Pilot (Phase 6). S9 bis S11 erweitern die Anwendung um *Soll*- und *Kann*-Anforderungen.

```
S1 ─► S2 ─► S4 ─► S5 ─► S6 ─► S7 ─► S8
 └──► S3 ────────► S5        S2 + S4 ─► S9
                             S3 ─► S10      S7 ─► S11
```

---

## S1 – MVP: Mit Code Prioritäten setzen und Ergebnis sehen

**Mehrwert:** Eine Bürgerin meldet sich mit dem Code aus dem Brief an, verteilt ihre 100 Punkte
auf Einrichtungen oder ganze Themen und sieht in der öffentlichen Übersicht, wie alle
Teilnehmenden gewichten, im Vergleich zu den Ausgaben der Stadt. Das ist der Kern von
StadtStimme: Interessen sichtbar machen und mit dem Haushalt vergleichen.

**Anforderungen**

| Bereich | FRs |
| --- | --- |
| Zugang | [FR-001](functional-requirements.md#fr-001) Anmeldung mit Code, [FR-002](functional-requirements.md#fr-002) ein Budget je Code, [FR-003](functional-requirements.md#fr-003) Code nur als Hash, [FR-004](functional-requirements.md#fr-004) Sperre nach Fehlversuchen, [FR-005](functional-requirements.md#fr-005) Fehlermeldungen, [FR-006](functional-requirements.md#fr-006) angemeldet bleiben, [FR-009](functional-requirements.md#fr-009) geschützte Funktionen, [FR-011](functional-requirements.md#fr-011) Codes erzeugen |
| Katalog | [FR-014](functional-requirements.md#fr-014) Themen, [FR-015](functional-requirements.md#fr-015) Einrichtungen, [FR-018](functional-requirements.md#fr-018) Ausgaben, [FR-019](functional-requirements.md#fr-019) CSV-Import |
| Punkte | [FR-022](functional-requirements.md#fr-022) Budget 100, [FR-023](functional-requirements.md#fr-023) Einrichtung oder Thema, [FR-024](functional-requirements.md#fr-024) bearbeiten und speichern |
| Übersicht | [FR-036](functional-requirements.md#fr-036) öffentliche Übersicht (Grundfassung: Vergleich je Thema, Teilnehmende, Datenstand), [FR-038](functional-requirements.md#fr-038) letztes abgeschlossenes Haushaltsjahr |
| System | [FR-078](functional-requirements.md#fr-078) Demo-Modus, [FR-079](functional-requirements.md#fr-079) Health-Check, [FR-080](functional-requirements.md#fr-080) Stadtname |

**Technischer Schnitt**

- **Datenbank:** `Category`, `Facility`, `Expenditure`, `AccessCode` (nur Hash), `Participant`,
  `FailedAttempt`, `Allocation` mit Constraints „genau ein Ziel“, „eine Vergabe je Ziel“,
  Punkte ≥ 0.
- **Backend:** Einlöse-Service mit HMAC und atomarem Rate-Limit; Verteil-Service mit
  Budgetprüfung in einer Transaktion mit Zeilensperre; Anteils-Berechnung an einer Stelle;
  Befehle `create_access_codes`, `import_catalog`; Demo-Daten im Entrypoint.
- **Frontend:** Anmeldeseite, „Punkte verteilen“ (Liste je Thema mit Plus/Minus und
  Zahleneingabe, Restbudget, Raster aus 100 Feldern), öffentliche Übersicht mit Balken
  „Wunsch und Haushalt“; App-Schale und Design-Tokens; ohne JavaScript bedienbar.

**Erstmals relevante ARs:** [AR-001](architecture-requirements.md#ar-001) bis
[AR-006](architecture-requirements.md#ar-006), [AR-008](architecture-requirements.md#ar-008),
[AR-009](architecture-requirements.md#ar-009), [AR-010](architecture-requirements.md#ar-010),
[AR-012](architecture-requirements.md#ar-012), [AR-013](architecture-requirements.md#ar-013),
[AR-015](architecture-requirements.md#ar-015) bis [AR-017](architecture-requirements.md#ar-017),
[AR-020](architecture-requirements.md#ar-020), [AR-022](architecture-requirements.md#ar-022),
[AR-027](architecture-requirements.md#ar-027), [AR-028](architecture-requirements.md#ar-028),
[AR-031](architecture-requirements.md#ar-031), [AR-035](architecture-requirements.md#ar-035),
[AR-036](architecture-requirements.md#ar-036).

**Abnahme:** `docker compose up` → Demo-Code einlösen → 60 Punkte an eine Schule, 40 an „Sport
allgemein“ → speichern → Übersicht zeigt Bildung und Sport mit Anteil neben den Ausgaben.
Ein zweiter Login mit demselben Code zeigt dieselbe Verteilung; 101 Punkte werden abgewiesen;
nach 10 falschen Codes ist die Anmeldung gesperrt. 5 Testpersonen schaffen den Ablauf in unter
5 Minuten (Gate Phase 3).

**Warum zuerst:** Ohne diesen Ablauf gibt es kein Beteiligungsverfahren. Alle anderen Slices
erweitern ihn. Budget und Code-Einlösen sind die Stellen mit dem höchsten Integritätsrisiko.

---

## S2 – Wunsch und Haushalt im Detail vergleichen

**Mehrwert:** Besucher sehen nicht nur Themen, sondern je Einrichtung, wo Bürgerwunsch und
Ausgaben auseinanderliegen, auf einer Karte und als Tabelle zum Herunterladen. Bürger finden
Ziele schneller und vergleichen ihre Verteilung mit allen.

**Anforderungen:** [FR-039](functional-requirements.md#fr-039) Lücke je Einrichtung und Thema,
[FR-040](functional-requirements.md#fr-040) Detail je Einrichtung,
[FR-041](functional-requirements.md#fr-041) Belastbarkeit,
[FR-042](functional-requirements.md#fr-042) Ergebnisse als CSV,
[FR-043](functional-requirements.md#fr-043) Karten,
[FR-017](functional-requirements.md#fr-017) Maßnahmen pflegen,
[FR-016](functional-requirements.md#fr-016) Gebäude,
[FR-020](functional-requirements.md#fr-020) CSV-Export des Katalogs,
[FR-025](functional-requirements.md#fr-025) Ziele filtern und auf der Karte finden,
[FR-026](functional-requirements.md#fr-026) eigene Verteilung mit allen vergleichen,
[FR-037](functional-requirements.md#fr-037) eigene Punkte in der Übersicht.

**Technischer Schnitt**

- **Datenbank:** `Measure` (mit Status), `Building`, Koordinaten an `Facility`.
- **Backend:** Lücken-Berechnung je Einrichtung und Thema, CSV-Export mit Schutz gegen
  Formel-Injektion, Kartendaten als JSON im Template.
- **Frontend:** Ergebnisseite mit Listen und Detail, Leaflet-Karte mit Kreisen nach Thema und
  Größe, Kachel-Ersatz, Liste als Alternative; Filter in „Punkte verteilen“.

**Erstmals relevante ARs:** [AR-003](architecture-requirements.md#ar-003) (Kacheln),
[AR-019](architecture-requirements.md#ar-019), [AR-023](architecture-requirements.md#ar-023),
[AR-024](architecture-requirements.md#ar-024), [AR-025](architecture-requirements.md#ar-025).

**Abnahme:** Ergebnisseite zeigt für die Demo-Einrichtungen die Lücke in Prozentpunkten; Klick
auf einen Kreis öffnet das Detail mit Maßnahmen; CSV öffnet sich in einer deutschen
Tabellenkalkulation in Spalten; Karte funktioniert auch, wenn der Kachelserver nicht antwortet.

Gebäude ([FR-016](functional-requirements.md#fr-016)) und der Vergleich der eigenen Verteilung
([FR-026](functional-requirements.md#fr-026)) sind *Kann*, stecken aber hier, weil sie im selben
Schnitt mit geringem Aufwand anfallen.

**Warum hier:** Erfüllt das zweite Produktziel (Vergleich mit den Ausgaben) vollständig und
braucht nur S1. Die Karte ist Grundlage für Vorschläge mit Ort (S4).

---

## S3 – Nachvollziehbare Punkte: Ereignis-Log, Verfall, Stichtag

**Mehrwert:** Die Verwaltung kann dem Gemeinderat einen reproduzierbaren Stand zu einem Stichtag
vorlegen und sieht, wie die Beteiligung läuft. Punkte inaktiver Zugänge verfallen, damit die
Ergebnisse aktuell bleiben.

**Anforderungen:** [FR-032](functional-requirements.md#fr-032) Ereignis-Log,
[FR-034](functional-requirements.md#fr-034) Verfall,
[FR-035](functional-requirements.md#fr-035) tägliche Aufgaben (zunächst nur Verfall),
[FR-010](functional-requirements.md#fr-010) Anmeldung der Verwaltung,
[FR-059](functional-requirements.md#fr-059) Beteiligung beobachten,
[FR-065](functional-requirements.md#fr-065) Zugänge je Charge,
[FR-064](functional-requirements.md#fr-064) Stichtags-Export,
[FR-030](functional-requirements.md#fr-030) Snapshot als Abstimmungszeitpunkt.

**Technischer Schnitt**

- **Datenbank:** `PointEvent` mit Trigger gegen UPDATE/DELETE, Migration bestehender Vergaben
  zu „vergeben“; Snapshot-Tabelle; `last_active_at` am Zugang.
- **Backend:** Jede Punkteänderung schreibt in derselben Transaktion ins Log; Stichtag und
  Snapshot aus dem Log; Befehl `run_daily_tasks` im Dienst `scheduler`; Verwaltungs-Login mit
  Rechten.
- **Frontend:** Verwaltungsseite (eigene Schale) mit Beteiligung je Woche, Chargen,
  Stichtags-Download, Snapshot anlegen, ansehen und vergleichen.

**Erstmals relevante ARs:** [AR-011](architecture-requirements.md#ar-011),
[AR-014](architecture-requirements.md#ar-014), [AR-018](architecture-requirements.md#ar-018),
[AR-026](architecture-requirements.md#ar-026), [AR-030](architecture-requirements.md#ar-030).

**Abnahme:** Verteilung ändern → Ereignisse im Log; Stichtags-CSV für gestern zweimal
herunterladen → identisch; Snapshot anlegen und nach weiterer Abstimmung mit einem zweiten
vergleichen; Zugang mit `last_active_at` vor 184 Tagen → nach dem täglichen Lauf ohne Punkte.

**Warum hier:** Das Log muss stehen, bevor Rückfluss (S6) und Löschen (S8) Punkte entziehen.
Je früher es kommt, desto kleiner ist die Datenmigration.

---

## S4 – Vorschläge einreichen und unterstützen

**Mehrwert:** Bürger bringen eigene Anliegen ein, die noch nicht im Katalog stehen, und zeigen
mit Unterstützungen, wie viele andere das auch wollen.

**Anforderungen:** [FR-044](functional-requirements.md#fr-044) einreichen,
[FR-045](functional-requirements.md#fr-045) Thema und Ort,
[FR-046](functional-requirements.md#fr-046) Tageslimit,
[FR-047](functional-requirements.md#fr-047) ähnliche Einträge,
[FR-048](functional-requirements.md#fr-048) sofort öffentlich,
[FR-049](functional-requirements.md#fr-049) unterstützen,
[FR-050](functional-requirements.md#fr-050) Weg eines Vorschlags,
[FR-055](functional-requirements.md#fr-055) suchen, filtern, sortieren,
[FR-007](functional-requirements.md#fr-007) Mein Bereich (Punktestand und eigene Vorschläge;
E-Mail-Einstellungen folgen in S7).

**Technischer Schnitt**

- **Datenbank:** `Proposal` (Constraint: nie Einrichtung und Punkt zugleich), `Support`
  (einmal je Zugang).
- **Backend:** Einreichen mit Tageslimit, Ähnlichkeitssuche über Wortstämme, Schritt aus
  Unterstützungen abgeleitet, Unterstützen mit Schutz gegen eigene Vorschläge.
- **Frontend:** Seite `/vorschlaege/` mit Formular in drei Schritten, Ortswahl auf der Karte
  (aus S2), Liste mit Filtern und Fortschritt bis zur Schwelle, „Mein Bereich“.

**Erstmals relevante ARs:** [AR-007](architecture-requirements.md#ar-007),
[AR-017](architecture-requirements.md#ar-017) (Tageslimit),
[AR-019](architecture-requirements.md#ar-019) (Bürgertexte sofort öffentlich).

**Abnahme:** Vorschlag mit neuem Ort in drei Schritten einreichen, dabei einmal zurückgehen;
er ist sofort in der Liste; ein zweiter Zugang unterstützt ihn, der Fortschritt steigt; der
sechste Vorschlag am Tag wird abgewiesen; der eigene Vorschlag lässt sich nicht unterstützen.

**Warum hier:** Braucht S1 und die Karte aus S2, liefert Bürgern einen zweiten Weg der
Beteiligung und ist Voraussetzung für S5.

---

## S5 – Stadt antwortet auf Vorschläge

**Mehrwert:** Vorschläge laufen nicht ins Leere: Die Verwaltung sieht, was auf eine Antwort
wartet, entscheidet öffentlich mit Begründung, und angenommene Vorschläge werden in „Punkte
verteilen“ sichtbar oder zu einer neuen Einrichtung.

**Anforderungen:** [FR-057](functional-requirements.md#fr-057) Wartet auf Sie,
[FR-060](functional-requirements.md#fr-060) Vorschläge nach Schritt,
[FR-058](functional-requirements.md#fr-058) entscheiden,
[FR-051](functional-requirements.md#fr-051) öffentliche Antwort,
[FR-052](functional-requirements.md#fr-052) neuer Ort wird Einrichtung,
[FR-028](functional-requirements.md#fr-028) Hinweis auf angenommene Vorschläge,
[FR-066](functional-requirements.md#fr-066) Inhalte moderieren.

**Technischer Schnitt**

- **Datenbank:** Status, Entscheidungsdatum, Antwort und Maßnahme am Vorschlag; Kennzeichen
  „entfernt“ mit Begründung.
- **Backend:** Entscheidungs-Service (einmalig, Antwort ≥ 20 Zeichen, Recht „Vorschlag
  ändern“), Anlegen der Einrichtung aus dem Vorschlag, Antwortfrist ab Schwelle.
- **Frontend:** Verwaltungsseite mit Warteliste und Entscheidungsseite; Antwort am Vorschlag;
  Hinweis in „Punkte verteilen“.

**Erstmals relevante ARs:** [AR-040](architecture-requirements.md#ar-040) (wer hat
entschieden).

**Abnahme:** Vorschlag erreicht die Schwelle → erscheint unter „Wartet auf Sie“ mit Frist →
Annehmen mit Begründung → öffentlich als angenommen mit Antwort; bei neuem Ort ist die neue
Einrichtung in „Punkte verteilen“ wählbar. Ohne Recht ist Entscheiden nicht möglich.

**Warum hier:** Schließt den Kreislauf aus S4. Braucht die Verwaltungsseite aus S3.

---

## S6 – Rückfluss: Erledigtes gibt Punkte frei

**Mehrwert:** Wenn die Stadt etwas umsetzt oder erledigt, bekommen die Unterstützer ihre Punkte
zurück und können sie für das nächste Anliegen einsetzen. Bürger sehen, dass ihre Punkte etwas
bewirkt haben.

**Anforderungen:** [FR-033](functional-requirements.md#fr-033) Rückfluss bei Umsetzung,
[FR-061](functional-requirements.md#fr-061) Einrichtungen nach Lücke,
[FR-062](functional-requirements.md#fr-062) als erledigt markieren,
[FR-063](functional-requirements.md#fr-063) wieder öffnen,
[FR-027](functional-requirements.md#fr-027) erledigte nicht wählbar,
[FR-031](functional-requirements.md#fr-031) Verlauf zurückgekommener und verfallener Punkte.

**Technischer Schnitt**

- **Datenbank:** `done_at` an `Facility`; Ereignis „zurückgegeben“ mit optionaler Maßnahme.
- **Backend:** Rückfluss-Service mit Sperren in fester Reihenfolge, ausgelöst durch
  Maßnahmenstatus (Admin, Import) und „erledigt“; Signal für spätere Benachrichtigung; Abweisen
  alter Formulare.
- **Frontend:** Einrichtungen nach Lücke mit Rückfrage „erledigt“, Wieder öffnen; Verlauf in
  „Punkte verteilen“.

**Abnahme:** Zwei Zugänge geben einer Einrichtung Punkte → Maßnahme auf „in Umsetzung“ → beide
haben die Punkte frei, „Sport allgemein“ bleibt; Einrichtung als erledigt → fehlt in „Punkte
verteilen“, ein altes Formular mit Punkten darauf wird abgewiesen; angenommener Vorschlag an
diesem Ort öffnet sie wieder.

**Warum hier:** Braucht das Log (S3) und für „wieder öffnen“ die Entscheidung über Vorschläge
(S5). Hohes Integritätsrisiko, daher vor den Erweiterungen S9 bis S11.

---

## S7 – Hinweise per E-Mail

**Mehrwert:** Bürger müssen nicht ständig nachsehen: Sie werden erinnert, bevor Punkte
verfallen, wenn Punkte zurückkommen und wenn sich bei ihren Vorschlägen etwas tut.

**Anforderungen:** [FR-070](functional-requirements.md#fr-070) E-Mail hinterlegen,
[FR-071](functional-requirements.md#fr-071) Double-Opt-in,
[FR-072](functional-requirements.md#fr-072) Verfallswarnung,
[FR-073](functional-requirements.md#fr-073) Hinweis bei Rückfluss,
[FR-075](functional-requirements.md#fr-075) Hinweis zu Vorschlägen,
[FR-076](functional-requirements.md#fr-076) Abmelden mit einem Klick,
[FR-077](functional-requirements.md#fr-077) robust bei Mailausfall.

**Technischer Schnitt**

- **Datenbank:** `NotificationContact` getrennt vom Zugang, Adresse verschlüsselt, Tokens als
  Hash, Zeitpunkt der letzten Warnung, gewählte Hinweisarten.
- **Backend:** Bestätigungs- und Abmelde-Flow, Empfänger für die Signale aus S5 und S6,
  Verfallswarnung als erster Schritt in `run_daily_tasks`, Mailpit lokal.
- **Frontend:** Einstellungen in „Mein Bereich“, Bestätigungs- und Abmeldeseite mit Knopf,
  Texte der Mails.

**Erstmals relevante ARs:** [AR-021](architecture-requirements.md#ar-021),
[AR-029](architecture-requirements.md#ar-029).

**Abnahme:** Adresse eintragen → Mail in Mailpit → Link öffnen und bestätigen → Rückfluss aus
S6 auslösen → Hinweis-Mail mit Abmeldelink → Abmelden löscht die Adresse. Mit gestopptem
Mailpit lässt sich eine Maßnahme trotzdem speichern.

**Warum hier:** Benachrichtigt über Ereignisse aus S3, S5 und S6; ohne sie gibt es nichts zu
melden.

---

## S8 – Zugänge verwalten und löschen

**Mehrwert:** Bürger können ihren Zugang selbst löschen (Recht auf Löschung), die Verwaltung
kann Zugänge bei Anfragen finden und bei Wegzug schließen. Voraussetzung für die
Datenschutzfreigabe vor dem Pilot.

**Anforderungen:** [FR-008](functional-requirements.md#fr-008) Zugang selbst löschen,
[FR-068](functional-requirements.md#fr-068) Zugang finden und einsehen,
[FR-069](functional-requirements.md#fr-069) Zugang schließen und wieder öffnen.

**Technischer Schnitt**

- **Datenbank:** Such-Hash der letzten 8 Zeichen am Code, Status „geschlossen“, Log ohne
  Fremdschlüssel-Constraint auf den Zugang.
- **Backend:** Lösch- und Schließ-Service (Punkte als „entzogen“ ins Log, E-Mail löschen,
  Sitzungen sofort ungültig), Recht für die Verwaltung.
- **Frontend:** Rückfrage in „Mein Bereich“, Suche und Detail eines Zugangs auf der
  Verwaltungsseite ohne Punkteverteilung.

**Abnahme:** Zugang löschen → Übersicht zählt seine Punkte nicht mehr, Log bleibt pseudonym,
Code lässt sich nicht erneut einlösen; Verwaltung findet einen Zugang über 8 Zeichen, schließt
ihn → die offene Sitzung auf einem anderen Gerät ist sofort abgemeldet.

**Warum hier:** Löschen muss Log (S3), Vorschläge (S4) und E-Mail (S7) berücksichtigen, also
erst nach ihnen. Es ist Muss für den Pilot und kommt deshalb vor den Erweiterungen S9 bis S11.

---

## S9 – Finden und teilen

**Mehrwert:** Besucher finden Einrichtungen und Vorschläge direkt und können sie weitergeben;
die Stadt wirbt vor Ort mit QR-Codes für einzelne Ziele.

**Anforderungen:** [FR-021](functional-requirements.md#fr-021) öffentliche Suche,
[FR-056](functional-requirements.md#fr-056) Vorschlag teilen,
[FR-029](functional-requirements.md#fr-029) Ziele per QR-Code.

**Technischer Schnitt**

- **Datenbank:** keine neuen Tabellen; dauerhafte URL je Vorschlag.
- **Backend:** Suche über Einrichtungen und Maßnahmen, Detailseite je Vorschlag, QR-Erzeugung
  ohne Zugangscode.
- **Frontend:** Suchleiste in der Kopfzeile mit Tastenkürzel „/“, Suchergebnisseite,
  Teilen-Knopf, QR-Download auf der Verwaltungsseite.

**Abnahme:** Suche nach „Schwimm“ findet das Hallenbad und seine Maßnahmen; ein geteilter
Vorschlagslink öffnet ohne Anmeldung genau diesen Vorschlag; der QR-Code eines Themas führt in
„Punkte verteilen“ mit diesem Thema.

---

## S10 – Briefdruck und Berichte für den Gemeinderat

**Mehrwert:** Die Verwaltung bringt die Codes ohne Umweg über die Kommandozeile in den
Briefdruck und legt dem Gemeinderat aufbereitete Berichte statt roher CSV-Dateien vor.

**Anforderungen:** [FR-012](functional-requirements.md#fr-012) Codes für den Briefdruck exportieren,
[FR-067](functional-requirements.md#fr-067) Berichte auf der Verwaltungsseite.

**Technischer Schnitt**

- **Datenbank:** Druckauftrag je Charge (wann, von wem, wie viele Codes), damit kein Code
  zweimal ausgegeben wird; Berichte verweisen auf Snapshots aus S3.
- **Backend:** Export einer Charge als Druckdatei (Klartext nur in diesem Moment, danach nicht
  mehr abrufbar, [AR-015](architecture-requirements.md#ar-015)); Bericht aus einem Snapshot oder
  dem Vergleich zweier Snapshots für einen gewählten Zeitraum.
- **Frontend:** Bereich „Zugänge“ auf der Verwaltungsseite mit Druckexport je Charge;
  Berichtsseite mit Zeitraum, Druckansicht und Download.

**Erstmals relevante ARs:** [AR-040](architecture-requirements.md#ar-040) (Druckexport und
Bericht sind protokollierte Verwaltungsaktionen).

**Abnahme:** Neue Charge mit 20 Codes erzeugen → als Druckdatei exportieren → ein zweiter
Export derselben Charge ist nicht möglich; Bericht aus den Snapshots zweier Gemeinderatstermine
zeigt die Veränderung je Thema und lässt sich drucken.

**Warum hier:** Beides baut auf S3 (Chargen, Snapshots) auf und ist *Kann*. Der Briefversand
funktioniert bis dahin über den Befehl aus S1, Gemeinderatsvorlagen über Stichtag und Snapshot.

---

## S11 – Mitwirkung erweitern

**Mehrwert:** Bürger beteiligen sich persönlicher und anschaulicher: mit einem Spitznamen bei
ihren Vorschlägen, mit einem Foto vom Ort, mit einer Meldung, wenn etwas Unpassendes
öffentlich steht, und mit einer Erinnerung, wenn noch Punkte frei sind.

**Anforderungen:** [FR-013](functional-requirements.md#fr-013) Spitzname, [FR-054](functional-requirements.md#fr-054) Foto zum Vorschlag,
[FR-053](functional-requirements.md#fr-053) Vorschläge melden, [FR-074](functional-requirements.md#fr-074) Erinnerung an freie Punkte.

**Technischer Schnitt**

- **Datenbank:** Spitzname am Zugang; Foto am Vorschlag (Datei außerhalb der Datenbank, Größe
  und Typ begrenzt); Meldung je Vorschlag und Zugang (einmal); Zeitpunkt der letzten
  Erinnerung am Kontakt.
- **Backend:** Prüfung des Spitznamens (Länge, keine Links); Foto-Upload mit Entfernen der
  Metadaten (Standort); Meldungen landen auf der Verwaltungsseite bei „Inhalte moderieren“
  aus S5; Erinnerung als weiterer Schritt in `run_daily_tasks`.
- **Frontend:** Spitzname in „Mein Bereich“ mit Hinweis, keinen echten Namen zu verwenden;
  Foto im Schritt „Anliegen“; Knopf „Melden“ am Vorschlag; neue Hinweisart in den
  E-Mail-Einstellungen.

**Erstmals relevante ARs:** [AR-020](architecture-requirements.md#ar-020) und
[AR-023](architecture-requirements.md#ar-023) (neue personenbezogene Daten: Spitzname, Foto),
[AR-017](architecture-requirements.md#ar-017) (Limit für Uploads und Meldungen).

**Abnahme:** Spitzname setzen → erscheint bei den eigenen Vorschlägen; Vorschlag mit Foto
einreichen → Foto ohne Standortdaten sichtbar; zwei Meldungen zum selben Vorschlag →
Verwaltungsseite zeigt ihn mit Zahl der Meldungen; Zugang mit freien Punkten und bestätigter
E-Mail → Erinnerung nach dem eingestellten Abstand, abbestellbar.

**Warum zuletzt:** Alle vier sind *Kann* und bauen auf Vorschlägen (S4), Moderation (S5) und
E-Mail (S7) auf. Spitzname und Foto bringen neue personenbezogene Daten und Moderationsaufwand
und kommen deshalb erst, wenn der Kern im Pilot läuft.

---

## Zuordnung FR → Slice

| FR | Slice | FR | Slice | FR | Slice | FR | Slice |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [FR-001](functional-requirements.md#fr-001) | S1 | [FR-021](functional-requirements.md#fr-021) | S9 | [FR-041](functional-requirements.md#fr-041) | S2 | [FR-061](functional-requirements.md#fr-061) | S6 |
| [FR-002](functional-requirements.md#fr-002) | S1 | [FR-022](functional-requirements.md#fr-022) | S1 | [FR-042](functional-requirements.md#fr-042) | S2 | [FR-062](functional-requirements.md#fr-062) | S6 |
| [FR-003](functional-requirements.md#fr-003) | S1 | [FR-023](functional-requirements.md#fr-023) | S1 | [FR-043](functional-requirements.md#fr-043) | S2 | [FR-063](functional-requirements.md#fr-063) | S6 |
| [FR-004](functional-requirements.md#fr-004) | S1 | [FR-024](functional-requirements.md#fr-024) | S1 | [FR-044](functional-requirements.md#fr-044) | S4 | [FR-064](functional-requirements.md#fr-064) | S3 |
| [FR-005](functional-requirements.md#fr-005) | S1 | [FR-025](functional-requirements.md#fr-025) | S2 | [FR-045](functional-requirements.md#fr-045) | S4 | [FR-065](functional-requirements.md#fr-065) | S3 |
| [FR-006](functional-requirements.md#fr-006) | S1 | [FR-026](functional-requirements.md#fr-026) | S2 | [FR-046](functional-requirements.md#fr-046) | S4 | [FR-066](functional-requirements.md#fr-066) | S5 |
| [FR-007](functional-requirements.md#fr-007) | S4 | [FR-027](functional-requirements.md#fr-027) | S6 | [FR-047](functional-requirements.md#fr-047) | S4 | [FR-067](functional-requirements.md#fr-067) | S10 |
| [FR-008](functional-requirements.md#fr-008) | S8 | [FR-028](functional-requirements.md#fr-028) | S5 | [FR-048](functional-requirements.md#fr-048) | S4 | [FR-068](functional-requirements.md#fr-068) | S8 |
| [FR-009](functional-requirements.md#fr-009) | S1 | [FR-029](functional-requirements.md#fr-029) | S9 | [FR-049](functional-requirements.md#fr-049) | S4 | [FR-069](functional-requirements.md#fr-069) | S8 |
| [FR-010](functional-requirements.md#fr-010) | S3 | [FR-030](functional-requirements.md#fr-030) | S3 | [FR-050](functional-requirements.md#fr-050) | S4 | [FR-070](functional-requirements.md#fr-070) | S7 |
| [FR-011](functional-requirements.md#fr-011) | S1 | [FR-031](functional-requirements.md#fr-031) | S6 | [FR-051](functional-requirements.md#fr-051) | S5 | [FR-071](functional-requirements.md#fr-071) | S7 |
| [FR-012](functional-requirements.md#fr-012) | S10 | [FR-032](functional-requirements.md#fr-032) | S3 | [FR-052](functional-requirements.md#fr-052) | S5 | [FR-072](functional-requirements.md#fr-072) | S7 |
| [FR-013](functional-requirements.md#fr-013) | S11 | [FR-033](functional-requirements.md#fr-033) | S6 | [FR-053](functional-requirements.md#fr-053) | S11 | [FR-073](functional-requirements.md#fr-073) | S7 |
| [FR-014](functional-requirements.md#fr-014) | S1 | [FR-034](functional-requirements.md#fr-034) | S3 | [FR-054](functional-requirements.md#fr-054) | S11 | [FR-074](functional-requirements.md#fr-074) | S11 |
| [FR-015](functional-requirements.md#fr-015) | S1 | [FR-035](functional-requirements.md#fr-035) | S3 | [FR-055](functional-requirements.md#fr-055) | S4 | [FR-075](functional-requirements.md#fr-075) | S7 |
| [FR-016](functional-requirements.md#fr-016) | S2 | [FR-036](functional-requirements.md#fr-036) | S1 | [FR-056](functional-requirements.md#fr-056) | S9 | [FR-076](functional-requirements.md#fr-076) | S7 |
| [FR-017](functional-requirements.md#fr-017) | S2 | [FR-037](functional-requirements.md#fr-037) | S2 | [FR-057](functional-requirements.md#fr-057) | S5 | [FR-077](functional-requirements.md#fr-077) | S7 |
| [FR-018](functional-requirements.md#fr-018) | S1 | [FR-038](functional-requirements.md#fr-038) | S1 | [FR-058](functional-requirements.md#fr-058) | S5 | [FR-078](functional-requirements.md#fr-078) | S1 |
| [FR-019](functional-requirements.md#fr-019) | S1 | [FR-039](functional-requirements.md#fr-039) | S2 | [FR-059](functional-requirements.md#fr-059) | S3 | [FR-079](functional-requirements.md#fr-079) | S1 |
| [FR-020](functional-requirements.md#fr-020) | S2 | [FR-040](functional-requirements.md#fr-040) | S2 | [FR-060](functional-requirements.md#fr-060) | S5 | [FR-080](functional-requirements.md#fr-080) | S1 |
