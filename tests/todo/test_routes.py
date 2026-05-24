from __future__ import annotations

from flask.testing import FlaskClient

from app.persistence import InMemoryTaskRepository
from app.services import TaskService


def test_index_empty_renders_empty_state(client: FlaskClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Nothing to do yet" in resp.data


def test_add_task_happy_path(client: FlaskClient, repo: InMemoryTaskRepository) -> None:
    resp = client.post("/tasks", data={"title": "Write spec"})
    assert resp.status_code == 303
    assert resp.headers["Location"].endswith("/")

    # Follow the redirect.
    followed = client.get("/")
    assert b"Write spec" in followed.data

    listed = repo.list()
    assert len(listed) == 1
    assert listed[0].title == "Write spec"
    assert listed[0].status == "todo"


def test_add_task_trims_whitespace(client: FlaskClient, repo: InMemoryTaskRepository) -> None:
    client.post("/tasks", data={"title": "  spaces  "})
    listed = repo.list()
    assert listed[0].title == "spaces"


def test_add_task_empty_title_is_400_with_inline_error(
    client: FlaskClient, repo: InMemoryTaskRepository
) -> None:
    resp = client.post("/tasks", data={"title": "   "})
    assert resp.status_code == 400
    assert b"non-empty" in resp.data or b"Nothing to do yet" in resp.data
    # Importantly: no task was created.
    assert repo.list() == []


def test_toggle_task_flips_status(client: FlaskClient, service: TaskService) -> None:
    t = service.add_task(title="toggle me")

    resp = client.post(f"/tasks/{t.id}/toggle")
    assert resp.status_code == 303

    after = client.get("/").data
    # The completed task is rendered in the done group with the task--done class.
    assert b"task--done" in after
    assert b"toggle me" in after


def test_toggle_task_flips_back(client: FlaskClient, service: TaskService) -> None:
    t = service.add_task(title="toggle twice")
    client.post(f"/tasks/{t.id}/toggle")
    client.post(f"/tasks/{t.id}/toggle")

    # After two toggles, the task should not be in the done group anymore.
    body = client.get("/").data
    assert b"toggle twice" in body
    # The "Done" heading should not be present if there are no done tasks.
    assert b"task-list--done" not in body


def test_toggle_missing_task_404(client: FlaskClient) -> None:
    resp = client.post("/tasks/nonexistent/toggle")
    assert resp.status_code == 404


def test_delete_task_removes_it(client: FlaskClient, service: TaskService) -> None:
    t = service.add_task(title="delete me")

    resp = client.post(f"/tasks/{t.id}/delete")
    assert resp.status_code == 303

    body = client.get("/").data
    assert b"delete me" not in body


def test_delete_missing_is_ok(client: FlaskClient) -> None:
    # Service silently no-ops; route should still redirect.
    resp = client.post("/tasks/nonexistent/delete")
    assert resp.status_code == 303


def test_unknown_status_renders_in_pending(
    client: FlaskClient, service: TaskService
) -> None:
    t = service.add_task(title="weird status")
    service.update_task(t.id, status="in-progress")

    resp = client.get("/")
    assert resp.status_code == 200
    assert b"weird status" in resp.data
    # The "Done" heading must not appear (only an unknown-status pending task).
    assert b"task-list--done" not in resp.data


def test_404_handler(client: FlaskClient) -> None:
    resp = client.get("/no-such-route")
    assert resp.status_code == 404
    assert b"404" in resp.data
    assert b"Not found" in resp.data
