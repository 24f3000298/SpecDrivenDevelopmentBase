"""Tests for CSV export."""

from __future__ import annotations

import csv
import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _parse_csv(body: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(body))
    return list(reader)


def test_export_csv_default_pagination() -> None:
    r = client.get("/reports/export.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert 'filename="reports.csv"' in r.headers.get("content-disposition", "")

    rows = _parse_csv(r.text)
    assert len(rows) == 20
    assert list(rows[0].keys()) == [
        "id",
        "title",
        "status",
        "owner",
        "amount",
        "created_at",
    ]


def test_export_csv_filters_by_status() -> None:
    r = client.get("/reports/export.csv", params={"status": "approved", "limit": 200})
    assert r.status_code == 200
    rows = _parse_csv(r.text)
    assert len(rows) > 0
    assert all(row["status"] == "approved" for row in rows)


def test_export_csv_matches_json_page() -> None:
    params = {"limit": 5, "offset": 5}
    json_page = client.get("/reports", params=params).json()
    csv_rows = _parse_csv(client.get("/reports/export.csv", params=params).text)

    assert len(csv_rows) == len(json_page["items"])
    csv_ids = [int(row["id"]) for row in csv_rows]
    json_ids = [item["id"] for item in json_page["items"]]
    assert csv_ids == json_ids


def test_export_csv_omits_internal_fields() -> None:
    r = client.get("/reports/export.csv", params={"limit": 200})
    assert r.status_code == 200
    assert "internal_id" not in r.text
    assert "owner_email" not in r.text


def test_export_csv_rejects_bad_sort_field() -> None:
    r = client.get("/reports/export.csv", params={"sort": "not_a_field"})
    assert r.status_code == 400
