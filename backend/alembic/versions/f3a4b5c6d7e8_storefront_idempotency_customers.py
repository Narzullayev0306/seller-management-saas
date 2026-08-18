"""storefront tenant flag, idempotency keys, case-insensitive customer emails

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-08-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'f3a4b5c6d7e8'
down_revision: Union[str, None] = 'e2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # every organization is a storefront by default; owners can disable it later
    op.add_column(
        'organizations',
        sa.Column('storefront_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    )

    # case-insensitive per-org unique customer email (race-condition protection)
    op.execute(
        """
        CREATE UNIQUE INDEX uq_customers_org_email_lower
        ON customers (organization_id, lower(email))
        WHERE email IS NOT NULL
        """
    )

    op.create_table('idempotency_keys',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('key', sa.String(length=100), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=True),
    sa.Column('request_hash', sa.String(length=64), nullable=True),
    sa.Column('status', sa.String(length=20), server_default='processing', nullable=False),
    sa.Column('response_status', sa.Integer(), nullable=True),
    sa.Column('response_body', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_idempotency_keys')),
    sa.UniqueConstraint('organization_id', 'key', name='uq_idempotency_keys_org_key')
    )
    op.create_index(op.f('ix_idempotency_keys_organization_id'), 'idempotency_keys', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_idempotency_keys_organization_id'), table_name='idempotency_keys')
    op.drop_table('idempotency_keys')
    op.execute("DROP INDEX IF EXISTS uq_customers_org_email_lower")
    op.drop_column('organizations', 'storefront_enabled')