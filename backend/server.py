from routes.recordRoute import router as record_router
from config.db import Base, engine
from fastapi import FastAPI

app = FastAPI()

app.include_router(record_router, prefix="/api/records", tags=["records"])

@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)


@app.get("/")
def index():
    return {"message": "Hello World"}

