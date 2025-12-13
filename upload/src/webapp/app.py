from flask import Flask, request, render_template, jsonify
import os
import ast
import hashlib
import time
import json

app = Flask(__name__)

JOB_DIR = "../scheduler/jobs"
LOG_DIR = "../scheduler/logs"
ARCHIVE_DIR = "../scheduler/archive"
METADATA_FILE = "../scheduler/metadata.json"
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

def load_metadata():
    """Load metadata from JSON file"""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_metadata(metadata):
    """Save metadata to JSON file"""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def get_metadata_for_hash(job_hash):
    """Get metadata for a specific job hash"""
    metadata = load_metadata()
    return metadata.get(job_hash, {
        "filename": "unknown",
        "username": "unknown",
        "timestamp": 0
    })

def get_queue_data():
    """Get queue data from job files and logs"""
    queue_items = []
    metadata = load_metadata()
    
    # Add active jobs
    if os.path.exists(JOB_DIR):
        for idx, job_file in enumerate(sorted([f for f in os.listdir(JOB_DIR) if f.endswith(".py")])):
            # Extract hash from filename (removing .py or _working.py)
            file_hash = job_file.replace("_working.py", "").replace(".py", "")
            meta = metadata.get(file_hash, {"filename": "unknown", "username": "unknown"})
            
            queue_items.append({
                "id": idx + 1,
                "filename": meta["filename"],
                "status": "running" if "_working" in job_file else "pending",
                "user": meta["username"],
                "hash": file_hash
            })
    
    # Add completed jobs
    if os.path.exists(LOG_DIR):
        for log_file in [f for f in os.listdir(LOG_DIR) if f.endswith(".log")]:
            job_hash = log_file.replace(".log", "")
            if any(item["hash"] == job_hash for item in queue_items):
                continue
            
            meta = metadata.get(job_hash, {"filename": "completed", "username": "unknown"})
            
            queue_items.append({
                "id": len(queue_items) + 1,
                "filename": meta["filename"],
                "status": "completed",
                "user": meta["username"],
                "hash": job_hash
            })
    
    return queue_items

@app.route('/queue')
def monitor():
    queue_items = get_queue_data()
    return render_template("queue.html", queue=queue_items)

@app.route('/api/queue')
def queue_api():
    return jsonify(get_queue_data())

@app.route('/job/<job_hash>')
def job_view(job_hash):
    """View individual job"""
    status = "completed"
    
    # Check if job is in queue
    if os.path.exists(JOB_DIR):
        for f in os.listdir(JOB_DIR):
            if f.replace("_working.py", "").replace(".py", "") == job_hash:
                status = "running" if "_working" in f else "pending"
                break
    
    # Get metadata
    meta = get_metadata_for_hash(job_hash)
    
    # Read log to determine if failed
    log_path = os.path.join(LOG_DIR, f"{job_hash}.log")
    output = ""
    if os.path.exists(log_path):
        output = open(log_path, 'r').read()
        if status == "completed" and "Job failed with error:" in output:
            status = "failed"
    
    return render_template("job.html", 
                         job_hash=job_hash,
                         filename=meta["filename"],
                         username=meta["username"],
                         status=status,
                         output=output)

@app.route('/api/job/<job_hash>')
def job_api(job_hash):
    status = "completed"
    
    if os.path.exists(JOB_DIR):
        for f in os.listdir(JOB_DIR):
            if f.replace("_working.py", "").replace(".py", "") == job_hash:
                status = "running" if "_working" in f else "pending"
                break
    
    log_path = os.path.join(LOG_DIR, f"{job_hash}.log")
    output = ""
    if os.path.exists(log_path):
        output = open(log_path, 'r').read()
        if status == "completed" and "Job failed with error:" in output:
            status = "failed"
    
    return jsonify({"status": status, "output": output})

@app.route("/editor", methods=["GET", "POST"])
def editor_view():
    if request.method == "POST":
        username = request.form.get("username", "anonymous")
        editor_code = request.form.get("editor_code")

        # Check username length
        if len(username) > 32:
            return jsonify({"error": "Username must be 32 characters or less"}), 400

        if not editor_code:
            return jsonify({"error": "No code provided"}), 400

        try:
            # Validate Python syntax
            ast.parse(editor_code)
        except SyntaxError:
            return jsonify({"error": "Code is not valid Python"}), 400
        except Exception:
            return jsonify({"error": "Error processing the code"}), 400

        # Check code size (max 5MB)
        if len(editor_code.encode("utf-8")) > 5 * 1024 * 1024:
            return jsonify({"error": "Code too large (max 5MB)"}), 400

        # Generate job hash
        job_hash = hashlib.sha256(
            editor_code[:8].encode() + str(time.time()).encode()
        ).hexdigest()[:8]
        
        # Save metadata
        metadata = load_metadata()
        metadata[job_hash] = {
            "filename": "editor.py",
            "username": username,
            "timestamp": time.time()
        }
        save_metadata(metadata)
        
        # Save code to job file
        os.makedirs(JOB_DIR, exist_ok=True)
        file_path = os.path.join(JOB_DIR, f"{job_hash}.py")
        with open(file_path, "w") as f:
            f.write(editor_code)

        return jsonify({"job_hash": job_hash})
    
    return render_template("editor.html")

@app.route("/")
def index():
    return render_template("editor.html")

