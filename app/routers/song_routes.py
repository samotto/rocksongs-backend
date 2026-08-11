from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Song, User
from app.schemas import MessageResponse, SongCreate, SongResponse, SongUpdate


router = APIRouter(tags=["songs"])


def require_super_user(user: User) -> None:
    if not user.super_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super-user access required")


@router.get("/songs", response_model=list[SongResponse])
def list_songs(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SongResponse]:
    songs = db.query(Song).order_by(Song.artist.asc(), Song.song.asc()).all()
    return [SongResponse.model_validate(song) for song in songs]


@router.post("/songs", response_model=SongResponse, status_code=status.HTTP_201_CREATED)
@router.post("/song", response_model=SongResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_song(
    payload: SongCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SongResponse:
    now = datetime.now(timezone.utc)
    song = Song(
        artist=payload.artist,
        album=payload.album,
        song=payload.song,
        overplayed=payload.overplayed,
        create_time=now,
        update_time=now,
        create_id=current_user.id,
        update_id=current_user.id,
    )
    db.add(song)
    db.commit()
    db.refresh(song)
    return SongResponse.model_validate(song)


@router.put("/songs/{song_id}", response_model=SongResponse)
@router.put("/song/{song_id}", response_model=SongResponse, include_in_schema=False)
def update_song(
    song_id: int,
    payload: SongUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SongResponse:
    require_super_user(current_user)
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    song.artist = payload.artist
    song.album = payload.album
    song.song = payload.song
    song.overplayed = payload.overplayed
    song.update_time = datetime.now(timezone.utc)
    song.update_id = current_user.id

    db.add(song)
    db.commit()
    db.refresh(song)
    return SongResponse.model_validate(song)


@router.delete("/songs/{song_id}", response_model=MessageResponse)
@router.delete("/song/{song_id}", response_model=MessageResponse, include_in_schema=False)
def delete_song(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    require_super_user(current_user)
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    db.delete(song)
    db.commit()
    return MessageResponse(message="song deleted")
