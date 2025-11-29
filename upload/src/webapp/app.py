from flask import Flask, request, render_template, jsonify, redirect, url_for
import os
import ast
import hashlib
import time

app = Flask(__name__)

JOB_DIR = "../scheduler/jobs"
LOG_DIR = "../scheduler/logs"
ARCHIVE_DIR = "../scheduler/archive"
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

def get_queue_data():
    """Get queue data from job files and logs"""
    queue_items = []
    
    # Add active jobs
    if os.path.exists(JOB_DIR):
        for idx, job_file in enumerate(sorted([f for f in os.listdir(JOB_DIR) if f.endswith(".py")])):
            parts = job_file.rsplit("_", 2)
            file_hash = parts[0] if len(parts) >= 3 else "unknown"
            username = parts[1] if len(parts) >= 3 else "unknown"
            original_name = "_".join(parts[2:]) if len(parts) >= 3 else job_file
            
            queue_items.append({
                "id": idx + 1,
                "filename": original_name,
                "status": "running" if "_working" in job_file else "pending",
                "user": username,
                "hash": file_hash
            })
    
    # Add completed jobs
    if os.path.exists(LOG_DIR):
        for log_file in [f for f in os.listdir(LOG_DIR) if f.endswith(".log")]:
            job_hash = log_file.replace(".log", "")
            if any(item["hash"] == job_hash for item in queue_items):
                continue
                
            with open(os.path.join(LOG_DIR, log_file), 'r') as f:
                first_line = f.readline()
                if "Job started:" in first_line:
                    parts = first_line.split("Job started: ")[1].strip().rsplit("_", 2)
                    username = parts[1] if len(parts) >= 3 else "unknown"
                    original_name = "_".join(parts[2:]) if len(parts) >= 3 else "completed"
                else:
                    username = "unknown"
                    original_name = "completed"
            
            queue_items.append({
                "id": len(queue_items) + 1,
                "filename": original_name,
                "status": "completed",
                "user": username,
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
    job_file = None
    status = "completed"
    
    # Check if job is in queue
    if os.path.exists(JOB_DIR):
        for f in os.listdir(JOB_DIR):
            if f.startswith(job_hash):
                job_file = f
                status = "running" if "_working" in f else "pending"
                break
    
    # Parse job info
    if job_file:
        parts = job_file.rsplit("_", 2)
        username = parts[1] if len(parts) >= 3 else "unknown"
        original_name = "_".join(parts[2:]) if len(parts) >= 3 else job_file
    else:
        username = "unknown"
        original_name = "completed"
    
    # Read log and code
    log_path = os.path.join(LOG_DIR, f"{job_hash}.log")
    output = open(log_path, 'r').read() if os.path.exists(log_path) else ""
    
    code_path = os.path.join(ARCHIVE_DIR, f"{job_hash}.py")
    code = open(code_path, 'r').read() if os.path.exists(code_path) else ""
    
    return render_template("job.html", 
                         job_hash=job_hash,
                         filename=original_name,
                         username=username,
                         status=status,
                         output=output,
                         code=code)

@app.route('/api/job/<job_hash>')
def job_api(job_hash):
    """API endpoint for job status polling"""
    status = "completed"
    
    if os.path.exists(JOB_DIR):
        for f in os.listdir(JOB_DIR):
            if f.startswith(job_hash):
                status = "running" if "_working" in f else "pending"
                break
    
    log_path = os.path.join(LOG_DIR, f"{job_hash}.log")
    output = open(log_path, 'r').read() if os.path.exists(log_path) else ""
    
    return jsonify({"status": status, "output": output})

def __hash_name(original_name: str, username: str, file):
    # hash content - 8 bytes of file ++ timestamp
    file_hash = hashlib.sha256(file.read(8)).hexdigest()[:8]
    file.seek(0)  # reset file pointer after reading
    
    return f"{file_hash}_{username}_{original_name}"

@app.route("/upload", methods=["GET", "POST"])
def upload_view():
    if request.method == "POST":
        uploaded_file = request.files.get("file")
        username = request.form.get("username", "anonymous")
        
        # Check username length
        if len(username) > 32:
            return render_template("upload.html",
                                 message="Username must be 32 characters or less",
                                 redirect_to="upload",
                                 code="error"
                                 )
        
        if uploaded_file:
            # check if python
            try:
                content = uploaded_file.read().decode('utf-8')
                ast.parse(content)
                uploaded_file.stream.seek(0)
            except SyntaxError:
                return render_template("upload.html",
                                     message="Uploaded file is not valid Python code",
                                     redirect_to="upload",
                                     code="error"
                                     )
            except Exception:
                return render_template("upload.html",
                                     message="Error processing the uploaded file",
                                     redirect_to="upload",
                                     code="error"
                                     )
            # check if too large
            if uploaded_file.content_length > 5 * 1024 * 1024:  # 5 MB limit
                return render_template("upload.html",
                                     message="File too large (max 5MB)",
                                     redirect_to="upload",
                                     code="error"
                                     )
            
            original_name = uploaded_file.filename if uploaded_file.filename else "unnamed.py"
            hashed_filename = __hash_name(original_name, username, uploaded_file)
            job_hash = hashed_filename.split("_")[0]  # Extract hash for redirect
            os.makedirs("../scheduler/jobs", exist_ok=True)
            file_path = f"../scheduler/jobs/{hashed_filename}"
            uploaded_file.save(file_path)
            
            # Redirect to job page
            return redirect(url_for('job_view', job_hash=job_hash))
        else:
            return render_template("upload.html",
                                 message="No file uploaded",
                                 redirect_to="upload",
                                 code="error"
                                 )
    else:
        return render_template("upload.html")

@app.route("/")
def index():
    return render_template("index.html")

