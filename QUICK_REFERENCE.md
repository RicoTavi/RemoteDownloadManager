# Quick Reference Guide

## Database Mode - Common Commands

### Scan Remote Server
```bash
python3 remote_scanner.py --scan                    # Scan default path
python3 remote_scanner.py --scan --path "/path"     # Scan specific path
```

### Browse Files
```bash
python3 remote_scanner.py --list                    # List all files
python3 remote_scanner.py --search "*.mp4"          # Search for videos
python3 remote_scanner.py --search "backup"         # Search by name
```

### Queue Files
```bash
python3 remote_scanner.py --queue 5                 # Queue single file
python3 remote_scanner.py --queue 1,5,10            # Queue multiple
python3 remote_scanner.py --queue 1-20              # Queue range
python3 remote_scanner.py --show-queue              # View queue
python3 remote_scanner.py --clear-queue             # Clear queue
```

### Add Notes & Sources
```bash
python3 remote_scanner.py --note 5 "My note here"
python3 remote_scanner.py --source 5 "/path/to/source.zip"
```

### Download
```bash
./download-manager.sh --from-db                     # Download queued files
```

## Interactive Mode
```bash
./download-manager.sh                               # Original menu-driven mode
```

## Complete Workflow Example
```bash
# 1. Scan
python3 remote_scanner.py --scan

# 2. Search
python3 remote_scanner.py --search "backup"

# 3. Queue (use IDs from search results)
python3 remote_scanner.py --queue 12,15,18

# 4. Add notes
python3 remote_scanner.py --note 12 "Critical backup"

# 5. Download
./download-manager.sh --from-db
```

## File Structure
```
/Volumes/Share/RSD/
├── download-manager.sh      # Main download script
├── remote_scanner.py        # Database manager
├── config.conf              # Configuration
├── remote_files.db          # SQLite database
├── logs/                    # Download logs
└── *.md                     # Documentation
```

## Database Tables

**remote_files** - File metadata from remote server
**downloads** - Download history and notes
**source_files** - Links to original source files

## Tips

- Scan regularly to keep database current
- Use notes to track important files
- Link source files for bidirectional reference
- Review queue before downloading
- Mix both modes as needed
