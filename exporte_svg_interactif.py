# -*- coding: utf-8 -*-
"""Exporte la carte des ferries en SVG vectoriel interactif (CartABl).

A lancer DANS QGIS, projet ferries_caraibes.qgz ouvert (console Python ou QGIS-MCP) :
    exec(open(r".../networks/scripts/exporte_svg_interactif.py", encoding="utf-8").read())

Le SVG produit (site/ferries_interactif.svg) donne un identifiant et des classes
à chaque liaison, port et zone, pour que CartABl puisse y accrocher des interactions.
Les règles CartABl sont écrites dans <metadata> : elles restent modifiables dans
l'éditeur CartABl (https://igarun.univ-nantes.io/CartABl/).
"""
import math
import os
from xml.sax.saxutils import escape

from qgis.core import (QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsFeatureRequest, QgsGeometry, QgsProject, QgsRectangle)

PROJET = QgsProject.instance()
DOSSIER = os.path.dirname(PROJET.fileName())
SORTIE = os.path.join(DOSSIER, "site", "ferries_interactif.svg")
CARTABL_JS = os.path.join(DOSSIER, "scripts", "cartabl.js")

# Liaisons « Gallows Bay » : le fichier 2025 les fait aboutir à Sainte-Croix,
# alors que Gallows Bay est aussi le port de Saint-Eustache (déjà relié sous
# le nom « Statia »). Mettre False pour les réafficher.
EXCLURE_GALLOWS_BAY = False

# ---------------------------------------------------------------- mise en page
LARGEUR, HAUTEUR = 1400, 990
K = 0.7  # la mise en page reprend celle du PNG 2025 (2000 px de large) à 70 %
FOND = "#d6e6f8"

ZONES = {  # clé : (valeur dans Ports/Routes, valeur dans zones.shp, libellé, couleur)
    "vi": ("Virgin Isl", "virgin islands", "Virgin Islands", "#b44ccc"),
    "north": ("North", "north", "Northern English-speaking", "#6fd35c"),
    "middle": ("Middle", "middle", "Creole-speaking", "#e0728a"),
    "south": ("South", "south", "Southern English-speaking", "#35c2a9"),
    "tt": ("TT and Bar", "TT", "Isolated (T&T, Barbados)", "#536de0"),
}
CLE_ZONE = {v[0]: k for k, v in ZONES.items()}
CLE_ZONE.update({v[1]: k for k, v in ZONES.items()})

FREQS = {  # classe : (libellé de légende, valeurs de Frequence2)
    "daily": ("Daily ferries", ("Daily",)),
    "weekly": ("Weekly ferries", ("Weekly",)),
    "yearly": ("A few sailings a year", ("Yearly",)),
    "limited": ("Limited or suspended", ("Limited", "Suspended")),
    "planned": ("Future routes", ("Planned",)),
}
CLE_FREQ = {v: k for k, (_, vals) in FREQS.items() for v in vals}

PORTS = {  # nom dans ports_lesser_antilles.geojson : (nom affiché, territoire)
    "Castries": ("Castries", "Saint Lucia"),
    "Grand-Bourg": ("Grand-Bourg", "Marie-Galante, Guadeloupe (Fr.)"),
    "Gustavia": ("Gustavia", "Saint-Barthélemy (Fr.)"),
    "Terre de haut": ("Terre-de-Haut", "Les Saintes, Guadeloupe (Fr.)"),
    "Terre de bas": ("Terre-de-Bas", "Les Saintes, Guadeloupe (Fr.)"),
    "Marigot": ("Marigot", "Saint-Martin (Fr.)"),
    "Philipsburg": ("Philipsburg", "Sint Maarten (NL)"),
    "Saba": ("Fort Bay", "Saba (NL)"),
    "Basseterre": ("Basseterre", "St. Kitts"),
    "Fort-de-France": ("Fort-de-France", "Martinique (Fr.)"),
    "Pointe a Pitre": ("Pointe-à-Pitre", "Guadeloupe (Fr.)"),
    "Roseau": ("Roseau", "Dominica"),
    "St. George's": ("St. George's", "Grenada"),
    "Kingstown": ("Kingstown", "St. Vincent"),
    "St. John's": ("St. John's", "Antigua"),
    "Port of Spain": ("Port of Spain", "Trinidad"),
    "Scarborough": ("Scarborough", "Tobago"),
    "Charlestown": ("Charlestown", "Nevis"),
    "Trois Rivieres": ("Trois-Rivières", "Guadeloupe (Fr.)"),
    "Port Elizabeth": ("Port Elizabeth", "Bequia, St. Vincent and the Grenadines"),
    "Statia": ("Oranjestad", "Sint Eustatius (NL)"),
    "Anguilla": ("Blowing Point", "Anguilla (UK)"),
    "Anegada": ("Anegada", "British Virgin Islands"),
    "Virgin Gorda": ("Virgin Gorda", "British Virgin Islands"),
    "Palm Island": ("Union Island", "St. Vincent and the Grenadines"),
    "Saint-Pierre": ("Saint-Pierre", "Martinique (Fr.)"),
    "Barbuda": ("Barbuda", "Antigua and Barbuda"),
    "Montserrat": ("Little Bay", "Montserrat (UK)"),
    "Petite Martinique": ("Petite Martinique", "Grenada"),
    "Carriacou": ("Carriacou", "Grenada"),
    "Port barbarde": ("Bridgetown", "Barbados"),
    "port desirade": ("La Désirade", "Guadeloupe (Fr.)"),
    "canouan": ("Canouan", "St. Vincent and the Grenadines"),
    "mustique": ("Mustique", "St. Vincent and the Grenadines"),
    "port mayreau": ("Mayreau", "St. Vincent and the Grenadines"),
    "Cruz Bay": ("Cruz Bay", "St. John, US Virgin Islands"),
    "Red Hook": ("Red Hook", "St. Thomas, US Virgin Islands"),
    "Charlotte": ("Charlotte Amalie", "St. Thomas, US Virgin Islands"),
    "Crown Bay": ("Crown Bay", "St. Thomas, US Virgin Islands"),
    "Frederiksted": ("Frederiksted", "St. Croix, US Virgin Islands"),
    "Christiansted": ("Christiansted", "St. Croix, US Virgin Islands"),
    "West End": ("West End", "Tortola, British Virgin Islands"),
    "Road Town": ("Road Town", "Tortola, British Virgin Islands"),
    "georgetown": ("Georgetown", "Guyana"),
    "Deshaies": ("Deshaies", "Guadeloupe (Fr.)"),
    "St-francçois": ("Saint-François", "Guadeloupe (Fr.)"),
}

