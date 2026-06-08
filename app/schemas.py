from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class HealthResponse(BaseModel):
    status: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserLoginResponse(BaseModel):
    id: int
    email: EmailStr
    super_user: bool

    model_config = ConfigDict(from_attributes=True)


class UserMeResponse(BaseModel):
    id: int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class SongBase(BaseModel):
    artist: str
    album: str | None = None
    song: str
    overplayed: bool = False


class SongCreate(SongBase):
    pass


class SongUpdate(SongBase):
    pass


class SongResponse(SongBase):
    id: int
    create_time: datetime
    update_time: datetime
    create_id: int
    update_id: int

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str
