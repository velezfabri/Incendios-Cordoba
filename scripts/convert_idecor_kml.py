"""Convert verified IDECOR 2024 KML exports to event GeoJSON."""
import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {'k': 'http://www.opengis.net/kml/2.2'}
EVENTS = {'el_durazno': ('El durazno', '02-09-2024', '10644'),
          'capilla_del_monte': ('Capilla del Monte', '19-09-2024', '42046')}


def ring(boundary):
    if boundary is None:
        raise ValueError('Falta un anillo KML')
    coords = boundary.findtext('.//k:coordinates', default='', namespaces=NS)
    points = [[float(part[0]), float(part[1])] for token in coords.split()
              if len(part := token.split(',')) >= 2]
    if len(points) < 4 or points[0] != points[-1]:
        raise ValueError('Anillo KML incompleto')
    if any(not (-180 <= lon <= 180 and -90 <= lat <= 90) for lon, lat in points):
        raise ValueError('Se esperan coordenadas WGS84')
    return points


def convert(paths):
    features = []
    for event_id, path in paths.items():
        root = ET.parse(path).getroot()
        placemarks = root.findall('.//k:Placemark', NS)
        if len(placemarks) != 1:
            raise ValueError(f'{path}: se espera exactamente un evento')
        placemark = placemarks[0]
        fields = {item.get('name'): item.findtext('k:value', default='', namespaces=NS)
                  for item in placemark.findall('.//k:ExtendedData/k:Data', NS)}
        site, day, area = EVENTS[event_id]
        if (fields.get('Sitio de Referencia (GIMF)', '').casefold() != site.casefold()
                or fields.get('Fecha de Detección') != day
                or fields.get('Área Detectada (ha)') != area):
            raise ValueError(f'{path}: sitio, fecha o área incorrectos')
        polygons = []
        for polygon in placemark.findall('.//k:Polygon', NS):
            exterior = ring(polygon.find('k:outerBoundaryIs', NS))
            holes = [ring(hole) for hole in polygon.findall('k:innerBoundaryIs', NS)]
            polygons.append([exterior, *holes])
        if not polygons:
            raise ValueError(f'{path}: faltan polígonos')
        features.append({'type': 'Feature', 'properties': {
            'event_id': event_id, 'site': site, 'detection_date': day,
            'affected_ha_official': int(area), 'geometry_source': 'IDECOR KML 2024'},
            'geometry': {'type': 'MultiPolygon', 'coordinates': polygons}})
    return {'type': 'FeatureCollection', 'features': features}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--durazno', required=True, type=Path)
    parser.add_argument('--capilla', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=Path('data/private/idecor_eventos_2024.geojson'))
    args = parser.parse_args()
    result = convert({'el_durazno': args.durazno, 'capilla_del_monte': args.capilla})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Guardado {args.output}: ' + ', '.join(
        f"{f['properties']['site']} ({len(f['geometry']['coordinates'])} polígonos)" for f in result['features']))


if __name__ == '__main__':
    main()
