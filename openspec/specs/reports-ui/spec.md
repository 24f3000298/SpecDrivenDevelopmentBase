# reports-ui Specification

## Purpose
TBD - created by archiving change add-csv-export. Update Purpose after archive.
## Requirements
### Requirement: Reports page lists data from the API
THE system SHALL expose a reports page that displays report rows by calling `GET /reports` with the user’s active filters, sort, and pagination.

#### Scenario: Default view loads first page
- **WHEN** the user opens the reports page
- **THEN** the page SHALL request `GET /reports` with default pagination
- **AND** the page SHALL render the returned items in a table

#### Scenario: User applies filters
- **WHEN** the user sets status and/or date filters and submits
- **THEN** the page SHALL request `GET /reports` with equivalent query parameters
- **AND** the table SHALL show only items from that response

#### Scenario: User changes page
- **WHEN** the user navigates to the next or previous page
- **THEN** the page SHALL request `GET /reports` with updated `offset`
- **AND** the table SHALL reflect the new page

### Requirement: Export CSV button downloads current view
THE system SHALL provide an Export CSV control that downloads CSV for **only the rows currently displayed** on the page.

#### Scenario: Export uses current query parameters
- **WHEN** the user clicks Export CSV while viewing a filtered, sorted, paginated page
- **THEN** the browser SHALL request the CSV export endpoint with the same `status`, `date_from`, `date_to`, `sort`, `descending`, `offset`, and `limit` as the active table request
- **AND** the downloaded file SHALL contain one row per item currently shown in the table

#### Scenario: Export disabled or empty on no rows
- **WHEN** the current page has zero items
- **THEN** the system SHALL NOT download a misleading non-empty export without user acknowledgment
- **AND** the user SHALL receive clear feedback that there is nothing to export

