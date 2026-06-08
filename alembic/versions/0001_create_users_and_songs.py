"""create users and songs tables

Revision ID: 0001_create_users_and_songs
Revises:
Create Date: 2026-05-29 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0001_create_users_and_songs"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("super_user", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("google_id", sa.Text(), nullable=True),
        sa.Column("create_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_logon_time", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "songs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("artist", sa.Text(), nullable=False),
        sa.Column("album", sa.Text(), nullable=True),
        sa.Column("song", sa.Text(), nullable=False),
        sa.Column("overplayed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("create_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("update_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("create_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("update_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_index("ix_songs_artist", "songs", ["artist"], unique=False)
    op.create_index("ix_songs_song", "songs", ["song"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_songs_song", table_name="songs")
    op.drop_index("ix_songs_artist", table_name="songs")
    op.drop_table("songs")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
