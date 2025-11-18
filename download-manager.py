#!/usr/bin/env python3
"""
Remote Server Download Manager - Python Edition
A fast, reliable file transfer tool with beautiful UI
"""

import os
import sys
import time
import json
import pickle
import hashlib
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import threading
import configparser

try:
    import paramiko
    from paramiko import SSHClient, AutoAddPolicy
except ImportError:
    print("❌ ERROR: paramiko is not installed")
    print("Install it with: pip3 install paramiko")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TransferSpeedColumn, TimeRemainingColumn
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich import box
except ImportError:
    print("❌ ERROR: rich is not installed")
    print("Install it with: pip3 install rich")
    sys.exit(1)


class Config:
    """Configuration manager"""

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = configparser.ConfigParser()

        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        # Read bash-style config (key=value format)
        self._read_bash_config()

    def _read_bash_config(self):
        """Read bash-style config file"""
        config_data = {}
        with open(self.config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes
                        value = value.strip().strip('"').strip("'")
                        # Expand ~ in paths
                        if value.startswith('~'):
                            value = os.path.expanduser(value)
                        config_data[key] = value

        self.data = config_data

    def get(self, key: str, default: str = "") -> str:
        return self.data.get(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(self.data.get(key, default))
        except ValueError:
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.data.get(key, str(default)).lower()
        return value in ('true', 'yes', '1')

    def get_download_paths(self) -> List[Tuple[str, str]]:
        """Get all configured download paths"""
        paths = []
        for i in range(1, 6):
            path = self.get(f'DOWNLOAD_PATH_{i}')
            name = self.get(f'PATH_{i}_NAME')
            if path:
                paths.append((name or f"Path {i}", path))
        return paths

    def set_bool(self, key: str, value: bool):
        """Update a boolean config value and save to file"""
        # Update in-memory data
        self.data[key] = 'true' if value else 'false'

        # Update config file
        try:
            with open(self.config_file, 'r') as f:
                lines = f.readlines()

            # Find and update the line
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith(key + '='):
                    lines[i] = f'{key}={self.data[key]}\n'
                    updated = True
                    break

            # If key doesn't exist, add it
            if not updated:
                lines.append(f'{key}={self.data[key]}\n')

            # Write back to file
            with open(self.config_file, 'w') as f:
                f.writelines(lines)
        except Exception as e:
            raise Exception(f"Failed to update config file: {e}")


class SFTPConnectionManager:
    """Manages SFTP connection with automatic reconnection"""

    def __init__(self, host: str, username: str, key_path: str):
        self.host = host
        self.username = username
        self.key_path = os.path.expanduser(key_path)
        self.ssh_client = None
        self.sftp_client = None
        self.console = Console()

    def connect(self) -> bool:
        """Establish SFTP connection"""
        try:
            self.ssh_client = SSHClient()
            self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())

            # Load private key
            if not os.path.exists(self.key_path):
                self.console.print(f"[red]❌ SSH key not found: {self.key_path}[/red]")
                return False

            # Try different key types (OpenSSH format support)
            key = None
            for key_class in [paramiko.Ed25519Key, paramiko.RSAKey, paramiko.ECDSAKey]:
                try:
                    key = key_class.from_private_key_file(self.key_path)
                    break
                except:
                    continue
            
            if key is None:
                self.console.print(f"[red]❌ Could not load SSH key (unsupported format)[/red]")
                return False

            # Connect with optimized settings
            self.ssh_client.connect(
                hostname=self.host,
                username=self.username,
                pkey=key,
                timeout=30,
                compress=False,  # Disable compression for speed
                allow_agent=False,
                look_for_keys=False
            )

            # Get SFTP client with optimized settings
            self.sftp_client = self.ssh_client.open_sftp()

            # Optimize window and packet sizes for speed
            self.sftp_client.get_channel().transport.window_size = 2147483647
            self.sftp_client.get_channel().transport.packetizer.REKEY_BYTES = pow(2, 40)
            self.sftp_client.get_channel().transport.packetizer.REKEY_PACKETS = pow(2, 40)

            return True

        except Exception as e:
            self.console.print(f"[red]❌ Connection failed: {e}[/red]")
            return False

    def disconnect(self):
        """Close SFTP connection"""
        if self.sftp_client:
            self.sftp_client.close()
        if self.ssh_client:
            self.ssh_client.close()

    def list_directory(self, path: str) -> List[Dict]:
        """List directory contents with file attributes"""
        if not self.sftp_client:
            return []

        try:
            files = []
            for attr in self.sftp_client.listdir_attr(path):
                file_info = {
                    'name': attr.filename,
                    'size': attr.st_size,
                    'mtime': attr.st_mtime,
                    'is_dir': self._is_directory(attr),
                    'mode': attr.st_mode
                }
                files.append(file_info)

            # Sort: by modification time (newest first), regardless of type
            files.sort(key=lambda x: -x['mtime'])
            return files

        except Exception as e:
            self.console.print(f"[red]❌ Failed to list directory: {e}[/red]")
            return []

    def _is_directory(self, attr) -> bool:
        """Check if file attribute is a directory"""
        import stat
        return stat.S_ISDIR(attr.st_mode)

    def download_file(self, remote_path: str, local_path: str, progress_callback=None, chunks=8) -> bool:
        """Download file with chunked parallel download (IDM-style)"""
        if not self.sftp_client:
            return False

        try:
            # Get file size
            file_size = self.sftp_client.stat(remote_path).st_size
            
            # If file is small, just download normally
            if file_size < 10 * 1024 * 1024:  # 10MB
                self.sftp_client.get(remote_path, local_path, callback=progress_callback)
                return True
            
            # Calculate chunk size
            chunk_size = file_size // chunks
            
            # Download chunks in parallel
            temp_files = []
            threads = []
            errors = []
            downloaded_bytes = [0]  # Mutable for thread access
            lock = threading.Lock()
            
            def download_chunk(chunk_idx, start, end):
                try:
                    # Create new SFTP connection for this chunk
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    
                    # Load key
                    key = None
                    for key_class in [paramiko.Ed25519Key, paramiko.RSAKey, paramiko.ECDSAKey]:
                        try:
                            key = key_class.from_private_key_file(self.key_path)
                            break
                        except:
                            continue
                    
                    if key is None:
                        errors.append(f"Chunk {chunk_idx}: Key load failed")
                        return
                    
                    ssh.connect(
                        hostname=self.host,
                        username=self.username,
                        pkey=key,
                        timeout=30,
                        compress=False
                    )
                    
                    sftp = ssh.open_sftp()
                    
                    # Optimize this connection too
                    sftp.get_channel().transport.window_size = 2147483647
                    sftp.get_channel().transport.packetizer.REKEY_BYTES = pow(2, 40)
                    sftp.get_channel().transport.packetizer.REKEY_PACKETS = pow(2, 40)
                    
                    # Download chunk
                    temp_file = f"{local_path}.part{chunk_idx}"
                    temp_files.append(temp_file)
                    
                    with sftp.file(remote_path, "r") as remote_file:
                        remote_file.seek(start)
                        with open(temp_file, "wb") as local_file:
                            bytes_to_read = end - start
                            bytes_read = 0
                            
                            while bytes_read < bytes_to_read:
                                chunk_data = remote_file.read(min(65536, bytes_to_read - bytes_read))
                                if not chunk_data:
                                    break
                                local_file.write(chunk_data)
                                bytes_read += len(chunk_data)
                                
                                # Update progress
                                with lock:
                                    downloaded_bytes[0] += len(chunk_data)
                                    if progress_callback:
                                        progress_callback(downloaded_bytes[0], file_size)
                    
                    sftp.close()
                    ssh.close()
                    
                except Exception as e:
                    errors.append(f"Chunk {chunk_idx}: {e}")
            
            # Start threads for each chunk
            for i in range(chunks):
                start = i * chunk_size
                end = file_size if i == chunks - 1 else (i + 1) * chunk_size
                
                thread = threading.Thread(target=download_chunk, args=(i, start, end))
                thread.start()
                threads.append(thread)
            
            # Wait for all chunks
            for thread in threads:
                thread.join()
            
            # Check for errors
            if errors:
                for error in errors:
                    self.console.print(f"[red]{error}[/red]")
                return False
            
            # Reassemble file
            with open(local_path, "wb") as output:
                for i in range(chunks):
                    temp_file = f"{local_path}.part{i}"
                    with open(temp_file, "rb") as chunk:
                        output.write(chunk.read())
                    os.remove(temp_file)
            
            return True
            
        except Exception as e:
            self.console.print(f"[red]❌ Download failed: {e}[/red]")
            return False

    def get_file_size(self, remote_path: str) -> int:
        """Get remote file size"""
        try:
            return self.sftp_client.stat(remote_path).st_size
        except:
            return 0

    def get_directory_size(self, remote_path: str) -> int:
        """Calculate total size of directory recursively"""
        if not self.sftp_client:
            return 0

        try:
            total_size = 0
            import stat

            def scan_dir(path):
                nonlocal total_size
                try:
                    for attr in self.sftp_client.listdir_attr(path):
                        full_path = os.path.join(path, attr.filename)
                        if stat.S_ISDIR(attr.st_mode):
                            scan_dir(full_path)  # Recursive
                        else:
                            total_size += attr.st_size
                except:
                    pass  # Skip inaccessible directories

            scan_dir(remote_path)
            return total_size
        except:
            return 0


class CacheManager:
    """Manages directory listing cache"""

    def __init__(self, cache_dir: str, max_age: int = 300):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age = max_age

    def _get_cache_key(self, path: str) -> str:
        """Generate cache key from path"""
        return hashlib.md5(path.encode()).hexdigest()

    def get(self, path: str) -> Optional[Tuple[List[Dict], int, Dict[str, int]]]:
        """Get cached directory listing if valid (returns files, age, folder_sizes)"""
        cache_key = self._get_cache_key(path)
        cache_file = self.cache_dir / f"{cache_key}.cache"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)

            cache_time = data['timestamp']
            age = time.time() - cache_time

            if age > self.max_age:
                return None

            # Return folder_sizes if available (for backward compatibility with old caches)
            folder_sizes = data.get('folder_sizes', {})
            return data['files'], int(age), folder_sizes

        except:
            return None

    def set(self, path: str, files: List[Dict], folder_sizes: Dict[str, int] = None):
        """Save directory listing to cache with optional folder sizes"""
        cache_key = self._get_cache_key(path)
        cache_file = self.cache_dir / f"{cache_key}.cache"

        data = {
            'timestamp': time.time(),
            'files': files,
            'folder_sizes': folder_sizes or {}
        }

        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)

    def clear(self):
        """Clear all cache"""
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()

    def get_stats(self) -> Tuple[int, int]:
        """Get cache statistics (count, size in bytes)"""
        cache_files = list(self.cache_dir.glob("*.cache"))
        count = len(cache_files)
        size = sum(f.stat().st_size for f in cache_files)
        return count, size


