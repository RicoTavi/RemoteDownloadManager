# 🚀 Quick Setup Guide

Welcome! Let's get your Remote Server Download Manager up and running in just a few minutes! 🎉

## ✅ Step-by-Step Setup

### 1️⃣ Check Requirements

First, make sure you have `lftp` installed on your NAS:

```bash
# Check if lftp is installed
which lftp

# If not installed, install it:
# For Debian/Ubuntu-based systems (including UGOS):
sudo apt-get update
sudo apt-get install lftp
```

### 2️⃣ Configure Your Settings

Open the configuration file:

```bash
nano config.conf
```

**Update these important settings:**

```bash
# Your SSH username for the remote server
REMOTE_USER="your_actual_username"

# Your server's hostname or IP address
REMOTE_HOST="192.168.1.100"  # or "server.example.com"

# Where your files are located on the remote server
REMOTE_BASE_PATH="/data/"

# Path to your SSH key (usually this is correct)
SSH_KEY_PATH="~/.ssh/id_rsa"

# Your NAS download locations
DOWNLOAD_PATH_1="/volume1/downloads"
PATH_1_NAME="📥 Downloads"

DOWNLOAD_PATH_2="/volume1/media"
PATH_2_NAME="🎬 Media"
```

**💡 Tips:**
- Use absolute paths (starting with `/`)
- Make sure the paths exist on your NAS
- You can add up to 5 quick-access download locations

### 3️⃣ Verify SSH Key Setup

Make sure your SSH key is set up correctly:

```bash
# Check if your SSH key exists
ls -la ~/.ssh/id_rsa

# If it doesn't exist, create one:
ssh-keygen -t rsa -b 4096

# Copy your public key to the remote server
ssh-copy-id -i ~/.ssh/id_rsa.pub your_username@your_server
```

**Test your SSH connection:**

```bash
ssh -i ~/.ssh/id_rsa your_username@your_server
```

If this works without asking for a password, you're all set! ✅

### 4️⃣ Test the Connection

Before using the full interface, test the connection:

```bash
./download-manager.sh
```

Then select option `4` (🔍 Test Connection) from the main menu.

If you see "✅ Connection successful!" - you're ready to go! 🎉

### 5️⃣ Start Using It!

From the main menu, select option `1` (📁 Browse Remote Server) and start exploring!

---

## 🎯 Quick Usage Tips

### Navigating Directories

- **Enter a folder**: Just type its number
- **Go back**: Type `..`
- **Go to base**: Type `0`
- **Return to menu**: Type `q`

### Selecting Files

- **One file**: `3`
- **Multiple files**: `1,3,5`
- **Range of files**: `2-6`
- **All files**: `all`

### Example Session

```
1. Launch: ./download-manager.sh
2. Select: 1 (Browse Remote Server)
3. Navigate to your files
4. Select files: 1,3,5
5. Choose destination: 1 (Downloads)
6. Watch the magic happen! ✨
```

---

## 🐛 Troubleshooting

### "lftp is not installed"

Install it:
```bash
sudo apt-get install lftp
```

### "Connection failed"

1. Check your config.conf settings
2. Test SSH manually: `ssh -i ~/.ssh/id_rsa user@host`
3. Verify the SSH key path is correct
4. Make sure the remote server is accessible

### "Permission denied"

Check SSH key permissions:
```bash
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
```

### "Directory doesn't exist"

Make sure the paths in config.conf exist:
```bash
# Check if path exists
ls -la /volume1/downloads

# Create if needed
mkdir -p /volume1/downloads
```

---

## 🎨 Making It Even Better

### Create a Shortcut

Add this to your `~/.bashrc` or `~/.zshrc`:

```bash
alias dlm='/path/to/download-manager.sh'
```

Then just type `dlm` to launch! 🚀

### Add More Download Locations

Edit `config.conf` and add:

```bash
DOWNLOAD_PATH_3="/volume1/backups"
PATH_3_NAME="💾 Backups"

DOWNLOAD_PATH_4="/volume1/documents"
PATH_4_NAME="📄 Documents"
```

---

## 📝 Need Help?

1. Check the logs: `cat logs/download-history.log`
2. Read the main README.md for detailed information
3. Use the built-in help: Select option `5` from main menu

---

## 🎉 You're All Set!

Enjoy your beautiful, stress-free file downloading experience! 

Remember: This tool is designed to make your life easier. If something feels confusing or difficult, that's feedback we can use to improve it! 💪

Happy downloading! 🚀✨