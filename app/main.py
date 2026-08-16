from fastapi import FastAPI
from .routers import works, runs

app = FastAPI()
app.include_router(works.router, prefix="/api")
app.include_router(runs.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "hello world"}
