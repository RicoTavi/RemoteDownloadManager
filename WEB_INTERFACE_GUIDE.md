# Web Interface Guide

## Overview

The web interface provides a visual, browser-based way to manage your remote file downloads. Access it from any device on your network!

## Installation

### 1. Install Flask

```bash
pip3 install flask
```

### 2. Verify Installation

```bash
python3 web_app.py --help
```

## Starting the Web Interface

### On Your NAS

```bash
cd /Volumes/Share/RSD
python3 web_app.py
```

The web server will start and be accessible at:
- **From the NAS:** http://localhost:5000
- **From your Mac/other devices:** http://YOUR-NAS-IP:5000

### Finding Your NAS IP Address

```bash
# On the NAS, run:
hostname -I
# or
ip addr show
```

## Using the Web Interface

### Main Page: File Browser

**Features:**
- 📁 Browse all files in the database
- 🔍 Search and filter files
- ✅ Select multiple files with checkboxes
- 📥 Queue files for download
- 📝 Add notes to files
- 🔗 Link source files

**Actions:**
1. **Scan Remote Server**
   - Click "🔄 Scan Remote" button
   - Optionally enter a specific path
   - Wait for scan to complete
   - Page refreshes with new files

2. **Search Files**
   - Type in the search box
   - Filter by download status
   - Results update instantly

3. **Queue Files**
   - Check boxes next to files you want
   - Click "📥 Queue Selected"
   - Or click ➕ button on individual files

4. **Add Notes**
   - Click 📝 button next to a file
   - Enter your notes
   - Click "Save Note"

5. **Link Source Files**
   - Click 🔗 button next to a file
   - Enter path to original source file
   - Add optional notes
   - Click "Link Source"

### Queue Page

**Features:**
- 📥 View all queued files
- 🚀 Trigger downloads
- 🗑️ Remove files from queue
- 📋 Clear entire queue

**Actions:**
1. **Start Download**
   - Click "🚀 Start Download" button
   - Confirm the action
   - Download runs in background on NAS
   - Check NAS terminal for progress

2. **Remove Files**
   - Click 🗑️ button next to file
   - Confirm removal

3. **Clear Queue**
   - Click "🗑️ Clear Queue" button
   - Confirm action
   - All queued files removed

### Footer Stats

Real-time statistics showing:
- 📊 Total files in database
- 📥 Files currently queued
- ✅ Completed downloads
- 💾 Total size of files

Updates every 10 seconds automatically.

## Running as a Background Service

### Option 1: Simple Screen Session

```bash
# Start in a screen session
screen -S download-web
python3 web_app.py

# Detach with: Ctrl+A, then D
# Reattach with: screen -r download-web
```

### Option 2: Systemd Service (Linux)

Create `/etc/systemd/system/download-web.service`:

```ini
[Unit]
Description=Remote Download Manager Web Interface
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/Volumes/Share/RSD
ExecStart=/usr/bin/python3 /Volumes/Share/RSD/web_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable download-web
sudo systemctl start download-web
sudo systemctl status download-web
```

### Option 3: Nohup

```bash
nohup python3 web_app.py > web_app.log 2>&1 &
```

## Accessing from Different Devices

### From Your Mac

Open browser and go to:
```
http://YOUR-NAS-IP:5000
```

Bookmark it for quick access!

### From Your Phone/Tablet

Same URL works on mobile devices:
```
http://YOUR-NAS-IP:5000
```

The interface is responsive and works on small screens.

### From Anywhere (Advanced - Requires Port Forwarding)

**Warning:** Only do this if you understand the security implications.

1. Set up port forwarding on your router (port 5000)
2. Use HTTPS with a reverse proxy (nginx, caddy)
3. Add authentication
4. Access via your public IP or domain

## Workflow Examples

### Example 1: Daily Backup Check

