"""knowledge source version and chunk migration

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'knowledge_source',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('source_type', sa.String(32), nullable=False),
        sa.Column('canonical_uri', sa.Text(), nullable=False, unique=True),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('owner_unit', sa.String(160), nullable=False),
        sa.Column('authority_level', sa.SmallInteger(), nullable=False),
        sa.Column('approval_status', sa.String(32), nullable=False),
        sa.Column('is_synthetic', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.CheckConstraint("source_type IN ('OFFICIAL_DOCUMENT', 'OFFICIAL_WEB', 'SYNTHETIC_DOCUMENT')", name='ck_knowledge_source_source_type'),
        sa.CheckConstraint('authority_level >= 1 AND authority_level <= 100', name='ck_knowledge_source_authority_level'),
        sa.CheckConstraint("approval_status IN ('DRAFT', 'APPROVED', 'REJECTED')", name='ck_knowledge_source_approval_status'),
        sa.CheckConstraint('version >= 1', name='ck_knowledge_source_version'),
    )

    op.create_table(
        'document_version',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('knowledge_source_id', sa.UUID(as_uuid=False), sa.ForeignKey('knowledge_source.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_label', sa.String(64), nullable=False),
        sa.Column('content_checksum', sa.String(64), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('storage_object_key', sa.Text(), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_by', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.CheckConstraint("status IN ('DRAFT', 'PUBLISHED', 'SUPERSEDED', 'ARCHIVED')", name='ck_document_version_status'),
        sa.CheckConstraint('version >= 1', name='ck_document_version_version'),
        sa.UniqueConstraint('knowledge_source_id', 'version_label', name='uq_document_version_source_label'),
    )

    op.create_table(
        'knowledge_chunk',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('document_version_id', sa.UUID(as_uuid=False), sa.ForeignKey('document_version.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ordinal', sa.Integer(), nullable=False),
        sa.Column('section_path', sa.String(500), nullable=True),
        sa.Column('page_start', sa.Integer(), nullable=True),
        sa.Column('page_end', sa.Integer(), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('content_checksum', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.CheckConstraint('version >= 1', name='ck_knowledge_chunk_version'),
        sa.CheckConstraint('page_end IS NULL OR page_start IS NULL OR page_end >= page_start', name='ck_knowledge_chunk_pages'),
        sa.UniqueConstraint('document_version_id', 'ordinal', name='uq_knowledge_chunk_version_ordinal'),
    )

    op.create_table(
        'retrieval_run',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('conversation_id', sa.UUID(as_uuid=False), nullable=True),
        sa.Column('message_id', sa.UUID(as_uuid=False), nullable=True),
        sa.Column('query_redacted', sa.Text(), nullable=False),
        sa.Column('filter_json', sa.Text(), nullable=True),
        sa.Column('lexical_candidate_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('vector_candidate_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reranked_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('algorithm_version', sa.String(64), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('retrieval_run')
    op.drop_table('knowledge_chunk')
    op.drop_table('document_version')
    op.drop_table('knowledge_source')
