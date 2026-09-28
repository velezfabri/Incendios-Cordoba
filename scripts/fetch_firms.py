"""Fetch VIIRS NOAA-20 historical observations for two focused local date windows.

Credentials: supply FIRMS_MAP_KEY as an environment variable. This script never
prints request URLs, response bodies, or credentials. Raw files are ignored by git.
"""
from __future__ import annotations

import csv
import os
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw_downloads"
API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
SOURCE = "VIIRS_NOAA20_SP"
# Exploratory rectangle only. Geographic attribution later requires official polygons.
BBOX = "-66.0,-35.2,-61.5,-29.2"
WINDOWS = ((date(2024, 9, 2), date(2024, 9, 7)),
           (date(2024, 9, 19), date(2024, 9, 24)))


def fetch(key: str) -> Path:
    if not key or not key.isascii() or not key.isalnum():
        raise ValueError("FIRMS_MAP_KEY ausente o formato inválido")
    rows: list[dict] = []
    fieldnames: list[str] | None = None
    for start, end in WINDOWS:
        cursor = start
        while cursor <= end:
            days = min(5, (end - cursor).days + 1)
            url = f"{API}/{key}/{SOURCE}/{BBOX}/{days}/{cursor.isoformat()}"
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "IncendiosArgentinaResearch/1.0"}), timeout=35) as response:
                    body = response.read(8_000_000).decode("utf-8-sig")
            except urllib.error.HTTPError as error:
                # HTTPError string contains the credential-bearing URL. Never print it.
                raise RuntimeError(f"FIRMS respondió HTTP {error.code}; revisá acceso y fecha") from None
            except (urllib.error.URLError, TimeoutError):
                raise RuntimeError("No se pudo conectar a FIRMS desde esta red") from None
            batch = list(csv.DictReader(body.splitlines()))
            if not batch and (not body.splitlines() or "latitude" not in body.splitlines()[0].lower()):
                raise RuntimeError("La respuesta de FIRMS no es un CSV de detecciones; revisá la clave y la disponibilidad")
            if batch and ("latitude" not in batch[0] or "longitude" not in batch[0] or "acq_date" not in batch[0]):
                raise RuntimeError("FIRMS devolvió columnas inesperadas")
            if batch:
                fieldnames = list(batch[0].keys())
                rows.extend(batch)
            cursor += timedelta(days=days)
    if not rows or not fieldnames:
        raise RuntimeError("La consulta no devolvió observaciones: no se publicará un mapa vacío como resultado")
    OUT.mkdir(parents=True, exist_ok=True)
    destination = OUT / "firms_viirs_noaa20_sp_cordoba_2024_event_windows.csv"
    with destination.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Descargadas {len(rows)} observaciones VIIRS NOAA-20 (rectángulo exploratorio); archivo privado: {destination.name}")
    return destination


if __name__ == "__main__":
    try:
        fetch(os.environ.get("FIRMS_MAP_KEY", ""))
    except (ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
