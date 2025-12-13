import time
import sys
import os
import json
import subprocess

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

JOB_DIR = "jobs"
LOG_DIR = "logs"
ARCHIVE_DIR = "archive"
METADATA_FILE = "metadata.json"
TIMEOUT_SECONDS = int(os.environ.get('JOB_TIMEOUT', 45))
IDLE_DELAY = int(os.environ.get('IDLE_ANIMATION_DELAY', 10))
os.makedirs(JOB_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

sys.path.insert(0, SRC_DIR)
from idle_animation import start_idle_animation, stop_idle_animation
from callback import DelayedCallback

idle_starter = DelayedCallback(IDLE_DELAY, start_idle_animation)

def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def cleanup_old_logs():
    if not os.path.exists(LOG_DIR):
        return
    
    log_files = [f for f in os.listdir(LOG_DIR) if f.endswith(".log")]
    if len(log_files) > 20:
        log_files_sorted = sorted(log_files, key=lambda f: os.path.getmtime(os.path.join(LOG_DIR, f)))
        
        for log_file in log_files_sorted[:len(log_files) - 20]:
            os.remove(os.path.join(LOG_DIR, log_file))
            job_hash = log_file.replace(".log", "")
            archive_file = f"{job_hash}.py"
            archive_path = os.path.join(ARCHIVE_DIR, archive_file)
            if os.path.exists(archive_path):
                os.remove(archive_path)

def run_job(working_path, log_path, archive_path, meta, job_hash):
    try:
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
        
        result = subprocess.run(
            [sys.executable, '-m', 'runner.main', working_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=SRC_DIR,
            env={**os.environ}
        )
        
        with open(log_path, 'a') as log_file:
            if result.stdout:
                log_file.write(result.stdout)
            if result.stderr:
                log_file.write("\nERRORS:\n" + result.stderr)
        
        if result.returncode == 0:
            with open(log_path, 'a') as log_file:
                log_file.write("\n\nJob completed\n")
        else:
            with open(log_path, 'a') as log_file:
                log_file.write(f"\n\nJob failed (exit code {result.returncode})\n")
                
    except subprocess.TimeoutExpired:
        with open(log_path, 'a') as log_file:
            log_file.write(f"\n\nTimed out after {TIMEOUT_SECONDS}s\n")
    
    except Exception as e:
        with open(log_path, 'a') as log_file:
            log_file.write(f"\n\nERROR: {e}\n")
    
    finally:
        if os.path.exists(working_path):
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
            job_path = os.path.join(JOB_DIR, job_file)
            working_path = job_path.replace(".py", "_working.py")
            job_hash = job_file.replace(".py", "")
            meta = metadata.get(job_hash, {"filename": "unknown", "username": "unknown"})
            
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
