from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.database as db_module
from app.routers import songs


@asynccontextmanager
async def lifespan(application: FastAPI):
    db_module.Base.metadata.create_all(bind=db_module.engine)
    yield


app = FastAPI(
    title="Rock Songs API",
    description="A CRUD service for managing rock songs",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(songs.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
