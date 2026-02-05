"""Encrypt LDAP bind passwords

Revision ID: 003
Revises: 002
Create Date: 2026-02-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """
    This migration adds encryption awareness for bind_password column.
    Note: Actual data encryption will be handled by the application layer.
    The column remains String(500) but will store encrypted data.
    
    To encrypt existing passwords, run the encrypt_passwords management command.
    """
    # Add a flag to track if password is encrypted
    op.add_column('ldap_servers', 
        sa.Column('password_encrypted', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade():
    """Remove encryption flag."""
    op.drop_column('ldap_servers', 'password_encrypted')
