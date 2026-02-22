"""Add cloud storage fields

Revision ID: 007
Revises: 006
Create Date: 2026-02-14

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Add cloud storage fields to backups table
    op.add_column('backups', sa.Column('cloud_uploaded', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('backups', sa.Column('cloud_storage_path', sa.String(length=1000), nullable=True))
    op.add_column('backups', sa.Column('cloud_uploaded_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('backups', sa.Column('cloud_provider', sa.String(length=50), nullable=True))
    op.add_column('backups', sa.Column('cloud_storage_class', sa.String(length=50), nullable=True))


def downgrade():
    # Remove cloud storage fields from backups table
    op.drop_column('backups', 'cloud_storage_class')
    op.drop_column('backups', 'cloud_provider')
    op.drop_column('backups', 'cloud_uploaded_at')
    op.drop_column('backups', 'cloud_storage_path')
    op.drop_column('backups', 'cloud_uploaded')
