#!/usr/bin/env python3

"""
Remote File Download Manager - Web Interface
A Flask-based web UI for managing remote file downloads
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import subprocess
import json
from pathlib import Path
from remote_scanner import Database
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'

# Paths
SCRIPT_DIR = Path(__file__).parent
SCANNER_SCRIPT = SCRIPT_DIR / "remote_scanner.py"
DOWNLOAD_SCRIPT = SCRIPT_DIR / "download-manager.sh"
CONFIG_FILE = SCRIPT_DIR / "config.conf"


def load_config():
    """Load configuration from bash config file"""
    config = {}
    if not CONFIG_FILE.exists():
        return config

    with open(CONFIG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                match = re.match(r'([A-Z_]+)="?([^"]*)"?', line)
                if match:
                    key, value = match.groups()
                    config[key] = value

    return config


def get_download_paths():
    """Get configured download paths from config"""
    config = load_config()
    paths = []

    for i in range(1, 6):
        path_key = f'DOWNLOAD_PATH_{i}'
        name_key = f'PATH_{i}_NAME'

        if path_key in config and config[path_key]:
            paths.append({
                'path': config[path_key],
                'name': config.get(name_key, f'Path {i}')
            })

    return paths


def format_size(size):
    """Format file size in human-readable format"""
    if not size:
        return "N/A"

    size = int(size)
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f}KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size/(1024*1024):.1f}MB"
    else:
        return f"{size/(1024*1024*1024):.2f}GB"


def get_file_emoji(filename):
    """Get emoji for file type"""
    ext = Path(filename).suffix.lstrip('.').lower()

    emoji_map = {
        'mp4': '🎥', 'mkv': '🎥', 'avi': '🎥', 'mov': '🎥',
        'mp3': '🎵', 'flac': '🎵', 'wav': '🎵',
        'jpg': '📷', 'jpeg': '📷', 'png': '📷', 'gif': '📷',
        'zip': '📦', 'tar': '📦', 'gz': '📦', 'rar': '📦',
        'pdf': '📝', 'doc': '📝', 'docx': '📝', 'txt': '📝',
        'json': '💾', 'xml': '💾', 'csv': '📊',
        'py': '💻', 'js': '💻', 'sh': '💻',
    }

    return emoji_map.get(ext, '📄')


@app.route('/')
def index():
    """Main page - file browser"""
    with Database() as db:
        files = db.search_files()

        # Format files for display
        formatted_files = []
        for file in files:
            formatted_files.append({
                'id': file['id'],
                'filename': file['filename'],
                'emoji': get_file_emoji(file['filename']),
                'remote_path': file['remote_path'],
                'size': format_size(file['file_size']),
                'size_bytes': file['file_size'],
                'modified': file['modified_date'],
                'server_added': file['server_added_date'],
                'first_seen': file['first_seen'],
                'last_seen': file['last_seen'],
                'status': file['download_status'] or '-',
                'notes': file['notes'],
                'source': file['source_file_path']
            })

    return render_template('index.html', files=formatted_files, config=load_config())


@app.route('/queue')
def queue_page():
    """Queue management page"""
    with Database() as db:
        queued = db.get_queued_files()

        formatted_queue = []
        for item in queued:
            formatted_queue.append({
                'download_id': item['download_id'],
                'file_id': item['file_id'],
                'filename': item['filename'],
                'emoji': get_file_emoji(item['filename']),
                'remote_path': item['remote_path'],
                'size': format_size(item['file_size']),
                'local_path': item['local_path'],
                'notes': item['download_notes']
            })

    download_paths = get_download_paths()
    return render_template('queue.html', queue=formatted_queue, download_paths=download_paths)


@app.route('/api/scan', methods=['POST'])
def scan_remote():
    """Trigger remote directory scan"""
    data = request.json
    path = data.get('path', '')

    try:
        cmd = ['python3', str(SCANNER_SCRIPT), '--scan']
        if path:
            cmd.extend(['--path', path])

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        return jsonify({
            'success': True,
            'message': 'Scan completed successfully',
            'output': result.stdout
        })
    except subprocess.CalledProcessError as e:
        return jsonify({
            'success': False,
            'message': f'Scan failed: {e.stderr}'
        }), 500


@app.route('/api/search', methods=['GET'])
def search_files():
    """Search files in database"""
    pattern = request.args.get('pattern', '')
    path = request.args.get('path', '')
    file_type = request.args.get('type', '')

    with Database() as db:
        files = db.search_files(
            pattern=pattern if pattern else None,
            path=path if path else None,
            file_type=file_type if file_type else None
        )

        formatted_files = []
        for file in files:
            formatted_files.append({
                'id': file['id'],
                'filename': file['filename'],
                'emoji': get_file_emoji(file['filename']),
                'remote_path': file['remote_path'],
                'size': format_size(file['file_size']),
                'modified': file['modified_date'],
                'status': file['download_status'] or '-',
                'notes': file['notes']
            })

    return jsonify(formatted_files)


@app.route('/api/queue/add', methods=['POST'])
def add_to_queue():
    """Add files to download queue"""
    data = request.json
    file_ids = data.get('file_ids', [])
    destinations = data.get('destinations', {})  # Map of file_id: destination_path

    if not file_ids:
        return jsonify({'success': False, 'message': 'No files specified'}), 400

    with Database() as db:
        count = 0
        for file_id in file_ids:
            try:
                # Get destination for this file (if specified)
                destination = destinations.get(str(file_id))
                db.queue_file(int(file_id), local_path=destination)
                count += 1
            except Exception as e:
                print(f"Error queuing file {file_id}: {e}")

    return jsonify({
        'success': True,
        'message': f'Queued {count} file(s)',
        'count': count
    })


@app.route('/api/queue/remove/<int:download_id>', methods=['POST'])
def remove_from_queue(download_id):
    """Remove file from download queue"""
    with Database() as db:
        cursor = db.conn.cursor()
        cursor.execute("DELETE FROM downloads WHERE id = ? AND status = 'queued'", (download_id,))
        db.conn.commit()

        if cursor.rowcount > 0:
            return jsonify({'success': True, 'message': 'Removed from queue'})
        else:
            return jsonify({'success': False, 'message': 'Not found or already processed'}), 404


@app.route('/api/queue/clear', methods=['POST'])
def clear_queue():
    """Clear entire download queue"""
    with Database() as db:
        db.clear_queue()

    return jsonify({'success': True, 'message': 'Queue cleared'})


@app.route('/api/note/update', methods=['POST'])
def update_note():
    """Add or update note for a file"""
    data = request.json
    file_id = data.get('file_id')
    note_text = data.get('note', '')

    if not file_id:
        return jsonify({'success': False, 'message': 'No file ID specified'}), 400

    with Database() as db:
        db.add_note(int(file_id), note_text)

    return jsonify({'success': True, 'message': 'Note updated'})


@app.route('/api/source/update', methods=['POST'])
def update_source():
    """Link source file to remote file"""
    data = request.json
    file_id = data.get('file_id')
    source_path = data.get('source_path', '')
    source_notes = data.get('source_notes', '')

    if not file_id or not source_path:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    with Database() as db:
        db.add_source_file(int(file_id), source_path, source_notes if source_notes else None)

    return jsonify({'success': True, 'message': 'Source file linked'})


@app.route('/api/download/trigger', methods=['POST'])
def trigger_download():
    """Trigger download process (runs bash script in background)"""
    try:
        # Start download in background
        subprocess.Popen(
            [str(DOWNLOAD_SCRIPT), '--from-db'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )

        return jsonify({
            'success': True,
            'message': 'Download process started. Check the NAS terminal or logs for progress.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to start download: {str(e)}'
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    with Database() as db:
        cursor = db.conn.cursor()

        # Total files
        cursor.execute("SELECT COUNT(*) FROM remote_files")
        total_files = cursor.fetchone()[0]

        # Queued files
        cursor.execute("SELECT COUNT(*) FROM downloads WHERE status = 'queued'")
        queued_files = cursor.fetchone()[0]

        # Completed downloads
        cursor.execute("SELECT COUNT(*) FROM downloads WHERE status = 'completed'")
        completed_downloads = cursor.fetchone()[0]

        # Total size in database
        cursor.execute("SELECT SUM(file_size) FROM remote_files")
        total_size = cursor.fetchone()[0] or 0

        return jsonify({
            'total_files': total_files,
            'queued_files': queued_files,
            'completed_downloads': completed_downloads,
            'total_size': format_size(total_size),
            'total_size_bytes': total_size
        })


if __name__ == '__main__':
    # Run on all interfaces so it's accessible from other devices on network
    # Using port 5001 (5000 is often used by AirPlay on macOS)
    app.run(host='0.0.0.0', port=5001, debug=True)
