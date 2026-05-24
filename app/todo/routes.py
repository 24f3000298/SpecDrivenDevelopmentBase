"""HTTP routes for the TODO view.

All mutations are POST + 303 redirect (Post/Redirect/Get). Empty-title
submissions re-render the index with HTTP 400 and an inline error message.
"""

from __future__ import annotations

from typing import cast

from flask import (
    abort,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.wrappers.response import Response

from app.domain import STATUS_DONE, STATUS_TODO, InvalidTaskError
from app.services import TaskNotFoundError, TaskService
from app.todo import bp


def _service() -> TaskService:
    return cast(TaskService, current_app.extensions["task_service"])


@bp.get("/")
def index() -> str:
    tasks = _service().list_tasks()
    return render_template("todo/index.html", tasks=tasks, error=None, draft="")


@bp.post("/tasks")
def add_task() -> Response | tuple[str, int]:
    raw_title = request.form.get("title", "")
    try:
        _service().add_task(title=raw_title)
    except InvalidTaskError as exc:
        tasks = _service().list_tasks()
        return (
            render_template("todo/index.html", tasks=tasks, error=str(exc), draft=raw_title),
            400,
        )
    return redirect(url_for("todo.index"), code=303)


@bp.post("/tasks/<task_id>/toggle")
def toggle_task(task_id: str) -> Response:
    svc = _service()
    current = svc.repo.get(task_id)
    if current is None:
        abort(404)
    new_status = STATUS_TODO if current.status == STATUS_DONE else STATUS_DONE
    try:
        svc.update_task(task_id, status=new_status)
    except TaskNotFoundError:
        abort(404)
    return redirect(url_for("todo.index"), code=303)


@bp.post("/tasks/<task_id>/delete")
def delete_task(task_id: str) -> Response:
    _service().delete_task(task_id)
    return redirect(url_for("todo.index"), code=303)
