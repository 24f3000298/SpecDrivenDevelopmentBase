## ADDED Requirements

### Requirement: Add-task form

The TODO view SHALL render an HTML `<form>` on the index page with `method="POST"` posting to a `POST /tasks` route. The form MUST contain:

- A single text input with `name="title"`, `required`, `maxlength="200"`.
- A submit button.

The route handler MUST:

- Trim leading/trailing whitespace from the submitted title.
- Reject submissions whose trimmed title is empty (return to the index page with an inline error message; do NOT create a task).
- On success, create the task via `TaskService.add_task` and redirect (HTTP 303 See Other) back to the index page (Post/Redirect/Get pattern) so that browser refresh does not double-submit.

The view MUST NOT call the repository or execute SQL directly — only the service.

#### Scenario: Adding a task via form submit

- **WHEN** the user submits the form with `title="Write spec"`
- **THEN** the server creates a task with `title="Write spec"`, `status="todo"`, and redirects to `GET /` where the new task is rendered at the bottom of the list

#### Scenario: Empty submission is rejected

- **WHEN** the user submits the form with `title="   "` (whitespace only)
- **THEN** no task is created, the response renders the index page again with an inline validation message, and the form retains usable focus order

#### Scenario: Refresh after add does not duplicate

- **WHEN** the user adds a task, the browser follows the 303 redirect, and the user presses the browser's refresh button
- **THEN** no duplicate task is created (the refresh re-fetches `GET /`, not the POST)

### Requirement: Task list display

The TODO view SHALL render the current set of tasks on `GET /` as a vertical list, ordered by `status == "done"` last and `order` ascending within each group. Each row MUST display:

- A toggle-complete control: a form with `method="POST"` posting to `POST /tasks/<id>/toggle` and a submit button whose label/state reflects whether the task is done.
- The task title. Completed tasks MUST be visually de-emphasized via a CSS class (e.g. `task--done` applies strike-through and muted color).
- A delete control: a form with `method="POST"` posting to `POST /tasks/<id>/delete` and a submit button.

For v1, tasks with statuses other than `"todo"` or `"done"` SHALL be rendered in the pending group; they MUST NOT be hidden or dropped.

All state-changing actions MUST use POST forms (not GET links) so they are not triggered by prefetchers or `<a>` hover behavior.

#### Scenario: Toggle moves task between groups

- **WHEN** the user submits the toggle form on a `"todo"` task
- **THEN** the server updates the task to `status="done"`, redirects to `GET /`, and the rendered list shows the task in the de-emphasized "done" group below the still-pending tasks

#### Scenario: Deleting a task

- **WHEN** the user submits the delete form for a task
- **THEN** the server removes the task via `TaskService.delete_task`, redirects to `GET /`, and the task no longer appears in the rendered list

#### Scenario: Unknown status renders gracefully

- **WHEN** `GET /` is requested while a task with `status="in-progress"` exists
- **THEN** the row renders in the pending group with no template error, and its toggle/delete forms still work

### Requirement: Empty state

The TODO view SHALL render a friendly empty-state block (short message) when no tasks exist. The empty state MUST disappear as soon as the first task is added.

#### Scenario: First-run empty state

- **WHEN** the app is loaded with no tasks in the database
- **THEN** the index page shows the empty-state message instead of an empty list element

#### Scenario: Empty state disappears on add

- **WHEN** the user adds the first task and the browser follows the redirect to `GET /`
- **THEN** the empty state is no longer present and the list shows the new task

### Requirement: Accessibility baseline

The TODO view SHALL meet a minimum accessibility baseline:

- The add-task input has an associated `<label>` (visible or visually hidden but present in the accessibility tree via `for=`/`id=` pairing).
- Each toggle button has an accessible name describing the task and the resulting action (e.g. "Mark 'Buy milk' as done" / "Mark 'Buy milk' as not done").
- Each delete button has an accessible name (e.g. "Delete 'Buy milk'").
- Validation messages from rejected submissions are programmatically associated with the offending input (`aria-describedby` or rendered inside the same `<label>`).
- Focus order is logical: skip-link → main heading → add-task input → list items in display order.

#### Scenario: Screen reader can identify delete buttons

- **WHEN** a screen reader user navigates to the delete button of a task titled "Buy milk"
- **THEN** the announced name unambiguously identifies which task will be deleted (e.g. "Delete 'Buy milk'")

### Requirement: Template structure for forward compatibility

The TODO view SHALL be rendered via Jinja templates organized so that a future board view can be added without modifying the TODO templates. Specifically:

- A `templates/base.html` defines the page skeleton (`<head>`, header, main slot, footer) and is shared across views.
- TODO-specific templates live under `templates/todo/` (e.g. `templates/todo/index.html`, `templates/todo/_task_row.html`).
- The `_task_row.html` partial renders a single task and is the unit that a future board column will reuse to render cards.

The TODO route handlers SHALL live in a Flask blueprint named `todo` registered at the root URL prefix. A future `board` blueprint will register at `/board` without touching the `todo` blueprint.

#### Scenario: TODO and Board can coexist

- **WHEN** a future change registers a `board` blueprint
- **THEN** no file under `app/todo/` or `templates/todo/` needs to be modified for the two views to coexist
