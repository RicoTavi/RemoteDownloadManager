#!/usr/bin/env python3

"""
Remote File Scanner & Database Manager
Companion tool for download-manager.sh

Scans remote SFTP servers, stores file metadata in SQLite database,
and manages download queues.
"""

import argparse
import sqlite3
import subprocess
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import re

# Database file location
DB_FILE = Path(__file__).parent / "remote_files.db"
CONFIG_FILE = Path(__file__).parent / "config.conf"


class Database:
    """Handle all database operations"""

    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        """Connect to database and create tables if needed"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def create_tables(self):
        """Create database schema"""
        cursor = self.conn.cursor()

        # Remote files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS remote_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remote_path TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_size INTEGER,
                modified_date TEXT,
                server_added_date TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                file_type TEXT,
                checksum TEXT,
                UNIQUE(remote_path, filename)
            )
        """)

        # Downloads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                download_date TEXT,
                local_path TEXT,
                status TEXT DEFAULT 'queued',
                notes TEXT,
                FOREIGN KEY (file_id) REFERENCES remote_files(id)
            )
        """)

        # Source files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                source_file_path TEXT,
                source_notes TEXT,
                FOREIGN KEY (file_id) REFERENCES remote_files(id)
            )
        """)

        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_filename
            ON remote_files(filename)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_remote_path
            ON remote_files(remote_path)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_download_status
            ON downloads(status)
        """)

        self.conn.commit()

    def add_or_update_file(self, remote_path, filename, file_size, modified_date, server_added_date, file_type):
        """Add a new file or update last_seen if it exists"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        # Try to find existing file
        cursor.execute("""
            SELECT id FROM remote_files
            WHERE remote_path = ? AND filename = ?
        """, (remote_path, filename))

        existing = cursor.fetchone()

        if existing:
            # Update last_seen and dates (in case file was modified/re-uploaded)
            cursor.execute("""
                UPDATE remote_files
                SET last_seen = ?, file_size = ?, modified_date = ?, server_added_date = ?
                WHERE id = ?
            """, (now, file_size, modified_date, server_added_date, existing[0]))
            return existing[0]
        else:
            # Insert new file
            cursor.execute("""
                INSERT INTO remote_files
                (remote_path, filename, file_size, modified_date, server_added_date, first_seen, last_seen, file_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (remote_path, filename, file_size, modified_date, server_added_date, now, now, file_type))
            return cursor.lastrowid

    def queue_file(self, file_id, local_path=None, notes=None):
        """Queue a file for download"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO downloads (file_id, local_path, status, notes)
            VALUES (?, ?, 'queued', ?)
        """, (file_id, local_path, notes))
        self.conn.commit()

    def get_queued_files(self):
        """Get all files queued for download"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                d.id as download_id,
                d.local_path,
                d.notes as download_notes,
                rf.id as file_id,
                rf.remote_path,
                rf.filename,
                rf.file_size,
                rf.modified_date,
                rf.file_type
            FROM downloads d
            JOIN remote_files rf ON d.file_id = rf.id
            WHERE d.status = 'queued'
            ORDER BY d.id
        """)
        return cursor.fetchall()

    def update_download_status(self, download_id, status, local_path=None):
        """Update download status"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        if local_path:
            cursor.execute("""
                UPDATE downloads
                SET status = ?, download_date = ?, local_path = ?
                WHERE id = ?
            """, (status, now, local_path, download_id))
        else:
            cursor.execute("""
                UPDATE downloads
                SET status = ?, download_date = ?
                WHERE id = ?
            """, (status, now, download_id))
        self.conn.commit()

    def add_note(self, file_id, notes):
        """Add or update notes for a file"""
        cursor = self.conn.cursor()

        # Check if there's already a download record
        cursor.execute("""
            SELECT id FROM downloads
            WHERE file_id = ?
            ORDER BY id DESC LIMIT 1
        """, (file_id,))

        result = cursor.fetchone()

        if result:
            # Update existing record
            cursor.execute("""
                UPDATE downloads
                SET notes = ?
                WHERE id = ?
            """, (notes, result[0]))
        else:
            # Create new download record just for notes
            cursor.execute("""
                INSERT INTO downloads (file_id, status, notes)
                VALUES (?, 'noted', ?)
            """, (file_id, notes))

        self.conn.commit()

    def add_source_file(self, file_id, source_path, source_notes=None):
        """Link a remote file to its source file"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO source_files (file_id, source_file_path, source_notes)
            VALUES (?, ?, ?)
        """, (file_id, source_path, source_notes))
        self.conn.commit()

    def search_files(self, pattern=None, path=None, file_type=None):
        """Search for files in the database"""
        cursor = self.conn.cursor()

        query = """
            SELECT
                rf.id,
                rf.remote_path,
                rf.filename,
                rf.file_size,
                rf.modified_date,
                rf.server_added_date,
                rf.first_seen,
                rf.last_seen,
                rf.file_type,
                d.status as download_status,
                d.notes,
                sf.source_file_path
            FROM remote_files rf
            LEFT JOIN downloads d ON rf.id = d.file_id
            LEFT JOIN source_files sf ON rf.id = sf.file_id
            WHERE 1=1
        """

        params = []

        if pattern:
            query += " AND rf.filename LIKE ?"
            params.append(f"%{pattern}%")

        if path:
            query += " AND rf.remote_path LIKE ?"
            params.append(f"%{path}%")

        if file_type:
            query += " AND rf.file_type = ?"
            params.append(file_type)

        query += " ORDER BY rf.last_seen DESC, rf.filename"

        cursor.execute(query, params)
        return cursor.fetchall()

    def get_file_by_id(self, file_id):
        """Get file details by ID"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM remote_files WHERE id = ?
        """, (file_id,))
        return cursor.fetchone()

    def clear_queue(self):
        """Clear all queued downloads"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM downloads WHERE status = 'queued'")
        self.conn.commit()


class RemoteScanner:
    """Scan remote SFTP server and populate database"""

    def __init__(self, config_file=CONFIG_FILE):
        self.config = self.load_config(config_file)

    def load_config(self, config_file):
        """Load configuration from bash config file"""
        config = {}

        if not config_file.exists():
            print(f"Error: Configuration file not found: {config_file}")
            sys.exit(1)

        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Parse bash variable assignments
                    match = re.match(r'([A-Z_]+)="?([^"]*)"?', line)
                    if match:
                        key, value = match.groups()
                        config[key] = value

        # Validate required settings
        required = ['REMOTE_USER', 'REMOTE_HOST', 'SSH_KEY_PATH', 'REMOTE_BASE_PATH']
        for key in required:
            if key not in config:
                print(f"Error: Missing required configuration: {key}")
                sys.exit(1)

        return config

    def scan_directory(self, remote_path=None):
        """Scan remote directory and return file list"""
        if remote_path is None:
            remote_path = self.config['REMOTE_BASE_PATH']

        print(f"Scanning remote directory: {remote_path}")

        # Build lftp command with full timestamp format
        cmd = [
            'lftp',
            '-e',
            f'set sftp:connect-program "ssh -a -x -i {self.config["SSH_KEY_PATH"]}"; '
            f'cd \'{remote_path}\'; cls -l --time-style=long-iso; exit',
            '-u', f'{self.config["REMOTE_USER"]},',
            f'sftp://{self.config["REMOTE_HOST"]}'
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return self.parse_directory_listing(result.stdout, remote_path)
        except subprocess.CalledProcessError as e:
            print(f"Error scanning directory: {e}")
            return []

    def parse_directory_listing(self, listing, remote_path):
        """Parse lftp ls -l output"""
        files = []

        for line in listing.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Parse ls -l format
            # Split into 7 parts, then everything after is the filename
            parts = line.split(None, 7)
            if len(parts) < 8:
                continue

            file_type_char = parts[0][0]  # First character: d=dir, -=file

            file_size = int(parts[4]) if parts[4].isdigit() else 0

            # With --time-style=long-iso, format is: YYYY-MM-DD HH:MM
            # parts[5] = date, parts[6] = time
            server_added_date = f"{parts[5]} {parts[6]}"
            modified_date = server_added_date  # Use same for modified (most accurate we can get)

            filename = parts[7]  # Everything from position 7 onwards (handles spaces in filenames)

            # Skip . and ..
            if filename in ['.', '..']:
                continue

            # Skip special files (symlinks, etc) but keep directories and regular files
            if file_type_char not in ['d', '-']:
                continue

            # Determine file type
            if file_type_char == 'd':
                ext = 'folder'
            else:
                ext = Path(filename).suffix.lstrip('.').lower()

            files.append({
                'filename': filename,
                'remote_path': remote_path,
                'file_size': file_size,
                'modified_date': modified_date,
                'server_added_date': server_added_date,
                'file_type': ext
            })

        return files

    def scan_and_store(self, remote_path=None, recursive=False):
        """Scan remote directory and store in database"""
        with Database() as db:
            files = self.scan_directory(remote_path)

            print(f"\nFound {len(files)} files")
            print("Storing in database...")

            count = 0
            for file_info in files:
                file_id = db.add_or_update_file(
                    file_info['remote_path'],
                    file_info['filename'],
                    file_info['file_size'],
                    file_info['modified_date'],
                    file_info['server_added_date'],
                    file_info['file_type']
                )
                count += 1

            print(f"✓ Stored {count} files in database")

            # TODO: Add recursive scanning if requested
            if recursive:
                print("\nNote: Recursive scanning not yet implemented")


def format_size(size):
    """Format file size in human-readable format"""
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f}KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size/(1024*1024):.1f}MB"
    else:
        return f"{size/(1024*1024*1024):.1f}GB"


def main():
    parser = argparse.ArgumentParser(
        description='Remote File Scanner & Database Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan remote directory and store in database
  %(prog)s --scan

  # Scan specific path
  %(prog)s --scan --path /remote/path

  # Search for files
  %(prog)s --list
  %(prog)s --search "*.mp4"
  %(prog)s --search "backup" --path "/data"

  # Queue files for download
  %(prog)s --queue 1,5,10
  %(prog)s --queue 1-20

  # Add notes to a file
  %(prog)s --note 5 "Important backup from 2024"

  # Link source file
  %(prog)s --source 5 "/local/path/original.zip"

  # View queued downloads
  %(prog)s --show-queue

  # Clear download queue
  %(prog)s --clear-queue

  # Export queue for bash script (JSON format)
  %(prog)s --export-queue
        """
    )

    # Actions
    parser.add_argument('--scan', action='store_true',
                        help='Scan remote directory and store in database')
    parser.add_argument('--list', action='store_true',
                        help='List all files in database')
    parser.add_argument('--search', metavar='PATTERN',
                        help='Search for files by pattern')
    parser.add_argument('--queue', metavar='IDS',
                        help='Queue files for download (comma-separated IDs or ranges like 1-5)')
    parser.add_argument('--note', nargs=2, metavar=('ID', 'NOTE'),
                        help='Add note to a file')
    parser.add_argument('--source', nargs='+', metavar=('ID', 'PATH'),
                        help='Link source file (ID and path, optional notes)')
    parser.add_argument('--show-queue', action='store_true',
                        help='Show queued downloads')
    parser.add_argument('--export-queue', action='store_true',
                        help='Export queued downloads as JSON for bash script')
    parser.add_argument('--clear-queue', action='store_true',
                        help='Clear all queued downloads')
    parser.add_argument('--mark-complete', nargs=2, metavar=('DOWNLOAD_ID', 'LOCAL_PATH'),
                        help='Mark a download as complete')
    parser.add_argument('--mark-failed', metavar='DOWNLOAD_ID',
                        help='Mark a download as failed')

    # Options
    parser.add_argument('--path', metavar='PATH',
                        help='Remote path to scan or filter by')
    parser.add_argument('--type', metavar='TYPE',
                        help='Filter by file type/extension')
    parser.add_argument('--recursive', action='store_true',
                        help='Scan directories recursively')

    args = parser.parse_args()

    # Execute actions
    if args.scan:
        scanner = RemoteScanner()
        scanner.scan_and_store(args.path, args.recursive)

    elif args.list or args.search:
        with Database() as db:
            results = db.search_files(
                pattern=args.search,
                path=args.path,
                file_type=args.type
            )

            if not results:
                print("No files found")
            else:
                print(f"\nFound {len(results)} files:\n")
                print(f"{'ID':<6} {'Filename':<45} {'Size':<10} {'Added to Server':<20} {'Status':<10}")
                print("=" * 120)

                for row in results:
                    file_id = row['id']
                    filename = row['filename'][:42] + "..." if len(row['filename']) > 45 else row['filename']
                    size = format_size(row['file_size']) if row['file_size'] else "N/A"
                    added_date = row['server_added_date'] if row['server_added_date'] else "N/A"
                    status = row['download_status'] if row['download_status'] else "-"

                    print(f"{file_id:<6} {filename:<45} {size:<10} {added_date:<20} {status:<10}")

                    if row['notes']:
                        print(f"       Note: {row['notes']}")
                    if row['source_file_path']:
                        print(f"       Source: {row['source_file_path']}")

    elif args.queue:
        with Database() as db:
            # Parse IDs (support comma-separated and ranges)
            file_ids = []
            for part in args.queue.split(','):
                part = part.strip()
                if '-' in part:
                    # Handle range
                    start, end = map(int, part.split('-'))
                    file_ids.extend(range(start, end + 1))
                else:
                    file_ids.append(int(part))

            # Queue each file
            queued = 0
            for file_id in file_ids:
                file_info = db.get_file_by_id(file_id)
                if file_info:
                    db.queue_file(file_id)
                    print(f"✓ Queued: {file_info['filename']} (ID: {file_id})")
                    queued += 1
                else:
                    print(f"✗ File ID {file_id} not found")

            print(f"\n{queued} file(s) queued for download")

    elif args.note:
        file_id, note_text = args.note
        with Database() as db:
            file_info = db.get_file_by_id(int(file_id))
            if file_info:
                db.add_note(int(file_id), note_text)
                print(f"✓ Added note to: {file_info['filename']}")
            else:
                print(f"✗ File ID {file_id} not found")

    elif args.source:
        file_id = int(args.source[0])
        source_path = args.source[1]
        source_notes = ' '.join(args.source[2:]) if len(args.source) > 2 else None

        with Database() as db:
            file_info = db.get_file_by_id(file_id)
            if file_info:
                db.add_source_file(file_id, source_path, source_notes)
                print(f"✓ Linked source file to: {file_info['filename']}")
            else:
                print(f"✗ File ID {file_id} not found")

    elif args.show_queue:
        with Database() as db:
            queued = db.get_queued_files()

            if not queued:
                print("No files queued for download")
            else:
                print(f"\n{len(queued)} file(s) queued for download:\n")
                print(f"{'Queue ID':<10} {'File ID':<10} {'Filename':<50} {'Size':<10}")
                print("=" * 100)

                for row in queued:
                    filename = row['filename'][:47] + "..." if len(row['filename']) > 50 else row['filename']
                    size = format_size(row['file_size']) if row['file_size'] else "N/A"

                    print(f"{row['download_id']:<10} {row['file_id']:<10} {filename:<50} {size:<10}")

                    if row['download_notes']:
                        print(f"           Note: {row['download_notes']}")
                    if row['local_path']:
                        print(f"           Destination: {row['local_path']}")

    elif args.export_queue:
        with Database() as db:
            queued = db.get_queued_files()

            # Export as JSON for bash script
            export_data = []
            for row in queued:
                export_data.append({
                    'download_id': row['download_id'],
                    'file_id': row['file_id'],
                    'remote_path': row['remote_path'],
                    'filename': row['filename'],
                    'local_path': row['local_path'],
                    'file_size': row['file_size']
                })

            print(json.dumps(export_data, indent=2))

    elif args.clear_queue:
        with Database() as db:
            db.clear_queue()
            print("✓ Download queue cleared")

    elif args.mark_complete:
        download_id, local_path = args.mark_complete
        with Database() as db:
            db.update_download_status(int(download_id), 'completed', local_path)
            print(f"✓ Marked download {download_id} as completed")

    elif args.mark_failed:
        with Database() as db:
            db.update_download_status(int(args.mark_failed), 'failed')
            print(f"✓ Marked download {args.mark_failed} as failed")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
