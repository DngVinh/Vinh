"""action preview confirmation and idempotency migration

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'action_preview',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('actor_user_id', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action_type', sa.String(64), nullable=False),
        sa.Column('normalized_payload', sa.Text(), nullable=False),
        sa.Column('payload_hash', sa.String(64), nullable=False),
        sa.Column('policy_decision', sa.String(32), nullable=False),
        sa.Column('confirmation_secret_hash', sa.String(128), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.CheckConstraint('version >= 1', name='ck_action_preview_version'),
    )

    op.create_table(
        'action_confirmation',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('preview_id', sa.UUID(as_uuid=False), sa.ForeignKey('action_preview.id', ondelete='CASCADE'), nullable=False),
        sa.Column('actor_user_id', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('confirmation_token_hash', sa.String(128), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'action_execution',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('preview_id', sa.UUID(as_uuid=False), sa.ForeignKey('action_preview.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('target_type', sa.String(64), nullable=True),
        sa.Column('target_id', sa.UUID(as_uuid=False), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error_code', sa.String(100), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.CheckConstraint("status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED', 'COMPENSATION_REQUIRED')", name='ck_action_execution_status'),
        sa.CheckConstraint('attempt_count >= 0', name='ck_action_execution_attempts'),
        sa.CheckConstraint('version >= 1', name='ck_action_execution_version'),
    )

    op.create_table(
        'idempotency_record',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('actor_user_id', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('operation_id', sa.String(100), nullable=False),
        sa.Column('idempotency_key', sa.String(128), nullable=False),
        sa.Column('request_fingerprint', sa.String(64), nullable=False),
        sa.Column('state', sa.String(32), nullable=False),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('response_reference', sa.Text(), nullable=True),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("state IN ('IN_PROGRESS', 'COMPLETED', 'FAILED_RETRYABLE', 'FAILED_FINAL')", name='ck_idempotency_record_state'),
        sa.UniqueConstraint('actor_user_id', 'operation_id', 'idempotency_key', name='uq_idempotency_record_key'),
    )


def downgrade() -> None:
    op.drop_table('idempotency_record')
    op.drop_table('action_execution')
    op.drop_table('action_confirmation')
    op.drop_table('action_preview')
