from fastapi import FastAPI
from .routers import works

app = FastAPI()
app.include_router(works.router)

@app.get("/")
async def root():
    return {"message": "hello world"}