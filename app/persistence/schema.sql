-- Storage schema for the tasks table.
-- `order` is a reserved SQL keyword, so the column is `order_index`
-- and the row-to-Task mapping renames it back to `order` in code.

CREATE TABLE IF NOT EXISTS tasks (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_order ON tasks (order_index);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status);
