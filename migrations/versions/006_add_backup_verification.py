"""Add backup verification fields

Revision ID: 006
Revises: 005
Create Date: 2026-02-14

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Add verification fields to backups table
    op.add_column('backups', sa.Column('checksum', sa.String(length=64), nullable=True))
    op.add_column('backups', sa.Column('checksum_algorithm', sa.String(length=20), server_default='sha256', nullable=True))
    op.add_column('backups', sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('backups', sa.Column('verification_status', sa.String(length=20), nullable=True))


def downgrade():
    # Remove verification fields from backups table
    op.drop_column('backups', 'verification_status')
    op.drop_column('backups', 'verified_at')
    op.drop_column('backups', 'checksum_algorithm')
    op.drop_column('backups', 'checksum')