TRADUCTIONS = {
    "excursions occasionnelles (quelques dates/an)": "Occasional excursions (a few dates a year)",
    "charters et excursions spéciales uniquement": "Charters and special excursions only",
    "regular (plusieurs fois/semaine)": "Several times a week",
    "regular (4 fois/semaine)": "4 times a week",
    "Service suspendu depuis avril 2024, reprise prévue 2025": "Suspended since April 2024",
    "Journées découverte programmées, non régulier": "Scheduled day trips, not a regular service",
    "Pas de service régulier, seulement voyages privés": "No regular service, private trips only",
    "Service en développement - non encore actif": "Service in development, not yet operating",
    "Inactive": "No service",
}

# Étiquettes : (texte, x, y) en pixels du PNG 2025, ancre au début sauf mention
PAYS = [
    ("British Virgin Is.", 632, 218), ("Anguilla", 672, 268), ("U.S. Virgin Is.", 562, 312),
    ("Sint Maarten/St-Martin", 795, 288), ("St-Barthélemy", 810, 328),
    ("Antigua and Barb.", 930, 405), ("Guadeloupe (Fr.)", 980, 454), ("St. Kitts and Nevis", 580, 450),
    ("Montserrat", 708, 527), ("Dominica", 830, 675), ("Martinique (Fr.)", 1062, 728),
    ("Saint Lucia", 860, 853), ("St. Vin. and Gren.", 735, 925), ("Barbados", 1048, 920),
    ("Grenada", 847, 1125), ("Trinidad and Tobago", 705, 1218), ("Guyana ↓", 1146, 1222),
]
MERS = [("Atlantic Ocean", 1168, 536), ("Caribbean Sea", 540, 981)]
NOMS_ZONES = [  # (zone, lignes, x, y, rotation)
    ("vi", ["Virgin Islands"], 547, 206, -14),
    ("north", ["Northern", "English-Speaking"], 617, 498, -8),
    ("middle", ["Creole-Speaking"], 1075, 560, 31),
    ("south", ["Southern", "English-Speaking"], 760, 1012, -9),
    ("tt", ["Isolated (T&T, Barbados)"], 1232, 912, 39),
]
LOUPES = {  # zones de zoom : (ouest, sud, est, nord) en degrés, coin où poser la loupe
    "vi": (-65.08, 17.62, -64.22, 18.82, "no"),
    "hub": (-63.38, 17.02, -62.50, 18.28, "no"),
    "gwada": (-61.90, 15.75, -60.98, 16.42, "ne"),
    "gren": (-61.62, 11.95, -61.05, 13.25, "se"),
}


# ---------------------------------------------------------------- projection
def merc(lon, lat):
    r = 6378137.0
    return r * math.radians(lon), r * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


# Calage sur le PNG 2025 : Anegada en (611, 218) px, Port of Spain en (955, 1262) px
_XA, _YA = merc(-64.33639, 18.7275)
_XB, _YB = merc(-61.5019, 10.6549)
_M_PAR_PX = ((_XB - _XA) / (955 - 611) + (_YA - _YB) / (1262 - 218)) / 2


def X(mx):
    return (611 + (mx - _XA) / _M_PAR_PX) * K


def Y(my):
    return (218 + (_YA - my) / _M_PAR_PX) * K


def px(v):
    """Coordonnée en pixels du PNG 2025 -> pixels du SVG."""
    return v * K


def etq(xp, yp):
    """Position d'une étiquette relevée sur le PNG 2025 -> pixels du SVG.
    Le PNG n'a pas tout à fait la même échelle en x et en y : on repasse par les mètres."""
    mx = _XA + (xp - 611) * (_XB - _XA) / (955 - 611)
    my = _YA - (yp - 218) * (_YA - _YB) / (1262 - 218)
    return X(mx), Y(my)


def inv(xp, yp):
    """Pixels du PNG 2025 -> mètres EPSG:3857."""
    return _XA + (xp - 611) * _M_PAR_PX, _YA - (yp - 218) * _M_PAR_PX


