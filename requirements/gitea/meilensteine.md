# Meilensteine – StadtStimme

Je Vertical Slice ein Meilenstein zum Kopieren nach Gitea (Neuer Meilenstein → Titel, Beschreibung).
Titel höchstens 50 Zeichen. Die Beschreibung ist Markdown. Die Anforderungen selbst stehen als Issues in [`issues.md`](issues.md) und werden dem Meilenstein zugeordnet. Fälligkeitsdatum bitte selbst setzen. Quelle: [`requirements/vertical-slices.md`](../vertical-slices.md).

---

## S1 – MVP: Prioritäten setzen und Ergebnis sehen

**Titel**

```text
S1 – MVP: Prioritäten setzen und Ergebnis sehen
```

**Beschreibung**

```markdown
**Mehrwert:** Eine Bürgerin meldet sich mit dem Code aus dem Brief an, verteilt ihre 100 Punkte auf Einrichtungen oder ganze Themen und sieht in der öffentlichen Übersicht, wie alle Teilnehmenden gewichten, im Vergleich zu den Ausgaben der Stadt. Das ist der Kern von StadtStimme: Interessen sichtbar machen und mit dem Haushalt vergleichen.

**Baut auf:** –

**Abnahme:** `docker compose up` → Demo-Code einlösen → 60 Punkte an eine Schule, 40 an „Sport allgemein“ → speichern → Übersicht zeigt Bildung und Sport mit Anteil neben den Ausgaben. Ein zweiter Login mit demselben Code zeigt dieselbe Verteilung; 101 Punkte werden abgewiesen; nach 10 falschen Codes ist die Anmeldung gesperrt. 5 Testpersonen schaffen den Ablauf in unter 5 Minuten (Gate Phase 3).

**Fertig, wenn:** alle Issues des Meilensteins geschlossen und die Abnahme im Browser erfüllt; Tests, Ruff, Mypy und CI grün; README und DECISIONS.md aktuell.
```

---

## S2 – Wunsch und Haushalt im Detail vergleichen

**Titel**

```text
S2 – Wunsch und Haushalt im Detail vergleichen
```

**Beschreibung**

```markdown
**Mehrwert:** Besucher sehen nicht nur Themen, sondern je Einrichtung, wo Bürgerwunsch und Ausgaben auseinanderliegen, auf einer Karte und als Tabelle zum Herunterladen. Bürger finden Ziele schneller und vergleichen ihre Verteilung mit allen.

**Baut auf:** S1

**Abnahme:** Ergebnisseite zeigt für die Demo-Einrichtungen die Lücke in Prozentpunkten; Klick auf einen Kreis öffnet das Detail mit Maßnahmen; CSV öffnet sich in einer deutschen Tabellenkalkulation in Spalten; Karte funktioniert auch, wenn der Kachelserver nicht antwortet.

**Fertig, wenn:** alle Issues des Meilensteins geschlossen und die Abnahme im Browser erfüllt; Tests, Ruff, Mypy und CI grün; README und DECISIONS.md aktuell.
```

---

## S3 – Ereignis-Log, Verfall und Stichtag

**Titel**

```text
S3 – Ereignis-Log, Verfall und Stichtag
```

**Beschreibung**

```markdown
**Mehrwert:** Die Verwaltung kann dem Gemeinderat einen reproduzierbaren Stand zu einem Stichtag vorlegen und sieht, wie die Beteiligung läuft. Punkte inaktiver Zugänge verfallen, damit die Ergebnisse aktuell bleiben.

**Baut auf:** S1

**Abnahme:** Verteilung ändern → Ereignisse im Log; Stichtags-CSV für gestern zweimal herunterladen → identisch; Snapshot anlegen und nach weiterer Abstimmung mit einem zweiten vergleichen; Zugang mit `last_active_at` vor 184 Tagen → nach dem täglichen Lauf ohne Punkte.

**Fertig, wenn:** alle Issues des Meilensteins geschlossen und die Abnahme im Browser erfüllt; Tests, Ruff, Mypy und CI grün; README und DECISIONS.md aktuell.
```

