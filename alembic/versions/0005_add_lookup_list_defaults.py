"""add lookup list defaults and allow zero sequence

Revision ID: 0005_lookup_defaults
Revises: 0004_lookup_lists
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0005_lookup_defaults"
down_revision: Union[str, None] = "0004_lookup_lists"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("lookup_lists", sa.Column("default_item_value", sa.Text(), nullable=True))

    op.drop_constraint("ck_lookup_list_items_sequence", "lookup_list_items", type_="check")
    op.create_check_constraint(
        "ck_lookup_list_items_sequence",
        "lookup_list_items",
        "sequence IS NULL OR sequence >= 0",
    )

    op.execute(
        sa.text(
            """
            UPDATE lookup_list_items AS item
            SET sequence = 0
            FROM lookup_lists AS list
            WHERE item.list_id = list.id
              AND lower(list.list_name) = 'role'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE lookup_lists
            SET sort_mode = 'Alphabetical', default_item_value = 'Basic'
            WHERE lower(list_name) = 'role'
              AND EXISTS (
                  SELECT 1
                  FROM lookup_list_items
                  WHERE lookup_list_items.list_id = lookup_lists.id
                    AND lookup_list_items.list_item_value = 'Basic'
                    AND lookup_list_items.active = true
              )
            """
        )
    )

    op.create_foreign_key(
        "fk_lookup_lists_default_item",
        "lookup_lists",
        "lookup_list_items",
        ["id", "default_item_value"],
        ["list_id", "list_item_value"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_lookup_lists_default_item", "lookup_lists", type_="foreignkey")
    op.drop_column("lookup_lists", "default_item_value")
    op.drop_constraint("ck_lookup_list_items_sequence", "lookup_list_items", type_="check")
    op.execute(sa.text("UPDATE lookup_list_items SET sequence = NULL WHERE sequence <= 0"))
    op.create_check_constraint(
        "ck_lookup_list_items_sequence",
        "lookup_list_items",
        "sequence IS NULL OR sequence > 0",
    )
