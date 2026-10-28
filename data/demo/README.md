# Demo-Daten: Musterstadt

Alle Daten sind **fiktiv**. Sie dienen der Entwicklung, den Tests und der Vorführung. Die Koordinaten
liegen beispielhaft in einer echten Kleinstadt, damit die Karte etwas zeigt; sie gehören zu keiner
realen Einrichtung.

| Datei | Inhalt |
| --- | --- |
| `facilities.csv` | 8 Einrichtungen in 5 Kategorien |
| `buildings.csv` | 5 Gebäude an 3 Einrichtungen; Einrichtungen mit nur einem Gebäude brauchen keinen Eintrag |
| `measures.csv` | 12 Maßnahmen, je genau einer Einrichtung zugeordnet (ADR-002), optional einem Gebäude |
| `expenditures.csv` | Ausgaben pro Einrichtung, optional pro Maßnahme, mit Quelle und Stand (ADR-006) |

## Spalten

| Datei | Spalte | Pflicht | Inhalt |
| --- | --- | --- | --- |
| facilities.csv | `external_id` | ja | Eindeutiger Schlüssel der Einrichtung |
| | `name` | ja | Name |
| | `category` | ja | Kategoriename; unbekannte Kategorien werden angelegt |
| | `address`, `description` | nein | Adresse, Kurzbeschreibung |
| | `latitude`, `longitude` | nein | Koordinaten (WGS 84, Punkt als Dezimaltrenner) für die Karte; nur zusammen |
| buildings.csv | `external_id` | ja | Eindeutiger Schlüssel des Gebäudes |
| | `facility_external_id` | ja | Einrichtung, zu der das Gebäude gehört |
| | `name` | ja | Name, z. B. „Turnhalle“ |
| | `address`, `description` | nein | Adresse, Kurzbeschreibung |
| measures.csv | `external_id` | ja | Eindeutiger Schlüssel der Maßnahme |
| | `facility_external_id` | ja | Einrichtung, zu der die Maßnahme gehört |
| | `building_external_id` | nein | Gebäude; muss zur Einrichtung gehören |
| | `title` | ja | Titel |
| | `description` | nein | Beschreibung |
| | `status` | ja | `offen`, `beschlossen`, `in Umsetzung`, `abgeschlossen`, `verworfen` |
| expenditures.csv | `facility_external_id` | ja | Einrichtung |
| | `measure_external_id` | nein | Maßnahme; muss zur Einrichtung gehören |
| | `fiscal_year` | ja | Haushaltsjahr (2000 bis 2100) |
| | `amount_eur` | ja | Betrag in Euro, nicht negativ |
| | `kind` | ja | `Plan` oder `Ist` |
| | `source`, `as_of` | ja | Quelle und Datenstand (`JJJJ-MM-TT`) |

Eine Ausgabe ist eindeutig durch Einrichtung, Maßnahme, Haushaltsjahr und Art.

Format: UTF-8, Komma als Trennzeichen, Punkt als Dezimaltrennzeichen. Die Verknüpfung läuft
über die `external_id`, damit ein Import wiederholbar ist.

Das Format ist vorläufig, bis es mit Exporten echter Fachverfahren abgeglichen ist.
