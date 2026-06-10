"""Driver enhancements: multi-truck mapping (driver_trucks), base_location, current_lat, current_lon

Revision ID: 20260312_driver_enhancements
Revises: 20260301_115250_bea1b8a2aab4
Create Date: 2026-03-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision = '20260312_driver_enhancements'
down_revision = 'bea1b8a2aab4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add new columns to drivers table
    op.add_column('drivers', sa.Column('base_location', sa.String(255), nullable=True))
    op.add_column('drivers', sa.Column('current_lat', sa.Numeric(10, 7), nullable=True))
    op.add_column('drivers', sa.Column('current_lon', sa.Numeric(10, 7), nullable=True))

    # 2. Create many-to-many association table
    op.create_table(
        'driver_trucks',
        sa.Column('driver_id', UUID(as_uuid=True),
                  sa.ForeignKey('drivers.id', ondelete='CASCADE'),
                  primary_key=True, nullable=False),
        sa.Column('truck_id', UUID(as_uuid=True),
                  sa.ForeignKey('trucks.id', ondelete='CASCADE'),
                  primary_key=True, nullable=False),
    )


def downgrade() -> None:
    op.drop_table('driver_trucks')
    op.drop_column('drivers', 'current_lon')
    op.drop_column('drivers', 'current_lat')
    op.drop_column('drivers', 'base_location')
