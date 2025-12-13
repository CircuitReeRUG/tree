import time
import sys
import os
import json
import subprocess
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from runner import execute_code
from idle_animation import start_idle_animation, stop_idle_animation

# all files will be added to jobs/ from the flask app
JOB_DIR = "jobs"
LOG_DIR = "logs"
ARCHIVE_DIR = "archive"
METADATA_FILE = "metadata.json"
TIMEOUT_SECONDS = int(os.environ.get('JOB_TIMEOUT', 45))
os.makedirs(JOB_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

def load_metadata():
    """Load metadata from JSON file"""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def cleanup_old_logs():
    """Remove oldest logs and archived code if more than 20 exist"""
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
    """Run the job using the code in the job_file."""
    try:
        with open(working_path, "r") as f:
            code = f.read()
        
        # copy to archive
        with open(archive_path, 'w') as archive:
            archive.write(code)
        
        with open(log_path, 'w') as log:
            log.write(f"Job: {meta['filename']}\n")
            log.write(f"User: {meta['username']}\n")
            log.write(f"Hash: {job_hash}\n")
            log.write("=" * 50 + "\n\n")
        
        time.sleep(0.5)
        
        result = subprocess.run(
            ['python', '-c', f'import sys; sys.path.insert(0, ".."); from runner import execute_code; print(execute_code(sys.stdin.read()))'],
            input=code,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Log output
        with open(log_path, 'a') as log_file:
            log_file.write(result.stdout)
            log_file.write(result.stderr)
        
        if result.returncode == 0:
            with open(log_path, 'a') as log_file:
                log_file.write("\n\nJob completed successfully\n")
        else:
            with open(log_path, 'a') as log_file:
                log_file.write(f"\n\nJob failed with return code: {result.returncode}\n")
                
    except subprocess.TimeoutExpired:
        with open(log_path, 'a') as log_file:
            log_file.write(f"\n\nJob timed out after {TIMEOUT_SECONDS} seconds\n")
    
    except Exception as e:
        error_msg = f"Error processing {job_hash}: {e}"
        print(error_msg)
        
        # log error
        with open(log_path, 'a') as log_file:
            log_file.write("\n" + "=" * 50 + "\n")
            log_file.write(f"ERROR: {e}\n")
    
    finally:
        if os.path.exists(working_path):
            os.remove(working_path)
            print(f"Job {job_hash} removed from queue.")
            
                    
def worker_loop():
    """Continuously checks for new jobs and executes them."""
    print("Worker started, monitoring for jobs...")
    metadata = load_metadata()
    
    start_idle_animation()
    
    while True:
        # Reload metadata each iteration to catch new jobs
        metadata = load_metadata()
        
        job_files = sorted([f for f in os.listdir(JOB_DIR) if f.endswith(".py") and not f.endswith("_working.py")])
        
        if job_files:
            stop_idle_animation()
            
            job_file = job_files[0] 
            job_path = os.path.join(JOB_DIR, job_file)
            working_path = job_path.replace(".py", "_working.py")
            
            job_hash = job_file.replace(".py", "")
            meta = metadata.get(job_hash, {"filename": "unknown", "username": "unknown"})
            
            log_path = os.path.join(LOG_DIR, f"{job_hash}.log")
            archive_path = os.path.join(ARCHIVE_DIR, f"{job_hash}.py")
            
            try:
                # working
                os.rename(job_path, working_path)
                print(f"Processing job: {job_hash} ({meta['filename']} by {meta['username']})")
                
                run_job(working_path, log_path, archive_path, meta, job_hash)
                
                print(f"Job {job_hash} completed.")
                
                time.sleep(1)
                
                cleanup_old_logs()
                
            except Exception as e:
                error_msg = f"Error processing {job_hash}: {e}"
                print(error_msg)
                
                # log error
                with open(log_path, 'a') as log_file:
                    log_file.write("\n" + "=" * 50 + "\n")
                    log_file.write(f"ERROR: {e}\n")                finally:
                if os.path.exists(working_path):
                    os.remove(working_path)
                    print(f"Job {job_hash} removed from queue.")
                
                start_idle_animation()
        
        time.sleep(2)

if __name__ == "__main__":
    worker_loop()