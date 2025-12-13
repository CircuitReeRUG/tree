from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    
    os.makedirs("../scheduler/jobs", exist_ok=True)
    os.makedirs("../scheduler/logs", exist_ok=True)
    
    from .routes.queue import queue_bp
    from .routes.job import job_bp
    from .routes.editor import editor_bp
    
    app.register_blueprint(queue_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(editor_bp)
    
    return app

app = create_app()

