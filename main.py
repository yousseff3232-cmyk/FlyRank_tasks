from fastapi import FastAPI , HTTPException
from pydantic import BaseModel
from typing import Optional

from starlette import status

app = FastAPI()


class TaskCreate(BaseModel):
  title: str
  description: Optional[str] = None

tasks_db =[

    {"id":1 , "title": "go to the gym today" ,"done": False},
    {"id":2 , "title": "Finish FlyRank task" , "done":True},
    {"id":3 , "title": "Study MySql with BroCode Course " , "done": False}

]

@app.get("/")
async def get_api_root():
    return {"name" : "Task API" ,
            "version" : "1.0",
            "endpoints" : ["/tasks"]}


@app.get("/health")
async def get_health():
    return {"status" : "ok"}
@app.get("/tasks")
async def get_tasks():
    return tasks_db


@app.get("/tasks/{task_id}")
async def get_single_task(task_id: int):

  for task in tasks_db:
      if task["id"] == task_id:
          return task

  raise HTTPException(status_code=404, detail="Task not found")


@app.post("/tasks" , status_code=status.HTTP_201_CREATED)
async def create_new_task(task_payload: TaskCreate):

    if not task_payload.title.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="VALIDATION ERROR :Title must not be empty or blank space")


    new_id = max(task["id"] for task in tasks_db)+1 if tasks_db else 1
    new_task= {
        "id":new_id,
        "title":task_payload.title.strip(),
        "done":False

}


    tasks_db.append(new_task)
    return new_task