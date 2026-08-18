"""account security, notifications, company settings, suppliers

Revision ID: c1d2e3f4a5b6
Revises: a1b2c3d4e5f6
Create Date: 2026-08-17 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- company settings -------------------------------------------------
    op.add_column('organizations', sa.Column('logo_url', sa.String(length=500), nullable=True))
    op.add_column('organizations', sa.Column('currency', sa.String(length=10), server_default='USD', nullable=False))
    op.add_column('organizations', sa.Column('timezone', sa.String(length=64), server_default='UTC', nullable=False))
    op.add_column('organizations', sa.Column('address', sa.String(length=300), nullable=True))
    op.add_column('organizations', sa.Column('phone', sa.String(length=30), nullable=True))
    op.add_column('organizations', sa.Column('email', sa.String(length=255), nullable=True))

    # ---- account security / status ---------------------------------------
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('users', sa.Column('status', sa.String(length=20), server_default='active', nullable=False))
    op.create_index(op.f('ix_users_status'), 'users', ['status'], unique=False)

    op.create_table('auth_tokens',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('purpose', sa.String(length=20), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_auth_tokens_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_auth_tokens')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_auth_tokens_token_hash'))
    )
    op.create_index(op.f('ix_auth_tokens_purpose'), 'auth_tokens', ['purpose'], unique=False)
    op.create_index(op.f('ix_auth_tokens_user_id'), 'auth_tokens', ['user_id'], unique=False)

    # ---- orders: payment status, shipping fee, creator --------------------
    op.add_column('orders', sa.Column('created_by', sa.Uuid(), nullable=True))
    op.add_column('orders', sa.Column('payment_status', sa.String(length=20), server_default='pending', nullable=False))
    op.add_column('orders', sa.Column('shipping_fee', sa.Numeric(precision=14, scale=2), server_default='0', nullable=False))
    op.create_index(op.f('ix_orders_created_by'), 'orders', ['created_by'], unique=False)
    op.create_foreign_key(op.f('fk_orders_created_by_users'), 'orders', 'users', ['created_by'], ['id'], ondelete='SET NULL')

    # ---- notifications ----------------------------------------------------
    op.create_table('notifications',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('type', sa.String(length=30), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('data', sa.JSON(), nullable=True),
    sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_notifications_organization_id_organizations'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_notifications_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_notifications'))
    )
    op.create_index(op.f('ix_notifications_organization_id'), 'notifications', ['organization_id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)

    # ---- suppliers --------------------------------------------------------
    op.create_table('suppliers',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('phone', sa.String(length=30), nullable=True),
    sa.Column('address', sa.String(length=300), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_suppliers_organization_id_organizations'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_suppliers'))
    )
    op.create_index(op.f('ix_suppliers_organization_id'), 'suppliers', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_suppliers_organization_id'), table_name='suppliers')
    op.drop_table('suppliers')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_organization_id'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_constraint(op.f('fk_orders_created_by_users'), 'orders', type_='foreignkey')
    op.drop_index(op.f('ix_orders_created_by'), table_name='orders')
    op.drop_column('orders', 'shipping_fee')
    op.drop_column('orders', 'payment_status')
    op.drop_column('orders', 'created_by')
    op.drop_index(op.f('ix_auth_tokens_user_id'), table_name='auth_tokens')
    op.drop_index(op.f('ix_auth_tokens_purpose'), table_name='auth_tokens')
    op.drop_table('auth_tokens')
    op.drop_index(op.f('ix_users_status'), table_name='users')
    op.drop_column('users', 'status')
    op.drop_column('users', 'email_verified')
    op.drop_column('organizations', 'email')
    op.drop_column('organizations', 'phone')
    op.drop_column('organizations', 'address')
    op.drop_column('organizations', 'timezone')
    op.drop_column('organizations', 'currency')
    op.drop_column('organizations', 'logo_url')