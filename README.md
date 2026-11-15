# Routes and Roots

Interactive map of inter-island ferry routes in the Lesser Antilles, and of the five regional
networks they draw: Virgin Islands, Northern English-speaking, Creole-speaking, Southern
English-speaking, and the isolated pair Trinidad and Tobago / Barbados.

Made for the #30DayMapChallenge 2026, Day 24: Network. It is the interactive version of a
static map published for the 2025 challenge (Day 26: Transport).

## Use the map

- Hover a route or a port to read its details in the panel on the left.
- Click a line type in the legend to show or hide it.
- Click a regional network (in the legend or on the map) to isolate it; click again to reset.
- Click a magnifier on the map to zoom on a dense area; click again to zoom out.

## Files

| File | Role |
|---|---|
| `index.html` | Page that embeds the map |
| `ferries_interactif.svg` | The map: vector drawing, styles, interaction rules and the CartABl runtime, all in one file |
| `exporte_svg_interactif.py` | PyQGIS script that generates the SVG from the QGIS project |
| `cartabl.js` | CartABl runtime, embedded in the SVG by the script |
| `apercu.png` | Preview image shown when the link is shared |
| `favicon.*`, `apple-touch-icon.png` | Browser tab icons |
| `LICENSE` | GNU GPL v3 |

## How it is made

The map is drawn in QGIS. A PyQGIS script reads the project layers and writes an SVG in which
every route, port and zone has its own identifier and classes. Interactions are declared as
[CartABl](https://igarun.univ-nantes.io/CartABl/) rules stored in the SVG `<metadata>`, so the
file can be opened in the CartABl editor to change them without writing code.

## Data and caveats

- Coastlines and countries: Natural Earth (public domain).
- Ferry routes and ports: compiled by the author in November 2025 from ferryroutes.com and
  operator websites. Timetables and service status change often: check with the operator
  before travelling. This map is not a booking or navigation tool.
- Round trips are merged into a single route.

## Licence

- Code (the script, and the SVG as a whole because it embeds the CartABl runtime):
  GNU General Public License v3.0 or later, see `LICENSE`.
- CartABl runtime: © 2022 Olivier Aubert, IGARUN, Nantes Université, GPL v3 or later.
- Map design and texts: © 2026 Estelle Sérèmes, also reusable under CC BY-SA 4.0.

## Credits

Map and data compilation: Estelle Sérèmes. Thanks to Next Generation Cartographers for the
feedback on the 2025 version.
