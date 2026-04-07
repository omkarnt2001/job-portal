import os
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")  # Supabase URL
engine = create_engine(DATABASE_URL)

@app.route("/jobs", methods=["GET"])
def get_jobs():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM jobs"))
        jobs = [dict(row) for row in result]
    return jsonify(jobs)

@app.route("/jobs", methods=["POST"])
def add_job():
    data = request.json
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO jobs (title, description) VALUES (:title, :description)"),
            **data
        )
    return jsonify({"status": "success"}), 201

if __name__ == "__main__":
    app.run(debug=True)
