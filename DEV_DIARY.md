# Development Diary

## Session: 2024-11-15

### Session Goal
Transform the bash-based remote file downloader into a full-featured database-driven system with web interface.

### Starting Point
- Working bash script ([download-manager.sh](download-manager.sh)) with interactive terminal UI
- LFTP-based downloads via SFTP
- Pre-configured download destinations
- Basic file browsing and multi-select

### What We Built

#### 1. Database System (SQLite)
**File:** [remote_scanner.py](remote_scanner.py)

**Database Schema:**
- `remote_files` table - Tracks files on remote server
  - Added `server_added_date` field to track when files appeared on server
  - Tracks first_seen/last_seen for historical data
  - Supports both files AND folders (type='folder')
- `downloads` table - Download queue and history
  - `local_path` field for per-file destinations
  - Status tracking (queued, completed, failed)
  - Notes field for user annotations
- `source_files` table - Links remote files to local source files

**Key Features:**
- Scan remote directories via LFTP
- Store metadata locally
- Search/filter capabilities
- Queue management
- Note-taking and source tracking

**CLI Commands:**
```bash
python3 remote_scanner.py --scan                    # Scan remote
python3 remote_scanner.py --list                    # List all files
python3 remote_scanner.py --search "pattern"        # Search
python3 remote_scanner.py --queue 1,5,10            # Queue files
python3 remote_scanner.py --note 5 "My note"        # Add note
python3 remote_scanner.py --source 5 "/path"        # Link source
python3 remote_scanner.py --show-queue              # View queue
python3 remote_scanner.py --export-queue            # Export as JSON
```

#### 2. Web Interface (Flask + DataTables)
**Files:** [web_app.py](web_app.py), [templates/](templates/), [static/](static/)

**Stack:**
- Flask web server (port 5001 - avoiding AirPlay conflict on macOS)
- jQuery + DataTables for spreadsheet-like UI
- Responsive design (works on mobile)
- ADHD-friendly colorful design

**Features:**
- Sortable columns (click headers for ▲/▼ sorting)
- Pagination (25/50/100/250/All rows per page)
- Column reordering (drag to rearrange)
- Persistent state (remembers your preferences)
- Smart file size sorting (understands KB/MB/GB)
- Live search and filtering
- Per-row destination selection
- Visual queue management

**Pages:**
- `/` - Main file browser with DataTables
- `/queue` - Queue management and download trigger

**API Endpoints:**
- `POST /api/scan` - Trigger remote scan
- `GET /api/search` - Search files
- `POST /api/queue/add` - Queue files (with destinations)
- `POST /api/queue/remove/<id>` - Remove from queue
- `POST /api/queue/clear` - Clear queue
- `POST /api/note/update` - Add/update notes
- `POST /api/source/update` - Link source files
- `POST /api/download/trigger` - Start download process
- `GET /api/stats` - Database statistics

#### 3. Enhanced Bash Script
**File:** [download-manager.sh](download-manager.sh)

**New Features:**
- `--from-db` flag for database-driven downloads
- Per-file destination handling
- Auto-creates destination directories
- Shows destination path during download
- Integrates with Python scanner for status updates

**Download Flow:**
1. Read queued files from database (JSON format)
2. Each file has optional `local_path` destination
3. Falls back to DOWNLOAD_PATH_1 if no destination specified
4. Downloads via LFTP to specified paths
5. Updates database with completion status

#### 4. Key Improvements During Session

**Issue 1: Filename Parsing**
- **Problem:** Files with spaces in names were truncated
- **Solution:** Changed `split(None, 8)` to `split(None, 7)` to capture full filename
- **File:** remote_scanner.py line 357

**Issue 2: Timestamp Format**
- **Problem:** Basic timestamp format didn't provide sortable dates
- **Solution:** Added `--time-style=long-iso` to LFTP command
- **Result:** ISO format timestamps (YYYY-MM-DD HH:MM) for proper sorting
- **File:** remote_scanner.py line 334

**Issue 3: Missing Folders**
- **Problem:** Only files were tracked, not directories
- **Solution:** Modified parser to include `file_type='d'` as 'folder'
- **File:** remote_scanner.py lines 359-377

**Issue 4: Port Conflict**
- **Problem:** Port 5000 used by macOS AirPlay
- **Solution:** Changed default port to 5001
- **File:** web_app.py line 337

**Issue 5: Per-File Destinations**
- **Problem:** All files in a batch went to same destination
- **Solution:** Added destination dropdown per file in UI, updated backend to handle map of file_id → destination
- **Files:** templates/index.html (destination column), web_app.py (API update), download-manager.sh (destination logic)

### Technical Decisions

**Why DataTables?**
- User has 250+ files typically
- Needed spreadsheet-like experience
- Sorting, pagination, column resizing
- Mature library with good documentation
- ~120KB overhead acceptable for feature set

**Why SQLite?**
- No server setup needed
- Portable single-file database
- Python built-in support
- Perfect for local file tracking

**Why Flask?**
- Lightweight, easy to deploy
- No complex configuration
- Debug mode for development
- Easy to integrate with existing Python code

