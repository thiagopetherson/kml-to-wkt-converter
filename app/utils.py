import xml.etree.ElementTree as ET  # Biblioteca padrão para parsear XML
from shapely.geometry import Polygon, LinearRing  # Criação de polígonos com e sem furos
import re  # Expressões regulares

def extract_all_possible_polygons(kml_string):
    """
    Lê e interpreta um KML (XML), respeitando:
    - Tags <Polygon>, <outerBoundaryIs> e <innerBoundaryIs>
    - Vários <Placemark> (cada um pode ter múltiplas geometrias)
    - MultiGeometry
    - Gera polígonos válidos com furos (ilhas internas)
    """
    # Remove namespace do XML (xmlns="...") para facilitar buscas XPath
    kml_string = re.sub(r'\sxmlns="[^"]+"', '', kml_string, count=1)
    root = ET.fromstring(kml_string)  # Converte string XML em árvore
    polygons = []

    for placemark in root.findall(".//Placemark"):
        for polygon_tag in placemark.findall(".//Polygon"):
            # Extrai o anel externo (contorno principal)
            outer = polygon_tag.find(".//outerBoundaryIs/LinearRing/coordinates")
            # Extrai todos os anéis internos (furos/ilhas)
            inner_rings = polygon_tag.findall(".//innerBoundaryIs/LinearRing/coordinates")

            if outer is None or outer.text is None:
                continue

            shell_coords = parse_coords(outer.text)
            if len(shell_coords) < 3:
                continue  # Ignora se não tem pontos suficientes

            if shell_coords[0] != shell_coords[-1]:
                shell_coords.append(shell_coords[0])  # Garante que o polígono esteja fechado

            holes = []
            for inner in inner_rings:
                if inner.text:
                    hole_coords = parse_coords(inner.text)
                    if len(hole_coords) >= 3:
                        if hole_coords[0] != hole_coords[-1]:
                            hole_coords.append(hole_coords[0])  # Fecha o furo
                        holes.append(hole_coords)

            try:
                ring = LinearRing(shell_coords)  # Valida o anel externo
                if not ring.is_valid:
                    continue
                poly = Polygon(ring, holes)  # Cria o polígono com furos
                if poly.is_valid:
                    polygons.append(poly)
            except Exception:
                continue

        # Caso não tenha <Polygon>, tenta capturar geometria bruta (ex: <LineString> com coordenadas)
        if not placemark.findall(".//Polygon"):
            for coords_tag in placemark.findall(".//coordinates"):
                coords = parse_coords(coords_tag.text or "")
                if len(coords) >= 3:
                    if coords[0] != coords[-1]:
                        coords.append(coords[0])
                    try:
                        poly = Polygon(coords)
                        if poly.is_valid:
                            polygons.append(poly)
                    except Exception:
                        continue

    return polygons


def parse_coords(coord_text):
    """
    Converte texto KML de coordenadas em lista de (lon, lat),
    ignorando duplicatas consecutivas.
    """
    coords = []
    last = None
    for raw in coord_text.strip().split():
        parts = raw.split(',')
        if len(parts) >= 2:
            lon, lat = float(parts[0]), float(parts[1])
            point = (lon, lat)
            if point != last:
                coords.append(point)
                last = point
    return coords
