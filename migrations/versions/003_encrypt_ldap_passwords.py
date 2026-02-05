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
    This migration adds encryption awareness for the bind_password column.
    Note: actual data encryption is handled by the application layer; this
    migration only adds the password_encrypted flag and does not modify
    existing bind_password values.

    After applying this migration, administrators must ensure that any
    existing LDAP bind passwords are re-saved through the application or
    updated via an administrative script that uses the application's normal
    password-encryption utilities, so that bind_password is stored in
    encrypted form and password_encrypted is set appropriately.
    """
    # Add a flag to track if password is encrypted
    op.add_column('ldap_servers', 
        sa.Column('password_encrypted', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade():
    """Remove encryption flag."""
    op.drop_column('ldap_servers', 'password_encrypted')
