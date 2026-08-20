"""purchase_orders and purchase_order_items tables

Revision ID: f2e3f4a5b6c7
Revises: f1e2f3a4b5c6
Create Date: 2026-08-19 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f2e3f4a5b6c7'
down_revision: Union[str, None] = 'f1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('purchase_orders',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('supplier_id', sa.Uuid(), nullable=True),
    sa.Column('po_number', sa.String(length=30), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('expected_date', sa.Date(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('total', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=True),
    sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_purchase_orders')),
    sa.UniqueConstraint('organization_id', 'po_number', name='uq_purchase_orders_org_number')
    )
    op.create_index(op.f('ix_purchase_orders_organization_id'), 'purchase_orders', ['organization_id'], unique=False)
    op.create_index(op.f('ix_purchase_orders_supplier_id'), 'purchase_orders', ['supplier_id'], unique=False)

    op.create_table('purchase_order_items',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('purchase_order_id', sa.Uuid(), nullable=False),
    sa.Column('product_id', sa.Uuid(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('unit_cost', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.CheckConstraint('quantity > 0', name='ck_po_items_quantity_positive'),
    sa.CheckConstraint('unit_cost >= 0', name='ck_po_items_unit_cost_non_negative'),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_purchase_order_items'))
    )
    op.create_index(op.f('ix_purchase_order_items_purchase_order_id'), 'purchase_order_items', ['purchase_order_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_purchase_order_items_purchase_order_id'), table_name='purchase_order_items')
    op.drop_table('purchase_order_items')
    op.drop_index(op.f('ix_purchase_orders_supplier_id'), table_name='purchase_orders')
    op.drop_index(op.f('ix_purchase_orders_organization_id'), table_name='purchase_orders')
    op.drop_table('purchase_orders')