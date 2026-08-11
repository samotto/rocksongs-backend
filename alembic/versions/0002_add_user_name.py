"""add unique user name

Revision ID: 0002_add_user_name
Revises: 0001_create_users_and_songs
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0002_add_user_name"
down_revision: Union[str, None] = "0001_create_users_and_songs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE users AS target
        SET name = split_part(target.email, '@', 1) ||
            CASE
              WHEN (
                SELECT count(*) FROM users AS candidate
                WHERE lower(split_part(candidate.email, '@', 1)) = lower(split_part(target.email, '@', 1))
              ) > 1 THEN '-' || target.id::text
              ELSE ''
            END
        """
    )
    op.alter_column("users", "name", nullable=False)
    op.create_index("uq_users_name_lower", "users", [sa.text("lower(name)")], unique=True)


def downgrade() -> None:
    op.drop_index("uq_users_name_lower", table_name="users")
    op.drop_column("users", "name")
