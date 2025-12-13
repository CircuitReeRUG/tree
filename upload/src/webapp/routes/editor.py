from flask import Blueprint, request, render_template, jsonify, redirect, url_for
import os
import ast
import hashlib
import time
import json
from datetime import datetime

editor_bp = Blueprint('editor', __name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scheduler'))
JOB_DIR = os.path.join(BASE_DIR, "jobs")
METADATA_FILE = os.path.join(BASE_DIR, "metadata.json")

def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_metadata(metadata):
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f)

@editor_bp.route("/")
def index():
    return render_template("editor.html")

@editor_bp.route("/editor", methods=["GET", "POST"])
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

@editor_bp.route('/submit', methods=['POST'])
def submit():
    username = request.form.get("username", "anonymous")[:32]
    code = request.form.get("editor_code")

    if not code:
        return jsonify({"error": "No code"}), 400

    try:
        ast.parse(code)
    except:
        return jsonify({"error": "Invalid Python"}), 400

    job_hash = hashlib.sha256((code[:8] + str(time.time())).encode()).hexdigest()[:8]
    filename = f"{job_hash}.py"
    filepath = os.path.join(JOB_DIR, filename)

    with open(filepath, "w") as f:
        f.write(code)

    job_queue = {}
    job_queue[job_hash] = {
        'username': username,
        'filename': filename,
        'filepath': filepath,
        'status': 'pending',
        'output': '',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    return redirect(url_for('editor.index'))
