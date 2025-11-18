# 🚀 Quick Start Guide

**Super fast, super simple download manager for your NAS**

---

## What It Does

✅ Browse files on remote server
✅ Download files crazy fast (uses rsync)
✅ Export file lists to CSV
✅ Run from anywhere on your NAS

---

## Get Started

### 1. First Time Setup
```bash
ssh ugreen
source ~/.bashrc
```

### 2. Launch It
```bash
dm
```

That's it. You're in.

---

## Main Menu

```
1. Browse Remote Server    ← Download stuff
2. Configure Settings      ← See settings
3. View Download Logs      ← See what happened
4. Test Connection         ← Check if working
5. Clear Cache            ← Clear old data
6. Help                   ← More info
0. Exit                   ← Leave
```

---

## Browse & Download

**Basic Flow:**
1. Type `1` → Browse files
2. Pick file number → Type `5` or `1,3,5` or `2-10`
3. Choose where to save
4. Watch it download ⚡

**Quick Commands:**
- `all` → Download everything
- `e` → Export to CSV
- `f` → Toggle folder sizes on/off
- `r` → Refresh list
- `..` → Go up one folder
- `q` → Back to main menu

---

## Export to CSV (No GUI)

**Get a file list without entering interactive mode:**

```bash
dm --export /remote/path
```

**Where it saves:**
`/volume1/Share/RSD/exports/`

**Includes:**
- File names
- Sizes (including folder sizes!)
- Dates
- Numbers (for easy downloading later)

---

## Use Cases

### Scenario 1: Quick Browse & Download
```bash
ssh ugreen
dm
→ Type: 1
→ Pick files: 5,12,18
→ Choose destination: 1
→ Done!
```

### Scenario 2: Get CSV to Review Later
```bash
ssh ugreen
dm --export /torrents/data
→ Opens CSV on iPad
→ Note numbers: 45, 67, 89
→ Back to dm: 45,67,89
→ Download!
```

### Scenario 3: From Anywhere
```bash
ssh ugreen
cd /tmp
dm
→ Works from any directory!
```

---

## Files & Folders

**Your files live here:**
- Scripts: `/volume1/Share/RSD/`
- CSV exports: `/volume1/Share/RSD/exports/`
- Logs: `/volume1/Share/RSD/logs/`
- Downloads: *You choose each time*

---

## Settings

**Edit config:**
```bash
nano /volume1/Share/RSD/config.conf
```

**Key settings:**
- `REMOTE_HOST` → Server address
- `REMOTE_USER` → Username
- `SSH_KEY_PATH` → Your SSH key
- `DOWNLOAD_PATH_1` → Quick save location #1
- `SHOW_FOLDER_SIZES` → Show folder sizes (true/false)

---

## Common Commands

| What You Want | Type This |
|---------------|-----------|
| Launch interactive | `dm` |
| Export to CSV | `dm --export /path` |
| Get help | `dm --help` |
| See all options | Press `?` when browsing |

---

## Speed

**Before (SFTP):** 🐌 Slow
**Now (rsync):** ⚡ 3-5x faster

You'll see real-time speed during downloads.

---

## Troubleshooting

**Can't run `dm`?**
```bash
source ~/.bashrc
```

**Connection failed?**
```bash
dm → Option 4 (Test Connection)
```

**Need to see what happened?**
```bash
dm → Option 3 (View Logs)
```

---

## That's It!

Just remember:
1. `dm` → Start it
2. `1` → Browse
3. Type numbers → Download

Everything else is optional.

---

**GitHub:** https://github.com/RicoTavi/RemoteDownloadManager
**Location:** `/volume1/Share/RSD/`
