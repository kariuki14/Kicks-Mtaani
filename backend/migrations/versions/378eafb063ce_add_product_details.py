"""add product details

Revision ID: 378eafb063ce
Revises: 97dffbc771e7
Create Date: 2026-10-26 12:33:04.544728

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "378eafb063ce"
down_revision: Union[str, Sequence[str], None] = "97dffbc771e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add optional product detail columns."""
    with op.batch_alter_table("products") as batch_op:
        batch_op.add_column(sa.Column("size", sa.String(length=100), nullable=True))
        batch_op.add_column(
            sa.Column("condition", sa.String(length=100), nullable=True)
        )
        batch_op.add_column(sa.Column("colorway", sa.String(length=200), nullable=True))


def downgrade() -> None:
    """Remove optional product detail columns."""
    with op.batch_alter_table("products") as batch_op:
        batch_op.drop_column("colorway")
        batch_op.drop_column("condition")
        batch_op.drop_column("size")
