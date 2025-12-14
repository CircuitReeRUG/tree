from flask import Blueprint, render_template, jsonify
import os
import json
from datetime import datetime

queue_bp = Blueprint('queue', __name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scheduler'))
JOB_DIR = os.path.join(BASE_DIR, "jobs")
LOG_DIR = os.path.join(BASE_DIR, "logs")
METADATA_FILE = os.path.join(BASE_DIR, "metadata.json")

def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def get_queue_data():
    queue_items = []
    metadata = load_metadata()
    
    if os.path.exists(JOB_DIR):
        for job_file in sorted([f for f in os.listdir(JOB_DIR) if f.endswith(".py")]):
            file_hash = job_file.replace("_working.py", "").replace(".py", "")
            meta = metadata.get(file_hash, {"filename": "unknown", "username": "unknown"})
            timestamp = meta.get('timestamp', 0)
            timestamp_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'N/A'
            
            queue_items.append({
                "filename": meta["filename"],
                "status": "running" if "_working" in job_file else "pending",
                "user": meta["username"],
                "hash": file_hash,
                "timestamp": timestamp_str,
                "timestamp_raw": timestamp
            })
    
    if os.path.exists(LOG_DIR):
        for log_file in [f for f in os.listdir(LOG_DIR) if f.endswith(".log")]:
            job_hash = log_file.replace(".log", "")
            if any(item["hash"] == job_hash for item in queue_items):
                continue
            meta = metadata.get(job_hash, {"filename": "completed", "username": "unknown"})
            timestamp = meta.get('timestamp', 0)
            timestamp_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'N/A'
            
            queue_items.append({
                "filename": meta["filename"],
                "status": "completed",
                "user": meta["username"],
                "hash": job_hash,
                "timestamp": timestamp_str,
                "timestamp_raw": timestamp
            })
    
    # Sort by timestamp (newest first)
    queue_items.sort(key=lambda x: x.get('timestamp_raw', 0), reverse=True)
    
    return queue_items

@queue_bp.route('/queue')
def monitor():
    queue_items = get_queue_data()
    jobs = [{'hash': item['hash'], 'username': item['user'], 'filename': item['filename'], 'status': item['status'], 'timestamp': item['timestamp']} for item in queue_items]
    return render_template('queue.html', jobs=jobs)

@queue_bp.route('/api/queue')
def queue_api():
    return jsonify(get_queue_data())

@queue_bp.route('/stream')
def stream_overlay():
    """OBS overlay showing current and last running user"""
    queue_items = get_queue_data()
    
    current_user = None
    last_user = None
    
    # Find currently running job
    for item in queue_items:
        if item['status'] == 'running':
            current_user = item['user']
            break
    
    # Find last completed job
    completed_items = [item for item in queue_items if item['status'] == 'completed']
    if completed_items:
        last_user = completed_items[0]['user']
    
    return render_template('stream_overlay.html', current_user=current_user, last_user=last_user)

@queue_bp.route('/api/stream')
def stream_api():
    """API endpoint for stream overlay data"""
    queue_items = get_queue_data()
    
    current_user = None
    last_user = None
    
    # Find currently running job
    for item in queue_items:
        if item['status'] == 'running':
            current_user = item['user']
            break
    
    # Find last completed job
    completed_items = [item for item in queue_items if item['status'] == 'completed']
    if completed_items:
        last_user = completed_items[0]['user']
    
    return jsonify({
        'current_user': current_user,
        'last_user': last_user
    })
