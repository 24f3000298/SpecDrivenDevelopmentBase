## Why

Users reviewing reports in the app need to pull the current table view into a spreadsheet for offline analysis, sharing with stakeholders, or reconciliation. Today the API only returns JSON; there is no way to download what they are looking at without manual copy-paste.

## What Changes

- Add a **Reports** web page that lists reports with the same filters, sort, and pagination as `GET /reports`.
- Add an **Export CSV** control on that page that downloads a CSV file for **only the rows currently visible** (the active page), not the full filtered dataset.
- Add a server-side CSV export endpoint that accepts the same query parameters as `GET /reports` and returns RFC 4180 CSV with public fields only.
- Add automated tests for the CSV endpoint (format, pagination scope, filters, and absence of internal fields).

## Capabilities

### New Capabilities

- `reports-ui`: Browser UI for browsing and paginating reports, including an export action tied to the current view.

### Modified Capabilities

- `reports`: Extend the Reports capability with a CSV export endpoint that mirrors list filters, sort, and pagination, and never exposes internal fields.

## Impact

- `app/main.py` — new CSV route and reports page route; static assets for the UI.
- `app/reports.py` — reuse existing query layer (no behavioral change expected).
- `app/models.py` — possible shared serialization helpers for CSV rows.
- `tests/test_reports.py` — new cases for CSV export.
- `openspec/specs/reports/spec.md` — folded in after archive via delta from this change.