---

## S4 – Vorschläge einreichen und unterstützen

**Titel**

```text
S4 – Vorschläge einreichen und unterstützen
```

**Beschreibung**

```markdown
**Mehrwert:** Bürger bringen eigene Anliegen ein, die noch nicht im Katalog stehen, und zeigen mit Unterstützungen, wie viele andere das auch wollen.

**Baut auf:** S1, S2

**Abnahme:** Vorschlag mit neuem Ort in drei Schritten einreichen, dabei einmal zurückgehen; er ist sofort in der Liste; ein zweiter Zugang unterstützt ihn, der Fortschritt steigt; der sechste Vorschlag am Tag wird abgewiesen; der eigene Vorschlag lässt sich nicht unterstützen.

**Fertig, wenn:** alle Issues des Meilensteins geschlossen und die Abnahme im Browser erfüllt; Tests, Ruff, Mypy und CI grün; README und DECISIONS.md aktuell.
```

---

## S5 – Stadt antwortet auf Vorschläge

**Titel**

```text
S5 – Stadt antwortet auf Vorschläge
```

**Beschreibung**

```markdown
**Mehrwert:** Vorschläge laufen nicht ins Leere: Die Verwaltung sieht, was auf eine Antwort wartet, entscheidet öffentlich mit Begründung, und angenommene Vorschläge werden in „Punkte verteilen“ sichtbar oder zu einer neuen Einrichtung.

**Baut auf:** S3, S4

**Abnahme:** Vorschlag erreicht die Schwelle → erscheint unter „Wartet auf Sie“ mit Frist → Annehmen mit Begründung → öffentlich als angenommen mit Antwort; bei neuem Ort ist die neue Einrichtung in „Punkte verteilen“ wählbar. Ohne Recht ist Entscheiden nicht möglich.

**Fertig, wenn:** alle Issues des Meilensteins geschlossen und die Abnahme im Browser erfüllt; Tests, Ruff, Mypy und CI grün; README und DECISIONS.md aktuell.
```

---

## S6 – Rückfluss: Erledigtes gibt Punkte frei

**Titel**

```text
S6 – Rückfluss: Erledigtes gibt Punkte frei
```

**Beschreibung**

```markdown
**Mehrwert:** Wenn die Stadt etwas umsetzt oder erledigt, bekommen die Unterstützer ihre Punkte zurück und können sie für das nächste Anliegen einsetzen. Bürger sehen, dass ihre Punkte etwas bewirkt haben.

**Baut auf:** S3, S5

**Abnahme:** Zwei Zugänge geben einer Einrichtung Punkte → Maßnahme auf „in Umsetzung“ → beide haben die Punkte frei, „Sport allgemein“ bleibt; Einrichtung als erledigt → fehlt in „Punkte verteilen“, ein altes Formular mit Punkten darauf wird abgewiesen; angenommener Vorschlag an diesem Ort öffnet sie wieder.

**Fertig, wenn:** alle Issues des Meilensteins geschlossen und die Abnahme im Browser erfüllt; Tests, Ruff, Mypy und CI grün; README und DECISIONS.md aktuell.
```

---

## S7 – Hinweise per E-Mail

**Titel**

```text
S7 – Hinweise per E-Mail
```

**Beschreibung**

```markdown
**Mehrwert:** Bürger müssen nicht ständig nachsehen: Sie werden erinnert, bevor Punkte verfallen, wenn Punkte zurückkommen und wenn sich bei ihren Vorschlägen etwas tut.

**Baut auf:** S3, S6

**Abnahme:** Adresse eintragen → Mail in Mailpit → Link öffnen und bestätigen → Rückfluss aus S6 auslösen → Hinweis-Mail mit Abmeldelink → Abmelden löscht die Adresse. Mit gestopptem Mailpit lässt sich eine Maßnahme trotzdem speichern.

**Fertig, wenn:** alle Issues des Meilensteins geschlossen und die Abnahme im Browser erfüllt; Tests, Ruff, Mypy und CI grün; README und DECISIONS.md aktuell.
```

