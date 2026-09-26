"""audit outbox and processed-event migration

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0008'
down_revision: Union[str, None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_event',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('actor_type', sa.String(32), nullable=False),
        sa.Column('actor_id', sa.UUID(as_uuid=False), nullable=True),
        sa.Column('action_code', sa.String(64), nullable=False),
        sa.Column('resource_type', sa.String(64), nullable=False),
        sa.Column('resource_id', sa.UUID(as_uuid=False), nullable=True),
        sa.Column('outcome', sa.String(32), nullable=False),
        sa.Column('reason_code', sa.String(80), nullable=True),
        sa.Column('correlation_id', sa.UUID(as_uuid=False), nullable=True),
        sa.Column('request_id', sa.UUID(as_uuid=False), nullable=True),
        sa.Column('metadata_safe', sa.Text(), nullable=True),
    )

    op.create_table(
        'outbox_event',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('event_type', sa.String(80), nullable=False),
        sa.Column('event_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('aggregate_type', sa.String(64), nullable=False),
        sa.Column('aggregate_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('partition_key', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('publish_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error_code', sa.String(100), nullable=True),
        sa.CheckConstraint('publish_attempts >= 0', name='ck_outbox_event_attempts'),
    )

    op.create_table(
        'inbox_receipt',
        sa.Column('consumer_name', sa.String(80), nullable=False),
        sa.Column('event_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('outcome', sa.String(32), nullable=False),
        sa.PrimaryKeyConstraint('consumer_name', 'event_id', name='pk_inbox_receipt'),
    )


def downgrade() -> None:
    op.drop_table('inbox_receipt')
    op.drop_table('outbox_event')
    op.drop_table('audit_event')
