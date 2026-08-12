from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('Admin', 'Basic', 'Pending')", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(Text, nullable=False, default="Basic", server_default="Basic")
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_logon_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    artist: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    album: Mapped[str | None] = mapped_column(Text, nullable=True)
    song: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    overplayed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    create_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    update_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
