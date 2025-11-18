# Changelog

## Version 2.0 - Database Mode (2024-11-15)

### Major New Features

#### Database-Driven Workflow
- Added SQLite database for tracking remote files
- New Python script `remote_scanner.py` for database management
- Queue-based download system
- Offline file browsing and searching
- Download history tracking

#### File Organization
- Custom notes for each file
- Source file tracking (bidirectional references)
- Advanced search capabilities
- File metadata storage (size, date, type)

#### Enhanced Download Management
- Queue multiple files for batch downloading
- Track download status (queued, completed, failed)
- Record local paths where files are saved
- Integration with existing bash script

### New Files
- `remote_scanner.py` - Database manager and scanner
- `remote_files.db` - SQLite database (auto-created)
- `DATABASE_WORKFLOW.md` - Detailed workflow documentation
- `QUICK_REFERENCE.md` - Quick command reference
- `CHANGELOG.md` - This file

### Modified Files
- `download-manager.sh` - Added `--from-db` flag for database mode
- `README.md` - Updated with database mode documentation

### Database Schema

**remote_files table:**
- Stores metadata about files on remote server
- Tracks first seen and last seen dates
- Records file size, type, and modification date

**downloads table:**
- Tracks download queue and history
- Stores custom notes
- Records local paths and download status

**source_files table:**
- Links remote files to their local source files
- Helps track which file was used to create remote file

### Usage

**Original Interactive Mode (unchanged):**
```bash
./download-manager.sh
```

**New Database Mode:**
```bash
# Scan remote directory
python3 remote_scanner.py --scan

# Search and queue files
python3 remote_scanner.py --search "*.mp4"
python3 remote_scanner.py --queue 1,5,10

# Download queued files
./download-manager.sh --from-db
```

### Benefits
- Keep historical records of remote files
- Plan downloads offline
- Track what you've downloaded and where
- Add contextual notes for better organization
- Link remote files to their sources
- Search without connecting to remote server

### Backward Compatibility
- Original interactive mode works exactly as before
- No breaking changes to existing workflow
- Database mode is optional enhancement
- Both modes share same configuration file

## Version 1.0 - Initial Release

### Features
- Interactive menu-driven interface
- SFTP/LFTP integration
- SSH key authentication
- Multi-file selection
- Pre-configured download paths
- Colorful emoji-enhanced UI
- Download logging
- ADHD-friendly design
