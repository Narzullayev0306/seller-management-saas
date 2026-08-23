"""refresh token session metadata (ip, user agent, family), session mgmt

Revision ID: f7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-08-19 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f7b8c9d0e1f2'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('refresh_tokens', sa.Column('family_id', sa.Uuid(), nullable=True))
    op.add_column('refresh_tokens', sa.Column('replaced_by', sa.Uuid(), nullable=True))
    op.add_column('refresh_tokens', sa.Column('created_ip', sa.String(length=64), nullable=True))
    op.add_column('refresh_tokens', sa.Column('user_agent', sa.String(length=512), nullable=True))
    op.create_index(op.f('ix_refresh_tokens_family_id'), 'refresh_tokens', ['family_id'], unique=False)
    op.create_foreign_key(
        'fk_refresh_tokens_replaced_by_refresh_tokens',
        'refresh_tokens',
        'refresh_tokens',
        ['replaced_by'],
        ['id'],
        ondelete='SET NULL',
    )
    # Backfill existing tokens into their own family.
    op.execute(
        "UPDATE refresh_tokens SET family_id = id WHERE family_id IS NULL"
    )
    op.alter_column('refresh_tokens', 'family_id', nullable=False)

    op.create_table('notification_preferences',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('in_app_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('email_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('new_order_alerts', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('low_stock_alerts', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('marketing_emails', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_notification_preferences')),
    sa.UniqueConstraint('user_id', name='uq_notification_preferences_user')
    )

    op.add_column('organizations', sa.Column('favicon_url', sa.String(length=500), nullable=True))
    op.add_column('organizations', sa.Column('primary_color', sa.String(length=9), nullable=True))
    op.add_column('organizations', sa.Column('secondary_color', sa.String(length=9), nullable=True))
    op.add_column('organizations', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('organizations', sa.Column('social_links', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('organizations', 'social_links')
    op.drop_column('organizations', 'description')
    op.drop_column('organizations', 'secondary_color')
    op.drop_column('organizations', 'primary_color')
    op.drop_column('organizations', 'favicon_url')
    op.drop_table('notification_preferences')
    op.drop_constraint(
        'fk_refresh_tokens_replaced_by_refresh_tokens', 'refresh_tokens', type_='foreignkey'
    )
    op.drop_index(op.f('ix_refresh_tokens_family_id'), table_name='refresh_tokens')
    op.drop_column('refresh_tokens', 'user_agent')
    op.drop_column('refresh_tokens', 'created_ip')
    op.drop_column('refresh_tokens', 'replaced_by')
    op.drop_column('refresh_tokens', 'family_id')