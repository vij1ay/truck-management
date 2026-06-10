"""Initial migration - Phase 1 Multi-tenant Auth RBAC

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Define enum types with create_type=False
    subscription_tier = postgresql.ENUM(
        'trial', 'basic', 'premium', 'enterprise',
        name='subscriptiontier',
        create_type=False
    )
    
    event_category = postgresql.ENUM(
        'auth', 'user_mgmt', 'role_mgmt', 'tenant_mgmt',
        name='eventcategory',
        create_type=False
    )

    bind = op.get_bind()
    enum_defs = [
        ("subscriptiontier", "'trial', 'basic', 'premium', 'enterprise'"),
        ("eventcategory", "'auth', 'user_mgmt', 'role_mgmt', 'tenant_mgmt'"),
    ]
    for type_name, values in enum_defs:
        bind.execute(sa.text(
            f"DO $$ BEGIN "
            f"IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{type_name}') THEN "
            f"CREATE TYPE {type_name} AS ENUM ({values}); "
            f"END IF; END $$;"
        ))
    
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('domain', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('subscription_tier', subscription_tier, nullable=False, default='trial'),
        sa.Column('max_users', sa.Integer(), nullable=False, default=10),
        sa.Column('settings', postgresql.JSONB(), nullable=False, default={}),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_tenants_name', 'tenants', ['name'], unique=False, postgresql_where=sa.text('is_deleted = false'))
    op.create_index('idx_tenants_active', 'tenants', ['is_active', 'is_deleted'])
    
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(50), unique=True, nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('permissions', postgresql.JSONB(), nullable=False, default=[]),
        sa.Column('is_system_role', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_roles_name', 'roles', ['name'])
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_users_email', 'users', ['email'], postgresql_where=sa.text('is_deleted = false'))
    op.create_index('idx_users_tenant', 'users', ['tenant_id', 'is_deleted'])
    op.create_index('idx_users_active', 'users', ['is_active', 'is_deleted'])
    
    # Create user_roles table
    op.create_table(
        'user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_user_roles_user', 'user_roles', ['user_id', 'is_deleted'])
    op.create_index('idx_user_roles_tenant', 'user_roles', ['tenant_id', 'is_deleted'])
    op.create_index('idx_user_roles_composite', 'user_roles', ['user_id', 'role_id', 'tenant_id'], postgresql_where=sa.text('is_deleted = false'))
    
    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True),
        sa.Column('token_hash', sa.String(255), unique=True, nullable=False),
        sa.Column('device_info', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, default=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_refresh_tokens_hash', 'refresh_tokens', ['token_hash'], postgresql_where=sa.text('revoked = false'))
    op.create_index('idx_refresh_tokens_user', 'refresh_tokens', ['user_id', 'revoked'])
    op.create_index('idx_refresh_tokens_expiry', 'refresh_tokens', ['expires_at'], postgresql_where=sa.text('revoked = false'))
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_category', event_category, nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('old_value', postgresql.JSONB(), nullable=True),
        sa.Column('new_value', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(), nullable=False, default={}),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_audit_logs_tenant', 'audit_logs', ['tenant_id', sa.text('created_at DESC')])
    op.create_index('idx_audit_logs_user', 'audit_logs', ['user_id', sa.text('created_at DESC')])
    op.create_index('idx_audit_logs_event', 'audit_logs', ['event_type', sa.text('created_at DESC')])
    op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_logs_created', 'audit_logs', [sa.text('created_at DESC')])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('refresh_tokens')
    op.drop_table('user_roles')
    op.drop_table('users')
    op.drop_table('roles')
    op.drop_table('tenants')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS eventcategory')
    op.execute('DROP TYPE IF EXISTS subscriptiontier')
