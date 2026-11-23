# Issues je Vertical Slice – StadtStimme

Welche Issues zu welchem Meilenstein (Vertical Slice) gehören. Details je Issue: [issues.md](issues.md), Meilensteine: [meilensteine.md](meilensteine.md), Slices: [../vertical-slices.md](../vertical-slices.md).

| Slice | Issues | Muss | Soll | Kann |
| --- | --- | --- | --- | --- |
| S1 – MVP: Prioritäten setzen und Ergebnis sehen | 20 | 18 | 2 | 0 |
| S2 – Wunsch und Haushalt im Detail vergleichen | 11 | 2 | 7 | 2 |
| S3 – Ereignis-Log, Verfall und Stichtag | 8 | 6 | 2 | 0 |
| S4 – Vorschläge einreichen und unterstützen | 9 | 6 | 3 | 0 |
| S5 – Stadt antwortet auf Vorschläge | 7 | 5 | 2 | 0 |
| S6 – Rückfluss: Erledigtes gibt Punkte frei | 6 | 4 | 2 | 0 |
| S7 – Hinweise per E-Mail | 7 | 0 | 7 | 0 |
| S8 – Zugänge verwalten und löschen | 3 | 1 | 2 | 0 |
| S9 – Finden und teilen | 3 | 0 | 1 | 2 |
| S10 – Briefdruck und Gemeinderatsberichte | 2 | 0 | 0 | 2 |
| S11 – Mitwirkung erweitern | 4 | 0 | 0 | 4 |
| **Summe** | **80** | | | |

## S1 – MVP: Prioritäten setzen und Ergebnis sehen

| Issue | Priorität | Rolle |
| --- | --- | --- |
| FR-001: Anmeldung mit Aktivierungscode | Muss | Bürger |
| FR-002: Ein Budget je Code | Muss | System |
| FR-003: Code nur als Hash speichern | Muss | System |
| FR-004: Sperre nach Fehlversuchen | Muss | System |
| FR-005: Verständliche Fehlermeldungen beim Einlösen | Muss | Bürger |
| FR-006: Angemeldet bleiben und Abmelden | Muss | Bürger |
| FR-009: Geschützte Bürgerfunktionen | Muss | System |
| FR-011: Aktivierungscodes erzeugen | Muss | Verwaltung |
| FR-014: Themen pflegen | Muss | Verwaltung |
| FR-015: Einrichtungen pflegen | Muss | Verwaltung |
| FR-018: Ausgaben pflegen | Muss | Verwaltung |
| FR-019: CSV-Import mit Vorschau | Muss | Verwaltung |
| FR-022: Budget von 100 Punkten | Muss | System |
| FR-023: Punkte an Einrichtung oder ganzes Thema | Muss | Bürger |
| FR-024: Verteilung bearbeiten und speichern | Muss | Bürger |
| FR-036: Öffentliche Übersicht | Muss | Besucher |
| FR-038: Vergleich mit dem letzten abgeschlossenen Haushaltsjahr | Muss | System |
| FR-078: Demo-Modus | Muss | System |
| FR-079: Health-Check | Soll | System |
| FR-080: Stadtname konfigurierbar | Soll | System |

## S2 – Wunsch und Haushalt im Detail vergleichen

| Issue | Priorität | Rolle |
| --- | --- | --- |
| FR-016: Gebäude als optionale Ebene | Kann | Verwaltung |
| FR-017: Maßnahmen pflegen | Muss | Verwaltung |
| FR-020: CSV-Export des Katalogs | Soll | Verwaltung |
| FR-025: Ziele filtern und auf der Karte finden | Soll | Bürger |
| FR-026: Eigene Verteilung mit dem Gesamtbild vergleichen | Kann | Bürger |
| FR-037: Eigene Punkte in der Übersicht | Soll | Bürger |
| FR-039: Lücke je Einrichtung und je Thema | Muss | Besucher |
| FR-040: Detail je Einrichtung | Soll | Besucher |
| FR-041: Einordnung der Belastbarkeit | Soll | Besucher |
| FR-042: Ergebnisse als CSV | Soll | Besucher |
| FR-043: Karten der Einrichtungen | Soll | Besucher |

## S3 – Ereignis-Log, Verfall und Stichtag

