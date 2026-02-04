"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.Enum('admin', 'operator', 'viewer', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('ldap_auth', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create ldap_servers table
    op.create_table(
        'ldap_servers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('host', sa.String(length=255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('use_ssl', sa.Boolean(), nullable=False),
        sa.Column('base_dn', sa.String(length=500), nullable=False),
        sa.Column('bind_dn', sa.String(length=500), nullable=True),
        sa.Column('bind_password', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_ldap_servers_id'), 'ldap_servers', ['id'], unique=False)

    # Create backups table
    op.create_table(
        'backups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ldap_server_id', sa.Integer(), nullable=False),
        sa.Column('backup_type', sa.Enum('full', 'incremental', name='backuptype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'completed', 'failed', name='backupstatus'), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('encrypted', sa.Boolean(), nullable=False),
        sa.Column('compression_enabled', sa.Boolean(), nullable=False),
        sa.Column('entry_count', sa.Integer(), nullable=True),
        sa.Column('parent_backup_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['ldap_server_id'], ['ldap_servers.id'], ),
        sa.ForeignKeyConstraint(['parent_backup_id'], ['backups.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_backups_id'), 'backups', ['id'], unique=False)

    # Create restore_jobs table
    op.create_table(
        'restore_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('backup_id', sa.Integer(), nullable=False),
        sa.Column('ldap_server_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'completed', 'failed', name='backupstatus'), nullable=False),
        sa.Column('selective_restore', sa.Boolean(), nullable=False),
        sa.Column('restore_filter', sa.Text(), nullable=True),
        sa.Column('point_in_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('entries_restored', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['backup_id'], ['backups.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['ldap_server_id'], ['ldap_servers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_restore_jobs_id'), 'restore_jobs', ['id'], unique=False)

    # Create scheduled_backups table
    op.create_table(
        'scheduled_backups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('ldap_server_id', sa.Integer(), nullable=False),
        sa.Column('backup_type', sa.Enum('full', 'incremental', name='backuptype'), nullable=False),
        sa.Column('cron_expression', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('retention_days', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['ldap_server_id'], ['ldap_servers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scheduled_backups_id'), 'scheduled_backups', ['id'], unique=False)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_id'), table_name='audit_logs')


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_scheduled_backups_id'), table_name='scheduled_backups')
    op.drop_table('scheduled_backups')
    op.drop_index(op.f('ix_restore_jobs_id'), table_name='restore_jobs')
    op.drop_table('restore_jobs')
    op.drop_index(op.f('ix_backups_id'), table_name='backups')
    op.drop_table('backups')
    op.drop_index(op.f('ix_ldap_servers_id'), table_name='ldap_servers')
    op.drop_table('ldap_servers')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
