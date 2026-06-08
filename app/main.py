from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.auth_routes import router as auth_router
from app.routers.song_routes import router as song_router
from app.schemas import HealthResponse


settings = get_settings()
app = FastAPI(title="RockSongs Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


app.include_router(auth_router)
app.include_router(song_router)
