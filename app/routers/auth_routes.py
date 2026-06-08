from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, verify_password
from app.config import get_settings
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, MessageResponse, UserLoginResponse, UserMeResponse


router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/login", response_model=UserLoginResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> UserLoginResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user.last_logon_time = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id))
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )

    return UserLoginResponse.model_validate(user)


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response) -> MessageResponse:
    response.delete_cookie(
        key="access_token",
        path="/",
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
    )
    return MessageResponse(message="logged out")


@router.get("/me", response_model=UserMeResponse)
def me(current_user: User = Depends(get_current_user)) -> UserMeResponse:
    return UserMeResponse.model_validate(current_user)
