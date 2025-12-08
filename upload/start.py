#!/usr/bin/env python3
import subprocess
import time
import os

processes = []

def main():
    print("Starting Chippy Tree services...")
    # cd to src/webapp and start Flask server
    flask_proc = subprocess.Popen(
        ["flask", "run", "--host=0.0.0.0", "--port=5000"],
        cwd="src/webapp/",
        env={**dict(os.environ), "FLASK_APP": "app.py"}
    )
    processes.append(flask_proc)
    print("Flask server started on http://localhost:5000")
    
    # cd to src/scheduler and start worker
    worker_proc = subprocess.Popen(
        ["python", "worker.py"],
        cwd="src/scheduler/"
    )
    processes.append(worker_proc)
    
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()