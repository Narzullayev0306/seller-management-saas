"""webhook_endpoints and webhook_deliveries tables

Revision ID: f3e4f5a6b7c8
Revises: f2e3f4a5b6c7
Create Date: 2026-08-19 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'f3e4f5a6b7c8'
down_revision: Union[str, None] = 'f2e3f4a5b6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('webhook_endpoints',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('url', sa.String(length=500), nullable=False),
    sa.Column('secret', sa.String(length=128), nullable=False),
    sa.Column('events', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('last_delivered_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_webhook_endpoints'))
    )
    op.create_index(op.f('ix_webhook_endpoints_organization_id'), 'webhook_endpoints', ['organization_id'], unique=False)

    op.create_table('webhook_deliveries',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('webhook_endpoint_id', sa.Uuid(), nullable=False),
    sa.Column('event_type', sa.String(length=50), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('response_status', sa.Integer(), nullable=True),
    sa.Column('response_body', sa.Text(), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['webhook_endpoint_id'], ['webhook_endpoints.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_webhook_deliveries'))
    )
    op.create_index('ix_webhook_deliveries_endpoint_created', 'webhook_deliveries', ['webhook_endpoint_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_webhook_deliveries_webhook_endpoint_id'), 'webhook_deliveries', ['webhook_endpoint_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_webhook_deliveries_webhook_endpoint_id'), table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_endpoint_created', table_name='webhook_deliveries')
    op.drop_table('webhook_deliveries')
    op.drop_index(op.f('ix_webhook_endpoints_organization_id'), table_name='webhook_endpoints')
    op.drop_table('webhook_endpoints')