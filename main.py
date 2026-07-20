from fastapi import FastAPI , HTTPException


app = FastAPI()


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