CADRE_PX = (455, 135, 1290, 1272)  # emprise de la carte, en pixels du PNG 2025
_x0, _y1 = inv(CADRE_PX[0], CADRE_PX[1])
_x1, _y0 = inv(CADRE_PX[2], CADRE_PX[3])
CADRE = QgsRectangle(_x0, _y0, _x1, _y1)
CRS3857 = QgsCoordinateReferenceSystem("EPSG:3857")
CRS4326 = QgsCoordinateReferenceSystem("EPSG:4326")


def f1(v):
    return ("%.1f" % v).rstrip("0").rstrip(".")


def chemin(geom, fx=X, fy=Y, ferme=True):
    """Géométrie QGIS (EPSG:3857) -> attribut d d'un <path>."""
    morceaux = []
    if ferme:
        polys = geom.asMultiPolygon() if geom.isMultipart() else [geom.asPolygon()]
        anneaux = [a for poly in polys for a in poly]
    else:
        anneaux = geom.asMultiPolyline() if geom.isMultipart() else [geom.asPolyline()]
    for a in anneaux:
        if len(a) < 2:
            continue
        pts = " ".join(f"{f1(fx(p.x()))},{f1(fy(p.y()))}" for p in a)
        morceaux.append("M" + pts + ("Z" if ferme else ""))
    return "".join(morceaux)


def nul(v):
    return v is None or str(v).strip() in ("", "NULL")


def att(v):
    """Valeur placée dans un attribut data-* et réinjectée telle quelle par CartABl
    dans le modèle (innerHTML) : elle doit donc être échappée deux fois."""
    v = "—" if nul(v) else str(v).strip()
    v = TRADUCTIONS.get(v, v)
    v = v[0].upper() + v[1:]
    return escape(escape(v), {'"': "&quot;"})


def couche(nom):
    return PROJET.mapLayersByName(nom)[0]


# ---------------------------------------------------------------- données
def lire_ports():
    c = couche("Ports")
    tr = QgsCoordinateTransform(c.crs(), CRS3857, PROJET)
    ports = {}
    for f in c.getFeatures():
        g = f.geometry()
        g.transform(tr)
        p = g.asPoint()
        nom = f["name"]
        affiche, territoire = PORTS.get(nom, (nom, ""))
        ports[nom] = {"nom": affiche, "terr": territoire, "x": p.x(), "y": p.y(),
                      "zone": CLE_ZONE.get(f["group"], "north"),
                      "ops": None if nul(f["operators"]) else f["operators"],
                      "adresse": None if nul(f["address"]) else f["address"],
                      "liaisons": []}
    return ports


def lire_routes(ports):
    c = couche("Ferry_lesser_antilles")
    joints = {n.split("Sheet1_")[1]: n for n in c.fields().names() if "Sheet1_" in n}

    def val(f, cle):
        v = f[cle]
        if nul(v) and cle in joints:
            v = f[joints[cle]]
        return None if nul(v) else str(v).strip()

    def proche(pt):
        nom = min(ports, key=lambda n: (ports[n]["x"] - pt.x()) ** 2 + (ports[n]["y"] - pt.y()) ** 2)
        return nom, math.hypot(ports[nom]["x"] - pt.x(), ports[nom]["y"] - pt.y())

    routes = {}
    for f in c.getFeatures():
        g = f.geometry()
        sommets = list(g.vertices())
        a, da = proche(sommets[0])
        b, db = proche(sommets[-1])
        hors_port = max(da, db) > 5000
        cle = tuple(sorted([val(f, "origin"), val(f, "destination")])) if hors_port else tuple(sorted([a, b]))
        r = routes.setdefault(cle, {"geom": g, "ports": None if hors_port else (a, b),
                                    "noms": (val(f, "origin"), val(f, "destination")),
                                    "zone": CLE_ZONE.get(f["group"], "north"),
                                    "freq": CLE_FREQ.get(f["Frequence2"], "limited"),
                                    "freq2": f["Frequence2"]})
        for cle_champ in ("operator", "frequency", "status", "note"):
            if not r.get(cle_champ):
                r[cle_champ] = val(f, cle_champ)

    if EXCLURE_GALLOWS_BAY:
        routes = {k: r for k, r in routes.items()
                  if not (r["ports"] and "Christiansted" in r["ports"])}
    liste = []
    for i, (cle, r) in enumerate(sorted(routes.items(), key=lambda kv: (kv[1]["zone"], kv[0])), 1):
        r["id"] = i
        liste.append(r)
    return liste


# ---------------------------------------------------------------- dessin
def svg_terres():
    c = [l for l in PROJET.mapLayers().values()
         if "countries" in l.name() and l.geometryType() == 2][0]
    tr = QgsCoordinateTransform(c.crs(), CRS3857, PROJET)
    inv_tr = QgsCoordinateTransform(CRS3857, c.crs(), PROJET)
    req = QgsFeatureRequest().setFilterRect(inv_tr.transformBoundingBox(CADRE))
    out = []
    for f in c.getFeatures(req):
        g = f.geometry()
        g.transform(tr)
        g = g.clipped(CADRE)
        if g.isEmpty():
            continue
        g = g.simplify(120)
        d = chemin(g)
        if d:
            out.append(f'<path d="{d}"><title>{escape(str(f["NAME"]))}</title></path>')
    return "\n".join(out), c


