"""FastAPI HTTP layer for the Reports app."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app.export import reports_to_csv
from app.models import ReportListResponse, ReportPublic, ReportStatus
from app.reports import query

_STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="SDD Workshop — Reports API", version="0.1.0")
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


def _paginated_public_reports(
    *,
    status: ReportStatus | None,
    date_from: datetime | None,
    date_to: datetime | None,
    sort: str,
    descending: bool,
    offset: int,
    limit: int,
) -> tuple[list[ReportPublic], int]:
    try:
        rows = query(
            status=status,
            date_from=date_from,
            date_to=date_to,
            sort=sort,
            descending=descending,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    page = rows[offset : offset + limit]
    return [ReportPublic.from_internal(r) for r in page], len(rows)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/reports/page", include_in_schema=False)
def reports_page() -> FileResponse:
    """Reports UI with filters, pagination, and CSV export."""

    return FileResponse(_STATIC_DIR / "reports.html")


@app.get("/reports", response_model=ReportListResponse)
def list_reports(
    status: ReportStatus | None = Query(None, description="Filter by status"),
    date_from: datetime | None = Query(None, description="Lower bound on created_at (inclusive)"),
    date_to: datetime | None = Query(None, description="Upper bound on created_at (inclusive)"),
    sort: str = Query("created_at", description="Sort field"),
    descending: bool = Query(True, description="Sort descending"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
) -> ReportListResponse:
    """Return a paginated list of reports.

    Public fields only — `internal_id` and `owner_email` are stripped via
    `ReportPublic.from_internal`.
    """

    items, total = _paginated_public_reports(
        status=status,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        descending=descending,
        offset=offset,
        limit=limit,
    )
    return ReportListResponse(items=items, total=total, offset=offset, limit=limit)


@app.get("/reports/export.csv")
def export_reports_csv(
    status: ReportStatus | None = Query(None, description="Filter by status"),
    date_from: datetime | None = Query(None, description="Lower bound on created_at (inclusive)"),
    date_to: datetime | None = Query(None, description="Upper bound on created_at (inclusive)"),
    sort: str = Query("created_at", description="Sort field"),
    descending: bool = Query(True, description="Sort descending"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
) -> Response:
    """Export the current page of reports as RFC 4180 CSV."""

    items, _ = _paginated_public_reports(
        status=status,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        descending=descending,
        offset=offset,
        limit=limit,
    )
    return Response(
        content=reports_to_csv(items),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="reports.csv"'},
    )
