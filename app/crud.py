from sqlalchemy.orm import Session

from app.models import Song
from app.schemas import SongCreate, SongUpdate


def get_song(db: Session, song_id: int) -> Song | None:
    return db.query(Song).filter(Song.id == song_id).first()


def get_songs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    artist: str | None = None,
    genre: str | None = None,
) -> list[Song]:
    query = db.query(Song)
    if artist:
        query = query.filter(Song.artist.ilike(f"%{artist}%"))
    if genre:
        query = query.filter(Song.genre.ilike(f"%{genre}%"))
    return query.offset(skip).limit(limit).all()


def create_song(db: Session, song: SongCreate) -> Song:
    db_song = Song(**song.model_dump())
    db.add(db_song)
    db.commit()
    db.refresh(db_song)
    return db_song


def update_song(db: Session, song_id: int, song: SongUpdate) -> Song | None:
    db_song = get_song(db, song_id)
    if db_song is None:
        return None
    update_data = song.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_song, field, value)
    db.commit()
    db.refresh(db_song)
    return db_song


def delete_song(db: Session, song_id: int) -> bool:
    db_song = get_song(db, song_id)
    if db_song is None:
        return False
    db.delete(db_song)
    db.commit()
    return True