def svg_situation(c, x, y, w, h):
    """Carte de situation : fond monde simplifié et cadre rouge de la zone."""
    ex0, ey0 = merc(-118, -9)
    ex1 = merc(-34, 0)[0]
    ech = w / (ex1 - ex0)
    ey1 = ey0 + h / ech
    emprise = QgsRectangle(ex0, ey0, ex1, ey1)
    fx = lambda mx: x + (mx - ex0) * ech
    fy = lambda my: y + (ey1 - my) * ech
    tr = QgsCoordinateTransform(c.crs(), CRS3857, PROJET)
    inv_tr = QgsCoordinateTransform(CRS3857, c.crs(), PROJET)
    req = QgsFeatureRequest().setFilterRect(inv_tr.transformBoundingBox(emprise))
    d = []
    for f in c.getFeatures(req):
        g = f.geometry()
        g.transform(tr)
        g = g.clipped(emprise).simplify(18000)
        if not g.isEmpty() and g.area() > 4e8:
            d.append(chemin(g, fx, fy))
    cadre = (f'<rect x="{f1(fx(CADRE.xMinimum()))}" y="{f1(fy(CADRE.yMaximum()))}" '
             f'width="{f1(CADRE.width() * ech)}" height="{f1(CADRE.height() * ech)}" '
             'fill="none" stroke="#d40000" stroke-width="1.6"/>')
    textes = "".join(f'<text x="{f1(fx(merc(lon, lat)[0]))}" y="{f1(fy(merc(lon, lat)[1]))}" class="situ">{t}</text>'
                     for t, lon, lat in (("USA", -98, 33.5), ("Brazil", -56, -6)))
    return (f'<g id="situation"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="#111" stroke-width="2"/>'
            f'<path d="{"".join(d)}" fill="#fff" stroke="#222" stroke-width="0.5" filter="url(#ombre-fine)"/>'
            f'{cadre}{textes}</g>')


def svg_zones():
    c = couche("zones")
    tr = QgsCoordinateTransform(c.crs(), CRS3857, PROJET)
    out = []
    for f in c.getFeatures():
        z = CLE_ZONE[f["group"]]
        g = f.geometry()
        g.transform(tr)
        g = g.clipped(CADRE)
        out.append(f'<path id="zone-{z}" class="zone grp-{z}" d="{chemin(g)}" fill="{ZONES[z][3]}">'
                   f'<title>{escape(ZONES[z][2])}</title></path>')
    return "\n".join(out)


def svg_routes(routes, ports):
    out = []
    for r in routes:
        if r["ports"]:
            a, b = (ports[n] for n in r["ports"])
            ports[r["ports"][0]]["liaisons"].append(r["id"])
            ports[r["ports"][1]]["liaisons"].append(r["id"])
            trajet = f'{a["nom"]} ⇄ {b["nom"]}'
            terr = a["terr"] if a["terr"] == b["terr"] else f'{a["terr"]} · {b["terr"]}'
            classes_ports = f' p-{a["id"]} p-{b["id"]}'
        else:
            trajet, terr, classes_ports = f'{r["noms"][0]} ⇄ {r["noms"][1]}', "British Virgin Islands", ""
        g = r["geom"].clipped(CADRE)
        d = chemin(g, ferme=False)
        z, fq = r["zone"], r["freq"]
        rail = f'<path class="rail" d="{d}"/>' if fq == "planned" else ""
        statut = r.get("status") or ("Active" if fq in ("daily", "weekly") else r["freq2"])
        out.append(
            f'<g id="route-{r["id"]}" class="route grp-{z} freq-{fq}{classes_ports}" '
            f'data-trajet="{att(trajet)}" data-terr="{att(terr)}" data-rythme="{att(FREQS[fq][0])}" '
            f'data-detail="{att(r.get("frequency") or r["freq2"])}" data-op="{att(r.get("operator"))}" '
            f'data-statut="{att(statut)}" data-note="{att(r.get("note"))}" data-zone="{att(ZONES[z][2])}">'
            f'<path class="fond" d="{d}"/>{rail}<path class="trait" d="{d}" stroke="{ZONES[z][3]}"/>'
            f'<path class="cible" d="{d}"/>'
            f'<title>{escape(trajet)} · {escape(str(r.get("frequency") or r["freq2"]))}</title></g>')
    return "\n".join(out)


def svg_ports(ports):
    out = []
    for p in ports.values():
        if not p["liaisons"]:
            continue
        n = len(p["liaisons"])
        out.append(
            f'<g id="port-{p["id"]}" class="port grp-{p["zone"]}" data-nom="{att(p["nom"])}" '
            f'data-terr="{att(p["terr"])}" data-ops="{att(p["ops"])}" data-adresse="{att(p["adresse"])}" '
            f'data-nb="{n} route{"s" if n > 1 else ""}" data-zone="{att(ZONES[p["zone"]][2])}">'
            f'<circle cx="{f1(X(p["x"]))}" cy="{f1(Y(p["y"]))}" r="4.2" fill="{ZONES[p["zone"]][3]}"/>'
            f'<circle class="coeur" cx="{f1(X(p["x"]))}" cy="{f1(Y(p["y"]))}" r="1.2"/>'
            f'<circle class="cible" cx="{f1(X(p["x"]))}" cy="{f1(Y(p["y"]))}" r="8"/>'
            f'<title>{escape(p["nom"])}, {escape(p["terr"])}</title></g>')
    return "\n".join(out)


