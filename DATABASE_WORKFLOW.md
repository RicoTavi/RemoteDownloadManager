# Database-Driven Download Workflow

This guide explains how to use the new database-driven workflow for managing remote file downloads.

## Overview

The enhanced system allows you to:
- Scan remote directories and store file metadata in a local SQLite database
- Browse and search files offline
- Add notes and track source files
- Queue files for download
- Download queued files via LFTP
- Track download history and status

## Quick Start

### 1. Scan Remote Directory

```bash
# Scan the default remote path (from config.conf)
python3 remote_scanner.py --scan

# Scan a specific path
python3 remote_scanner.py --scan --path "/remote/specific/path"
```

This connects to your remote server via LFTP and stores all file metadata in `remote_files.db`.

### 2. Browse Available Files

```bash
# List all files in database
python3 remote_scanner.py --list

# Search for specific files
python3 remote_scanner.py --search "*.mp4"
python3 remote_scanner.py --search "backup"
python3 remote_scanner.py --search "video" --path "/media"
```

Output shows:
- File ID (needed for queuing)
- Filename
- Size
- Modified date
- Download status
- Notes (if any)
- Source file links (if any)

### 3. Queue Files for Download

```bash
# Queue single file (by ID from --list output)
python3 remote_scanner.py --queue 5

# Queue multiple files (comma-separated)
python3 remote_scanner.py --queue 1,5,10,23

# Queue range of files
python3 remote_scanner.py --queue 1-20

# Mix ranges and individual IDs
python3 remote_scanner.py --queue 1-10,15,20-25
```

### 4. Review Queue

```bash
# See what's queued
python3 remote_scanner.py --show-queue
```

### 5. Download Queued Files

```bash
# Download all queued files
./download-manager.sh --from-db
```

This will:
- Load queued files from database
- Ask you to select a destination
- Download files via LFTP
- Update database with download status and local paths

### 6. Add Notes and Source Files

```bash
# Add note to a file
python3 remote_scanner.py --note 5 "Important backup from 2024-11-14"

# Link source file (the file you used to create/upload this)
python3 remote_scanner.py --source 5 "/local/path/original.zip"

# Add source with notes
python3 remote_scanner.py --source 5 "/path/original.zip" "Created from project archive"
```

## Database Structure

### Tables

**remote_files**
- Stores metadata about files on the remote server
- Tracks when files were first/last seen
- Allows historical tracking

**downloads**
- Tracks download attempts
- Stores local paths where files were saved
- Records success/failure status
- Holds your custom notes

**source_files**
- Links remote files to their original source files
- Helps you remember which local file was used to create the remote file

## Common Workflows

### Workflow 1: Regular Scanning

```bash
# Weekly scan to keep database current
python3 remote_scanner.py --scan

# Review what's new
python3 remote_scanner.py --list | head -20

# Queue interesting files
python3 remote_scanner.py --queue 1,3,7

# Download
./download-manager.sh --from-db
```

### Workflow 2: Project-Based Organization

```bash
# Scan project directory
python3 remote_scanner.py --scan --path "/remote/projects/website"

# Find all backups
python3 remote_scanner.py --search "backup" --path "/remote/projects"

# Add notes about important files
python3 remote_scanner.py --note 15 "Production backup before migration"

# Link to source
python3 remote_scanner.py --source 15 "/local/projects/website.zip"

# Queue and download
python3 remote_scanner.py --queue 15
./download-manager.sh --from-db
```

### Workflow 3: Batch Processing

```bash
# Scan directory
python3 remote_scanner.py --scan --path "/media/videos"

# Queue all video files (IDs 1-50, for example)
python3 remote_scanner.py --queue 1-50

# Review queue before downloading
python3 remote_scanner.py --show-queue

# Download all
./download-manager.sh --from-db
```

## Advanced Usage

### Search by File Type

```bash
# Find all videos
python3 remote_scanner.py --search "*.mp4"
python3 remote_scanner.py --search "*.mkv"

# Find all archives
python3 remote_scanner.py --search "*.zip"
python3 remote_scanner.py --search "*.tar.gz"
```

### Managing the Queue

```bash
# See what's queued
python3 remote_scanner.py --show-queue

# Clear queue (if you changed your mind)
python3 remote_scanner.py --clear-queue

# Re-queue different files
python3 remote_scanner.py --queue 10-20
```

### Tracking Downloads

After downloading, the database automatically records:
- When the file was downloaded
- Where it was saved locally
- Whether download succeeded or failed

View this info with:
```bash
python3 remote_scanner.py --list
```

Files will show status: `queued`, `completed`, or `failed`

## Tips

1. **Regular Scans**: Run `--scan` periodically to keep your database current and track what appears/disappears from the remote server

2. **Use Notes**: Add notes liberally to remember why files are important:
   ```bash
   python3 remote_scanner.py --note 23 "Client project backup - keep indefinitely"
   ```

3. **Track Sources**: Always link source files so you can recreate remote files if needed:
   ```bash
   python3 remote_scanner.py --source 23 "/projects/client-backup-2024.zip"
   ```

4. **Search Before Queuing**: Use `--search` to find exactly what you want before queuing large batches

5. **Review Queue**: Always check `--show-queue` before running the download

## Original Interactive Mode

The original interactive browsing still works:

```bash
# Run without --from-db flag
./download-manager.sh
```

This gives you the menu-driven interface for quick, ad-hoc downloads.

## Database Location

The database file is stored at:
```
/Volumes/Share/RSD/remote_files.db
```

This is a standard SQLite database. You can:
- Back it up regularly
- Query it directly with SQLite tools
- Move it to another system

## Troubleshooting

### Python Not Found
Ensure Python 3 is installed:
```bash
python3 --version
```

### Database Locked
If you get "database is locked" errors, make sure you're not running multiple operations simultaneously.

### Queue Not Showing Files
Clear and rescan:
```bash
python3 remote_scanner.py --clear-queue
python3 remote_scanner.py --scan
python3 remote_scanner.py --queue 1-10
```

## Examples in Action

```bash
# Complete workflow example
$ python3 remote_scanner.py --scan --path "/backups"
Scanning remote directory: /backups
Found 47 files
Storing in database...
✓ Stored 47 files in database

$ python3 remote_scanner.py --search "database"
Found 3 files:

ID     Filename                                           Size       Modified             Status
========================================================================================================================
12     database_backup_2024-11-14.sql.gz                 245.3MB    Nov 14 10:30         -
18     database_backup_2024-11-13.sql.gz                 243.1MB    Nov 13 10:30         -
23     database_schema.sql                               15.2KB     Nov 10 14:22         -

$ python3 remote_scanner.py --note 12 "Latest production backup - critical"
✓ Added note to: database_backup_2024-11-14.sql.gz

$ python3 remote_scanner.py --queue 12
✓ Queued: database_backup_2024-11-14.sql.gz (ID: 12)
1 file(s) queued for download

$ ./download-manager.sh --from-db
[Downloads the file via LFTP with pretty interface]

$ python3 remote_scanner.py --list | grep database
12     database_backup_2024-11-14.sql.gz                 245.3MB    Nov 14 10:30         completed
       Note: Latest production backup - critical
```

## Integration with Existing Workflow

You can mix both modes:
- Use database mode for planned, tracked downloads
- Use interactive mode for quick, one-off downloads
- Both use the same LFTP configuration
- Both log to the same log files
