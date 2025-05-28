import os
from flask import Flask


def create_app():
    """Create and configure Flask application"""
    # Get the path to the project root (parent of app directory)
    app_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(app_dir)

    # Create Flask app with correct template and static directories
    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, "templates"),
        static_folder=os.path.join(project_root, "static"),
    )

    app.secret_key = "hellas-direct-chatbot-secret-key"  # Required for sessions
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

    # Set upload folder relative to project root
    upload_folder = os.path.join(project_root, "uploads")
    app.config["UPLOAD_FOLDER"] = upload_folder

    # Create uploads directory if it doesn't exist
    os.makedirs(upload_folder, exist_ok=True)

    return app


def get_api_key():
    """Get OpenAI API key from environment or return default"""
    API_KEY = ""
    if not API_KEY:
        API_KEY = os.getenv("OPENAI_API_KEY")

    if not API_KEY:
        raise ValueError(
            "API key is not set. Please set the API key as a static variable or in the environment variable OPENAI_API_KEY."
        )

    return API_KEY
