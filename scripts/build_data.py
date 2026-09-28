"""Build the audited, dependency-free static data snapshot."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "source"
OUTPUT = ROOT / "site" / "data"


def read_csv(name: str) -> list[dict]:
    with (SOURCE / name).open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def unique(rows: list[dict], field: str) -> None:
    keys = [row[field] for row in rows]
    assert len(keys) == len(set(keys)), f"Duplicado en {field}"


def integers(rows: list[dict], fields: tuple[str, ...]) -> list[dict]:
    for row in rows:
        for field in fields:
            row[field] = int(row[field]) if row[field] else None
            assert row[field] is None or row[field] >= 0, f"Negativo: {row}"
    return rows


def write_csv(name: str, rows: list[dict], fields: tuple[str, ...]) -> None:
    with (OUTPUT / name).open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build() -> dict:
    years = integers(read_csv("national_years_2018_2024.csv"), ("year", "reported_fires", "affected_ha", "source_page"))
    jurisdictions = integers(read_csv("national_jurisdictions_2024.csv"),
        ("reported_fires", "affected_ha", "native_forest_ha", "cultivated_forest_ha", "shrubland_ha", "grassland_ha", "undetermined_ha"))
    months = integers(read_csv("cordoba_months_2024.csv"), ("month", "reported_fires", "affected_ha"))
    departments = integers(read_csv("cordoba_departments_2024.csv"), ("department_fire_records", "affected_ha"))

    for rows, key in ((years, "year"), (jurisdictions, "jurisdiction"), (months, "month"), (departments, "department")):
        unique(rows, key)
    assert [r["year"] for r in years] == list(range(2018, 2025))
    assert [r["month"] for r in months] == list(range(1, 13))
    assert len(jurisdictions) == 25 and len(departments) == 26
    assert sum(r["status"] == "sin_informacion" for r in jurisdictions) == 5
    for row in jurisdictions:
        if row["status"] == "sin_informacion":
            assert row["reported_fires"] is row["affected_ha"] is None
        else:
            assert row["status"] == "reportado" and row["reported_fires"] is not None and row["affected_ha"] is not None
    national_2024 = years[-1]
    assert (national_2024["reported_fires"], national_2024["affected_ha"]) == (5175, 392277)
    assert sum(r["reported_fires"] or 0 for r in jurisdictions) == 5175
    # Published component hectares are rounded independently in the national table.
    assert abs(sum(r["affected_ha"] or 0 for r in jurisdictions) - 392277) <= 1
    assert next(r for r in jurisdictions if r["jurisdiction"] == "Córdoba")["affected_ha"] == 103325
    assert next(r for r in jurisdictions if r["jurisdiction"] == "Parques Nacionales")["reported_fires"] == 104
    assert (sum(r["reported_fires"] for r in months), sum(r["affected_ha"] for r in months)) == (586, 103327)
    assert next(r for r in months if r["month"] == 9)["affected_ha"] == 78298
    assert (sum(r["department_fire_records"] for r in departments), sum(r["affected_ha"] for r in departments)) == (606, 103327)

    coverage = []
    for year in range(2018, 2025):
        for jurisdiction in jurisdictions:
            audited = year == 2024
            coverage.append({"year": year, "jurisdiction": jurisdiction["jurisdiction"],
                "status": jurisdiction["status"] if audited else "no_auditado",
                "reported_fires": jurisdiction["reported_fires"] if audited else None,
                "affected_ha": jurisdiction["affected_ha"] if audited else None})

    payload = {
        "metadata": {"snapshot": "2026-09-28", "year_scope": "2018–2024: total nacional reportado; jurisdicciones auditadas solo 2024",
            "national_source": "Anuario de Estadística Forestal, edición 2025, capítulo 4",
            "cordoba_source": "DirGR e IDECOR, Informe Anual 2024, febrero 2025",
            "national_coverage_2024": "19 provincias/CABA informaron; 5 sin información; Parques Nacionales separado",
            "national_rounding_ha": 1,
            "cordoba_report_pdf_typo": "Resumen: 103.237 ha; tablas y cuerpo: 103.327 ha"},
        "nationalYears": years, "jurisdictions2024": jurisdictions, "cordobaMonths": months,
        "cordobaDepartments": departments, "coverage": coverage,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "analysis.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv("argentina_anual_2018_2024.csv", years, ("year", "reported_fires", "affected_ha", "source_page"))
    write_csv("cobertura_jurisdicciones_2018_2024.csv", coverage, ("year", "jurisdiction", "status", "reported_fires", "affected_ha"))
    write_csv("cordoba_mensual_2024.csv", months, ("month", "month_name", "reported_fires", "affected_ha"))
    write_csv("cordoba_departamentos_2024.csv", departments, ("department", "department_fire_records", "affected_ha"))
    print("Datos validados y publicados en site/data/")
    return payload


if __name__ == "__main__":
    build()
