import os
import psycopg
from psycopg.rows import dict_row
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Response
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:dev@db:5432/tasks")


def get_db():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            # 1. Create table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN DEFAULT FALSE
                );
            """)

            # 2. Seed-once check
            cur.execute("SELECT COUNT(*) FROM tasks;")
            count = cur.fetchone()["count"]

            if count == 0:
                cur.executemany(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s);",
                    [
                        ("AI Seed Task 1", False),
                        ("AI Seed Task 2", True),
                        ("AI Seed Task 3", False)
                    ]
                )
            conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI Generated Containerized Task API", lifespan=lifespan)


class TaskSchema(BaseModel):
    title: str


class TaskUpdateSchema(BaseModel):
    title: str
    done: bool


# --- Endpoints ---

@app.get("/tasks", status_code=status.HTTP_200_OK)
def get_tasks():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks ORDER BY id ASC;")
            return cur.fetchall()


@app.get("/tasks/{task_id}", status_code=status.HTTP_200_OK)
def get_task(task_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks WHERE id = %s;", (task_id,))
            task = cur.fetchone()
            if not task:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
            return task


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskSchema):
    # Notice: AI version checked title length but forgot .strip() validation
    if not payload.title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title cannot be empty")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, FALSE) RETURNING id, title, done;",
                (payload.title,)
            )
            new_task = cur.fetchone()
            conn.commit()
            return new_task


@app.put("/tasks/{task_id}", status_code=status.HTTP_200_OK)
def update_task(task_id: int, payload: TaskUpdateSchema):
    if not payload.title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title cannot be empty")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id, title, done;",
                (payload.title, payload.done, task_id)
            )
            updated = cur.fetchone()
            if not updated:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
            conn.commit()
            return updated


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id;", (task_id,))
            deleted = cur.fetchone()
            if not deleted:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
            conn.commit()
            return Response(status_code=status.HTTP_204_NO_CONTENT)