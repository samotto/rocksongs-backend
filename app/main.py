from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.auth_routes import router as auth_router
from app.routers.song_routes import router as song_router
from app.routers.user_routes import router as user_router
from app.schemas import HealthResponse


settings = get_settings()
app = FastAPI(title="RockSongs Backend")

allowed_origins = [settings.frontend_origin]
if not settings.cookie_secure:
    allowed_origins.extend(["http://127.0.0.1:5173", "http://localhost:5173"])
allowed_origins = list(dict.fromkeys(allowed_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


app.include_router(auth_router)
app.include_router(song_router)
app.include_router(user_router)
