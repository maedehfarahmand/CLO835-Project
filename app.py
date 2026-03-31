import os
import boto3
import logging
from flask import Flask, render_template, request, redirect, url_for
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
COLOR = os.environ.get("APP_COLOR", "#f0f4f8")

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


def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


# ── Home: list all employees ──────────────────────────────────────────────────
@app.route("/")
def home():
    employees = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM employees;")
        employees = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        logging.error(f"DB connection failed: {e}")
    return render_template("index.html", name=STUDENT_NAME, employees=employees, color=COLOR)


# ── Add employee form ─────────────────────────────────────────────────────────
@app.route("/addemp", methods=["GET"])
def addemp():
    return render_template("addemp.html", color=COLOR)


# ── Add employee submit ───────────────────────────────────────────────────────
@app.route("/addemp", methods=["POST"])
def addemp_post():
    emp_id        = request.form.get("emp_id")
    first_name    = request.form.get("first_name")
    last_name     = request.form.get("last_name")
    primary_skill = request.form.get("primary_skill")
    location      = request.form.get("location")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO employees (emp_id, first_name, last_name, primary_skill, location) "
            "VALUES (%s, %s, %s, %s, %s)",
            (emp_id, first_name, last_name, primary_skill, location)
        )
        conn.commit()
        cursor.close()
        conn.close()
        name = f"{first_name} {last_name}"
    except Exception as e:
        logging.error(f"Failed to add employee: {e}")
        name = "Unknown (DB error)"

    return render_template("addempoutput.html", name=name, color=COLOR)


# ── Get employee form ─────────────────────────────────────────────────────────
@app.route("/getemp", methods=["GET", "POST"])
def getemp():
    return render_template("getemp.html", color=COLOR)


# ── Fetch employee data ───────────────────────────────────────────────────────
@app.route("/fetchdata", methods=["POST"])
def fetchdata():
    emp_id = request.form.get("emp_id")
    emp = {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM employees WHERE emp_id = %s;", (emp_id,))
        emp = cursor.fetchone() or {}
        cursor.close()
        conn.close()
    except Exception as e:
        logging.error(f"Failed to fetch employee: {e}")

    return render_template(
        "getempoutput.html",
        id=emp.get("emp_id", "N/A"),
        fname=emp.get("first_name", "N/A"),
        lname=emp.get("last_name", "N/A"),
        interest=emp.get("primary_skill", "N/A"),
        location=emp.get("location", "N/A"),
        color=COLOR
    )


# ── About page ────────────────────────────────────────────────────────────────
@app.route("/about")
def about():
    return render_template("about.html", name=STUDENT_NAME, color=COLOR)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)
