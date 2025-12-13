from flask import Blueprint, render_template, jsonify
import os
import json

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
            queue_items.append({
                "filename": meta["filename"],
                "status": "running" if "_working" in job_file else "pending",
                "user": meta["username"],
                "hash": file_hash
            })
    
    if os.path.exists(LOG_DIR):
        for log_file in [f for f in os.listdir(LOG_DIR) if f.endswith(".log")]:
            job_hash = log_file.replace(".log", "")
            if any(item["hash"] == job_hash for item in queue_items):
                continue
            meta = metadata.get(job_hash, {"filename": "completed", "username": "unknown"})
            queue_items.append({
                "filename": meta["filename"],
                "status": "completed",
                "user": meta["username"],
                "hash": job_hash
            })
    
    return queue_items

@queue_bp.route('/queue')
def monitor():
    jobs = []
    for job_hash, job_data in job_queue.items():
        jobs.append({
            'hash': job_hash,
            'username': job_data['username'],
            'filename': job_data['filename'],
            'status': job_data['status'],
            'timestamp': job_data.get('timestamp', 'N/A')
        })
    return render_template('queue.html', jobs=jobs)

@queue_bp.route('/api/queue')
def queue_api():
    return jsonify(get_queue_data())
