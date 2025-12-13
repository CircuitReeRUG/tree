from flask import Blueprint, render_template, jsonify
import os
import json

queue_bp = Blueprint('queue', __name__)

JOB_DIR = "../../scheduler/jobs"
LOG_DIR = "../../scheduler/logs"
METADATA_FILE = "../../scheduler/metadata.json"

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
    return render_template("queue.html", queue=get_queue_data())

@queue_bp.route('/api/queue')
def queue_api():
    return jsonify(get_queue_data())