class DownloadManager:
    """Main download manager application"""

    def __init__(self, config_path: str):
        self.console = Console()
        self.script_dir = Path(__file__).parent

        # Load configuration
        try:
            self.config = Config(config_path)
        except Exception as e:
            self.console.print(f"[red]❌ Error loading config: {e}[/red]")
            sys.exit(1)

        # Initialize components
        self.sftp = SFTPConnectionManager(
            self.config.get('REMOTE_HOST'),
            self.config.get('REMOTE_USER'),
            self.config.get('SSH_KEY_PATH')
        )

        cache_dir = self.script_dir / '.cache'
        self.cache = CacheManager(str(cache_dir), max_age=300)

        # State
        self.current_path = self.config.get('REMOTE_BASE_PATH')
        self.base_path = self.config.get('REMOTE_BASE_PATH')

        # Setup logging
        log_dir = self.script_dir / 'logs'
        log_dir.mkdir(exist_ok=True)
        self.log_file = log_dir / 'download-history.log'

    def log(self, message: str):
        """Log message to file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_file, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")

    def show_banner(self):
        """Display application banner"""
        self.console.clear()
        banner = """
[cyan bold]╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║     🚀  REMOTE SERVER DOWNLOAD MANAGER  📥                        ║
║                                                                   ║
║     [dim]Fast, reliable file transfers with Python + Paramiko[/dim]       ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝[/cyan bold]
"""
        self.console.print(banner)

    def format_size(self, bytes: int) -> str:
        """Format bytes to human-readable size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.1f}{unit}"
            bytes /= 1024.0
        return f"{bytes:.1f}PB"

    def format_time(self, seconds: int) -> str:
        """Format seconds to human-readable time"""
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        secs = seconds % 60
        if minutes < 60:
            return f"{minutes}m {secs}s"
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"

    def get_file_emoji(self, filename: str) -> str:
        """Get emoji based on file extension"""
        ext = Path(filename).suffix.lower()
        emoji_map = {
            # Videos
            '.mp4': '🎥', '.mkv': '🎥', '.avi': '🎥', '.mov': '🎥', '.wmv': '🎥',
            '.flv': '🎥', '.webm': '🎥', '.m4v': '🎥', '.mpg': '🎥', '.mpeg': '🎥',
            # Audio
            '.mp3': '🎵', '.flac': '🎵', '.wav': '🎵', '.aac': '🎵', '.ogg': '🎵',
            '.m4a': '🎵', '.wma': '🎵', '.opus': '🎵',
            # Images
            '.jpg': '📷', '.jpeg': '📷', '.png': '📷', '.gif': '📷', '.bmp': '📷',
            '.svg': '📷', '.webp': '📷', '.ico': '📷', '.tiff': '📷',
            # Archives
            '.zip': '📦', '.tar': '📦', '.gz': '📦', '.bz2': '📦', '.7z': '📦',
            '.rar': '📦', '.xz': '📦', '.tgz': '📦',
            # Documents
            '.pdf': '📝', '.doc': '📝', '.docx': '📝', '.txt': '📝', '.rtf': '📝',
            '.odt': '📝',
            # Spreadsheets
            '.xls': '📊', '.xlsx': '📊', '.csv': '📊', '.ods': '📊',
            # Code
            '.js': '💻', '.py': '💻', '.sh': '💻', '.bash': '💻', '.java': '💻',
            '.cpp': '💻', '.c': '💻', '.h': '💻', '.go': '💻', '.rs': '💻',
            '.php': '💻', '.rb': '💻',
            # Data
            '.json': '💾', '.xml': '💾', '.yaml': '💾', '.yml': '💾', '.toml': '💾',
            '.ini': '💾', '.conf': '💾',
        }
        return emoji_map.get(ext, '📄')

    def browse_files(self, force_refresh: bool = False):
        """Browse remote files"""
        while True:
            self.show_banner()

            # Connection info
            self.console.print(f"[green]🔗 Connected to: [bold]{self.config.get('REMOTE_USER')}@{self.config.get('REMOTE_HOST')}[/bold][/green]")
            self.console.print(f"[cyan]📁 Current Path: [bold]{self.current_path}[/bold][/cyan]\n")

            # Get directory listing (cached or fresh)
            cached_data = None if force_refresh else self.cache.get(self.current_path)
            folder_sizes = {}

            if cached_data:
                files, age, folder_sizes = cached_data
                self.console.print(f"[dim]📦 Using cached data ({self.format_time(age)} old)[/dim]")
            else:
                with self.console.status("[cyan]🔄 Fetching directory listing...[/cyan]"):
                    files = self.sftp.list_directory(self.current_path)
                    if files:
                        # Cache will be updated later with folder sizes if enabled
                        pass

            force_refresh = False  # Reset after use

            if not files:
                self.console.print("[yellow]⚠️  No files found or error occurred[/yellow]")
                input("\nPress Enter to continue...")
                return

            # Create table
            table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
            table.add_column("#", style="dim", width=4)
            table.add_column("Name", style="white")
            table.add_column("Size", justify="right", style="yellow")
            table.add_column("Modified", style="dim")

            # Add navigation options
            if self.current_path != self.base_path:
                table.add_row("[yellow]0[/yellow]", "[yellow]🏠 Back to base directory[/yellow]", "", "")
                table.add_row("[yellow]..[/yellow]", "[yellow]⬆️  Go up one level[/yellow]", "", "")

            # Add files (calculate directory sizes if enabled and needed)
            show_folder_sizes = self.config.get_bool('SHOW_FOLDER_SIZES', False)
            has_dirs = any(f['is_dir'] for f in files)
            need_to_calculate = show_folder_sizes and has_dirs and not folder_sizes

            if need_to_calculate:
                self.console.print("[dim]📊 Calculating folder sizes...[/dim]")

            for idx, file_info in enumerate(files, 1):
                emoji = "📁" if file_info['is_dir'] else self.get_file_emoji(file_info['name'])
                name = file_info['name'] + "/" if file_info['is_dir'] else file_info['name']

                # Calculate or use cached size for directories
                if file_info['is_dir']:
                    if show_folder_sizes:
                        # Check cache first, then calculate if needed
                        if file_info['name'] in folder_sizes:
                            dir_size = folder_sizes[file_info['name']]
                        else:
                            dir_path = os.path.join(self.current_path, file_info['name'])
                            dir_size = self.sftp.get_directory_size(dir_path)
                            folder_sizes[file_info['name']] = dir_size
                        size = self.format_size(dir_size) if dir_size > 0 else ""
                    else:
                        size = ""  # Don't show size when disabled
                else:
                    size = self.format_size(file_info['size'])

                mtime = datetime.fromtimestamp(file_info['mtime']).strftime('%Y-%m-%d %H:%M')

                style = "cyan bold" if file_info['is_dir'] else "white"
                table.add_row(str(idx), f"{emoji} {name}", size, mtime, style=style)

            # Cache the results with folder sizes
            if files and (not cached_data or need_to_calculate):
                self.cache.set(self.current_path, files, folder_sizes)

            self.console.print(table)

            # Options
            self.console.print("\n[bold blue]Options:[/bold blue]")
            self.console.print("  • Enter number to select")
            self.console.print("  • Multiple files: [cyan]1,3,5[/cyan] or [cyan]2-6[/cyan]")
            self.console.print("  • Type [cyan]'all'[/cyan] to select all files")
            self.console.print("  • Type [cyan]'e'[/cyan] to export directory to CSV")
            self.console.print("  • Type [cyan]'r'[/cyan] to refresh directory listing")

            # Show folder sizes status and toggle option
            folder_status = "[green]ON[/green]" if show_folder_sizes else "[dim]OFF[/dim]"
            self.console.print(f"  • Type [cyan]'f'[/cyan] to toggle folder sizes (currently: {folder_status})")

            self.console.print("  • Type [cyan]'q'[/cyan] to return to main menu")

            if self.current_path != self.base_path:
                self.console.print("  • Type [cyan]'..'[/cyan] to go up")

            choice = Prompt.ask("\n[magenta bold]➤ Your choice[/magenta bold]")

            # Handle choice
            if choice.lower() == 'q':
                return
            elif choice == '..':
                if self.current_path != self.base_path:
                    self.current_path = str(Path(self.current_path).parent)
            elif choice == '0':
                self.current_path = self.base_path
            elif choice.lower() == 'r':
                force_refresh = True
                continue
            elif choice.lower() == 'e':
                # Export to CSV
                self.export_to_csv(files)
                continue
            elif choice.lower() == 'f':
                # Toggle folder sizes
                current_value = self.config.get_bool('SHOW_FOLDER_SIZES', False)
                new_value = not current_value
                self.config.set_bool('SHOW_FOLDER_SIZES', new_value)
                status = "enabled" if new_value else "disabled"
                self.console.print(f"\n[green]✓ Folder sizes {status}![/green]")
                time.sleep(1)
                continue
            elif choice.lower() == 'all':
                selected = [f for f in files if not f['is_dir']]
                if selected:
                    self.download_files(selected)
                else:
                    self.console.print("[yellow]⚠️  No files to select[/yellow]")
                    input("\nPress Enter to continue...")
            else:
                # Parse selection
                selected_files = self.parse_selection(choice, files)
                if selected_files:
                    # Check if single directory navigation
                    if len(selected_files) == 1 and selected_files[0]['is_dir']:
                        self.current_path = os.path.join(self.current_path, selected_files[0]['name'])
                    else:
                        # Filter out directories, download only files
                        files_only = [f for f in selected_files if not f['is_dir']]
                        if files_only:
                            self.download_files(files_only)
                else:
                    self.console.print("[yellow]⚠️  Invalid selection[/yellow]")
                    time.sleep(1)

    def parse_selection(self, choice: str, files: List[Dict]) -> List[Dict]:
        """Parse user selection (ranges, comma-separated, etc.)"""
        selected = []
        parts = choice.split(',')

        for part in parts:
            part = part.strip()

            # Handle range (e.g., 2-5)
            if '-' in part:
                try:
                    start, end = part.split('-')
                    start, end = int(start), int(end)
                    for i in range(start, end + 1):
                        if 1 <= i <= len(files):
                            selected.append(files[i - 1])
                except:
                    continue
            # Handle single number
            elif part.isdigit():
                idx = int(part)
                if 1 <= idx <= len(files):
                    selected.append(files[idx - 1])

        return selected

    def export_to_csv(self, files: List[Dict]):
        """Export current directory listing to CSV file"""
        self.show_banner()

        # Create exports directory
        exports_dir = self.script_dir / 'exports'
        exports_dir.mkdir(exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        folder_name = Path(self.current_path).name or 'root'
        csv_filename = f"directory_listing_{folder_name}_{timestamp}.csv"
        csv_path = exports_dir / csv_filename

        self.console.print(f"[cyan]📊 Exporting directory listing...[/cyan]\n")
        self.console.print(f"[cyan]Current Directory: [bold]{self.current_path}[/bold][/cyan]")
        self.console.print(f"[cyan]Total Items: [bold]{len(files)}[/bold][/cyan]\n")

        # Write CSV
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                writer.writerow(['Number', 'Name', 'Type', 'Size', 'Size (Bytes)', 'Full Path', 'Modified'])

                # Write data
                for idx, file_info in enumerate(files, 1):
                    file_type = 'Folder' if file_info['is_dir'] else 'File'
                    size_bytes = file_info['size']
                    size_human = self.format_size(size_bytes) if not file_info['is_dir'] else ''
                    full_path = os.path.join(self.current_path, file_info['name'])
                    modified = datetime.fromtimestamp(file_info['mtime']).strftime('%Y-%m-%d %H:%M:%S')

                    writer.writerow([
                        idx,
                        file_info['name'],
                        file_type,
                        size_human,
                        size_bytes if not file_info['is_dir'] else '',
                        full_path,
                        modified
                    ])

            self.console.print(f"[green]✅ Export successful![/green]")
            self.console.print(f"[green]📄 File saved to:[/green]")
            self.console.print(f"[cyan]   {csv_path}[/cyan]\n")

            self.console.print("[yellow]💡 Tip:[/yellow]")
            self.console.print("[dim]   • Open the CSV to browse the directory on another screen[/dim]")
            self.console.print("[dim]   • Note the numbers of files you want to download[/dim]")
            self.console.print("[dim]   • Return here and enter those numbers (e.g., 5,12,18-22)[/dim]")

            self.log(f"EXPORT: Exported directory listing to {csv_path}")

        except Exception as e:
            self.console.print(f"[red]❌ Export failed: {e}[/red]")
            self.log(f"EXPORT FAILED: {e}")

        input("\nPress Enter to continue...")

    def download_files(self, files: List[Dict]):
        """Download selected files"""
        self.show_banner()

        # Show selected files
        panel = Panel(
            "\n".join([f"{self.get_file_emoji(f['name'])} {f['name']}" for f in files]),
            title="[bold]📥 Selected Files for Download[/bold]",
            border_style="cyan"
        )
        self.console.print(panel)

        # Choose destination
        paths = self.config.get_download_paths()

        self.console.print("\n[bold blue]📍 Choose Download Destination:[/bold blue]")
        for idx, (name, path) in enumerate(paths, 1):
            self.console.print(f"  {idx}. {name} [dim]({path})[/dim]")
        self.console.print(f"  {len(paths) + 1}. 📝 Custom path")
        self.console.print("  0. ❌ Cancel")

        choice = Prompt.ask("\n[magenta bold]➤ Select destination[/magenta bold]")

        if choice == '0':
            return

        try:
            idx = int(choice)
            if 1 <= idx <= len(paths):
                dest_path = paths[idx - 1][1]
            elif idx == len(paths) + 1:
                dest_path = Prompt.ask("[cyan]Enter custom path[/cyan]")
            else:
                self.console.print("[yellow]⚠️  Invalid choice[/yellow]")
                input("\nPress Enter to continue...")
                return
        except:
            self.console.print("[yellow]⚠️  Invalid choice[/yellow]")
            input("\nPress Enter to continue...")
            return

        # Create destination if needed
        dest_path_obj = Path(dest_path)
        if not dest_path_obj.exists():
            if Confirm.ask(f"[yellow]Destination doesn't exist. Create it?[/yellow]"):
                dest_path_obj.mkdir(parents=True, exist_ok=True)
            else:
                return

        # Create subdirectory based on current remote folder name
        current_folder_name = Path(self.current_path).name
        if current_folder_name:  # Only create subdirectory if we have a folder name
            dest_path_obj = dest_path_obj / current_folder_name
            dest_path_obj.mkdir(parents=True, exist_ok=True)
            dest_path = str(dest_path_obj)

        # Download files
        self.show_banner()
        self.console.print(f"[cyan]Source: [bold]{self.current_path}[/bold][/cyan]")
        self.console.print(f"[cyan]Destination: [bold]{dest_path}[/bold][/cyan]\n")

        success_count = 0
        fail_count = 0

        for file_info in files:
            remote_file = os.path.join(self.current_path, file_info['name'])
            local_file = os.path.join(dest_path, file_info['name'])

            emoji = self.get_file_emoji(file_info['name'])
            self.console.print(f"\n[blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/blue]")
            self.console.print(f"[blue]📥 Downloading: {emoji} [bold]{file_info['name']}[/bold][/blue]")

            # Get file size and chunk config
            file_size = self.sftp.get_file_size(remote_file)
            chunks = self.config.get_int('DOWNLOAD_CHUNKS', 8)
            
            if file_size:
                self.console.print(f"[cyan]   📊 File Size: [bold]{self.format_size(file_size)}[/bold][/cyan]")
                if file_size >= 10 * 1024 * 1024:  # 10MB+
                    self.console.print(f"[cyan]   🚀 Using {chunks} parallel chunks (IDM-style)[/cyan]")

            self.console.print(f"[yellow]   ⏳ Transfer in progress...[/yellow]\n")

            # Download with progress bar
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=self.console
            ) as progress:
                task = progress.add_task(f"Downloading {file_info['name']}", total=file_size)

                def callback(transferred, total):
                    progress.update(task, completed=transferred)

                success = self.sftp.download_file(remote_file, local_file, callback, chunks=chunks)

            print()  # Extra newline after progress

            if success:
                final_size = Path(local_file).stat().st_size
                self.console.print(f"[green]✅ ✓ Downloaded: {file_info['name']}[/green]")
                self.console.print(f"[green]   💾 Saved: {self.format_size(final_size)} → {local_file}[/green]")
                self.log(f"SUCCESS: Downloaded {remote_file} to {local_file}")
                success_count += 1
            else:
                self.console.print(f"[red]❌ Failed: {file_info['name']}[/red]")
                self.log(f"FAILED: Download of {remote_file} to {local_file}")
                fail_count += 1

        # Summary
        self.console.print("\n[blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/blue]")
        self.console.print("\n[bold]📊 Download Summary:[/bold]")
        self.console.print(f"[green]  ✅ Successful: {success_count}[/green]")
        if fail_count > 0:
            self.console.print(f"[red]  ❌ Failed: {fail_count}[/red]")

        self.console.print(f"\n[cyan]Files saved to: [bold]{dest_path}[/bold][/cyan]")

        input("\nPress Enter to continue...")

    def show_main_menu(self):
        """Show main menu"""
        while True:
            self.show_banner()

            self.console.print(f"[green]🔗 Server: [bold]{self.config.get('REMOTE_USER')}@{self.config.get('REMOTE_HOST')}[/bold][/green]")
            self.console.print(f"[cyan]📁 Base Path: [bold]{self.base_path}[/bold][/cyan]\n")

            menu = Panel(
                "[cyan]  1. 📁 Browse Remote Server[/cyan]\n"
                "[cyan]  2. ⚙️  Configure Settings[/cyan]\n"
                "[cyan]  3. 📝 View Download Logs[/cyan]\n"
                "[cyan]  4. 🔍 Test Connection[/cyan]\n"
                "[cyan]  5. 🗑️  Clear Cache[/cyan]\n"
                "[cyan]  6. ❓ Help[/cyan]\n"
                "[red]  0. 🚪 Exit[/red]",
                title="[bold]🎯 Main Menu[/bold]",
                border_style="blue"
            )
            self.console.print(menu)

            choice = Prompt.ask("\n[magenta bold]➤ Select option[/magenta bold]")

            if choice == '1':
                self.browse_files()
            elif choice == '2':
                self.show_config()
            elif choice == '3':
                self.show_logs()
            elif choice == '4':
                self.test_connection()
            elif choice == '5':
                self.clear_cache()
            elif choice == '6':
                self.show_help()
            elif choice == '0':
                self.console.print("\n[green]👋 Thanks for using Remote Server Download Manager![/green]\n")
                return
            else:
                self.console.print("[yellow]⚠️  Invalid option[/yellow]")
                time.sleep(1)

    def show_config(self):
        """Show configuration"""
        self.show_banner()

        folder_sizes = "Enabled" if self.config.get_bool('SHOW_FOLDER_SIZES', False) else "Disabled"
        chunks = self.config.get_int('DOWNLOAD_CHUNKS', 8)

        panel = Panel(
            f"[cyan]• Remote User: [bold]{self.config.get('REMOTE_USER')}[/bold][/cyan]\n"
            f"[cyan]• Remote Host: [bold]{self.config.get('REMOTE_HOST')}[/bold][/cyan]\n"
            f"[cyan]• Base Path: [bold]{self.config.get('REMOTE_BASE_PATH')}[/bold][/cyan]\n"
            f"[cyan]• SSH Key: [bold]{self.config.get('SSH_KEY_PATH')}[/bold][/cyan]\n"
            f"[cyan]• Download Chunks: [bold]{chunks}[/bold][/cyan]\n"
            f"[cyan]• Show Folder Sizes: [bold]{folder_sizes}[/bold][/cyan]\n\n"
            f"[yellow]Tips:[/yellow]\n"
            f"[dim]• Toggle folder sizes with 'f' when browsing[/dim]\n"
            f"[dim]• Edit {self.config.config_file} for other settings[/dim]",
            title="[bold]⚙️  Configuration[/bold]",
            border_style="cyan"
        )
        self.console.print(panel)

        input("\nPress Enter to continue...")

    def show_logs(self):
        """Show recent logs"""
        self.show_banner()

        self.console.print(Panel("[bold]📝 Recent Download Logs[/bold]", border_style="cyan"))

        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    self.console.print(line.strip())
        else:
            self.console.print("[yellow]No logs found[/yellow]")

        input("\nPress Enter to continue...")

    def test_connection(self):
        """Test SFTP connection"""
        self.show_banner()

        self.console.print(f"[cyan]Testing connection to {self.config.get('REMOTE_USER')}@{self.config.get('REMOTE_HOST')}...[/cyan]\n")

        with self.console.status("[cyan]Connecting...[/cyan]"):
            if self.sftp.connect():
                self.console.print("[green]✅ Connection successful![/green]")
            else:
                self.console.print("[red]❌ Connection failed![/red]")

        input("\nPress Enter to continue...")

    def clear_cache(self):
        """Clear cache"""
        self.show_banner()

        count, size = self.cache.get_stats()

        panel = Panel(
            f"[cyan]• Cached directories: [bold]{count}[/bold][/cyan]\n"
            f"[cyan]• Cache size: [bold]{self.format_size(size)}[/bold][/cyan]",
            title="[bold]🗑️  Cache Management[/bold]",
            border_style="cyan"
        )
        self.console.print(panel)

        if count == 0:
            self.console.print("[yellow]Cache is already empty[/yellow]")
        elif Confirm.ask("\n[yellow]Are you sure you want to clear the cache?[/yellow]"):
            self.cache.clear()
            self.console.print("[green]✅ Cache cleared successfully[/green]")
        else:
            self.console.print("[cyan]Cache clear cancelled[/cyan]")

        input("\nPress Enter to continue...")

    def show_help(self):
        """Show help"""
        self.show_banner()

        help_text = """[bold cyan]Navigation:[/bold cyan]
  • Use numbers to select files or folders
  • Enter folders by selecting their number
  • Use '..' to go up one directory level
  • Use '0' to return to base directory

[bold cyan]File Selection:[/bold cyan]
  • Single file: [white]3[/white]
  • Multiple files: [white]1,3,5[/white]
  • Range: [white]2-6[/white]
  • All files: [white]all[/white]

[bold cyan]Performance:[/bold cyan]
  • Fast SFTP with paramiko
  • Automatic directory caching (5 min)
  • Optimized transfer settings
  • Real-time progress display

[bold cyan]Tips:[/bold cyan]
  • Configure settings in config.conf
  • Check logs if downloads fail
  • Test connection before browsing
  • Use pre-configured paths for quick downloads
  • Press 'r' to refresh cached directories
"""

        panel = Panel(help_text, title="[bold]❓ Help & Tips[/bold]", border_style="cyan")
        self.console.print(panel)

        input("\nPress Enter to continue...")

    def run(self):
        """Main application loop"""
        self.show_banner()

        # Connect
        with self.console.status("[cyan]Connecting to remote server...[/cyan]"):
            if not self.sftp.connect():
                self.console.print("[red]❌ Failed to connect to remote server[/red]")
                self.console.print("[yellow]Please check your configuration and SSH key[/yellow]")
                return

        self.console.print("[green]✅ Connected successfully![/green]")
        time.sleep(1)

        try:
            self.show_main_menu()
        finally:
            self.sftp.disconnect()


def main():
    """Entry point"""
    script_dir = Path(__file__).parent
    config_file = script_dir / "config.conf"

    if not config_file.exists():
        console = Console()
        console.print(f"[red]❌ Configuration file not found: {config_file}[/red]")
        console.print("[yellow]Please create config.conf from the template[/yellow]")
        sys.exit(1)

    app = DownloadManager(str(config_file))
    app.run()


if __name__ == "__main__":
    main()
