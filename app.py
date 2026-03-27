import os
import boto3
import logging
from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Environment variables
BACKGROUND_IMAGE_URL = os.environ.get("BACKGROUND_IMAGE_URL", "")
STUDENT_NAME = os.environ.get("STUDENT_NAME", "Student")
DB_HOST = os.environ.get("DBHOST")
DB_USER = os.environ.get("DBUSER")
DB_PASSWORD = os.environ.get("DBPWD")
DB_NAME = os.environ.get("DATABASE")

# Optional: download background image from S3
def download_background():
    if BACKGROUND_IMAGE_URL.startswith("s3://"):
        parts = BACKGROUND_IMAGE_URL[5:].split("/", 1)
        bucket, key = parts[0], parts[1]
        logging.info(f"Downloading background image from: {BACKGROUND_IMAGE_URL}")
        s3 = boto3.client("s3")
        os.makedirs("static", exist_ok=True)
        s3.download_file(bucket, key, "static/background.jpg")

download_background()

# Connect to MySQL and fetch entries
def get_student_entries():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM employees;")  # Change table name as needed
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        logging.error(f"DB connection failed: {e}")
        return []

@app.route("/")
def index():
    employees = get_student_entries()
    return render_template("index.html", name=STUDENT_NAME, employees=employees)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)