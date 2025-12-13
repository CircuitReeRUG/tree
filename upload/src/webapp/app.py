from flask import Flask, request, render_template, jsonify
import os
import ast
import hashlib
import time
import json

app = Flask(__name__)

JOB_DIR = "../scheduler/jobs"
LOG_DIR = "../scheduler/logs"
METADATA_FILE = "../scheduler/metadata.json"
os.makedirs(JOB_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_metadata(metadata):
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f)

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

@app.route('/queue')
def monitor():
    return render_template("queue.html", queue=get_queue_data())

@app.route('/api/queue')
def queue_api():
    return jsonify(get_queue_data())

@app.route('/job/<job_hash>')
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

@app.route('/api/job/<job_hash>')
def job_api(job_hash):
    status = "completed"
    if os.path.exists(JOB_DIR):
        for f in os.listdir(JOB_DIR):
            if f.replace("_working.py", "").replace(".py", "") == job_hash:
                status = "running" if "_working" in f else "pending"
    
    log_path = os.path.join(LOG_DIR, f"{job_hash}.log")
    output = open(log_path, 'r').read() if os.path.exists(log_path) else ""
    return jsonify({"status": status, "output": output})

@app.route("/editor", methods=["GET", "POST"])
def editor_view():
    if request.method == "POST":
        username = request.form.get("username", "anonymous")[:32]
        code = request.form.get("editor_code")

        if not code:
            return jsonify({"error": "No code"}), 400

        try:
            ast.parse(code)
        except:
            return jsonify({"error": "Invalid Python"}), 400

        job_hash = hashlib.sha256((code[:8] + str(time.time())).encode()).hexdigest()[:8]
        
        metadata = load_metadata()
        metadata[job_hash] = {"filename": "editor.py", "username": username, "timestamp": time.time()}
        save_metadata(metadata)
        
        with open(os.path.join(JOB_DIR, f"{job_hash}.py"), "w") as f:
            f.write(code)

        return jsonify({"job_hash": job_hash})
    
    return render_template("editor.html")

@app.route("/")
def index():
    return render_template("editor.html")

