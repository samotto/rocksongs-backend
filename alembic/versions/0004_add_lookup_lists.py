"""add reusable lookup lists

Revision ID: 0004_lookup_lists
Revises: 0003_user_roles
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0004_lookup_lists"
down_revision: Union[str, None] = "0003_user_roles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lookup_lists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("list_name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_mode", sa.Text(), nullable=False, server_default="Alphabetical"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("create_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("update_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("create_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("update_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.CheckConstraint(
            "sort_mode IN ('Alphabetical', 'Sequence')",
            name="ck_lookup_lists_sort_mode",
        ),
    )
    op.create_index("ix_lookup_lists_id", "lookup_lists", ["id"], unique=False)
    op.create_index("uq_lookup_lists_name_lower", "lookup_lists", [sa.text("lower(list_name)")], unique=True)

    op.create_table(
        "lookup_list_items",
        sa.Column("list_id", sa.Integer(), sa.ForeignKey("lookup_lists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("list_item_value", sa.Text(), nullable=False),
        sa.Column("list_item_text", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("create_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("update_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("create_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("update_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.CheckConstraint("sequence IS NULL OR sequence > 0", name="ck_lookup_list_items_sequence"),
        sa.PrimaryKeyConstraint("list_id", "list_item_value"),
    )
    op.create_index(
        "uq_lookup_list_items_value_lower",
        "lookup_list_items",
        ["list_id", sa.text("lower(list_item_value)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_lookup_list_items_value_lower", table_name="lookup_list_items")
    op.drop_table("lookup_list_items")
    op.drop_index("uq_lookup_lists_name_lower", table_name="lookup_lists")
    op.drop_index("ix_lookup_lists_id", table_name="lookup_lists")
    op.drop_table("lookup_lists")
