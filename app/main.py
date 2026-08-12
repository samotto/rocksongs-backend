from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import User
from app.routers.auth_routes import router as auth_router
from app.routers.song_routes import router as song_router
from app.routers.user_routes import router as user_router
from app.schemas import HealthResponse


settings = get_settings()
app = FastAPI(title="RockSongs Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    # Running this query verifies that the database connection and users table
    # are available. An empty users table is still considered healthy.
    db.execute(select(User.id).limit(1)).first()
    return HealthResponse(status="ok")


app.include_router(auth_router)
app.include_router(song_router)
app.include_router(user_router)
