"""Phase 2 - Master Data Management

Revision ID: 002_phase2_master_data
Revises: 001_initial
Create Date: 2026-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '002_phase2_master_data'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Define enum types (create_type=False means we manage creation manually)
trucktype = postgresql.ENUM(
    'flatbed', 'container', 'tanker', 'refrigerated', 'tipper', 'lowbed', 'other',
    name='trucktype', create_type=False
)
truckstatus = postgresql.ENUM(
    'active', 'inactive', 'in_maintenance', 'decommissioned',
    name='truckstatus', create_type=False
)
ownershiptype = postgresql.ENUM(
    'owned', 'contract', 'leased',
    name='ownershiptype', create_type=False
)
driverstatus = postgresql.ENUM(
    'available', 'on_trip', 'on_leave', 'inactive', 'blacklisted',
    name='driverstatus', create_type=False
)
licenseclass = postgresql.ENUM(
    'lmv', 'hmv', 'hgv', 'other',
    name='licenseclass', create_type=False
)
clienttype = postgresql.ENUM(
    'company', 'individual',
    name='clienttype', create_type=False
)
documenttype = postgresql.ENUM(
    'rc_book', 'insurance', 'fitness', 'pollution', 'permit',
    'driver_license', 'medical', 'contract', 'other',
    name='documenttype', create_type=False
)
documentstatus = postgresql.ENUM(
    'active', 'expired', 'pending', 'rejected',
    name='documentstatus', create_type=False
)
entitytype = postgresql.ENUM(
    'truck', 'driver', 'client',
    name='entitytype', create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()

    # ---------------------------------------------------------------------------
    # Create ENUMs idempotently via DO $$ blocks (PostgreSQL does not support
    # `CREATE TYPE IF NOT EXISTS`, so we check pg_type manually)
    # ---------------------------------------------------------------------------
    enum_defs = [
        ("trucktype",     "'flatbed','container','tanker','refrigerated','tipper','lowbed','other'"),
        ("truckstatus",   "'active','inactive','in_maintenance','decommissioned'"),
        ("ownershiptype", "'owned','contract','leased'"),
        ("driverstatus",  "'available','on_trip','on_leave','inactive','blacklisted'"),
        ("licenseclass",  "'lmv','hmv','hgv','other'"),
        ("clienttype",    "'company','individual'"),
        ("documenttype",  "'rc_book','insurance','fitness','pollution','permit','driver_license','medical','contract','other'"),
        ("documentstatus","'active','expired','pending','rejected'"),
        ("entitytype",    "'truck','driver','client'"),
    ]
    for type_name, values in enum_defs:
        bind.execute(sa.text(
            f"DO $$ BEGIN "
            f"IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{type_name}') THEN "
            f"CREATE TYPE {type_name} AS ENUM ({values}); "
            f"END IF; END $$;"
        ))


    # ---------------------------------------------------------------------------
    # drivers table (before trucks — trucks has FK to drivers)
    # ---------------------------------------------------------------------------
    op.create_table(
        'drivers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('employee_id', sa.String(50), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('license_no', sa.String(50), nullable=False),
        sa.Column('license_class', licenseclass, nullable=False),
        sa.Column('license_expiry', sa.Date(), nullable=False),
        sa.Column('status', driverstatus, nullable=False, server_default='available'),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('emergency_contact_name', sa.String(100), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_drivers_tenant', 'drivers', ['tenant_id', 'is_deleted'])
    op.create_index('idx_drivers_status', 'drivers', ['tenant_id', 'status', 'is_deleted'])
    op.create_index('idx_drivers_available', 'drivers', ['tenant_id', 'is_available', 'is_deleted'])
    op.create_index(
        'idx_drivers_license_no', 'drivers', ['tenant_id', 'license_no'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false')
    )
    op.create_index(
        'idx_drivers_employee_id', 'drivers', ['tenant_id', 'employee_id'],
        postgresql_where=sa.text('is_deleted = false AND employee_id IS NOT NULL')
    )
    op.create_index('idx_drivers_expiry', 'drivers', ['license_expiry'])

    # ---------------------------------------------------------------------------
    # trucks table
    # ---------------------------------------------------------------------------
    op.create_table(
        'trucks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('registration_no', sa.String(20), nullable=False),
        sa.Column('ownership_type', ownershiptype, nullable=False),
        sa.Column('truck_type', trucktype, nullable=False),
        sa.Column('status', truckstatus, nullable=False, server_default='active'),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('make', sa.String(100), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('color', sa.String(50), nullable=True),
        sa.Column('capacity_tons', sa.Numeric(10, 2), nullable=True),
        sa.Column('assigned_driver_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('drivers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('owner_name', sa.String(200), nullable=True),
        sa.Column('owner_phone', sa.String(20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_trucks_tenant', 'trucks', ['tenant_id', 'is_deleted'])
    op.create_index('idx_trucks_status', 'trucks', ['tenant_id', 'status', 'is_deleted'])
    op.create_index('idx_trucks_available', 'trucks', ['tenant_id', 'is_available', 'is_deleted'])
    op.create_index(
        'idx_trucks_registration', 'trucks', ['tenant_id', 'registration_no'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false')
    )
    op.create_index('idx_trucks_type', 'trucks', ['tenant_id', 'truck_type', 'is_deleted'])
    op.create_index('idx_trucks_driver', 'trucks', ['assigned_driver_id'])

    # ---------------------------------------------------------------------------
    # clients table
    # ---------------------------------------------------------------------------
    op.create_table(
        'clients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_type', clienttype, nullable=False, server_default='company'),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('contact_person', sa.String(200), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('alternate_phone', sa.String(20), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('pincode', sa.String(10), nullable=True),
        sa.Column('gst_no', sa.String(20), nullable=True),
        sa.Column('pan_no', sa.String(20), nullable=True),
        sa.Column('credit_limit', sa.Numeric(15, 2), nullable=True, server_default='0'),
        sa.Column('payment_terms_days', sa.Integer(), nullable=True, server_default='30'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_clients_tenant', 'clients', ['tenant_id', 'is_deleted'])
    op.create_index('idx_clients_name', 'clients', ['tenant_id', 'company_name'],
                    postgresql_where=sa.text('is_deleted = false'))
    op.create_index('idx_clients_active', 'clients', ['tenant_id', 'is_active', 'is_deleted'])
    op.create_index('idx_clients_email', 'clients', ['tenant_id', 'email'],
                    postgresql_where=sa.text('is_deleted = false AND email IS NOT NULL'))

    # ---------------------------------------------------------------------------
    # documents table
    # ---------------------------------------------------------------------------
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_type', entitytype, nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_type', documenttype, nullable=False),
        sa.Column('document_status', documentstatus, nullable=False, server_default='active'),
        sa.Column('file_url', sa.String(1024), nullable=True),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('issue_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_documents_tenant', 'documents', ['tenant_id', 'is_deleted'])
    op.create_index('idx_documents_entity', 'documents', ['entity_type', 'entity_id', 'is_deleted'])
    op.create_index('idx_documents_expiry', 'documents', ['expiry_date'],
                    postgresql_where=sa.text('is_deleted = false AND expiry_date IS NOT NULL'))
    op.create_index('idx_documents_status', 'documents', ['tenant_id', 'document_status', 'is_deleted'])
    op.create_index('idx_documents_type', 'documents', ['entity_type', 'entity_id', 'document_type'],
                    postgresql_where=sa.text('is_deleted = false'))


def downgrade() -> None:
    op.drop_table('documents')
    op.drop_table('clients')
    op.drop_table('trucks')
    op.drop_table('drivers')

    bind = op.get_bind()
    for _type in ['entitytype', 'documentstatus', 'documenttype', 'clienttype',
                   'licenseclass', 'driverstatus', 'ownershiptype', 'truckstatus', 'trucktype']:
        bind.execute(sa.text(f'DROP TYPE IF EXISTS {_type}'))
