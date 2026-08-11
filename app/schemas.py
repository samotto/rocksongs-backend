from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class HealthResponse(BaseModel):
    status: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserLoginResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    super_user: bool

    model_config = ConfigDict(from_attributes=True)


class UserMeResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    super_user: bool

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    super_user: bool = False


class UserUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    super_user: bool


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    super_user: bool
    create_time: datetime
    last_logon_time: datetime | None

    model_config = ConfigDict(from_attributes=True)


class PasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=72)


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
