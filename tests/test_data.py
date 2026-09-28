import sys
import unittest
import csv
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_data import build
import match_firms
from match_firms import inside_polygon, local_date


class SourceRelationships(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build()

    def test_national_missing_remains_null(self):
        rows = self.data["coverage"]
        self.assertEqual(175, len(rows))
        self.assertEqual(150, sum(r["status"] == "no_auditado" for r in rows))
        missing = [r for r in rows if r["year"] == 2024 and r["status"] == "sin_informacion"]
        self.assertEqual(5, len(missing))
        self.assertTrue(all(r["affected_ha"] is None for r in missing))

    def test_cordoba_sources_are_distinct(self):
        national = next(r for r in self.data["jurisdictions2024"] if r["jurisdiction"] == "Córdoba")
        self.assertEqual((582, 103325), (national["reported_fires"], national["affected_ha"]))
        months = self.data["cordobaMonths"]
        self.assertEqual((586, 103327), (sum(r["reported_fires"] for r in months), sum(r["affected_ha"] for r in months)))

    def test_spatial_match_respects_hole_and_local_date(self):
        geometry = {"type": "Polygon", "coordinates": [
            [[-65, -33], [-64, -33], [-64, -32], [-65, -32], [-65, -33]],
            [[-64.7, -32.7], [-64.3, -32.7], [-64.3, -32.3], [-64.7, -32.3], [-64.7, -32.7]],
        ]}
        self.assertTrue(inside_polygon(-64.9, -32.5, geometry))
        self.assertFalse(inside_polygon(-64.5, -32.5, geometry))
        self.assertFalse(inside_polygon(-63.9, -32.5, geometry))
        self.assertEqual("2024-09-02", str(local_date({"acq_date": "2024-09-03", "acq_time": "0100"})))

    def test_full_match_rejects_outside_point(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            shape = directory / "areas.geojson"
            features = []
            for event_id, west, south in (("el_durazno", -64.9, -32.4), ("capilla_del_monte", -64.6, -30.9)):
                features.append({"type": "Feature", "properties": {"event_id": event_id},
                    "geometry": {"type": "Polygon", "coordinates": [[
                        [west, south], [west + .2, south], [west + .2, south + .2], [west, south + .2], [west, south]]]}})
            shape.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
            raw = directory / "firms.csv"
            with raw.open("w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["latitude", "longitude", "acq_date", "acq_time", "confidence"])
                writer.writeheader()
                writer.writerows([
                    {"latitude": -32.3, "longitude": -64.8, "acq_date": "2024-09-03", "acq_time": "0100", "confidence": "n"},
                    {"latitude": -30.8, "longitude": -64.5, "acq_date": "2024-09-19", "acq_time": "1300", "confidence": "h"},
                    {"latitude": -31.8, "longitude": -64.8, "acq_date": "2024-09-03", "acq_time": "0100", "confidence": "n"},
                ])
            original = match_firms.OUT
            try:
                match_firms.OUT = directory / "out"
                result = match_firms.build_matches(raw, shape)
            finally:
                match_firms.OUT = original
            self.assertEqual([1, 1], [len(event["detections"]) for event in result["events"]])
            self.assertEqual("validated_polygon_and_time_match", result["status"])


if __name__ == "__main__":
    unittest.main()
