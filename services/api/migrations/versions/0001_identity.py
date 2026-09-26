"""identity and role binding

Revision ID: 0001
Revises: 
Create Date: 2026-09-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_identity',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('display_name', sa.String(160), nullable=False),
        sa.Column('primary_email', sa.String(254), nullable=True, unique=True),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('is_synthetic', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('last_authenticated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.CheckConstraint("status IN ('ACTIVE', 'SUSPENDED', 'DISABLED')", name='ck_user_identity_status'),
        sa.CheckConstraint('version >= 1', name='ck_user_identity_version'),
    )

    op.create_table(
        'identity_link',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('user_id', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('issuer', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('provider_type', sa.String(32), nullable=False),
        sa.Column('claims_version', sa.String(32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.CheckConstraint("provider_type IN ('SYNTHETIC', 'ENTRA_OIDC')", name='ck_identity_link_provider_type'),
        sa.CheckConstraint('version >= 1', name='ck_identity_link_version'),
        sa.UniqueConstraint('issuer', 'subject', name='uq_identity_link_issuer_subject'),
    )

    op.create_table(
        'role_binding',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('user_id', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(32), nullable=False),
        sa.Column('scope_type', sa.String(32), nullable=False),
        sa.Column('scope_key', sa.String(100), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.CheckConstraint("role IN ('STUDENT', 'SUPPORT_OFFICER', 'KNOWLEDGE_ADMIN', 'SYSTEM_ADMIN')", name='ck_role_binding_role'),
        sa.CheckConstraint("scope_type IN ('INSTITUTION', 'FACULTY', 'QUEUE')", name='ck_role_binding_scope_type'),
        sa.CheckConstraint('version >= 1', name='ck_role_binding_version'),
    )

    op.create_table(
        'student_profile',
        sa.Column('user_id', sa.UUID(as_uuid=False), sa.ForeignKey('user_identity.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('student_code', sa.String(32), nullable=False, unique=True),
        sa.Column('faculty_code', sa.String(32), nullable=False),
        sa.Column('program_code', sa.String(64), nullable=False),
        sa.Column('cohort_year', sa.SmallInteger(), nullable=False),
        sa.Column('academic_status', sa.String(32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.CheckConstraint("academic_status IN ('ACTIVE', 'LEAVE', 'GRADUATED', 'WITHDRAWN')", name='ck_student_profile_academic_status'),
        sa.CheckConstraint('cohort_year >= 2000 AND cohort_year <= 2100', name='ck_student_profile_cohort_year'),
        sa.CheckConstraint('version >= 1', name='ck_student_profile_version'),
    )


def downgrade() -> None:
    op.drop_table('student_profile')
    op.drop_table('role_binding')
    op.drop_table('identity_link')
    op.drop_table('user_identity')
