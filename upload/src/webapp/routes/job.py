from flask import Blueprint, render_template, jsonify
import os
import json

job_bp = Blueprint('job', __name__)

JOB_DIR = "../../scheduler/jobs"
LOG_DIR = "../../scheduler/logs"
METADATA_FILE = "../../scheduler/metadata.json"

def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

@job_bp.route('/job/<job_hash>')
def job_view(job_hash):
    status = "completed"
    
    if os.path.exists(JOB_DIR):
        for f in os.listdir(JOB_DIR):
            if f.replace("_working.py", "").replace(".py", "") == job_hash:
                status = "running" if "_working" in f else "pending"
                break
    
    meta = load_metadata().get(job_hash, {"filename": "unknown", "username": "unknown"})
    log_path = os.path.join(LOG_DIR, f"{job_hash}.log")
    output = open(log_path, 'r').read() if os.path.exists(log_path) else ""
    
    return render_template("job.html", job_hash=job_hash, filename=meta["filename"],
                         username=meta["username"], status=status, output=output)

@job_bp.route('/api/job/<job_hash>')
def job_api(job_hash):
    status = "completed"
    if os.path.exists(JOB_DIR):
        for f in os.listdir(JOB_DIR):
            if f.replace("_working.py", "").replace(".py", "") == job_hash:
                status = "running" if "_working" in f else "pending"
    
    log_path = os.path.join(LOG_DIR, f"{job_hash}.log")
    output = open(log_path, 'r').read() if os.path.exists(log_path) else ""
    return jsonify({"status": status, "output": output})
