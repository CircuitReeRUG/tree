from flask import Flask, request, render_template, jsonify, redirect, url_for
import os
import ast
import hashlib
import time
import json
from io import BytesIO

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
    """API endpoint for job status polling"""
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

def __hash_name(file):
    """Generate hash from file content and timestamp"""
    file_hash = hashlib.sha256(file.read(8) + str(time.time()).encode()).hexdigest()[:8]
    file.seek(0)
    return file_hash

@app.route("/editor")
def editor_view():
    return render_template("editor.html")


class EditorUploadWrapper:
    """Wrap raw editor code to mimic the subset of FileStorage used by upload_view."""
    def __init__(self, code: str, username: str = "anonymous", filename: str = "editor.py"):
        self._buf = BytesIO(code.encode("utf-8"))
        self.filename = filename
        self.content_length = len(code.encode("utf-8"))

    def read(self, *args, **kwargs):
        return self._buf.read(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self._buf.seek(*args, **kwargs)

    def save(self, dst_path):
        # Reset to start then write entire buffer to destination path
        self._buf.seek(0)
        with open(dst_path, "wb") as f:
            f.write(self._buf.read())


@app.route("/upload", methods=["GET", "POST"])
def upload_view():
    if request.method == "POST":
        username = request.form.get("username", "anonymous")
        editor_code = request.form.get("editor_code")

        if editor_code and "file" not in request.files:
            uploaded_file = EditorUploadWrapper(editor_code, username)
        else:
            uploaded_file = request.files.get("file")

        # Check username length
        if len(username) > 32:
            return render_template("upload.html",
                                   message="Username must be 32 characters or less",
                                   redirect_to="upload",
                                   code="error")

        if uploaded_file:
            try:
                # Read entire content once for validation, then rewind
                content = uploaded_file.read().decode("utf-8")
                ast.parse(content)
                uploaded_file.seek(0)
            except SyntaxError:
                return render_template("upload.html",
                                       message="Uploaded file is not valid Python code",
                                       redirect_to="upload",
                                       code="error")
            except Exception:
                return render_template("upload.html",
                                       message="Error processing the uploaded file",
                                       redirect_to="upload",
                                       code="error")

            if getattr(uploaded_file, "content_length", None) and uploaded_file.content_length > 5 * 1024 * 1024:
                return render_template("upload.html",
                                       message="File too large (max 5MB)",
                                       redirect_to="upload",
                                       code="error")

            original_name = uploaded_file.filename if getattr(uploaded_file, "filename", None) else "unnamed.py"
            job_hash = __hash_name(uploaded_file)
            
            # Save metadata
            metadata = load_metadata()
            metadata[job_hash] = {
                "filename": original_name,
                "username": username,
                "timestamp": time.time()
            }
            save_metadata(metadata)
            
            # Save file with hash-only name
            os.makedirs(JOB_DIR, exist_ok=True)
            file_path = os.path.join(JOB_DIR, f"{job_hash}.py")
            uploaded_file.save(file_path)

            return redirect(url_for("job_view", job_hash=job_hash))
        else:
            return render_template("upload.html",
                                   message="No file uploaded",
                                   redirect_to="upload",
                                   code="error")
    else:
        return render_template("upload.html")

@app.route("/")
def index():
    return render_template("index.html")

