"""ticket and immutable ticket-event migration

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ticket',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('requester_user_id', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.String(32), nullable=False),
        sa.Column('priority', sa.String(32), nullable=False),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('subject', sa.String(200), nullable=False),
        sa.Column('description_redacted', sa.Text(), nullable=False),
        sa.Column('queue_key', sa.String(100), nullable=False),
        sa.Column('assigned_user_id', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='SET NULL'), nullable=True),
        sa.Column('sla_due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.CheckConstraint("category IN ('GENERAL_SUPPORT', 'ACADEMIC_POLICY', 'DOCUMENT_REQUEST_SUPPORT', 'FACILITY', 'COMPLAINT', 'OTHER')", name='ck_ticket_category'),
        sa.CheckConstraint("priority IN ('LOW', 'NORMAL', 'HIGH', 'CRITICAL')", name='ck_ticket_priority'),
        sa.CheckConstraint("status IN ('DRAFT', 'CONFIRMATION_REQUIRED', 'OPEN', 'ASSIGNED', 'IN_PROGRESS', 'WAITING_STUDENT', 'RESOLVED', 'CLOSED', 'ESCALATED', 'CANCELLED')", name='ck_ticket_status'),
        sa.CheckConstraint('version >= 1', name='ck_ticket_version'),
    )

    op.create_table(
        'ticket_event',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('ticket_id', sa.UUID(as_uuid=False), sa.ForeignKey('ticket.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sequence_no', sa.BigInteger(), nullable=False),
        sa.Column('event_type', sa.String(32), nullable=False),
        sa.Column('actor_user_id', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='SET NULL'), nullable=True),
        sa.Column('from_status', sa.String(32), nullable=True),
        sa.Column('to_status', sa.String(32), nullable=True),
        sa.Column('comment_redacted', sa.Text(), nullable=True),
        sa.Column('visibility', sa.String(32), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("event_type IN ('CREATED', 'STATUS_CHANGED', 'ASSIGNED', 'COMMENTED', 'ESCALATED', 'ATTACHMENT_LINKED')", name='ck_ticket_event_type'),
        sa.CheckConstraint("visibility IN ('REQUESTER_AND_STAFF', 'STAFF_ONLY', 'AUDIT_ONLY')", name='ck_ticket_event_visibility'),
        sa.UniqueConstraint('ticket_id', 'sequence_no', name='uq_ticket_event_ticket_sequence'),
    )


def downgrade() -> None:
    op.drop_table('ticket_event')
    op.drop_table('ticket')
