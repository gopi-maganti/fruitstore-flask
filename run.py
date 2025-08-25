import os

from dotenv import load_dotenv
from flask import send_from_directory

from app import create_app

# Load environment variables from .env
load_dotenv()

# Initialize the Flask app
app = create_app()


# Serve uploaded files (e.g., fruit images)
@app.route("/static/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_RUN_PORT", 5000))

    print(f"🚀 Starting app at http://{host}:{port}")
    app.run(debug=True, host=host, port=port)
