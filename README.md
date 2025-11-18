# 🚀 Remote Server Download Manager 📥

A beautiful, user-friendly command-line tool for downloading files from remote servers via SFTP/LFTP with an emoji-rich, colorful interface designed to make file management enjoyable!

## ✨ Features

### Interactive Mode
- 🎨 **Colorful Interface** - Easy-to-read color-coded menus and messages
- 😊 **Emoji-Enhanced** - Visual indicators for files, folders, and status
- 🧭 **Easy Navigation** - Browse remote directories like a file explorer
- 📋 **Multi-Select** - Download multiple files at once with simple number ranges
- 📍 **Quick Destinations** - Pre-configured download locations on your NAS
- 📊 **Progress Tracking** - Visual progress bars for downloads
- 🔐 **SSH Key Auth** - Secure authentication using SSH keys
- 📝 **Activity Logging** - Keep track of all downloads
- ♿ **ADHD-Friendly** - Clear visual organization, minimal typing required

### Database Mode (NEW!)
- 🗄️ **SQLite Database** - Store and track all remote files locally
- 🔍 **Offline Browsing** - Search files without connecting to remote server
- 📝 **Note Taking** - Add custom notes to files for organization
- 🔗 **Source Tracking** - Link remote files to their original local sources
- 📊 **Download History** - Track what you've downloaded and where
- 📥 **Queue Management** - Queue files for batch downloading
- 🔎 **Advanced Search** - Find files by name, type, path, or date
- 📈 **Status Tracking** - Monitor queued, completed, and failed downloads

### Web Interface (NEW!)
- 🌐 **Browser-Based UI** - Access from any device on your network
- 🖱️ **Click to Queue** - Visual file selection with checkboxes
- 📱 **Mobile Friendly** - Works on phones and tablets
- 🎨 **ADHD-Friendly Design** - Colorful, clear, low-friction interface
- ⚡ **Real-Time Updates** - Stats update automatically
- 🔍 **Live Search** - Filter files as you type
- 📊 **Visual Dashboard** - See stats and queue status at a glance

## 🎯 Perfect For

- Downloading files from remote servers without wrestling with command-line syntax
- Managing multiple file transfers efficiently
- Reducing pre-execution fatigue with simple menu navigation
- Anyone who wants a more pleasant terminal experience!

## 📋 Requirements

- Linux-based system (tested on UGOS/Ugreen NAS)
- `lftp` installed
- SSH key authentication set up for your remote server
- Bash shell
- Python 3 (for database mode and web interface)
- Flask (`pip3 install flask` for web interface)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download this repository
cd /path/to/your/preferred/location

# Make the script executable
chmod +x download-manager.sh

