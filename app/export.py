"""CSV export helpers."""

from __future__ import annotations

import csv
import io

from app.models import ReportPublic

CSV_COLUMNS = ("id", "title", "status", "owner", "amount", "created_at")


def reports_to_csv(items: list[ReportPublic]) -> str:
    """Serialize public report rows to RFC 4180 CSV."""

    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n")
    writer.writerow(CSV_COLUMNS)
    for item in items:
        writer.writerow(
            [
                item.id,
                item.title,
                item.status,
                item.owner,
                item.amount,
                item.created_at.isoformat(),
            ]
        )
    return buf.getvalue()
