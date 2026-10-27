# Demo-Daten: Musterstadt

Alle Daten sind **fiktiv**. Sie dienen der Entwicklung, den Tests und der Vorführung.

| Datei | Inhalt |
| --- | --- |
| `facilities.csv` | 8 Einrichtungen (Hallenbad, Kita, Schule, Bibliothek, Bahnhof, ...) |
| `measures.csv` | 12 Maßnahmen, je genau einer Einrichtung zugeordnet (ADR-002) |
| `expenditures.csv` | Ausgaben pro Einrichtung, optional pro Maßnahme, mit Quelle und Stand (ADR-006) |

Format: UTF-8, Komma als Trennzeichen, Punkt als Dezimaltrennzeichen. Die Verknüpfung läuft
über die `external_id`, damit ein Import wiederholbar ist.

Status einer Maßnahme: `offen`, `beschlossen`, `in Umsetzung`, `abgeschlossen`, `verworfen`.

Das Format ist vorläufig. Den Import und die Datenmodelle baut Phase 1; dort wird das Format
an die Exporte echter Fachverfahren angepasst.
