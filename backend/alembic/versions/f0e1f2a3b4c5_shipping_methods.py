"""shipping_methods table

Revision ID: f0e1f2a3b4c5
Revises: f9d0e1f2a3b4
Create Date: 2026-08-19 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f0e1f2a3b4c5'
down_revision: Union[str, None] = 'f9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('shipping_methods',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('price', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('min_order_amount', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('max_order_amount', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('estimated_delivery_days', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('price >= 0', name='ck_shipping_methods_price_non_negative'),
    sa.CheckConstraint('min_order_amount >= 0', name='ck_shipping_methods_min_order_non_negative'),
    sa.CheckConstraint('max_order_amount >= 0', name='ck_shipping_methods_max_order_non_negative'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_shipping_methods')),
    sa.UniqueConstraint('organization_id', 'name', name='uq_shipping_methods_org_name')
    )
    op.create_index(op.f('ix_shipping_methods_organization_id'), 'shipping_methods', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_shipping_methods_organization_id'), table_name='shipping_methods')
    op.drop_table('shipping_methods')