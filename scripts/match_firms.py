"""Cross historical FIRMS detections with IDECOR event polygons and local dates.

Input GeoJSON must be an authorized export from IDECOR, in WGS84 lon/lat, with
the exact `event_id` values in featured_events_2024.csv assigned after checking
the original event attributes. No proximity-only matching is published.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS_FILE = ROOT / "data" / "source" / "featured_events_2024.csv"
OUT = ROOT / "site" / "data"
UTC_MINUS_3 = timezone(timedelta(hours=-3))


def rings(geometry: dict):
    if geometry["type"] == "Polygon":
        yield from [geometry["coordinates"]]
    elif geometry["type"] == "MultiPolygon":
        yield from geometry["coordinates"]
    else:
        raise ValueError("Solo se aceptan polígonos y multipolígonos")


def inside_ring(lon: float, lat: float, ring: list) -> bool:
    hit = False
    for index in range(len(ring)):
        x1, y1 = ring[index - 1][:2]
        x2, y2 = ring[index][:2]
        if (y1 > lat) != (y2 > lat):
            crossing = (x2 - x1) * (lat - y1) / (y2 - y1) + x1
            if lon < crossing:
                hit = not hit
    return hit


def inside_polygon(lon: float, lat: float, geometry: dict) -> bool:
    for polygon in rings(geometry):
        if polygon and inside_ring(lon, lat, polygon[0]):
            if not any(inside_ring(lon, lat, hole) for hole in polygon[1:]):
                return True
    return False


def load_polygons(path: Path, events: dict) -> dict[str, list[dict]]:
    collection = json.loads(path.read_text(encoding="utf-8"))
    if collection.get("type") != "FeatureCollection" or not collection.get("features"):
        raise ValueError("Se requiere un GeoJSON FeatureCollection con polígonos oficiales")
    polygons = {event_id: [] for event_id in events}
    for feature in collection["features"]:
        event_id = feature.get("properties", {}).get("event_id")
        if event_id not in polygons:
            raise ValueError("El GeoJSON contiene un event_id desconocido o faltante")
        geometry = feature["geometry"]
        coordinates = [point for polygon in rings(geometry) for ring in polygon for point in ring]
        if not coordinates or any(len(p) < 2 or not (-180 <= p[0] <= 180 and -90 <= p[1] <= 90) for p in coordinates):
            raise ValueError("Las coordenadas deben estar en WGS84 [longitud, latitud]")
        polygons[event_id].append(geometry)
    if any(not parts for parts in polygons.values()):
        raise ValueError("Falta el polígono de al menos un evento seleccionado")
    return polygons


def local_date(row: dict) -> date:
    utc_date = date.fromisoformat(row["acq_date"])
    time = row.get("acq_time", "0").strip().zfill(4)
    hour, minute = int(time[:2]), int(time[2:])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("Hora de observación fuera de rango")
    instant = datetime(utc_date.year, utc_date.month, utc_date.day, hour, minute, tzinfo=timezone.utc)
    return instant.astimezone(UTC_MINUS_3).date()


def build_matches(raw_path: Path, polygons_path: Path) -> dict:
    with EVENTS_FILE.open(encoding="utf-8", newline="") as file:
        events = {row["event_id"]: row for row in csv.DictReader(file)}
    geometries = load_polygons(polygons_path, events)
    with raw_path.open(encoding="utf-8-sig", newline="") as file:
        detections = list(csv.DictReader(file))
    if not detections:
        raise ValueError("CSV FIRMS vacío")
    required = {"latitude", "longitude", "acq_date", "acq_time", "confidence"}
    if not required.issubset(detections[0]):
        raise ValueError("Faltan columnas obligatorias en FIRMS")
    seen = set()
    featured = []
    for event_id, event in events.items():
        matches = []
        start, end = date.fromisoformat(event["start_local"]), date.fromisoformat(event["end_local"])
        for row in detections:
            lon, lat = float(row["longitude"]), float(row["latitude"])
            if not (-66 <= lon <= -61.5 and -35.2 <= lat <= -29.2):
                continue
            observed = local_date(row)
            if not start <= observed <= end:
                continue
            if not any(inside_polygon(lon, lat, geometry) for geometry in geometries[event_id]):
                continue
            key = (event_id, row["acq_date"], row["acq_time"], row["latitude"], row["longitude"], row.get("satellite", ""))
            if key in seen:
                continue
            seen.add(key)
            matches.append({"lon": lon, "lat": lat, "date_utc": row["acq_date"], "time_utc": row["acq_time"].zfill(4),
                "date_local": observed.isoformat(), "confidence": row["confidence"], "frp_mw": row.get("frp", ""),
                "satellite": row.get("satellite", "")})
        matches.sort(key=lambda r: (r["date_utc"], r["time_utc"], r["lat"], r["lon"]))
        featured.append({"id": event_id, "site": event["site"], "start_local": event["start_local"],
            "end_local": event["end_local"], "affected_ha_official": int(event["area_ha"]),
            "geometries": geometries[event_id], "detections": matches})
    result = {"status": "validated_polygon_and_time_match", "source": "NASA FIRMS VIIRS NOAA-20 SP",
        "geometry_source": "IDECOR Áreas Afectadas por Incendios 2024 (exportación revisada)",
        "note": "Puntos dentro del polígono final y durante los cinco primeros días locales. No prueban causa ni representan incidentes o hectáreas.",
        "events": featured}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "thermal_matches.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (OUT / "detecciones_verificadas_2024.csv").open("w", encoding="utf-8", newline="") as file:
        fields = ("event_id", "date_local", "date_utc", "time_utc", "latitude", "longitude", "confidence", "frp_mw", "satellite")
        writer = csv.DictWriter(file, fieldnames=fields); writer.writeheader()
        for event in featured:
            for row in event["detections"]:
                writer.writerow({"event_id": event["id"], "date_local": row["date_local"], "date_utc": row["date_utc"],
                    "time_utc": row["time_utc"], "latitude": row["lat"], "longitude": row["lon"],
                    "confidence": row["confidence"], "frp_mw": row["frp_mw"], "satellite": row["satellite"]})
    return result


def main():
    parser = argparse.ArgumentParser(description="Cruzar NASA FIRMS con polígonos IDECOR verificados")
    parser.add_argument("--raw", type=Path, required=True, help="CSV de FIRMS, fuera de git")
    parser.add_argument("--polygons", type=Path, required=True, help="GeoJSON oficial etiquetado, fuera de git")
    args = parser.parse_args()
    output = build_matches(args.raw, args.polygons)
    for item in output["events"]:
        print(f"{item['site']}: {len(item['detections'])} observaciones satelitales dentro del polígono y período")


if __name__ == "__main__":
    main()
