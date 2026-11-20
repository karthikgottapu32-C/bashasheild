"""
BhashaShield Database Reliability & Online Backup Utility.

Provides non-blocking, atomic online SQLite backups using the SQLite Backup API
(sqlite3.Connection.backup), ensuring database integrity even under active concurrent writes.
Also provides point-in-time restoration and integrity verification.
"""

import sqlite3
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings

def get_backup_dir() -> Path:
    backup_dir = Path(settings.DATABASE_PATH).parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir

def perform_backup(target_file: str = None) -> Path:
    """
    Creates an atomic, non-blocking online backup of the active SQLite database.
    """
    source_db = Path(settings.DATABASE_PATH)
    if not source_db.exists():
        raise FileNotFoundError(f"Source database not found at {source_db}")

    if target_file:
        dest_path = Path(target_file)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dest_path = get_backup_dir() / f"bhashashield_backup_{timestamp}.db"

    print(f"[*] Starting atomic online backup: {source_db} -> {dest_path}")
    source_conn = sqlite3.connect(str(source_db), timeout=10.0)
    source_conn.execute("PRAGMA journal_mode=WAL;")
    
    dest_conn = sqlite3.connect(str(dest_path))
    try:
        # SQLite Online Backup API: step(-1) copies all remaining pages atomically
        source_conn.backup(dest_conn, pages=-1)
        print(f"[+] Backup completed successfully: {dest_path} ({dest_path.stat().st_size} bytes)")
    finally:
        dest_conn.close()
        source_conn.close()

    # Verify backup integrity
    verify_database(str(dest_path))
    return dest_path

def verify_database(db_path: str) -> bool:
    """
    Executes PRAGMA integrity_check to ensure backup is valid and uncorrupted.
    """
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"Database file not found: {path}")

    conn = sqlite3.connect(str(path))
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchall()
        for row in result:
            if row[0] != "ok":
                print(f"[-] Integrity check FAILED for {path}: {row[0]}")
                return False
        print(f"[+] Integrity check PASSED for {path} (Status: OK)")
        return True
    finally:
        conn.close()

def restore_backup(backup_file: str, target_db: str = None) -> bool:
    """
    Safely restores a backup to the primary database location.
    """
    backup_path = Path(backup_file)
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found at {backup_path}")

    # Verify backup before restoring
    print(f"[*] Verifying integrity of backup before restoration: {backup_path}")
    if not verify_database(str(backup_path)):
        raise RuntimeError("Restoration aborted: Backup file failed integrity verification.")

    dest_db = Path(target_db or settings.DATABASE_PATH)
    dest_db.parent.mkdir(parents=True, exist_ok=True)

    print(f"[*] Restoring backup to {dest_db}...")
    source_conn = sqlite3.connect(str(backup_path))
    dest_conn = sqlite3.connect(str(dest_db), timeout=10.0)
    try:
        source_conn.backup(dest_conn, pages=-1)
        dest_conn.execute("PRAGMA journal_mode=WAL;")
        print(f"[+] Database restoration completed successfully to {dest_db}")
        return True
    finally:
        dest_conn.close()
        source_conn.close()

def main():
    parser = argparse.ArgumentParser(description="BhashaShield Database Backup & Recovery Utility")
    parser.add_argument("--backup", action="store_true", help="Perform atomic online backup")
    parser.add_argument("--restore", type=str, help="Restore database from specified backup file")
    parser.add_argument("--verify", type=str, help="Verify integrity of specified database/backup file")
    parser.add_argument("--output", type=str, help="Custom output path for backup file")
    args = parser.parse_args()

    if args.verify:
        is_ok = verify_database(args.verify)
        sys.exit(0 if is_ok else 1)
    elif args.restore:
        success = restore_backup(args.restore)
        sys.exit(0 if success else 1)
    else:
        # Default action is backup
        dest = perform_backup(args.output)
        print(f"Backup saved to: {dest}")

if __name__ == "__main__":
    main()
