"""outbox events for transactional domain events

Revision ID: b2c3d4e5f6a7
Revises: f3a4b5c6d7e8
Create Date: 2026-08-18 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'f3a4b5c6d7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'outbox_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('event_type', sa.String(length=80), nullable=False),
        sa.Column('aggregate_type', sa.String(length=60), nullable=False),
        sa.Column('aggregate_id', sa.Uuid(), nullable=True),
        sa.Column('payload', JSONB(), nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_outbox_events')),
    )
    op.create_index('ix_outbox_events_processed_created', 'outbox_events', ['processed_at', 'created_at'])
    op.create_index('ix_outbox_events_org_created', 'outbox_events', ['organization_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_outbox_events_org_created', table_name='outbox_events')
    op.drop_index('ix_outbox_events_processed_created', table_name='outbox_events')
    op.drop_table('outbox_events')