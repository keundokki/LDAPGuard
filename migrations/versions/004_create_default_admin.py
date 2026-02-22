"""Create default admin user

Revision ID: 004
Revises: 003
Create Date: 2026-02-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create default admin user if it doesn't exist
    conn = op.get_bind()
    try:
        # Check if admin user already exists
        result = conn.execute(sa.text("SELECT id FROM users WHERE username = 'admin'"))
        if result.fetchone() is None:
            # Use a pre-computed bcrypt hash for password "admin"
            # This hash was generated locally: bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode()
            ADMIN_PASSWORD_HASH = "$2b$12$4dKd8P/F0bvQvH2sNjISI.0EdR.nAoNlCn2d0p2oiU5eC9x8vWg5C"
            
            # Insert default admin user
            conn.execute(
                sa.text(
                    """
                    INSERT INTO users (username, email, hashed_password, full_name, role, is_active, ldap_auth, created_at)
                    VALUES ('admin', 'admin@example.com', :hashed_password, 'Administrator', 'admin', true, false, now())
                    """
                ),
                {"hashed_password": ADMIN_PASSWORD_HASH}
            )
            conn.commit()
    except Exception as e:
        # If admin user creation fails, that's okay - it might already exist or be created elsewhere
        conn.execute(sa.text("ROLLBACK"))
        pass


def downgrade() -> None:
    # Delete the default admin user
    conn = op.get_bind()
    try:
        conn.execute(sa.text("DELETE FROM users WHERE username = 'admin'"))
        conn.commit()
    except Exception:
        conn.execute(sa.text("ROLLBACK"))
        pass

