"""booking overlap guard and idempotency migration

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-27
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0010'
down_revision: Union[str, None] = '0009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def preflight_check(connection) -> None:
    """AC-TASK-DB-BOOKFIX-001-03: Preflight check detects existing active overlaps before applying constraints."""
    query = sa.text("""
        SELECT b1.id AS id1, b2.id AS id2, b1.room_id
        FROM room_booking b1
        JOIN room_booking b2 ON b1.room_id = b2.room_id AND b1.id != b2.id
        WHERE b1.status = 'CONFIRMED' AND b2.status = 'CONFIRMED'
          AND b1.starts_at < b2.ends_at AND b2.starts_at < b1.ends_at
    """)
    result = connection.execute(query).fetchall()
    if result:
        raise RuntimeError(
            f"Preflight migration failed: {len(result)} overlapping active bookings detected. "
            "Migration stopped without modifying ambiguous data."
        )


def upgrade() -> None:
    conn = op.get_bind()
    preflight_check(conn)

    # 1. Add idempotency_key and payload_hash columns to room_booking
    op.add_column('room_booking', sa.Column('idempotency_key', sa.String(128), nullable=True))
    op.add_column('room_booking', sa.Column('payload_hash', sa.String(64), nullable=True))
    op.create_index('uq_room_booking_idempotency_key', 'room_booking', ['idempotency_key'], unique=True)

    # 2. Add composite index for overlap lookup
    op.create_index('ix_room_booking_overlap_guard', 'room_booking', ['room_id', 'status', 'starts_at', 'ends_at'])


def downgrade() -> None:
    op.drop_index('ix_room_booking_overlap_guard', table_name='room_booking')
    op.drop_index('uq_room_booking_idempotency_key', table_name='room_booking')
    op.drop_column('room_booking', 'payload_hash')
    op.drop_column('room_booking', 'idempotency_key')
