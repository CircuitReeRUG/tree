import time
import sys
import os
import json
import multiprocessing

from idle_animation import start_idle_animation, stop_idle_animation
from callback import DelayedCallback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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

def execute_code_wrapper(code, result_queue):
    """Wrapper to run execute_code in a separate process"""
    try:
        result = execute_code(code)
        result_queue.put(('success', result))
    except Exception as e:
        result_queue.put(('error', str(e)))

def update_stats(success=True):
    """Update stats file with job completion"""
    stats_file = os.path.join(BASE_DIR, 'stats.json') if 'BASE_DIR' in globals() else 'stats.json'
    
    if not os.path.isabs(stats_file):
        stats_file = os.path.join(os.path.dirname(__file__), 'stats.json')
    
    if os.path.exists(stats_file):
        with open(stats_file, 'r') as f:
            stats_data = json.load(f)
    else:
        stats_data = {'start_time': time.time(), 'total_jobs': 0, 'total_errors': 0}
    
    stats_data['total_jobs'] = stats_data.get('total_jobs', 0) + 1
    if not success:
        stats_data['total_errors'] = stats_data.get('total_errors', 0) + 1
    
    with open(stats_file, 'w') as f:
        json.dump(stats_data, f)

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
    
    # Create a queue for the result
    result_queue = multiprocessing.Queue()
    
    # Start the process
    process = multiprocessing.Process(target=execute_code_wrapper, args=(code, result_queue))
    process.start()
    
    # Wait for timeout
    process.join(timeout=TIMEOUT_SECONDS)
    
    if process.is_alive():
        # Timeout occurred - kill the process
        process.terminate()
        process.join(timeout=1)
        if process.is_alive():
            process.kill()
            process.join()
        result = f"Error: Job exceeded {TIMEOUT_SECONDS} second timeout"
        update_stats(success=False)
    else:
        # Process finished normally
        if not result_queue.empty():
            status, result = result_queue.get()
            if status == 'error':
                result = f"Error: {result}"
                update_stats(success=False)
            else:
                update_stats(success=True)
        else:
            result = "Error: Job finished but produced no output"
            update_stats(success=False)
    
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