| Issue | Priorität | Rolle |
| --- | --- | --- |
| FR-010: Anmeldung der Verwaltung | Muss | Verwaltung |
| FR-030: Snapshot als Abstimmungszeitpunkt | Soll | Verwaltung |
| FR-032: Unveränderliches Ereignis-Log | Muss | System |
| FR-034: Verfall nach Inaktivität | Muss | System |
| FR-035: Tägliche Aufgaben | Muss | System |
| FR-059: Beteiligung beobachten | Muss | Verwaltung |
| FR-064: Stichtags-Export | Muss | Verwaltung |
| FR-065: Zugänge je Charge | Soll | Verwaltung |

## S4 – Vorschläge einreichen und unterstützen

| Issue | Priorität | Rolle |
| --- | --- | --- |
| FR-007: Mein Bereich | Soll | Bürger |
| FR-044: Vorschlag einreichen | Muss | Bürger |
| FR-045: Thema und Ort eines Vorschlags | Muss | Bürger |
| FR-046: Tageslimit für Vorschläge | Muss | System |
| FR-047: Ähnliche Einträge vorschlagen | Soll | Bürger |
| FR-048: Vorschläge sofort öffentlich | Muss | System |
| FR-049: Vorschlag unterstützen | Muss | Bürger |
| FR-050: Weg eines Vorschlags | Muss | Besucher |
| FR-055: Vorschlagsliste durchsuchen, filtern und sortieren | Soll | Besucher |

## S5 – Stadt antwortet auf Vorschläge

| Issue | Priorität | Rolle |
| --- | --- | --- |
| FR-028: Hinweis auf angenommene Vorschläge | Soll | Bürger |
| FR-051: Öffentliche Antwort der Stadt | Muss | Besucher |
| FR-052: Neuer Ort wird Einrichtung | Soll | System |
| FR-057: Wartet auf Sie | Muss | Verwaltung |
| FR-058: Vorschlag entscheiden | Muss | Verwaltung |
| FR-060: Vorschläge nach Schritt | Muss | Verwaltung |
| FR-066: Inhalte moderieren | Muss | Verwaltung |

## S6 – Rückfluss: Erledigtes gibt Punkte frei

| Issue | Priorität | Rolle |
| --- | --- | --- |
| FR-027: Erledigte Einrichtungen nicht wählbar | Muss | System |
| FR-031: Verlauf zurückgekommener und verfallener Punkte | Soll | Bürger |
| FR-033: Rückfluss bei Umsetzung einer Maßnahme | Muss | System |
| FR-061: Einrichtungen nach Lücke | Soll | Verwaltung |
| FR-062: Einrichtung als erledigt markieren | Muss | Verwaltung |
| FR-063: Einrichtung wieder öffnen | Muss | Verwaltung |

## S7 – Hinweise per E-Mail

| Issue | Priorität | Rolle |
| --- | --- | --- |
| FR-070: E-Mail freiwillig hinterlegen | Soll | Bürger |
| FR-071: Double-Opt-in | Soll | System |
| FR-072: Verfallswarnung | Soll | System |
| FR-073: Hinweis bei Rückfluss | Soll | System |
| FR-075: Hinweis zu eigenen und unterstützten Vorschlägen | Soll | System |
| FR-076: Abmelden mit einem Klick | Soll | Bürger |
| FR-077: Robust bei Mailausfall | Soll | System |

## S8 – Zugänge verwalten und löschen

| Issue | Priorität | Rolle |
| --- | --- | --- |
| FR-008: Zugang selbst löschen | Muss | Bürger |
| FR-068: Zugang finden und einsehen | Soll | Verwaltung |
| FR-069: Zugang schließen und wieder öffnen | Soll | Verwaltung |

## S9 – Finden und teilen

| Issue | Priorität | Rolle |
| --- | --- | --- |
| FR-021: Öffentliche Suche | Soll | Besucher |
| FR-029: Ziele per QR-Code verlinken | Kann | Verwaltung |
| FR-056: Vorschlag teilen | Kann | Bürger |

## S10 – Briefdruck und Gemeinderatsberichte

| Issue | Priorität | Rolle |
| --- | --- | --- |
| FR-012: Codes für den Briefdruck exportieren | Kann | Verwaltung |
| FR-067: Berichte auf der Verwaltungsseite | Kann | Verwaltung |

## S11 – Mitwirkung erweitern

| Issue | Priorität | Rolle |
| --- | --- | --- |
| FR-013: Spitzname | Kann | Bürger |
| FR-053: Vorschläge melden | Kann | Bürger |
| FR-054: Foto zum Vorschlag | Kann | Bürger |
| FR-074: Erinnerung an freie Punkte | Kann | System |
