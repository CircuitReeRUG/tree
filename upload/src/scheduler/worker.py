import time
import sys
import os
import json

from idle_animation import start_idle_animation, stop_idle_animation
from callback import DelayedCallback
from runner.main import execute_code

JOB_DIR = "jobs"
LOG_DIR = "logs"
ARCHIVE_DIR = "archive"
METADATA_FILE = "metadata.json"
TIMEOUT_SECONDS = int(os.environ.get('JOB_TIMEOUT', 45))
IDLE_DELAY = int(os.environ.get('IDLE_ANIMATION_DELAY', 10))

os.makedirs(JOB_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

idle_starter = DelayedCallback(IDLE_DELAY, start_idle_animation)

def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def cleanup_old_logs():
    log_files = [f for f in os.listdir(LOG_DIR) if f.endswith(".log")]
    if len(log_files) <= 20:
        return
    
    log_files_sorted = sorted(log_files, key=lambda f: os.path.getmtime(os.path.join(LOG_DIR, f)))
    for log_file in log_files_sorted[:len(log_files) - 20]:
        os.remove(os.path.join(LOG_DIR, log_file))
        job_hash = log_file.replace(".log", "")
        archive_path = os.path.join(ARCHIVE_DIR, f"{job_hash}.py")
        if os.path.exists(archive_path):
            os.remove(archive_path)

def run_job(working_path, log_path, archive_path, meta, job_hash):
    with open(working_path, "r") as f:
        code = f.read()
    
    with open(archive_path, 'w') as archive:
        archive.write(code)
    
    with open(log_path, 'w') as log:
        log.write(f"Job: {meta['filename']}\n")
        log.write(f"User: {meta['username']}\n")
        log.write(f"Hash: {job_hash}\n")
        log.write("=" * 50 + "\n\n")
    
    time.sleep(0.5)
    
    result = execute_code(code)
    
    with open(log_path, 'a') as log_file:
        log_file.write(result)
    
    os.remove(working_path)

def worker_loop():
    print("Worker started")
    idle_starter.poke()
    
    while True:
        metadata = load_metadata()
        job_files = sorted([f for f in os.listdir(JOB_DIR) if f.endswith(".py") and not f.endswith("_working.py")])
        
        if job_files:
            stop_idle_animation()
            idle_starter.cancel()
            
            job_file = job_files[0]
            job_hash = job_file.replace(".py", "")
            meta = metadata.get(job_hash, {"filename": "unknown", "username": "unknown"})
            
            job_path = os.path.join(JOB_DIR, job_file)
            working_path = job_path.replace(".py", "_working.py")
            log_path = os.path.join(LOG_DIR, f"{job_hash}.log")
            archive_path = os.path.join(ARCHIVE_DIR, f"{job_hash}.py")
            
            os.rename(job_path, working_path)
            print(f"Running: {job_hash}")
            
            run_job(working_path, log_path, archive_path, meta, job_hash)
            cleanup_old_logs()
            
            idle_starter.poke()
        
        time.sleep(2)

if __name__ == "__main__":
    worker_loop()
