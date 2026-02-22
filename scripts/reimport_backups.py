#!/usr/bin/env python3
"""
Script to re-import backup files from disk into the database.
This scans the /app/backups directory and creates database records for orphaned files.
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, '/app')

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from api.models.models import Backup, LDAPServer, User, BackupType, BackupStatus, BackupCategory
from api.core.config import settings


def parse_backup_filename(filename):
    """
    Parse backup filename to extract server name, type, and timestamp.
    Format: ServerName_type_YYYYMMDD_HHMMSS.ldif[.gz][.enc]
    """
    # Remove extensions
    name = filename.replace('.ldif.gz.enc', '').replace('.ldif.gz', '').replace('.ldif', '')
    
    # Pattern: ServerName_type_YYYYMMDD_HHMMSS
    pattern = r'^(.+?)_(full|incremental)_(\d{8})_(\d{6})$'
    match = re.match(pattern, name)
    
    if match:
        server_name = match.group(1)
        backup_type = match.group(2)
        date_str = match.group(3)  # YYYYMMDD
        time_str = match.group(4)  # HHMMSS
        
        # Parse timestamp
        timestamp_str = f"{date_str}{time_str}"
        timestamp = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
        
        return {
            'server_name': server_name,
            'backup_type': backup_type,
            'timestamp': timestamp,
            'date_str': date_str,
            'time_str': time_str
        }
    
    return None


def reimport_backups():
    """Re-import orphaned backup files into database."""
    
    # Create synchronous engine for this script
    db_url = settings.DATABASE_URL.replace('+asyncpg', '')
    engine = create_engine(db_url, echo=True)
    
    backup_dir = Path('/app/backups')
    
    with Session(engine) as session:
        # Get all LDAP servers
        servers = {s.name: s.id for s in session.execute(select(LDAPServer)).scalars()}
        print(f"\nFound servers: {servers}")
        
        # Get admin user
        admin_user = session.execute(select(User).where(User.username == 'admin')).scalar_one()
        print(f"Admin user ID: {admin_user.id}")
        
        # Get existing backup file paths
        existing_paths = {path for path in session.execute(select(Backup.file_path)).scalars()}
        print(f"\nExisting backup records: {len(existing_paths)}")
        
        # Scan backup directory
        backup_files = sorted([f for f in os.listdir(backup_dir) if f.endswith(('.ldif', '.ldif.gz', '.ldif.gz.enc'))])
        print(f"Found {len(backup_files)} backup files on disk\n")
        
        imported = 0
        skipped = 0
        
        for filename in backup_files:
            file_path = f"/app/backups/{filename}"
            
            # Skip if already in database
            if file_path in existing_paths:
                print(f"SKIP: {filename} - already in database")
                skipped += 1
                continue
            
            # Parse filename
            info = parse_backup_filename(filename)
            if not info:
                print(f"SKIP: {filename} - couldn't parse filename")
                skipped += 1
                continue
            
            # Find matching server
            server_id = servers.get(info['server_name'])
            if not server_id:
                print(f"SKIP: {filename} - server '{info['server_name']}' not found")
                skipped += 1
                continue
            
            # Get file stats
            full_path = backup_dir / filename
            file_size = full_path.stat().st_size
            
            # Determine encryption and compression
            encrypted = filename.endswith('.enc')
            compressed = '.gz' in filename
            
            # Create backup record
            backup = Backup(
                ldap_server_id=server_id,
                backup_type=BackupType.FULL if info['backup_type'] == 'full' else BackupType.INCREMENTAL,
                category=BackupCategory.DIRECTORY,
                status=BackupStatus.COMPLETED,
                file_path=file_path,
                file_size=file_size,
                encrypted=encrypted,
                compression_enabled=compressed,
                entry_count=None,  # Unknown
                created_by=admin_user.id,
                started_at=info['timestamp'],
                completed_at=info['timestamp'],
                created_at=info['timestamp'],
                # New fields from migrations
                retry_count=0,
                max_retries=3,
            )
            
            session.add(backup)
            print(f"IMPORT: {filename} -> server_id={server_id}, size={file_size}, encrypted={encrypted}, compressed={compressed}")
            imported += 1
        
        # Commit all imports
        session.commit()
        
        print(f"\n{'='*60}")
        print(f"Re-import complete!")
        print(f"  Imported: {imported} backups")
        print(f"  Skipped:  {skipped} backups")
        print(f"  Total:    {imported + skipped} files processed")
        print(f"{'='*60}\n")


if __name__ == '__main__':
    reimport_backups()
