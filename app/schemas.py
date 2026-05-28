from datetime import datetime

from pydantic import BaseModel, Field


class SongBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    artist: str = Field(..., min_length=1, max_length=255)
    album: str | None = Field(None, max_length=255)
    year: int | None = Field(None, ge=1900, le=2100)
    genre: str | None = Field(None, max_length=100)
    duration_seconds: int | None = Field(None, ge=1)


class SongCreate(SongBase):
    pass


class SongUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    artist: str | None = Field(None, min_length=1, max_length=255)
    album: str | None = Field(None, max_length=255)
    year: int | None = Field(None, ge=1900, le=2100)
    genre: str | None = Field(None, max_length=100)
    duration_seconds: int | None = Field(None, ge=1)


class SongResponse(SongBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
