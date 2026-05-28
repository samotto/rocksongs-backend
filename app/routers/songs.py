from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import SongCreate, SongResponse, SongUpdate

router = APIRouter(prefix="/songs", tags=["songs"])


@router.get("/", response_model=list[SongResponse])
def list_songs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    artist: str | None = Query(None),
    genre: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return crud.get_songs(db, skip=skip, limit=limit, artist=artist, genre=genre)


@router.post("/", response_model=SongResponse, status_code=201)
def create_song(song: SongCreate, db: Session = Depends(get_db)):
    return crud.create_song(db, song)


@router.get("/{song_id}", response_model=SongResponse)
def get_song(song_id: int, db: Session = Depends(get_db)):
    db_song = crud.get_song(db, song_id)
    if db_song is None:
        raise HTTPException(status_code=404, detail="Song not found")
    return db_song


@router.put("/{song_id}", response_model=SongResponse)
def update_song(song_id: int, song: SongUpdate, db: Session = Depends(get_db)):
    db_song = crud.update_song(db, song_id, song)
    if db_song is None:
        raise HTTPException(status_code=404, detail="Song not found")
    return db_song


@router.delete("/{song_id}", status_code=204)
def delete_song(song_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_song(db, song_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Song not found")
