from fastapi import FastAPI


app = FastAPI()


@app.get("/hello")
async def hello_server():
    return {"message": "Hello from Fly Rank server!" }