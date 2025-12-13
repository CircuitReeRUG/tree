from flask import Blueprint, request, render_template, jsonify
import os
import ast
import hashlib
import time
import json

editor_bp = Blueprint('editor', __name__)

JOB_DIR = "../../scheduler/jobs"
METADATA_FILE = "../../scheduler/metadata.json"

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