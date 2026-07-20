from fastapi import FastAPI
from .routers import works, runs

app = FastAPI()
app.include_router(works.router)
app.include_router(runs.router)

@app.get("/")
async def root():
    return {"message": "hello world"}