def svg_etiquettes():
    out = []
    for t, x, y in PAYS:
        x, y = etq(x, y)
        out.append(f'<text class="pays" x="{f1(x)}" y="{f1(y)}">{escape(t)}</text>')
    for t, x, y in MERS:
        x, y = etq(x, y)
        out.append(f'<text class="mer" x="{f1(x)}" y="{f1(y)}">{t}</text>')
    for z, lignes, x, y, rot in NOMS_ZONES:
        x, y = etq(x, y)
        tspans = "".join(f'<tspan x="{f1(x)}" dy="{0 if i == 0 else 13}">{escape(l)}</tspan>'
                         for i, l in enumerate(lignes))
        out.append(f'<text class="nomzone grp-{z}" x="{f1(x)}" y="{f1(y)}" fill="{ZONES[z][3]}" '
                   f'transform="rotate({rot} {f1(x)} {f1(y)})">{tspans}</text>')
    return "\n".join(out)


def svg_loupes():
    out = []
    for cle, (o, s, e, n, coin) in LOUPES.items():
        x0, y0 = merc(o, n)
        x1, y1 = merc(e, s)
        x, y, w, h = X(x0), Y(y0), X(x1) - X(x0), Y(y1) - Y(y0)
        out.append(f'<rect id="cadre-{cle}" class="cadre" x="{f1(x)}" y="{f1(y)}" width="{f1(w)}" height="{f1(h)}"/>')
        cx = x + 9 if "o" in coin else x + w - 13
        cy = y + 9 if "n" in coin else y + h - 13
        out.append(f'<g id="loupe-{cle}" class="loupe"><title>Zoom in / out</title>'
                   f'<circle cx="{f1(cx)}" cy="{f1(cy)}" r="7"/>'
                   f'<path d="M{f1(cx - 3.5)},{f1(cy)}h7M{f1(cx)},{f1(cy - 3.5)}v7"/>'
                   f'<path d="M{f1(cx + 5)},{f1(cy + 5)}l4.5,4.5" class="manche"/></g>')
    return "\n".join(out)


def svg_legende(routes):
    x, y = 1040, 150
    out = [f'<text class="titreleg" x="{x}" y="{y}">Ferry service</text>',
           f'<text class="aideleg" x="{x}" y="{y + 18}">Click a line type to show or hide it</text>']
    y += 44
    for fq, (lib, _) in FREQS.items():
        n = sum(1 for r in routes if r["freq"] == fq)
        d = f"M{x + 4},{y}H{x + 84}"
        out.append(f'<g id="leg-freq-{fq}" class="leg-freq"><rect class="cible" x="{x - 6}" y="{y - 17}" width="340" height="34"/>'
                   f'<g class="route freq-{fq} exemple"><path class="fond" d="{d}"/>'
                   + (f'<path class="rail" d="{d}"/>' if fq == "planned" else "") +
                   f'<path class="trait" d="{d}" stroke="#9bd1ff"/></g>'
                   f'<text class="libleg" x="{x + 100}" y="{y + 6}">{lib} <tspan class="nbleg">({n})</tspan></text></g>')
        y += 40
    y += 26
    out.append(f'<text class="titreleg" x="{x}" y="{y}">Regional networks</text>')
    out.append(f'<text class="aideleg" x="{x}" y="{y + 18}">Click a network to isolate it, click again to reset</text>')
    y += 44
    for z, (_, _, lib, coul) in ZONES.items():
        n = sum(1 for r in routes if r["zone"] == z)
        out.append(f'<g id="leg-zone-{z}" class="leg-zone grp-{z}"><rect class="cible" x="{x - 6}" y="{y - 17}" width="340" height="34"/>'
                   f'<rect x="{x + 4}" y="{y - 11}" width="80" height="22" rx="11" fill="{coul}" fill-opacity="0.45" stroke="{coul}" stroke-width="1.5"/>'
                   f'<text class="libleg" x="{x + 100}" y="{y + 6}">{escape(lib)} <tspan class="nbleg">({n})</tspan></text></g>')
        y += 40
    y += 26
    out.append(f'<text class="titreleg" x="{x}" y="{y}">Ports</text>')
    out.append(f'<text class="aideleg" x="{x}" y="{y + 18}">Hover a port to see its routes</text>')
    y += 46
    out.append(f'<circle cx="{x + 44}" cy="{y}" r="9" fill="#7b2a86" stroke="#111" stroke-width="2.4"/>'
               f'<circle cx="{x + 44}" cy="{y}" r="2.6" fill="#111"/>'
               f'<text class="libleg" x="{x + 100}" y="{y + 6}">Ferry port</text>')
    return "\n".join(out)


def div(classe, contenu):
    return f'<div xmlns="http://www.w3.org/1999/xhtml" class="{classe}">{contenu}</div>'


