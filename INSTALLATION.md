# Installation & Deployment Guide

## Complete Setup Instructions

### Prerequisites

- UGOS/Ugreen NAS or Linux system
- SSH access to remote server
- SSH key authentication configured
- `lftp` installed
- Python 3 installed

### Step 1: Upload Files to NAS

Upload all files from this directory to your NAS:

```bash
# From your Mac, copy files to NAS
scp -r /Volumes/Share/RSD/* user@your-nas:/volume1/downloads/RSD/

# Or use your NAS file manager to upload the entire folder
```

### Step 2: Install Dependencies on NAS

SSH into your NAS and install requirements:

```bash
ssh user@your-nas

# Navigate to the directory
cd /volume1/downloads/RSD

# Install Flask for web interface
pip3 install -r requirements.txt

# Or manually:
pip3 install flask

# Verify lftp is installed
which lftp

# If not installed:
# Debian/Ubuntu: sudo apt-get install lftp
# RedHat/CentOS: sudo yum install lftp
```

### Step 3: Configure Settings

Edit the configuration file:

```bash
nano config.conf
```

Update these settings:
- `REMOTE_USER` - Your SSH username for remote server
- `REMOTE_HOST` - Remote server hostname or IP
- `REMOTE_BASE_PATH` - Starting directory on remote server
- `SSH_KEY_PATH` - Path to your SSH private key
- `DOWNLOAD_PATH_1`, `DOWNLOAD_PATH_2`, etc. - Local NAS download destinations

### Step 4: Make Scripts Executable

```bash
chmod +x download-manager.sh
chmod +x remote_scanner.py
chmod +x web_app.py
```

### Step 5: Test Installation

#### Test Terminal Mode

```bash
./download-manager.sh
```

You should see the colorful menu. Press `0` to exit.

#### Test Database Mode

```bash
# Initialize database by scanning
python3 remote_scanner.py --scan

# List files
python3 remote_scanner.py --list

# Check queue
python3 remote_scanner.py --show-queue
```

#### Test Web Interface

```bash
# Start web server
python3 web_app.py
```

Then from your Mac, open browser to: `http://YOUR-NAS-IP:5000`

Press `Ctrl+C` to stop the web server.

## Deployment Options

### Option A: Run Manually (Quick Testing)

**Terminal Mode:**
```bash
./download-manager.sh
```

**Web Interface:**
```bash
python3 web_app.py
```

### Option B: Run in Screen (Background, Can Reattach)

Perfect for leaving web interface running:

```bash
# Start web interface in screen
screen -S download-web
python3 web_app.py

# Detach: Press Ctrl+A, then D
# Reattach later: screen -r download-web
```

### Option C: Systemd Service (Auto-Start on Boot)

Create `/etc/systemd/system/download-web.service`:

```ini
[Unit]
Description=Remote Download Manager Web Interface
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/volume1/downloads/RSD
ExecStart=/usr/bin/python3 /volume1/downloads/RSD/web_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable download-web
sudo systemctl start download-web
sudo systemctl status download-web
```

View logs:
```bash
sudo journalctl -u download-web -f
```

### Option D: Cron for Automated Scans

Add to crontab to scan daily:

```bash
crontab -e

# Add this line (scans daily at 2 AM):
0 2 * * * cd /volume1/downloads/RSD && /usr/bin/python3 remote_scanner.py --scan >> logs/scan.log 2>&1
```

## Usage Workflows

### Quick Start Workflow

1. **Start web interface** (in screen or as service)
2. **Bookmark** `http://YOUR-NAS-IP:5000` on your Mac/phone
3. **Open bookmark** whenever you want to download files
4. **Scan, queue, download** - all from the browser!

### Daily Usage

**From your Mac's browser:**
1. Visit `http://nas-ip:5000`
2. Click "Scan Remote" to update database
3. Search or browse files
4. Check boxes next to files you want
5. Click "Queue Selected"
6. Go to Queue page
7. Click "Start Download"
8. Close browser - downloads continue on NAS

### Command Line Usage

**One-off downloads:**
```bash
./download-manager.sh  # Interactive menu
```

**Database workflow:**
```bash
# Scan and search
python3 remote_scanner.py --scan
python3 remote_scanner.py --search "backup"

# Queue files (IDs from search results)
python3 remote_scanner.py --queue 5,10,15

# Add notes
python3 remote_scanner.py --note 5 "Important file"

# Download
./download-manager.sh --from-db
```

## File Structure

```
RSD/
├── download-manager.sh       # Main bash download script
├── remote_scanner.py         # Database management CLI
├── web_app.py               # Web interface server
├── config.conf              # Configuration file
├── remote_files.db          # SQLite database (created automatically)
├── requirements.txt         # Python dependencies
│
├── templates/               # Web interface HTML
│   ├── base.html
│   ├── index.html
│   └── queue.html
│
├── static/                  # Web interface CSS
│   └── style.css
│
├── logs/                    # Download logs
│   └── download-history.log
│
└── docs/                    # Documentation
    ├── README.md
    ├── DATABASE_WORKFLOW.md
    ├── WEB_INTERFACE_GUIDE.md
    ├── QUICK_REFERENCE.md
    ├── ROADMAP.md
    └── INSTALLATION.md (this file)
```

## Recommended Setup

For the best experience:

1. **Install as systemd service** - Web interface always available
2. **Add cron job** - Daily automatic scans
3. **Bookmark** the web interface on all devices
4. **Use web interface** for browsing and queuing
5. **Let NAS download** in background
6. **Check terminal mode** when you're SSH'd in for quick downloads

## Network Access

### Find Your NAS IP

```bash
# On NAS:
hostname -I

# Or:
ip addr show
```

### Access Points

- **Web Interface:** `http://YOUR-NAS-IP:5000`
- **SSH Access:** `ssh user@YOUR-NAS-IP`
- **Logs:** `ssh user@nas "tail -f /volume1/downloads/RSD/logs/download-history.log"`

## Security Considerations

### Web Interface Security

The web interface runs without authentication by default (for ease of use on home networks).

**Recommendations:**
- Only run on trusted home/office networks
- Don't expose port 5000 to the internet
- If needed, add authentication (see WEB_INTERFACE_GUIDE.md)

### SSH Key Security

```bash
# Ensure your SSH key has correct permissions
chmod 600 ~/.ssh/id_rsa
```

## Troubleshooting

### Common Issues

**Flask not found:**
```bash
pip3 install flask
```

**Permission denied:**
```bash
chmod +x *.sh *.py
```

**Can't access web interface:**
- Check firewall on NAS
- Verify web server is running: `ps aux | grep web_app.py`
- Try from NAS first: `curl http://localhost:5000`

**Database errors:**
```bash
# Re-initialize database
rm remote_files.db
python3 remote_scanner.py --scan
```

### Getting Help

1. Check documentation in this folder
2. Review logs: `tail -f logs/download-history.log`
3. Test connection: `./download-manager.sh` (choose option 4: Test Connection)

## Next Steps

After installation:

1. **Read the guides:**
   - [README.md](README.md) - Overview
   - [WEB_INTERFACE_GUIDE.md](WEB_INTERFACE_GUIDE.md) - Web UI details
   - [DATABASE_WORKFLOW.md](DATABASE_WORKFLOW.md) - Database usage
   - [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command cheat sheet

2. **Set up automation:**
   - Configure systemd service
   - Add cron job for scans

3. **Start using it:**
   - Scan your remote server
   - Queue some files
   - Download them!

Enjoy your new download manager! 🚀
