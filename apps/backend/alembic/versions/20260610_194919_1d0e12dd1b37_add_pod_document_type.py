"""add_pod_document_type

Revision ID: 1d0e12dd1b37
Revises: 78b45832017f
Create Date: 2026-06-10 19:49:19.358444

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d0e12dd1b37'
down_revision: Union[str, None] = '78b45832017f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adding values to a Postgres ENUM type cannot run inside a transaction block.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'pod'")
        op.execute("ALTER TYPE entitytype ADD VALUE IF NOT EXISTS 'load'")


def downgrade() -> None:
    # Postgres does not support dropping values from an ENUM type.
    pass
