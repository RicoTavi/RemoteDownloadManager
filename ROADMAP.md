# Feature Roadmap

## Completed Features ✅

### Version 1.0
- [x] Interactive terminal browsing
- [x] LFTP/SFTP integration
- [x] Multi-file selection
- [x] Pre-configured download paths
- [x] Colorful ADHD-friendly UI
- [x] Download logging

### Version 2.0
- [x] SQLite database for file tracking
- [x] Remote directory scanning
- [x] Offline file browsing
- [x] Queue management
- [x] Note-taking system
- [x] Source file tracking
- [x] Download history
- [x] CLI database operations

## Completed ✅

### Version 2.1 - Web Interface (2024-11-15)
- [x] Flask-based web UI
- [x] Visual file browser with DataTables
- [x] Click-based queue management
- [x] Search and filter interface
- [x] Note and source editing in browser
- [x] Responsive design (works on phone/tablet)
- [x] Sortable columns (click headers)
- [x] Pagination (25/50/100/250/All)
- [x] Column reordering (drag headers)
- [x] Persistent state (remembers sort/page)
- [x] Smart file size sorting
- [x] **Per-file destination paths** - Different files to different folders
- [x] Server added date tracking
- [x] Top-level folder inclusion

## In Progress 🚧

### Version 2.2 - Future Enhancements
- [ ] Auto-start service configuration
- [ ] Custom UI theme/styling

## Future Enhancements 💡

### High Priority

- [ ] **Recursive directory scanning** - Scan entire directory trees on remote server
  - Currently scans single directory only
  - Add `--recursive` flag functionality
  - Store full path hierarchy in database

- [ ] **Automatic scanning schedule** - Periodic scans via cron
  - Create cron helper script
  - Configurable scan intervals
  - Email/notification on new files found

### Medium Priority
- [ ] **File filtering rules** - Auto-queue files based on patterns
  - Example: Auto-queue all `.mp4` files larger than 1GB
  - Rule-based destination assignment
  - Configurable filters in config.conf

- [ ] **Download bandwidth limiting** - Control transfer speed
  - Add lftp rate limiting options
  - Configurable per-download or globally

- [ ] **Duplicate detection** - Prevent re-downloading same files
  - Check local filesystem before downloading
  - Checksum comparison
  - Warning in UI if file exists

- [ ] **File preview/metadata** - View more details before downloading
  - Extended file attributes
  - Preview for text files
  - Media file metadata (duration, resolution, etc.)

### Low Priority / Nice to Have
- [ ] **Multi-server support** - Manage multiple remote servers
  - Separate database tables per server
  - Server selection in UI
  - Multiple config profiles

- [ ] **Download resume** - Resume interrupted downloads
  - LFTP supports this, just need to expose it
  - Track partial downloads in database

- [ ] **File tagging system** - Tag files for organization
  - Add tags table to database
  - Tag-based search and filtering
  - Predefined tag categories

- [ ] **Statistics dashboard** - Visualize download history
  - Total data downloaded
  - Most downloaded file types
  - Download success rate
  - Charts and graphs

- [ ] **API endpoints** - RESTful API for automation
  - JSON API alongside web UI
  - Programmatic access to database
  - Webhook support for completed downloads

- [ ] **Mobile app** - Native iOS/Android app
  - Uses API from above
  - Push notifications for completed downloads
  - Quick file browser

## Community Requests 📬

Have an idea? Add it here!

---

## Version History

**v2.1** (In Progress) - Web Interface
**v2.0** (2024-11-15) - Database Mode
**v1.0** (Initial) - Interactive Terminal Mode
