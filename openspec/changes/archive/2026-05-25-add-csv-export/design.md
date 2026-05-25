## Context

The Reports app is a FastAPI service with an in-memory dataset and a `GET /reports` JSON endpoint. Filtering, sorting, and pagination live in `app/reports.py` and are reused by the HTTP layer. There is no UI today. Project conventions require RFC 4180 CSV via the standard-library `csv` module and never exposing `internal_id` or `owner_email` in user-facing output.

The PM request is narrow: a CSV export button on the reports page that downloads **what is currently showing** (the active page after filters/sort), not the entire matching result set.

## Goals / Non-Goals

**Goals:**

- Serve a reports page where users can filter, sort, and paginate the same data as `GET /reports`.
- Provide `GET /reports/export.csv` (or equivalent) accepting the **same query parameters** as `GET /reports`, returning only the current page as CSV.
- Wire the page’s Export CSV control to that endpoint with the page’s current query string.
- Cover CSV behavior with pytest (status, headers, row count, filters, no internal fields).

**Non-Goals:**

- Exporting all rows matching filters across pages (full-dataset export).
- Excel (`.xlsx`) or other formats.
- Authentication, rate limiting, or async job-based exports.
- Changing the JSON list contract or seed data.

## Decisions

### 1. Server-side CSV endpoint (not browser-only generation)

**Choice:** Add `GET /reports/export.csv` that reuses `query()` and applies the same `offset`/`limit` slice as JSON.

**Rationale:** Keeps export logic testable in pytest, enforces RFC 4180 and field redaction in one place, and matches project style conventions. The UI stays thin: it forwards the current query params.

**Alternative considered:** Client-side CSV from the JSON already loaded — simpler but duplicates column rules, harder to test for RFC 4180 and field omission, and drifts from backend conventions.

### 2. “Currently showing” = current page only

**Choice:** CSV row count equals `limit` (or fewer on the last page); `offset`/`limit` are required semantics identical to JSON.

**Rationale:** Matches the PM wording and avoids surprise multi-megabyte downloads.

**Alternative considered:** `export=all` flag — rejected as out of scope.

### 3. Static HTML page served by FastAPI

**Choice:** `GET /reports/page` returns `app/static/reports.html`; mount `/static` for assets if needed.

**Rationale:** No new frontend toolchain; fits workshop scope. Page calls existing JSON for the table and CSV endpoint for download.

**Alternative considered:** Separate SPA repo — unnecessary for this exercise.

### 4. CSV columns mirror `ReportPublic`

**Choice:** Header row: `id`, `title`, `status`, `owner`, `amount`, `created_at` (ISO 8601 for datetime).

**Rationale:** Aligns with documented public JSON fields; `internal_id` and `owner_email` never appear.

### 5. Response headers

**Choice:** `Content-Type: text/csv; charset=utf-8` and `Content-Disposition: attachment; filename="reports.csv"`.

**Rationale:** Browsers trigger download; charset is explicit.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Users expect “export all filtered rows” | UI label “Export CSV” with tooltip or summary text clarifying current page; spec scenarios document page scope. |
| Duplicate query-param parsing between JSON and CSV routes | Extract shared dependency or helper in `main.py` that builds filter args once. |
| CSV injection if titles contain `=cmd` | Prefix risky cell values per RFC 4180 quoting; use `csv.writer` with `quoting=csv.QUOTE_MINIMAL`. |
| Static files omitted from package install | Ship HTML under `app/static/` and reference via `Path(__file__)`; document in README. |

## Migration Plan

1. Implement CSV route and tests (baseline tests stay green).
2. Add static page and page route.
3. Manual smoke: run uvicorn, open `/reports/page`, filter, paginate, export, open CSV in a spreadsheet app.
4. After merge, `openspec archive add-csv-export` to fold deltas into `openspec/specs/`.

Rollback: remove new routes and static files; no data migration.

## Open Questions

- None blocking implementation. Filename could include date stamp later if product wants it.
