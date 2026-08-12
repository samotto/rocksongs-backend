"""replace super_user with role

Revision ID: 0003_user_roles
Revises: 0002_add_user_name
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0003_user_roles"
down_revision: Union[str, None] = "0002_add_user_name"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE users
        SET role = CASE
            WHEN super_user THEN 'Admin'
            WHEN last_logon_time IS NULL THEN 'Pending'
            ELSE 'Basic'
        END
        """
    )
    op.alter_column("users", "role", nullable=False, server_default="Basic")
    op.create_check_constraint("ck_users_role", "users", "role IN ('Admin', 'Basic', 'Pending')")
    op.drop_column("users", "super_user")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("super_user", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.execute("UPDATE users SET super_user = true WHERE role = 'Admin'")
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_column("users", "role")
