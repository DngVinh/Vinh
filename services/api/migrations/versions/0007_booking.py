"""room and booking migration

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'room',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('room_code', sa.String(32), nullable=False, unique=True),
        sa.Column('display_name', sa.String(160), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('features', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.CheckConstraint('capacity > 0', name='ck_room_capacity'),
        sa.CheckConstraint("status IN ('AVAILABLE', 'MAINTENANCE', 'INACTIVE')", name='ck_room_status'),
        sa.CheckConstraint('version >= 1', name='ck_room_version'),
    )

    op.create_table(
        'room_booking',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('room_id', sa.UUID(as_uuid=False), sa.ForeignKey('room.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requester_user_id', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('purpose_redacted', sa.String(300), nullable=False),
        sa.Column('attendee_count', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('action_execution_id', sa.UUID(as_uuid=False), sa.ForeignKey('action_execution.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.CheckConstraint('starts_at < ends_at', name='ck_room_booking_duration'),
        sa.CheckConstraint('attendee_count >= 1', name='ck_room_booking_attendees'),
        sa.CheckConstraint("status IN ('CONFIRMED', 'CANCELLED', 'COMPLETED')", name='ck_room_booking_status'),
        sa.CheckConstraint('version >= 1', name='ck_room_booking_version'),
    )


def downgrade() -> None:
    op.drop_table('room_booking')
    op.drop_table('room')
