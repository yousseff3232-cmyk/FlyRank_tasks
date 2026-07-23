from contextlib import asynccontextmanager
import sqlite3
from typing import List

from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field

DATABASE = "todo.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                [
                    ("Learn FastAPI", 0),
                    ("Build To-Do API", 1),
                    ("Deploy Project", 0),
                ],
            )
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="SQLite To-Do API", lifespan=lifespan)


class TaskCreate(BaseModel):
    title: str = Field(..., examples=["Buy milk"])


class TaskUpdate(BaseModel):
    title: str
    done: bool


class Task(BaseModel):
    id: int
    title: str
    done: bool


def validate_title(title: str):
    if not title or not title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title cannot be empty.",
        )


@app.get("/tasks", response_model=List[Task])
def get_tasks():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, done FROM tasks ORDER BY id"
        ).fetchall()

    return [
        Task(id=row["id"], title=row["title"], done=bool(row["done"]))
        for row in rows
    ]


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    return Task(
        id=row["id"],
        title=row["title"],
        done=bool(row["done"]),
    )


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    validate_title(task.title)

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (task.title.strip(), 0),
        )
        conn.commit()
        task_id = cursor.lastrowid

        row = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

    return Task(
        id=row["id"],
        title=row["title"],
        done=bool(row["done"]),
    )


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: TaskUpdate):
    validate_title(task.title)

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE tasks
            SET title = ?, done = ?
            WHERE id = ?
            """,
            (task.title.strip(), int(task.done), task_id),
        )

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found.")

        conn.commit()

        row = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

    return Task(
        id=row["id"],
        title=row["title"],
        done=bool(row["done"]),
    )


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,),
        )

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found.")

        conn.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)