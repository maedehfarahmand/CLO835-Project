import os
import boto3
import logging
import pymysql
from flask import Flask, render_template

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Environment variables from ConfigMap and Secret
BACKGROUND_IMAGE_URL = os.environ.get("BACKGROUND_IMAGE_URL", "")
STUDENT_NAME = os.environ.get("STUDENT_NAME", "Student")
DB_HOST = os.environ.get("DBHOST", "mysql-service")  # Service name in K8s
DB_USER = os.environ.get("DBUSER")
DB_PASSWORD = os.environ.get("DBPWD")
DB_NAME = os.environ.get("DATABASE")

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

def get_student_names():
    """Fetch student names from MySQL database."""
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT name FROM students")  # Replace with your table
                rows = cursor.fetchall()
                names = [row['name'] for row in rows]
                return names
    except Exception as e:
        logging.error(f"Error connecting to MySQL: {e}")
        return []

@app.route("/")
def index():
    student_list = get_student_names()
    return render_template("index.html", name=STUDENT_NAME, students=student_list)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)