1. Open browser to `http://nas:5000`
2. Click "🔄 Scan Remote"
3. Search for "backup"
4. Check files you want
5. Click "📥 Queue Selected"
6. Go to Queue page
7. Click "🚀 Start Download"
8. Close browser - downloads continue!

### Example 2: Organizing Media

1. Browse files
2. Find video files
3. Click 📝 to add notes: "Episode 5, Season 2"
4. Click 🔗 to link source: "/media/source/show.zip"
5. Queue for download
6. Download to media folder

### Example 3: Batch Processing

1. Scan remote server
2. Use "Select All" checkbox
3. Queue everything
4. Add notes to important files
5. Start download
6. Come back later, everything's done!

## Tips & Tricks

### Keyboard Shortcuts

- **Ctrl+F** - Focus search box (browser default)
- **Shift+Click** - Select range (when selecting multiple checkboxes)

### Workflow Tips

1. **Scan regularly** - Run scans on a schedule to keep database current
2. **Use notes** - Add context to files so you remember why they're important
3. **Link sources** - Always link back to original files for tracking
4. **Filter by status** - Quickly find files you haven't downloaded yet
5. **Mobile access** - Check queue status from your phone

### ADHD-Friendly Features

- **Clear visual hierarchy** - Important actions are highlighted
- **Colorful status badges** - Easy to scan at a glance
- **Instant feedback** - Notifications confirm every action
- **Minimal clicks** - Common tasks are 1-2 clicks
- **No page refreshes** - Most actions happen without reloading
- **Persistent queue** - Come back anytime, your queue is saved

## Troubleshooting

### Can't Access from Mac

1. Check NAS IP address: `hostname -I` on NAS
2. Verify web server is running: `ps aux | grep web_app.py`
3. Check firewall: Ensure port 5000 is open
4. Try from NAS first: `curl http://localhost:5000`

### Web Server Won't Start

```bash
# Check if port 5000 is already in use
lsof -i :5000

# Kill existing process if needed
kill -9 PID

# Or use a different port
# Edit web_app.py and change: app.run(host='0.0.0.0', port=5001)
```

### Flask Not Installed

```bash
# Install Flask
pip3 install flask

# Or with sudo if needed
sudo pip3 install flask

# Verify
python3 -c "import flask; print(flask.__version__)"
```

### Database Errors

```bash
# Check database exists
ls -lh remote_files.db

# If missing, run a scan
python3 remote_scanner.py --scan

# Check permissions
chmod 644 remote_files.db
```

### Downloads Not Starting

1. Verify bash script is executable: `chmod +x download-manager.sh`
2. Check script location in web_app.py
3. Look at NAS terminal for error messages
4. Check logs: `tail -f logs/download-history.log`

## Security Notes

### Network Access

The web interface runs on `0.0.0.0:5000`, meaning it's accessible from any device on your network. This is intentional for convenience.

**Recommendations:**
- Only run on trusted networks (home/office)
- Don't expose to the internet without authentication
- Consider adding basic auth if needed

### Adding Authentication (Optional)

To add simple password protection, install Flask-HTTPAuth:

```bash
pip3 install Flask-HTTPAuth
```

Then modify web_app.py (we can add this later if needed).

## Advanced Configuration

### Changing the Port

Edit `web_app.py`, last line:
```python
app.run(host='0.0.0.0', port=8080, debug=False)
```

### Production Mode

For production (always-on) use:
```python
app.run(host='0.0.0.0', port=5000, debug=False)
```

Set `debug=False` for better performance and security.

### Using a Production WSGI Server

For heavy use, install Gunicorn:

```bash
pip3 install gunicorn

# Run with:
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

## Feature Requests

See [ROADMAP.md](ROADMAP.md) for planned enhancements, including:
- Per-file destination selection
- Real-time download progress
- File preview
- And more!

## Support

If you encounter issues:
1. Check this guide
2. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) (if it exists)
3. Review logs in `logs/` directory
4. Check database with: `sqlite3 remote_files.db "SELECT * FROM remote_files LIMIT 5;"`
