"""Add retry logic fields to backups table

Revision ID: 005
Revises: 004
Create Date: 2026-02-14

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Add retry logic fields to backups table
    op.add_column('backups', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('backups', sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'))
    op.add_column('backups', sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    # Remove retry logic fields from backups table
    op.drop_column('backups', 'next_retry_at')
    op.drop_column('backups', 'max_retries')
    op.drop_column('backups', 'retry_count')
