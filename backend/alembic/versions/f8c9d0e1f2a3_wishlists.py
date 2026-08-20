"""wishlists and wishlist_items for storefront customer/guest wishlists

Revision ID: f8c9d0e1f2a3
Revises: f7b8c9d0e1f2
Create Date: 2026-08-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f8c9d0e1f2a3'
down_revision: Union[str, None] = 'f7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('wishlists',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('customer_id', sa.Uuid(), nullable=True),
    sa.Column('session_token', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wishlists')),
    sa.UniqueConstraint('organization_id', 'customer_id', name='uq_wishlists_org_customer'),
    sa.UniqueConstraint('organization_id', 'session_token', name='uq_wishlists_org_session')
    )
    op.create_index(op.f('ix_wishlists_customer_id'), 'wishlists', ['customer_id'], unique=False)
    op.create_index(op.f('ix_wishlists_organization_id'), 'wishlists', ['organization_id'], unique=False)

    op.create_table('wishlist_items',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('wishlist_id', sa.Uuid(), nullable=False),
    sa.Column('product_id', sa.Uuid(), nullable=False),
    sa.Column('product_variant_id', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['product_variant_id'], ['product_variants.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['wishlist_id'], ['wishlists.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wishlist_items')),
    sa.UniqueConstraint('wishlist_id', 'product_id', 'product_variant_id', name='uq_wishlist_items_wishlist_product_variant')
    )
    op.create_index(op.f('ix_wishlist_items_wishlist_id'), 'wishlist_items', ['wishlist_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_wishlist_items_wishlist_id'), table_name='wishlist_items')
    op.drop_table('wishlist_items')
    op.drop_index(op.f('ix_wishlists_organization_id'), table_name='wishlists')
    op.drop_index(op.f('ix_wishlists_customer_id'), table_name='wishlists')
    op.drop_table('wishlists')