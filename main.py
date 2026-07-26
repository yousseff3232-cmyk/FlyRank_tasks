import os
from itertools import count

import psycopg
from psycopg.rows import dict_row
from typing import List
from fastapi import FastAPI , HTTPException , status, Response
from pydantic import BaseModel ,Field
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:dev@localhost:5432/tasks")



app = FastAPI(title= "Task API - Containerized Postgres Edition " ,description= "A production-grade RESTFul API connected to postgreSQL database in Docker ", version= "3.0" )




def get_db_connection():

   return psycopg.connect(DATABASE_URL,row_factory=dict_row)



def init_db():

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
              CREATE TABLE IF NOT EXISTS tasks (
              id SERIAL PRIMARY KEY,
              title TEXT NOT NULL,
              done BOOLEAN NOT NULL DEFAULT False);
            """)

            cursor.execute("SELECT COUNT(*) FROM tasks;")
            count = cursor.fetchone()["count"]

            if count ==0:
                initial_task = [
                    ("Learning FastAPI fundamentals",True),
                    ("Build in-Memory CRUD API " ,True),
                    ("Connect CRUD API to Postgres in Docker" , False)

                ]
            cursor.executemany("INSERT INTO tasks (title, done) VALUES (%s,%s);", initial_task)
        conn.commit()

@app.on_event("startup")
def on_startup():
    init_db()




class TaskCreate(BaseModel):
  title: str = Field(...,min_length=1,
  description = "Task title cannot be empty or blank space")

class TaskUpdate(BaseModel):
    title: str = Field(...,min_length=1, description="Updated task title")
    done:bool

class TaskResponse(BaseModel):
    id: int
    title: str
    done: bool



@app.get("/" , tags=["Metadata"])
def get_api_root():
    return {"name" : "PostgreSQL To-Do API" ,
            "DataBase" : "PostgreSQL",
            "status" : "Active"}


@app.get("/health" , tags=["Metadata"])
def health_check():
    return {"status" : "Healthy" , "database_connected": True }




@app.get("/tasks", response_model= list[TaskResponse], tags=["Tasks"])
def get_all_tasks():
  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute("SELECT id , title , done FROM tasks")
  row = cursor.fetchall()
  conn.close()

  return [
      {"id":row["id"], "title":row["title"], "done":bool(row["done"])}
      for row in row      
  ]

@app.get("/tasks/{task_id}" , response_model=TaskResponse, tags=["Tasks"])
def get_single_task(task_id: int):
  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute("SELECT id , title , done FROM tasks WHERE id = ?", (task_id,))
  row = cursor.fetchone()
  conn.close()

  if row is None:
   raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Task not found")

  return {"id":row["id"], "title":row["title"], "done":bool(row["done"])}


@app.post("/tasks" , response_model=TaskResponse , status_code=status.HTTP_201_CREATED, tags=["Tasks"])
def create_new_task(task_in: TaskCreate):

    clean_title = task_in.title.strip()
    if not clean_title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="VALIDATION ERROR :Title must not be empty or blank space")
    conn= get_db_connection()
    cursor = conn.cursor()


    cursor.execute("INSERT INTO tasks (title, done) VALUES (?,?)", (clean_title,0))
    conn.commit()

    new_id = cursor.lastrowid
    conn.close()

    return {"id": new_id, "title":clean_title, "done":False}



@app.put("/tasks/{task_id}" , response_model=TaskResponse , tags=["Tasks"])
def update_tasks(task_id:int, task_in:TaskUpdate):
    clean_title = task_in.title.strip()
    if not clean_title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail="VALIDATION ERROR :Title must not be empty or blank space")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if cursor.fetchone() is None:
       conn.close()
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Task not found")

    done_int = 1 if task_in.done else 0
    cursor.execute("UPDATE tasks SET title= ? , done=? ,WHERE id = ?", (clean_title,done_int,task_id))
    conn.commit()
    conn.close()

    return {"id":task_id , "title":clean_title, "done":done_int}


@app.delete("/tasks{task_id}" , status_code=status.HTTP_204_NO_CONTENT, tags=["Tasks"])
def delete_task(task_id:int):
  conn = get_db_connection()
  cursor = conn.cursor()


  cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
  conn.commit()


  rows_affected = cursor.rowcount
  conn.close()

  if rows_affected == 0:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Task not found")
  return None