def svg_fiches():
    x, y, w, h = 22, 128, 292, 318
    fo = f'<foreignObject x="{x + 14}" y="{y + 12}" width="{w - 28}" height="{h - 20}">'
    cadre = f'<rect class="fichefond" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>'
    aide = (f'<g id="fiche-aide">{cadre}{fo}'
            + div("ftitre", "Explore the map")
            + div("ftexte", "Hover a route or a port to read its details here.")
            + div("ftexte", "Click the legend to filter line types or isolate a regional network.")
            + div("ftexte", "Click a magnifier ⊕ on the map to zoom on a dense area, and again to zoom out.")
            + '</foreignObject></g>')
    route = (f'<g id="fiche-route" style="display:none">{cadre}{fo}'
             + div("fsur", "Ferry route")
             + div("ftitre", "{{ origin.dataset.trajet }}")
             + div("fsous", "{{ origin.dataset.terr }}")
             + div("flib", "Service") + div("fval", "{{ origin.dataset.rythme }}")
             + div("flib", "Frequency") + div("fval", "{{ origin.dataset.detail }}")
             + div("flib", "Operator") + div("fval", "{{ origin.dataset.op }}")
             + div("flib", "Status") + div("fval", "{{ origin.dataset.statut }}")
             + div("flib", "Note") + div("fval", "{{ origin.dataset.note }}")
             + div("flib", "Network") + div("fval", "{{ origin.dataset.zone }}")
             + '</foreignObject></g>')
    port = (f'<g id="fiche-port" style="display:none">{cadre}{fo}'
            + div("fsur", "Ferry port")
            + div("ftitre", "{{ origin.dataset.nom }}")
            + div("fsous", "{{ origin.dataset.terr }}")
            + div("flib", "Connections") + div("fval", "{{ origin.dataset.nb }}")
            + div("flib", "Operators") + div("fval", "{{ origin.dataset.ops }}")
            + div("flib", "Terminal") + div("fval", "{{ origin.dataset.adresse }}")
            + div("flib", "Network") + div("fval", "{{ origin.dataset.zone }}")
            + '</foreignObject></g>')
    return aide + route + port


