from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user, hash_password
from app.database import get_db
from app.models import Song, User
from app.schemas import MessageResponse, PasswordResetRequest, UserCreate, UserResponse, UserUpdate


router = APIRouter(prefix="/users", tags=["users"])


def require_super_user(user: User) -> None:
    if not user.super_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super-user access required")


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UserResponse]:
    require_super_user(current_user)
    users = db.query(User).order_by(User.email.asc()).all()
    return [UserResponse.model_validate(user) for user in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    require_super_user(current_user)

    email = str(payload.email).strip().lower()
    name = (payload.name or email.split("@", 1)[0]).strip()
    if db.query(User).filter(func.lower(User.email) == email.lower()).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists")
    if db.query(User).filter(func.lower(User.name) == name.lower()).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this name already exists")

    user = User(
        name=name,
        email=email,
        super_user=payload.super_user,
        password_hash=hash_password(payload.password),
        create_time=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    require_super_user(current_user)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    email = str(payload.email).strip().lower()
    name = payload.name.strip()
    duplicate_email = db.query(User).filter(func.lower(User.email) == email.lower(), User.id != user_id).first()
    if duplicate_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists")
    duplicate_name = db.query(User).filter(func.lower(User.name) == name.lower(), User.id != user_id).first()
    if duplicate_name:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this name already exists")

    user.name = name
    user.email = email
    user.super_user = payload.super_user
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    require_super_user(current_user)
    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You cannot delete your own account")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Keep the song audit foreign keys valid after the user is removed.
    db.query(Song).filter(Song.create_id == user_id).update(
        {Song.create_id: current_user.id}, synchronize_session=False
    )
    db.query(Song).filter(Song.update_id == user_id).update(
        {Song.update_id: current_user.id}, synchronize_session=False
    )
    db.delete(user)
    db.commit()
    return MessageResponse(message="user deleted")


@router.post("/{user_id}/reset-password", response_model=MessageResponse)
def reset_password(
    user_id: int,
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    if current_user.id != user_id and not current_user.super_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot reset this user's password")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password_hash = hash_password(payload.new_password)
    db.add(user)
    db.commit()
    return MessageResponse(message="password updated")
