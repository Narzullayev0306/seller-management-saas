"""customer accounts, refresh tokens, carts and cart items

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('customer_accounts',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('customer_id', sa.Uuid(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_customer_accounts')),
    sa.UniqueConstraint('customer_id', name='uq_customer_accounts_customer'),
    sa.UniqueConstraint('organization_id', 'email', name='uq_customer_accounts_org_email')
    )
    op.create_index(op.f('ix_customer_accounts_organization_id'), 'customer_accounts', ['organization_id'], unique=False)

    op.create_table('customer_refresh_tokens',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('account_id', sa.Uuid(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['customer_accounts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_customer_refresh_tokens')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_customer_refresh_tokens_token_hash'))
    )
    op.create_index(op.f('ix_customer_refresh_tokens_account_id'), 'customer_refresh_tokens', ['account_id'], unique=False)

    op.create_table('carts',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('customer_id', sa.Uuid(), nullable=True),
    sa.Column('session_token', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_carts')),
    sa.UniqueConstraint('organization_id', 'customer_id', name='uq_carts_org_customer'),
    sa.UniqueConstraint('organization_id', 'session_token', name='uq_carts_org_session')
    )
    op.create_index(op.f('ix_carts_customer_id'), 'carts', ['customer_id'], unique=False)
    op.create_index(op.f('ix_carts_organization_id'), 'carts', ['organization_id'], unique=False)

    op.create_table('cart_items',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('cart_id', sa.Uuid(), nullable=False),
    sa.Column('product_id', sa.Uuid(), nullable=False),
    sa.Column('product_variant_id', sa.Uuid(), nullable=True),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('quantity > 0 AND quantity <= 100', name='ck_cart_items_quantity_range'),
    sa.ForeignKeyConstraint(['cart_id'], ['carts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['product_variant_id'], ['product_variants.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cart_items')),
    sa.UniqueConstraint('cart_id', 'product_id', 'product_variant_id', name='uq_cart_items_cart_product_variant')
    )
    op.create_index(op.f('ix_cart_items_cart_id'), 'cart_items', ['cart_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_cart_items_cart_id'), table_name='cart_items')
    op.drop_table('cart_items')
    op.drop_index(op.f('ix_carts_organization_id'), table_name='carts')
    op.drop_index(op.f('ix_carts_customer_id'), table_name='carts')
    op.drop_table('carts')
    op.drop_index(op.f('ix_customer_refresh_tokens_account_id'), table_name='customer_refresh_tokens')
    op.drop_table('customer_refresh_tokens')
    op.drop_index(op.f('ix_customer_accounts_organization_id'), table_name='customer_accounts')
    op.drop_table('customer_accounts')
