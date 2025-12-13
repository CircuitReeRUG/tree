from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scheduler'))
    os.makedirs(os.path.join(BASE_DIR, "jobs"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
    
    from .routes.queue import queue_bp
    from .routes.job import job_bp
    from .routes.editor import editor_bp
    
    app.register_blueprint(queue_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(editor_bp)
    
    return app

app = create_app()

