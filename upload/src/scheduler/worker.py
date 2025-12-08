import time
import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from runner import execute_code

# all files will be added to jobs/ from the flask app
JOB_DIR = "jobs"
LOG_DIR = "logs"
ARCHIVE_DIR = "archive"
METADATA_FILE = "metadata.json"
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

def worker_loop():
    """Continuously checks for new jobs and executes them."""
    print("Worker started, monitoring for jobs...")
    metadata = load_metadata()
    
    while True:
        # Reload metadata each iteration to catch new jobs
        metadata = load_metadata()
        
        job_files = sorted([f for f in os.listdir(JOB_DIR) if f.endswith(".py") and not f.endswith("_working.py")])
        
        if job_files:
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
                
                result = execute_code(code)
                
                # Append result to log
                with open(log_path, 'a') as log:
                    log.write("\n" + "=" * 50 + "\n")
                    log.write("Output:\n")
                    log.write(result)
                    log.write("\n\nJob completed successfully\n")
                
                print(f"Job {job_hash} completed. Result: {result}")
                
                time.sleep(1)
                
                cleanup_old_logs()
                
            except Exception as e:
                error_msg = f"Error processing {job_hash}: {e}"
                print(error_msg)
                
                # log error
                with open(log_path, 'a') as log:
                    log.write("\n" + "=" * 50 + "\n")
                    log.write(f"ERROR: {e}\n")
                
            finally:
                if os.path.exists(working_path):
                    os.remove(working_path)
                    print(f"Job {job_hash} removed from queue.")
        
        time.sleep(2)

if __name__ == "__main__":
    worker_loop()