**Why Keep Bash Script?**
- LFTP already working well
- Maintains existing download logic
- Separation of concerns (Python = DB, Bash = Download)
- User familiar with it

### File Structure
```
RSD/
├── download-manager.sh       # Enhanced bash downloader (--from-db mode)
├── remote_scanner.py         # Python CLI + database manager
├── web_app.py               # Flask web server (port 5001)
├── config.conf              # User configuration
├── remote_files.db          # SQLite database (auto-created)
├── requirements.txt         # Python dependencies (Flask)
│
├── templates/               # Jinja2 templates
│   ├── base.html           # Base layout with DataTables includes
│   ├── index.html          # File browser page
│   └── queue.html          # Queue management page
│
├── static/                  # Static assets
│   └── style.css           # Custom CSS (ADHD-friendly design)
│
├── logs/                    # Download logs
│   └── download-history.log
│
└── docs/                    # Documentation
    ├── README.md           # Main overview
    ├── DATABASE_WORKFLOW.md
    ├── WEB_INTERFACE_GUIDE.md
    ├── QUICK_REFERENCE.md
    ├── INSTALLATION.md
    ├── ROADMAP.md
    ├── CHANGELOG.md
    └── DEV_DIARY.md (this file)
```

### Current State

**Working Features:**
✅ Three modes of operation (Terminal, CLI, Web)
✅ Database tracking of 250+ files
✅ Web interface running on port 5001
✅ Per-file destination selection
✅ Sortable, paginated table view
✅ Notes and source file tracking
✅ Queue management
✅ LFTP downloads to multiple destinations
✅ Top-level folders included in database
✅ Server added date tracking

**Known Limitations:**
- No recursive directory scanning (planned)
- Web interface uses default design (user wants to customize)
- No auto-start service configured yet
- Folders can't be downloaded (only files)

### Next Steps for Future Sessions

1. **UI Customization**
   - User wants to personalize colors/styling
   - All styles in static/style.css
   - CSS variables at top for easy theming

2. **Systemd Service Setup**
   - Auto-start web interface on boot
   - Template in INSTALLATION.md
   - Needs testing on actual NAS

3. **Recursive Scanning**
   - Scan subdirectories
   - Store full path hierarchy
   - Optional feature (may be large dataset)

4. **Folder Downloads**
   - Support downloading entire folders
   - Would use `lftp mirror` command
   - Add to bash script download logic

### Commands to Remember

**Start Web Interface:**
```bash
cd /Volumes/Share/RSD
python3 web_app.py
# Access at http://localhost:5001 or http://NAS-IP:5001
```

**Scan Remote Server:**
```bash
python3 remote_scanner.py --scan
```

**Download Queued Files:**
```bash
./download-manager.sh --from-db
```

**View Queue:**
```bash
python3 remote_scanner.py --show-queue
```

### Dependencies
- Python 3.x
- Flask (`pip3 install flask`)
- lftp (for SFTP connections)
- SSH key authentication configured

### Notes for Future Developer (or Future You!)

**Database Schema Changes:**
- If you modify the schema, delete remote_files.db and rescan
- Or write a migration script using ALTER TABLE

**Adding New Download Destinations:**
- Edit config.conf
- Add DOWNLOAD_PATH_6, PATH_6_NAME, etc.
- Update templates/index.html to show in dropdown (lines 61-76)

**Customizing DataTables:**
- Configuration in templates/index.html lines 343-404
- Can change default sort, page length, etc.

**Port Changes:**
- Update web_app.py line 337
- Update all documentation mentioning port 5001

**CSS Customization:**
- All styles in static/style.css
- CSS variables lines 15-47 for easy theming
- DataTables overrides lines 559-653

### Performance Notes
- Database queries are fast even with 250+ files
- DataTables handles pagination client-side
- LFTP transfers run sequentially (one at a time)
- Web server is single-threaded (Flask development server)

### Security Notes
- Web interface has NO authentication (runs on local network only)
- SSH key authentication for SFTP
- Database file permissions should be 644
- Don't expose port 5001 to internet without auth

### Success Metrics
✅ Can browse 250+ files with ease
✅ Spreadsheet-like sorting/filtering works
✅ Per-file destinations function correctly
✅ Database tracks all necessary metadata
✅ Web UI accessible from Mac browser
✅ Downloads work via LFTP as before
✅ All three modes operational

### User Feedback
- "This is groovy" ✨
- Wants to customize design (future work)
- Happy with functionality as-is

### Time Investment
- Full session: ~3-4 hours
- Result: Production-ready v2.1 with web interface

---

## End of Session Notes

**What went well:**
- Iterative development approach worked great
- User provided clear feedback on issues
- Quick pivots when problems arose (port conflict, filename parsing, etc.)
- DataTables integration was smooth
- Per-file destinations implemented successfully in one shot

**What to improve next time:**
- Could have asked about UI preferences earlier
- Might want to add authentication from the start for production

**Ready for production:** YES ✅
**User satisfied:** YES ✅
**Documentation complete:** YES ✅

---

*Next session: UI customization and/or systemd service setup*
