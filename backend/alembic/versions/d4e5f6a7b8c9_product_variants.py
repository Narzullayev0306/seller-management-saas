"""product_variants table and order_items.product_variant_id

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-18 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'product_variants',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('product_id', sa.Uuid(), nullable=False),
        sa.Column('sku', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('price', sa.Numeric(14, 2), nullable=False),
        sa.Column('cost_price', sa.Numeric(14, 2), nullable=False),
        sa.Column('stock_quantity', sa.Integer(), server_default='0', nullable=False),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('price >= 0', name='ck_product_variants_price_non_negative'),
        sa.CheckConstraint('cost_price >= 0', name='ck_product_variants_cost_price_non_negative'),
        sa.CheckConstraint('stock_quantity >= 0', name='ck_product_variants_stock_non_negative'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_product_variants')),
        sa.UniqueConstraint('organization_id', 'sku', name='uq_product_variants_org_sku'),
    )
    op.create_index('ix_product_variants_org_product', 'product_variants', ['organization_id', 'product_id'])

    op.add_column('order_items', sa.Column('product_variant_id', sa.Uuid(), nullable=True))
    op.create_index('ix_order_items_product_variant_id', 'order_items', ['product_variant_id'])
    op.create_foreign_key(
        'fk_order_items_product_variant_id',
        'order_items',
        'product_variants',
        ['product_variant_id'],
        ['id'],
        ondelete='RESTRICT',
    )


def downgrade() -> None:
    op.drop_constraint('fk_order_items_product_variant_id', 'order_items', type_='foreignkey')
    op.drop_index('ix_order_items_product_variant_id', table_name='order_items')
    op.drop_column('order_items', 'product_variant_id')
    op.drop_index('ix_product_variants_org_product', table_name='product_variants')
    op.drop_table('product_variants')