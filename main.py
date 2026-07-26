import os
import psycopg
from psycopg.rows import dict_row
from contextlib import asynccontextmanager
from fastapi import FastAPI , HTTPException , status, Response
from pydantic import BaseModel ,Field
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:dev@localhost:5432/tasks")



app = FastAPI(title= "Task API - Containerized Postgres Edition " ,description= "A production-grade RESTFul API connected to postgres SQL database in Docker ", version= "3.0" )




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

@asynccontextmanager
async def lifespan( _app :FastAPI):

    init_db()
    yield


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
   with get_db_connection() as conn:
       with conn.cursor() as cursor:
           cursor.execute("SELECT ID , title , done FROM tasks ORDER BY id ASC;")
           rows = cursor.fetchall()
           return rows


@app.get("/tasks/{task_id}" , response_model=TaskResponse, tags=["Tasks"])
def get_single_task(task_id: int):
   with get_db_connection() as conn:
       with conn.cursor() as cursor:
           cursor.execute("SELECT id , title, done FROM tasks WHERE id = %s;", (task_id,))
           row = cursor.fetchone()


           if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Task not found")
           return row

@app.post("/tasks" , response_model=TaskResponse , status_code=status.HTTP_201_CREATED, tags=["Tasks"])
def create_new_task(task_in: TaskCreate):

    clean_title = task_in.title.strip()
    if not clean_title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="VALIDATION ERROR :Title must not be empty or blank space")

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
           cursor.execute("INSERT INTO tasks (title, done) VALUES (%s,%s) RETURNING id , title , done ;", (clean_title,False) )

        new_task = cursor.fetchone()
        conn.commit()
        return new_task


@app.put("/tasks/{task_id}" , response_model=TaskResponse , tags=["Tasks"])
def update_tasks(task_id:int, task_in:TaskUpdate):
    clean_title = task_in.title.strip()
    if not clean_title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail="VALIDATION ERROR :Title must not be empty or blank space")

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE task SET title = %s WHERE id  = %S RETURNING id , title , done ;", (clean_title, task_in.done ,task_id))
            updated_task = cursor.fetchone()

            if updated_task is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Task not found")
            conn.commit()
            return updated_task




@app.delete("/tasks{task_id}" , status_code=status.HTTP_204_NO_CONTENT, tags=["Tasks"])
def delete_task(task_id:int):
  with get_db_connection() as conn:
      with conn.cursor() as cursor:
          cursor.execute("DELETE FROM tasks WHERE id = %s RETURNING id;", (task_id,))

          deleted_task = cursor.fetchone()

          if deleted_task is None:
              raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Task not found")


          cursor.execute("SELECT COUNT(*) FROM tasks;")
          count = cursor.fetchone()["count"]

          if count == 0:
              cursor.executemany(
                  """
                  INSERT INTO tasks (title, done)
                  VALUES (%s, %s);
                  """,
                  [
                      ("Learn Postgres in Docker", True),
                      ("Environment Variables Setup", True),
                      ("Containerize FastAPI Stack", False),
                  ]
              )

          conn.commit()
          return Response(status_code=status.HTTP_204_NO_CONTENT)