---

## S8 – Zugänge verwalten und löschen

**Titel**

```text
S8 – Zugänge verwalten und löschen
```

**Beschreibung**

```markdown
**Mehrwert:** Bürger können ihren Zugang selbst löschen (Recht auf Löschung), die Verwaltung kann Zugänge bei Anfragen finden und bei Wegzug schließen. Voraussetzung für die Datenschutzfreigabe vor dem Pilot.

**Baut auf:** S3, S4, S7

**Abnahme:** Zugang löschen → Übersicht zählt seine Punkte nicht mehr, Log bleibt pseudonym, Code lässt sich nicht erneut einlösen; Verwaltung findet einen Zugang über 8 Zeichen, schließt ihn → die offene Sitzung auf einem anderen Gerät ist sofort abgemeldet.

**Fertig, wenn:** alle Issues des Meilensteins geschlossen und die Abnahme im Browser erfüllt; Tests, Ruff, Mypy und CI grün; README und DECISIONS.md aktuell.
```

---

## S9 – Finden und teilen

**Titel**

```text
S9 – Finden und teilen
```

**Beschreibung**

```markdown
**Mehrwert:** Besucher finden Einrichtungen und Vorschläge direkt und können sie weitergeben; die Stadt wirbt vor Ort mit QR-Codes für einzelne Ziele.

**Baut auf:** S2, S4

**Abnahme:** Suche nach „Schwimm“ findet das Hallenbad und seine Maßnahmen; ein geteilter Vorschlagslink öffnet ohne Anmeldung genau diesen Vorschlag; der QR-Code eines Themas führt in „Punkte verteilen“ mit diesem Thema.

**Fertig, wenn:** alle Issues des Meilensteins geschlossen und die Abnahme im Browser erfüllt; Tests, Ruff, Mypy und CI grün; README und DECISIONS.md aktuell.
```

---

## S10 – Briefdruck und Gemeinderatsberichte

**Titel**

```text
S10 – Briefdruck und Gemeinderatsberichte
```

**Beschreibung**

```markdown
**Mehrwert:** Die Verwaltung bringt die Codes ohne Umweg über die Kommandozeile in den Briefdruck und legt dem Gemeinderat aufbereitete Berichte statt roher CSV-Dateien vor.

**Baut auf:** S3

**Abnahme:** Neue Charge mit 20 Codes erzeugen → als Druckdatei exportieren → ein zweiter Export derselben Charge ist nicht möglich; Bericht aus den Snapshots zweier Gemeinderatstermine zeigt die Veränderung je Thema und lässt sich drucken.

**Fertig, wenn:** alle Issues des Meilensteins geschlossen und die Abnahme im Browser erfüllt; Tests, Ruff, Mypy und CI grün; README und DECISIONS.md aktuell.
```

---

## S11 – Mitwirkung erweitern

**Titel**

```text
S11 – Mitwirkung erweitern
```

**Beschreibung**

```markdown
**Mehrwert:** Bürger beteiligen sich persönlicher und anschaulicher: mit einem Spitznamen bei ihren Vorschlägen, mit einem Foto vom Ort, mit einer Meldung, wenn etwas Unpassendes öffentlich steht, und mit einer Erinnerung, wenn noch Punkte frei sind.

**Baut auf:** S4, S5, S7

**Abnahme:** Spitzname setzen → erscheint bei den eigenen Vorschlägen; Vorschlag mit Foto einreichen → Foto ohne Standortdaten sichtbar; zwei Meldungen zum selben Vorschlag → Verwaltungsseite zeigt ihn mit Zahl der Meldungen; Zugang mit freien Punkten und bestätigter E-Mail → Erinnerung nach dem eingestellten Abstand, abbestellbar.

**Fertig, wenn:** alle Issues des Meilensteins geschlossen und die Abnahme im Browser erfüllt; Tests, Ruff, Mypy und CI grün; README und DECISIONS.md aktuell.
```
