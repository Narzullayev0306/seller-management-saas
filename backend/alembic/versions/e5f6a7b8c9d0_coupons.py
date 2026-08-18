"""coupons and coupon_redemptions tables

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-18 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'coupons',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=300), nullable=True),
        sa.Column('discount_type', sa.String(length=10), nullable=False),
        sa.Column('discount_value', sa.Numeric(14, 2), nullable=False),
        sa.Column('min_subtotal', sa.Numeric(14, 2), server_default='0', nullable=False),
        sa.Column('max_redemptions', sa.Integer(), nullable=True),
        sa.Column('max_per_customer', sa.Integer(), nullable=True),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("discount_type IN ('percent', 'fixed')", name='ck_coupons_discount_type'),
        sa.CheckConstraint("(discount_type = 'percent' AND discount_value <= 100) OR discount_type = 'fixed'", name='ck_coupons_discount_value_range'),
        sa.CheckConstraint('discount_value > 0', name='ck_coupons_discount_value_positive'),
        sa.CheckConstraint('min_subtotal >= 0', name='ck_coupons_min_subtotal_non_negative'),
        sa.CheckConstraint('max_redemptions IS NULL OR max_redemptions > 0', name='ck_coupons_max_redemptions_positive'),
        sa.CheckConstraint('max_per_customer IS NULL OR max_per_customer > 0', name='ck_coupons_max_per_customer_positive'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_coupons')),
        sa.UniqueConstraint('organization_id', 'code', name='uq_coupons_org_code'),
    )
    op.create_index('ix_coupons_org_status', 'coupons', ['organization_id', 'active'])

    op.create_table(
        'coupon_redemptions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('coupon_id', sa.Uuid(), nullable=False),
        sa.Column('order_id', sa.Uuid(), nullable=False),
        sa.Column('customer_id', sa.Uuid(), nullable=True),
        sa.Column('discount_amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['coupon_id'], ['coupons.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_coupon_redemptions')),
        sa.UniqueConstraint('organization_id', 'order_id', name='uq_coupon_redemptions_org_order'),
    )
    op.create_index('ix_coupon_redemptions_org_coupon', 'coupon_redemptions', ['organization_id', 'coupon_id'])


def downgrade() -> None:
    op.drop_index('ix_coupon_redemptions_org_coupon', table_name='coupon_redemptions')
    op.drop_table('coupon_redemptions')
    op.drop_index('ix_coupons_org_status', table_name='coupons')
    op.drop_table('coupons')