"""schedule_entry and knowledge_chunk vector search migration

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-23
"""
from typing import Sequence, Union
from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa

revision: str = '0009'
down_revision: Union[str, None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'schedule_entry',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('student_user_id', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_system', sa.String(32), nullable=False),
        sa.Column('source_record_id', sa.String(128), nullable=False, unique=True),
        sa.Column('course_code', sa.String(32), nullable=False),
        sa.Column('course_name', sa.String(200), nullable=False),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('location_label', sa.String(160), nullable=True),
        sa.Column('instructor_display_name', sa.String(160), nullable=True),
        sa.Column('sync_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("source_system IN ('SYNTHETIC_SIS')", name='ck_schedule_entry_source_system'),
        sa.CheckConstraint('starts_at < ends_at', name='ck_schedule_entry_duration'),
        sa.CheckConstraint('sync_version >= 1', name='ck_schedule_entry_sync_version'),
    )

    # For embedding column:
    op.add_column('knowledge_chunk', sa.Column('embedding', Vector(1536), nullable=True))

    # For tsvector column (raw SQL):
    op.execute("ALTER TABLE knowledge_chunk ADD COLUMN content_tsv tsvector")

    # For HNSW index:
    op.execute("CREATE INDEX ix_knowledge_chunk_embedding ON knowledge_chunk USING hnsw (embedding vector_cosine_ops)")

    # For GIN index:
    op.execute("CREATE INDEX ix_knowledge_chunk_tsv ON knowledge_chunk USING gin (content_tsv)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunk_tsv")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunk_embedding")
    op.drop_column('knowledge_chunk', 'content_tsv')
    op.drop_column('knowledge_chunk', 'embedding')
    op.drop_table('schedule_entry')
