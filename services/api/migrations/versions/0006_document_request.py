"""document-request migration

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'document_request',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('student_user_id', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_type', sa.String(64), nullable=False),
        sa.Column('purpose_code', sa.String(64), nullable=False),
        sa.Column('delivery_method', sa.String(32), nullable=False),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('action_execution_id', sa.UUID(as_uuid=False), sa.ForeignKey('action_execution.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ticket_id', sa.UUID(as_uuid=False), sa.ForeignKey('ticket.id', ondelete='SET NULL'), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.CheckConstraint("delivery_method IN ('DIGITAL', 'PICKUP')", name='ck_document_request_delivery_method'),
        sa.CheckConstraint("status IN ('DRAFT', 'PENDING_CONFIRMATION', 'SUBMITTED', 'VALIDATING', 'PROCESSING', 'READY', 'FULFILLED', 'REJECTED', 'CANCELLED')", name='ck_document_request_status'),
        sa.CheckConstraint('version >= 1', name='ck_document_request_version'),
    )


def downgrade() -> None:
    op.drop_table('document_request')