def css(routes, ports):
    regles = ["""
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,700;1,700;1,800&amp;family=Noto+Serif:ital,wght@0,400;0,600;1,400&amp;display=swap');
text { font-family: 'Noto Serif', Georgia, serif; fill: #323232; }
.titre { font-family: 'Playfair Display', Georgia, serif; font-size: 31px; font-weight: 500; fill: #2c2325; text-anchor: middle; }
.titre .gras { font-style: italic; font-weight: 800; }
.pays { font-size: 15.5px; font-weight: 600; paint-order: stroke; stroke: #d6e6f8; stroke-width: 3px; stroke-opacity: .55; pointer-events: none; }
.mer { font-size: 15px; font-style: italic; fill: #2b3a8c; pointer-events: none; }
.nomzone { font-size: 12.5px; paint-order: stroke; stroke: #fff; stroke-width: 2.5px; stroke-opacity: .5; font-weight: 600; font-style: italic; pointer-events: none; }
.situ { font-size: 9px; font-family: Arial, Helvetica, sans-serif; text-anchor: middle; }
.credits { font-size: 11.5px; font-weight: 600; fill: #222; text-anchor: middle; }
.titreleg { font-family: 'Playfair Display', Georgia, serif; font-size: 21px; font-style: italic; font-weight: 800; fill: #111; }
.aideleg { font-size: 11px; font-style: italic; fill: #44506a; }
.libleg { font-size: 15px; font-weight: 600; fill: #1c1c1c; }
.nbleg { font-weight: 400; fill: #5a6072; }

#terres path { fill: #fff; stroke: #010101; stroke-width: .9; stroke-linejoin: round; }
.zone { fill-opacity: .36; stroke: none; cursor: pointer; }
.zone:hover { fill-opacity: .5; }

.route path { fill: none; stroke-linecap: round; }
.route .fond { stroke: #0b0b0b; stroke-width: 3.6px; }
.route .trait { stroke-width: 1.7px; }
.route .cible { stroke: #000; stroke-opacity: 0; stroke-width: 11px; pointer-events: stroke; }
.route.freq-weekly .fond { stroke-width: 2.7px; }
.route.freq-weekly .trait { stroke-width: 1.1px; }
.route.freq-yearly .trait { stroke-dasharray: 5 6; stroke-linecap: butt; }
.route.freq-limited .fond { stroke-width: 2.7px; }
.route.freq-limited .trait { stroke-width: 1.3px; stroke-dasharray: 1.5 4.5; stroke-linecap: butt; }
.route.freq-planned .fond { stroke-width: 6px; stroke-linecap: butt; }
.route .rail { stroke: #e9f1fb; stroke-width: 4.4px; stroke-linecap: butt; }
.route.exemple .trait, .route.exemple .fond { stroke-linecap: butt; }
.route.actif .fond { stroke: #111; stroke-width: 8px; }
.route.actif .trait { stroke-width: 3.4px; stroke: #fff36b; stroke-dasharray: none; }
.route, .port, .zone, .nomzone, .leg-zone, .leg-freq { transition: opacity .25s; }

.port circle { stroke: #0b0b0b; stroke-width: 1.1px; }
.port .coeur { fill: #0b0b0b; stroke: none; }
.port .cible, .leg-freq .cible, .leg-zone .cible { fill: #000; fill-opacity: 0; stroke: none; }
.port.actif circle:first-child { r: 7px; stroke-width: 2px; }

.leg-freq:hover .libleg, .leg-zone:hover .libleg { fill: #0a3a8c; text-decoration: underline; }
.leg-freq.eteint { opacity: .32; }
.cadre { fill: none; stroke: none; pointer-events: none; }
.loupe circle { fill: #fff; stroke: #1f2a44; stroke-width: 1.6px; }
.loupe path { stroke: #1f2a44; stroke-width: 1.6px; fill: none; stroke-linecap: round; }
.loupe .manche { stroke-width: 2.4px; }
.loupe:hover circle { fill: #fff36b; }

/* Vue zoomée : CartABl pose data-_action sur la racine, on affine alors traits et textes */
svg[data-_action^="panzoom"] .route .fond { stroke-width: 1.3px; }
svg[data-_action^="panzoom"] .route .trait { stroke-width: .6px; }
svg[data-_action^="panzoom"] .route.freq-weekly .fond, svg[data-_action^="panzoom"] .route.freq-limited .fond { stroke-width: 1px; }
svg[data-_action^="panzoom"] .route.freq-weekly .trait, svg[data-_action^="panzoom"] .route.freq-limited .trait { stroke-width: .45px; }
svg[data-_action^="panzoom"] .route.freq-yearly .trait { stroke-dasharray: 2 2.4; }
svg[data-_action^="panzoom"] .route.freq-limited .trait { stroke-dasharray: .7 1.6; }
svg[data-_action^="panzoom"] .route .cible { stroke-width: 3.5px; }
svg[data-_action^="panzoom"] .route.actif .fond { stroke-width: 2.6px; }
svg[data-_action^="panzoom"] .route.actif .trait { stroke-width: 1.2px; }
svg[data-_action^="panzoom"] .port circle:first-child { r: 1.6px; stroke-width: .4px; }
svg[data-_action^="panzoom"] .port .coeur { r: .45px; }
svg[data-_action^="panzoom"] .port .cible { r: 3px; }
svg[data-_action^="panzoom"] .port.actif circle:first-child { r: 2.6px; stroke-width: .7px; }
svg[data-_action^="panzoom"] .pays { font-size: 6.5px; stroke-width: 1.2px; }
svg[data-_action^="panzoom"] .nomzone { font-size: 5.5px; stroke-width: 1px; }
svg[data-_action^="panzoom"] #terres path { stroke-width: .35px; }
svg[data-_action^="panzoom"] .loupe { transform-box: fill-box; transform-origin: center; transform: scale(.45); }

.fichefond { fill: #fff; fill-opacity: .9; stroke: #1f2a44; stroke-width: 1.2px; }
.fsur { font: italic 11px 'Noto Serif', Georgia, serif; color: #5a6072; letter-spacing: .04em; text-transform: uppercase; }
.ftitre { font: 800 italic 19px/1.2 'Playfair Display', Georgia, serif; color: #111; margin: 2px 0 3px; }
.fsous { font: 12px/1.3 'Noto Serif', Georgia, serif; color: #333; margin-bottom: 8px; padding-bottom: 7px; border-bottom: 1px solid #c6cfde; }
.flib { font: italic 10.5px 'Noto Serif', Georgia, serif; color: #5a6072; margin-top: 5px; }
.fval { font: 600 12.5px/1.3 'Noto Serif', Georgia, serif; color: #1c1c1c; }
.ftexte { font: 13px/1.45 'Noto Serif', Georgia, serif; color: #26303f; margin-top: 9px; }
"""]
    for z in ZONES:
        sauf = f":not(.grp-{z})"
        regles.append(
            f"#carte.focus-{z} .route{sauf}, #carte.focus-{z} .port{sauf}, #carte.focus-{z} .zone{sauf}, "
            f"#carte.focus-{z} .nomzone{sauf}, #carte.focus-{z} .leg-zone{sauf} {{ opacity: .12; }}")
    # Survol d'un port : seules ses liaisons restent visibles ; survol d'une liaison : ses ports ressortent
    for p in ports.values():
        if p["liaisons"]:
            regles.append(f'#carte:has(#port-{p["id"]}.actif) #routes .route:not(.p-{p["id"]}) {{ opacity: .1; }}')
    for r in routes:
        if r["ports"]:
            a, b = (ports[n]["id"] for n in r["ports"])
            regles.append(f'#carte:has(#route-{r["id"]}.actif) :is(#port-{a}, #port-{b}) circle:first-child '
                          '{ r: 6.5px; stroke-width: 2px; }')
    return "\n".join(regles)


def regle(source, evenement, *actions):
    corps = "".join("<cartabl:action " + " ".join(f'{k}="{v}"' for k, v in a.items()) + "/>" for a in actions)
    return f'<cartabl:rule source="{source}" event="{evenement}">{corps}</cartabl:rule>'


def regles_cartabl():
    r = [
        regle(".route:not(.exemple)", "mouseenter",
              {"name": "addClass", "selector": "this", "classname": "actif"},
              {"name": "hide", "selector": "#fiche-aide, #fiche-port"},
              {"name": "show_template", "selector": "#fiche-route"}),
        regle(".route:not(.exemple)", "mouseleave",
              {"name": "removeClass", "selector": "this", "classname": "actif"}),
        regle(".port", "mouseenter",
              {"name": "addClass", "selector": "this", "classname": "actif"},
              {"name": "hide", "selector": "#fiche-aide, #fiche-route"},
              {"name": "show_template", "selector": "#fiche-port"}),
        regle(".port", "mouseleave",
              {"name": "removeClass", "selector": "this", "classname": "actif"}),
    ]
    for fq in FREQS:
        r.append(regle(f"#leg-freq-{fq}", "click",
                       {"name": "toggleClass", "selector": "this", "classname": "eteint"},
                       {"name": "toggle", "selector": f"#routes .freq-{fq}"}))
    for z in ZONES:
        actions = [{"name": "removeClass", "selector": "#carte", "classname": f"focus-{a}"} for a in ZONES if a != z]
        actions.append({"name": "toggleClass", "selector": "#carte", "classname": f"focus-{z}"})
        r.append(regle(f"#leg-zone-{z}, #zone-{z}", "click", *actions))
    for cle in LOUPES:
        r.append(regle(f"#loupe-{cle}", "click", {"name": "panzoom", "selector": f"#cadre-{cle}"}))
    return "\n".join(r)


