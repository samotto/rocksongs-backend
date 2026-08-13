"""add user audit fields

Revision ID: 0006_user_audit
Revises: 0005_lookup_defaults
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0006_user_audit"
down_revision: Union[str, None] = "0005_lookup_defaults"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("update_time", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("create_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("update_id", sa.Integer(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE users
            SET update_time = create_time,
                create_id = id,
                update_id = id
            """
        )
    )
    op.create_foreign_key(
        "fk_users_create_id_users",
        "users",
        "users",
        ["create_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_users_update_id_users",
        "users",
        "users",
        ["update_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_users_update_time", "users", ["update_time"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_update_time", table_name="users")
    op.drop_constraint("fk_users_update_id_users", "users", type_="foreignkey")
    op.drop_constraint("fk_users_create_id_users", "users", type_="foreignkey")
    op.drop_column("users", "update_id")
    op.drop_column("users", "create_id")
    op.drop_column("users", "update_time")
