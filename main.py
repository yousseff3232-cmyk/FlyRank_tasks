import sqlite3
from fastapi import FastAPI , HTTPException
from pydantic import BaseModel ,Field
from typing import List , Optional
from starlette import status
from starlette.responses import Response

app = FastAPI(title= "Task API - SQLite Edition " , description= "A production-grade RESTFul API connected to SQLite" , version="2.0")


DB_NAME = "tasks.db"




def get_db_connection():

    row_factory = sqlite3.Row

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn




def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(""" CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL , done INTEGER DEFAULT 0 )""")


    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]




    if count == 0:
        initial_task = [
            ("Learning FastAPI fundamentals",1),
            ("Build in-Memory CRUD API " ,1),
            ("Connect CRUD API toSQLite Database",0)
        ]
        cursor.executemany("INSERT INTO tasks (title, done) VALUES (?,?)", initial_task)
        conn.commit()
    conn.close()

@app.on_event("startup")
def on_startup():
    init_db()




class TaskCreate(BaseModel):
  title: str = Field(...,min_length=1,
  description = "Task title cannot be empty")

class TaskUpdate(BaseModel):
    title: str = Field(...,min_length=1, description="Updated task title")
    done:bool

@app.get("/" , tags=["Metadata"])
def get_api_root():
    return {"name" : "SQlite To-Do API" ,
            "DataBase" : "DB_NAME",
            "status" : "active"}


@app.get("/health" , tags=["Metadata"])
def health_check():
    return {"status" : "Healthy" , "database_connected": True }




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

@app.put("/tasks/{task_id}")
async def update_tasks(task_id:int, task_payload:TaskUpdate):
    for task in tasks_db:
        if task["id"] == task_id:

            if task_payload.title is not None:
                if not task_payload.title.strip():
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "Validation ERROR : title cannot be empty or blank space")
        task["title"] = task_payload.title.strip()

        if task_payload.done is not None:
            task["done"] = task_payload.done
        return task


    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Task not found")



@app.delete("/tasks{task_id" , status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id:int):

    for index , task in enumerate(tasks_db):
        if task["id"] == task_id:
            tasks_db.pop(index)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Task not found")