"""return_requests and refunds tables

Revision ID: f1e2f3a4b5c6
Revises: f0e1f2a3b4c5
Create Date: 2026-08-19 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f1e2f3a4b5c6'
down_revision: Union[str, None] = 'f0e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('return_requests',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('order_id', sa.Uuid(), nullable=False),
    sa.Column('order_item_id', sa.Uuid(), nullable=False),
    sa.Column('product_id', sa.Uuid(), nullable=False),
    sa.Column('product_variant_id', sa.Uuid(), nullable=True),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('condition', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('decided_by', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['decided_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['order_item_id'], ['order_items.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['product_variant_id'], ['product_variants.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_return_requests'))
    )
    op.create_index(op.f('ix_return_requests_order_id'), 'return_requests', ['order_id'], unique=False)
    op.create_index(op.f('ix_return_requests_order_item_id'), 'return_requests', ['order_item_id'], unique=False)
    op.create_index(op.f('ix_return_requests_organization_id'), 'return_requests', ['organization_id'], unique=False)
    op.create_index('ix_return_requests_org_status', 'return_requests', ['organization_id', 'status'], unique=False)

    op.create_table('refunds',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('order_id', sa.Uuid(), nullable=False),
    sa.Column('return_request_id', sa.Uuid(), nullable=True),
    sa.Column('payment_id', sa.Uuid(), nullable=True),
    sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('refunded_by', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['refunded_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['return_request_id'], ['return_requests.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_refunds'))
    )
    op.create_index(op.f('ix_refunds_order_id'), 'refunds', ['order_id'], unique=False)
    op.create_index(op.f('ix_refunds_organization_id'), 'refunds', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_refunds_organization_id'), table_name='refunds')
    op.drop_index(op.f('ix_refunds_order_id'), table_name='refunds')
    op.drop_table('refunds')
    op.drop_index('ix_return_requests_org_status', table_name='return_requests')
    op.drop_index(op.f('ix_return_requests_organization_id'), table_name='return_requests')
    op.drop_index(op.f('ix_return_requests_order_item_id'), table_name='return_requests')
    op.drop_index(op.f('ix_return_requests_order_id'), table_name='return_requests')
    op.drop_table('return_requests')