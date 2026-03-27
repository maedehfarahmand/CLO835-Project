import os
import boto3
import logging
from flask import Flask, render_template

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# From ConfigMap env vars
BACKGROUND_IMAGE_URL = os.environ.get("BACKGROUND_IMAGE_URL", "")  # s3://bucket/image.jpg
STUDENT_NAME = os.environ.get("STUDENT_NAME", "Student")
DB_USER = os.environ.get("DBUSER")
DB_PASSWORD = os.environ.get("DBPWD")

def download_background():
    """Download background image from S3 to local static folder."""
    if BACKGROUND_IMAGE_URL.startswith("s3://"):
        parts = BACKGROUND_IMAGE_URL[5:].split("/", 1)
        bucket, key = parts[0], parts[1]
        logging.info(f"Downloading background image from: {BACKGROUND_IMAGE_URL}")
        s3 = boto3.client("s3")
        os.makedirs("static", exist_ok=True)
        s3.download_file(bucket, key, "static/background.jpg")

download_background()

@app.route("/")
def index():
    return render_template("index.html", name=STUDENT_NAME)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)
