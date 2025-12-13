#!/usr/bin/env python3
import subprocess
import time
import os
import sys

processes = []

def main():
    print("Starting Chippy Tree services...")
    
    flask_proc = subprocess.Popen(
        ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"],
        cwd="webapp",
        env={**dict(os.environ), "FLASK_APP": "app.py"}
    )
    processes.append(flask_proc)
    print("Flask server started on http://localhost:5000")
    
    # Start worker scheduler
    worker_proc = subprocess.Popen(
        ["python", "worker.py"],
        cwd="scheduler"
    )
    processes.append(worker_proc)
    print("Worker scheduler started")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down services...")
        for proc in processes:
            proc.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
