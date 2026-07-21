from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="AI Generated Task API")

class Task(BaseModel):
    title: str
    description: Optional[str] = None

tasks = [{"id": 1, "title": "AI Task", "done": False}]

@app.get("/tasks")
def get_tasks():
    return tasks

@app.post("/tasks", status_code=201)
def create_task(task: Task):
    new_id = len(tasks) + 1
    new_task = {"id": new_id, "title": task.title, "done": False}
    tasks.append(new_task)
    return new_task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    for idx, t in enumerate(tasks):
        if t["id"] == task_id:
            tasks.pop(idx)
            return {"message": "Deleted"}
    raise HTTPException(status_code=404, detail="Not found")