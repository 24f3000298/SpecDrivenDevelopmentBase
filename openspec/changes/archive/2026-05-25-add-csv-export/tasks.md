## 1. CSV export endpoint

- [x] 1.1 Add a helper (e.g. in `app/export.py` or `app/main.py`) that builds CSV from a list of `ReportPublic` rows using `csv.writer` and RFC 4180 quoting
- [x] 1.2 Add `GET /reports/export.csv` reusing the same query parameters and `query()` + offset/limit slice as `GET /reports`
- [x] 1.3 Set `Content-Type: text/csv; charset=utf-8` and `Content-Disposition: attachment; filename="reports.csv"`
- [x] 1.4 Return HTTP 400 for invalid `sort`, matching JSON list behavior

## 2. Tests for CSV export

- [x] 2.1 Test default export returns 200, CSV header row, and 20 data rows (matching default pagination)
- [x] 2.2 Test `?status=approved&limit=200` — every data row has status `approved`
- [x] 2.3 Test `?limit=5&offset=5` — CSV row count matches JSON page and IDs align
- [x] 2.4 Test CSV body does not contain `internal_id` or `owner_email`
- [x] 2.5 Test invalid `sort` returns 400
- [x] 2.6 Run full pytest suite; existing baseline tests remain green

## 3. Reports UI

- [x] 3.1 Add `app/static/reports.html` with filters (status, dates), sort, page size, prev/next pagination, and table columns matching public fields
- [x] 3.2 Mount static files and add `GET /reports/page` serving the HTML
- [x] 3.3 Wire Export CSV to open/download `GET /reports/export.csv` with the same query string as the active table request
- [x] 3.4 Show user feedback when the current page has zero rows (no silent empty file)

## 4. Documentation and manual check

- [x] 4.1 Update README with `/reports/page` and `/reports/export.csv` endpoints
- [x] 4.2 Manual smoke: uvicorn, filter + paginate, export CSV, confirm row count matches visible table
