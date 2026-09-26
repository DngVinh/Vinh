"""conversation message and handover migration

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'conversation',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('owner_user_id', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('channel', sa.String(32), nullable=False, server_default='WEB'),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retention_expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.CheckConstraint("status IN ('ACTIVE', 'HANDED_OVER', 'CLOSED', 'ARCHIVED')", name='ck_conversation_status'),
        sa.CheckConstraint("channel IN ('WEB')", name='ck_conversation_channel'),
        sa.CheckConstraint('version >= 1', name='ck_conversation_version'),
    )

    op.create_table(
        'message',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('conversation_id', sa.UUID(as_uuid=False), sa.ForeignKey('conversation.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sequence_no', sa.BigInteger(), nullable=False),
        sa.Column('sender_type', sa.String(32), nullable=False),
        sa.Column('sender_user_id', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='SET NULL'), nullable=True),
        sa.Column('content_redacted', sa.Text(), nullable=False),
        sa.Column('content_format', sa.String(32), nullable=False, server_default='MARKDOWN_SAFE'),
        sa.Column('citation_set_id', sa.UUID(as_uuid=False), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('redacted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("sender_type IN ('USER', 'ASSISTANT', 'STAFF', 'SYSTEM')", name='ck_message_sender_type'),
        sa.CheckConstraint("content_format IN ('PLAIN_TEXT', 'MARKDOWN_SAFE')", name='ck_message_content_format'),
        sa.UniqueConstraint('conversation_id', 'sequence_no', name='uq_message_conversation_sequence'),
    )

    op.create_table(
        'handover',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('conversation_id', sa.UUID(as_uuid=False), sa.ForeignKey('conversation.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requester_user_id', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('queue_key', sa.String(100), nullable=False),
        sa.Column('reason_code', sa.String(80), nullable=False),
        sa.Column('risk_level', sa.String(32), nullable=False),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('summary_redacted', sa.Text(), nullable=False),
        sa.Column('context_reference_ids', sa.Text(), nullable=True),
        sa.Column('assigned_user_id', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='SET NULL'), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.CheckConstraint("risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')", name='ck_handover_risk_level'),
        sa.CheckConstraint("status IN ('QUEUED', 'ASSIGNED', 'ACCEPTED', 'IN_PROGRESS', 'RESOLVED', 'RETURNED', 'CANCELLED')", name='ck_handover_status'),
        sa.CheckConstraint('version >= 1', name='ck_handover_version'),
    )


def downgrade() -> None:
    op.drop_table('handover')
    op.drop_table('message')
    op.drop_table('conversation')