def construire():
    ports = lire_ports()
    for i, p in enumerate(ports.values(), 1):
        p["id"] = i
    routes = lire_routes(ports)
    terres, couche_pays = svg_terres()
    d_routes = svg_routes(routes, ports)  # remplit aussi ports[...]["liaisons"]
    cx0, cy0 = px(CADRE_PX[0]), px(CADRE_PX[1])
    cw, ch = px(CADRE_PX[2] - CADRE_PX[0]), px(CADRE_PX[3] - CADRE_PX[1])
    # Échelle graphique : 100 km au sol vers 15° N
    km100 = 100000 / math.cos(math.radians(15)) / _M_PAR_PX * K
    ex, ey = 34, 668
    echelle = (f'<g id="echelle"><path d="M{ex},{ey - 5}V{ey}H{f1(ex + km100)}V{ey - 5}M{f1(ex + km100 / 2)},{ey - 4}V{ey}" '
               'fill="none" stroke="#111" stroke-width="1"/>'
               f'<text x="{f1(ex + km100 / 2)}" y="{ey - 9}" class="situ">50</text>'
               f'<text x="{f1(ex + km100)}" y="{ey - 9}" class="situ">100 km</text></g>')
    nx, ny = px(1198), px(196)
    nord = (f'<g id="nord"><text x="{f1(nx)}" y="{f1(ny - 22)}" text-anchor="middle" '
            'style="font:700 15px Arial,Helvetica,sans-serif;fill:#111">N</text>'
            f'<path d="M{f1(nx)},{f1(ny - 18)}l5,18l18,5l-18,5l-5,18l-5,-18l-18,-5l18,-5z" fill="#111"/>'
            f'<circle cx="{f1(nx)}" cy="{f1(ny + 5)}" r="5" fill="#fff" stroke="#111" stroke-width="1.5"/></g>')

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:cartabl="http://olivieraubert.net/namespaces/cartabl"
     viewBox="0 0 {LARGEUR} {HAUTEUR}" id="ferries-lesser-antilles" role="img"
     aria-label="Interactive map of inter-island ferry routes in the Lesser Antilles">
<title>Routes and Roots: Inter-Island Mobility and Divisions in the Lesser Antilles</title>
<metadata>
<cartabl:cartabl version="1.2-dev" comment="Interactive version prepared for CartABl - see https://igarun.univ-nantes.io/CartABl/"/>
{regles_cartabl()}
</metadata>
<defs>
<style class="cartabl">{css(routes, ports)}</style>
<filter id="ombre" x="-20%" y="-20%" width="150%" height="150%"><feDropShadow dx="2.6" dy="2.6" stdDeviation="1.1" flood-color="#000" flood-opacity=".85"/></filter>
<filter id="ombre-fine" x="-5%" y="-5%" width="115%" height="115%"><feDropShadow dx="1.2" dy="1.2" stdDeviation=".5" flood-color="#000" flood-opacity=".7"/></filter>
<clipPath id="clip-carte"><rect x="{f1(cx0)}" y="{f1(cy0)}" width="{f1(cw)}" height="{f1(ch)}"/></clipPath>
</defs>
<g id="carte">
<rect id="fond" width="{LARGEUR}" height="{HAUTEUR}" fill="{FOND}"/>
<text class="titre" x="{LARGEUR / 2}" y="64"><tspan class="gras">Routes and Roots :</tspan> Inter-Island Mobility and Divisions in the Lesser Antilles</text>
<g clip-path="url(#clip-carte)">
<g id="zones">
{svg_zones()}
</g>
<g id="terres" filter="url(#ombre)">
{terres}
</g>
<g id="routes">
{d_routes}
</g>
<g id="ports">
{svg_ports(ports)}
</g>
</g>
<g id="etiquettes">
{svg_etiquettes()}
</g>
<g id="loupes">
{svg_loupes()}
</g>
{nord}
<g id="legende">
{svg_legende(routes)}
</g>
{svg_situation(couche_pays, 22, 470, 292, 168)}
{echelle}
<g id="fiches">
{svg_fiches()}
</g>
<text class="credits" x="{LARGEUR / 2}" y="968">Data: Natural Earth, ferryroutes.com (2025)  |  Map: Estelle Sérèmes  |  #30DayMapChallenge 2026 · Day 24: Network  |  Interactions: CartABl (IGARUN, Nantes Université)</text>
</g>
<script type="text/javascript" class="cartabl"><![CDATA[
{open(CARTABL_JS, encoding="utf-8").read()}
]]></script>
</svg>
'''
    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    with open(SORTIE, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"{len(routes)} liaisons, {sum(1 for p in ports.values() if p['liaisons'])} ports -> {SORTIE} "
          f"({os.path.getsize(SORTIE) // 1024} Ko)")
    print("calage x/y (m par px) :", round((_XB - _XA) / (955 - 611)), round((_YA - _YB) / (1262 - 218)))


construire()
