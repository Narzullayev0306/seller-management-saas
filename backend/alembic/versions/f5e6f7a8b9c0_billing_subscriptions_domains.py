"""billing (subscriptions + invoices) and organization_domains tables

Revision ID: f5e6f7a8b9c0
Revises: f4e5f6a7b8c9
Create Date: 2026-08-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f5e6f7a8b9c0'
down_revision: Union[str, None] = 'f4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('subscriptions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('plan', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('current_period_start', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_subscriptions')),
    sa.UniqueConstraint('organization_id', name=op.f('uq_subscriptions_organization_id'))
    )
    op.create_index(op.f('ix_subscriptions_organization_id'), 'subscriptions', ['organization_id'], unique=True)

    op.create_table('invoices',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('invoice_number', sa.String(length=30), nullable=False),
    sa.Column('plan', sa.String(length=20), nullable=False),
    sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_invoices'))
    )
    op.create_index(op.f('ix_invoices_organization_id'), 'invoices', ['organization_id'], unique=False)

    op.create_table('organization_domains',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('domain', sa.String(length=253), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('verification_token', sa.String(length=64), nullable=False),
    sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_primary', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_organization_domains')),
    sa.UniqueConstraint('domain', name=op.f('uq_organization_domains_domain'))
    )
    op.create_index(op.f('ix_organization_domains_organization_id'), 'organization_domains', ['organization_id'], unique=False)

    # Backfill a subscription row for every existing organization.
    op.execute(
        """
        INSERT INTO subscriptions (id, organization_id, plan, status, current_period_start)
        SELECT gen_random_uuid(), id, plan, 'active', now()
        FROM organizations
        """
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_organization_domains_organization_id'), table_name='organization_domains')
    op.drop_table('organization_domains')
    op.drop_index(op.f('ix_invoices_organization_id'), table_name='invoices')
    op.drop_table('invoices')
    op.drop_index(op.f('ix_subscriptions_organization_id'), table_name='subscriptions')
    op.drop_table('subscriptions')