# Optional: Create a symbolic link for easy access
sudo ln -s $(pwd)/download-manager.sh /usr/local/bin/dlm
```

### 2. Configuration

Edit the `config.conf` file with your settings:

```bash
nano config.conf
```

Update these values:
- `REMOTE_USER` - Your SSH username
- `REMOTE_HOST` - Server hostname or IP address
- `REMOTE_BASE_PATH` - Starting directory on remote server (e.g., /data/)
- `SSH_KEY_PATH` - Path to your SSH private key
- `DOWNLOAD_PATH_1`, `DOWNLOAD_PATH_2`, etc. - Your NAS download locations

### 3. Run

```bash
./download-manager.sh
# or if you created the symbolic link:
dlm
```

## 🎨 Interface Guide

### Color Meanings

- 🟢 **Green** - Success messages, completed actions
- 🔵 **Blue** - Headers, section titles, menu options
- 🟡 **Yellow** - Warnings, important notices
- 🔴 **Red** - Errors, critical issues
- 🔷 **Cyan** - File/folder names, paths
- 🟣 **Magenta** - Selected items, highlights

### Emoji Guide

#### File Types
- 📁 Folders/Directories
- 🎥 Video files (.mp4, .mkv, .avi, etc.)
- 🎵 Audio files (.mp3, .flac, .wav, etc.)
- 📷 Image files (.jpg, .png, .gif, etc.)
- 📦 Archives (.zip, .tar, .gz, etc.)
- 📝 Documents (.pdf, .doc, .txt, etc.)
- 💾 Data files (.json, .xml, .csv, etc.)
- 📄 Generic files

#### Status Indicators
- ✅ Success/Connected
- ⚠️ Warning
- ❌ Error
- 🔗 Connection status
- 📥 Downloading
- 🎯 Selected
- 🏠 Home/Back

## 📖 Usage Examples

### Mode 1: Interactive Browsing (Original)

1. **Launch the manager:**
   ```bash
   ./download-manager.sh
   ```

2. **Navigate directories:**
   - Select numbered folders to enter them
   - Use "Back" option to go up one level
   - Use "Home" to return to base path

3. **Select files:**
   - Single file: `3`
   - Multiple files: `1,3,5`
   - Range: `2-6`
   - All files: `all`

4. **Choose destination:**
   - Select from pre-configured paths
   - Or enter a custom path

5. **Download:**
   - Watch the progress bar
   - Get confirmation when complete!

### Mode 2: Database-Driven (NEW!)

1. **Scan remote directory:**
   ```bash
   python3 remote_scanner.py --scan
   ```

2. **Search for files:**
   ```bash
   python3 remote_scanner.py --list
   python3 remote_scanner.py --search "*.mp4"
   python3 remote_scanner.py --search "backup"
   ```

3. **Queue files for download:**
   ```bash
   python3 remote_scanner.py --queue 1,5,10
   python3 remote_scanner.py --queue 1-20
   ```

4. **Add notes (optional):**
   ```bash
   python3 remote_scanner.py --note 5 "Important backup"
   python3 remote_scanner.py --source 5 "/path/to/source.zip"
   ```

5. **Download queued files:**
   ```bash
   ./download-manager.sh --from-db
   ```

### Mode 3: Web Interface (NEW!)

1. **Install Flask:**
   ```bash
   pip3 install flask
   ```

2. **Start the web server:**
   ```bash
   python3 web_app.py
   ```

3. **Open in browser:**
   - From your Mac/PC: `http://YOUR-NAS-IP:5000`
   - From the NAS: `http://localhost:5000`

4. **Use the visual interface:**
   - Click to browse files
   - Check boxes to select files
   - Queue files with one click
   - Start downloads from the Queue page

**See [WEB_INTERFACE_GUIDE.md](WEB_INTERFACE_GUIDE.md) for detailed web interface documentation.**
**See [DATABASE_WORKFLOW.md](DATABASE_WORKFLOW.md) for detailed database mode documentation.**
**See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for a quick command reference.**

## 🔧 Configuration Options

### Adding More Download Destinations

Edit `config.conf` and add:

```bash
DOWNLOAD_PATH_4="/volume1/your-new-path"
PATH_4_NAME="Your Custom Name"
```

### Changing the Remote Base Path

If your files are in a different location:

```bash
REMOTE_BASE_PATH="/your/custom/path/"
```

### Using a Different SSH Key

```bash
SSH_KEY_PATH="/path/to/your/custom/key"
```

## 📝 Logs

Download activity is logged to `logs/download-history.log`

View recent downloads:
```bash
tail -f logs/download-history.log
```

## 🐛 Troubleshooting

### Connection Issues

1. **Verify SSH key authentication works:**
   ```bash
   ssh -i ~/.ssh/id_rsa user@hostname
   ```

2. **Check lftp is installed:**
   ```bash
   which lftp
   ```

3. **Test lftp connection:**
   ```bash
   lftp sftp://user@hostname
   ```

### Permission Issues

Make sure the script is executable:
```bash
chmod +x download-manager.sh
```

### Path Issues

Ensure all paths in `config.conf` are absolute paths and exist on your system.

## 🤝 Support

If you encounter issues:
1. Check the logs in `logs/download-history.log`
2. Verify your configuration in `config.conf`
3. Test your SSH connection manually
4. Ensure lftp is properly installed

## 📄 License

Free to use and modify for personal use.

## 🎉 Enjoy!

Happy downloading! May your file transfers be swift and your terminal experience delightful! 🚀✨