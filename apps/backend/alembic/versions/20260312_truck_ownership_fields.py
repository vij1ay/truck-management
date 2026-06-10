"""Truck ownership-specific fields: owner_contact, contractor, leased

Revision ID: 20260312_truck_ownership_fields
Revises: 20260312_driver_enhancements
Create Date: 2026-03-12
"""
from alembic import op
import sqlalchemy as sa

revision = '20260312_truck_ownership_fields'
down_revision = '20260312_driver_enhancements'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename owner_phone -> owner_contact and add all new columns
    op.add_column('trucks', sa.Column('owner_contact',       sa.String(100),  nullable=True))

    op.add_column('trucks', sa.Column('contractor_name',     sa.String(200),  nullable=True))
    op.add_column('trucks', sa.Column('contractor_contact',  sa.String(100),  nullable=True))
    op.add_column('trucks', sa.Column('contract_start_date', sa.String(10),   nullable=True))
    op.add_column('trucks', sa.Column('contract_end_date',   sa.String(10),   nullable=True))

    op.add_column('trucks', sa.Column('lessor_name',         sa.String(200),  nullable=True))
    op.add_column('trucks', sa.Column('lessor_contact',      sa.String(100),  nullable=True))
    op.add_column('trucks', sa.Column('lease_start_date',    sa.String(10),   nullable=True))
    op.add_column('trucks', sa.Column('lease_end_date',      sa.String(10),   nullable=True))

    # Migrate any existing owner_phone data into owner_contact, then drop the old column
    op.execute("UPDATE trucks SET owner_contact = owner_phone WHERE owner_phone IS NOT NULL")
    op.drop_column('trucks', 'owner_phone')


def downgrade() -> None:
    op.add_column('trucks', sa.Column('owner_phone', sa.String(20), nullable=True))
    op.execute("UPDATE trucks SET owner_phone = owner_contact WHERE owner_contact IS NOT NULL")
    op.drop_column('trucks', 'owner_contact')
    op.drop_column('trucks', 'lease_end_date')
    op.drop_column('trucks', 'lease_start_date')
    op.drop_column('trucks', 'lessor_contact')
    op.drop_column('trucks', 'lessor_name')
    op.drop_column('trucks', 'contract_end_date')
    op.drop_column('trucks', 'contract_start_date')
    op.drop_column('trucks', 'contractor_contact')
    op.drop_column('trucks', 'contractor_name')
