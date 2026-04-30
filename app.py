import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "camps.db"
SEED_JSON_PATH = BASE_DIR / "camps.json"
def resolve_admin_token():
    # Keep backward compatibility with earlier Railway variable naming.
    for key in ("ADMIN_TOKEN", "NIETZSCHE", "Nietzsche"):
        value = os.environ.get(key)
        if value:
            return value
    return "change-me-before-production"


ADMIN_TOKEN = resolve_admin_token()

app = Flask(__name__, static_folder=".", static_url_path="")
BOOTSTRAP_STATUS = {
    "lastRunAt": None,
    "trigger": None,
    "success": None,
    "scripts": [],
    "approvedCount": 0,
    "totalCount": 0,
    "message": "No bootstrap run yet.",
}


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db()
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS camps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            county TEXT NOT NULL,
            price_eur REAL,
            hours TEXT,
            extended_hours_note TEXT,
            camp_weeks_text TEXT,
            food_provided TEXT NOT NULL,
            age_min INTEGER,
            age_max INTEGER,
            source_url TEXT,
            source_type TEXT NOT NULL DEFAULT 'manual',
            status TEXT NOT NULL DEFAULT 'approved',
            submitted_by_name TEXT,
            submitted_by_email TEXT,
            notes TEXT,
            last_checked_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.commit()
    # Lightweight schema migrations for existing databases.
    existing_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(camps)").fetchall()
    }
    if "location_detail" not in existing_columns:
        connection.execute("ALTER TABLE camps ADD COLUMN location_detail TEXT")
    if "extended_hours_note" not in existing_columns:
        connection.execute("ALTER TABLE camps ADD COLUMN extended_hours_note TEXT")
    if "camp_weeks_text" not in existing_columns:
        connection.execute("ALTER TABLE camps ADD COLUMN camp_weeks_text TEXT")
    connection.commit()
    connection.close()


def seed_db_if_empty():
    connection = get_db()
    existing_count = connection.execute("SELECT COUNT(*) AS count FROM camps").fetchone()["count"]

    if existing_count > 0 or not SEED_JSON_PATH.exists():
        connection.close()
        return

    with open(SEED_JSON_PATH, "r", encoding="utf-8") as file:
        camps = json.load(file)

    now = datetime.utcnow().isoformat()
    for camp in camps:
        connection.execute(
            """
            INSERT INTO camps
            (name, type, county, price_eur, hours, food_provided, age_min, age_max, source_type, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'seed', 'approved', ?, ?)
            """,
            (
                camp["name"],
                camp["type"],
                camp["county"],
                camp.get("priceEur"),
                camp.get("hours"),
                "yes" if camp.get("foodProvided") else "no",
                camp.get("ageMin"),
                camp.get("ageMax"),
                now,
                now,
            ),
        )

    connection.commit()
    connection.close()


def row_to_camp(row):
    weeks_text = row["camp_weeks_text"] or ""
    camp_weeks = [week.strip() for week in weeks_text.split("|") if week.strip()]
    return {
        "id": row["id"],
        "name": row["name"],
        "type": row["type"],
        "county": row["county"],
        "locationDetail": row["location_detail"],
        "priceEur": row["price_eur"],
        "hours": row["hours"],
        "extendedHours": row["extended_hours_note"],
        "campWeeks": camp_weeks,
        "foodProvided": row["food_provided"] == "yes",
        "ageMin": row["age_min"],
        "ageMax": row["age_max"],
        "sourceUrl": row["source_url"],
        "sourceType": row["source_type"],
        "status": row["status"],
        "submittedByName": row["submitted_by_name"],
        "submittedByEmail": row["submitted_by_email"],
        "notes": row["notes"],
        "lastCheckedAt": row["last_checked_at"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


@app.get("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/api/camps")
def list_camps():
    status = request.args.get("status", "approved")
    connection = get_db()
    rows = connection.execute(
        "SELECT * FROM camps WHERE status = ? ORDER BY updated_at DESC",
        (status,),
    ).fetchall()
    connection.close()
    return jsonify([row_to_camp(row) for row in rows])


@app.post("/api/submissions")
def create_submission():
    payload = request.get_json(silent=True) or {}
    required_fields = ["name", "type", "county", "hours", "contactName", "contactEmail"]
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    food_value = payload.get("foodProvided", "unknown")
    if food_value not in {"yes", "no", "unknown"}:
        return jsonify({"error": "foodProvided must be yes, no, or unknown"}), 400

    now = datetime.utcnow().isoformat()
    connection = get_db()
    connection.execute(
        """
        INSERT INTO camps
        (name, type, county, location_detail, price_eur, hours, extended_hours_note, camp_weeks_text, food_provided, age_min, age_max, source_url, source_type, status,
         submitted_by_name, submitted_by_email, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'user_submission', 'pending_review', ?, ?, ?, ?, ?)
        """,
        (
            payload["name"].strip(),
            payload["type"].strip(),
            payload["county"].strip(),
            (payload.get("locationDetail") or "").strip() or None,
            payload.get("priceEur"),
            payload["hours"].strip(),
            (payload.get("extendedHours") or "").strip() or None,
            (payload.get("campWeeksText") or "").strip() or None,
            food_value,
            payload.get("ageMin"),
            payload.get("ageMax"),
            payload.get("sourceUrl"),
            payload["contactName"].strip(),
            payload["contactEmail"].strip(),
            payload.get("notes", "").strip(),
            now,
            now,
        ),
    )
    connection.commit()
    connection.close()
    return jsonify({"message": "Submission received and pending review."}), 201


def is_admin(request_obj):
    return request_obj.headers.get("x-admin-token") == ADMIN_TOKEN


def get_camp_counts(connection):
    approved = connection.execute(
        "SELECT COUNT(*) AS count FROM camps WHERE status = 'approved'"
    ).fetchone()["count"]
    total = connection.execute("SELECT COUNT(*) AS count FROM camps").fetchone()["count"]
    return approved, total


def mark_seed_rejected(connection):
    now = datetime.utcnow().isoformat()
    connection.execute(
        "UPDATE camps SET status = 'rejected', updated_at = ? WHERE source_type = 'seed'",
        (now,),
    )


def run_bootstrap_scripts():
    scripts = [
        "ingest_real_data.py",
        "ingest_key_camps.py",
        "ingest_location_priority_camps.py",
        "ingest_hidden_discovery_camps.py",
        "ingest_requested_camps.py",
        "ingest_sports_and_weeks.py",
        "discover_from_seed_urls.py",
        "sync_live_overrides.py",
    ]
    results = []
    for script in scripts:
        script_path = BASE_DIR / script
        if not script_path.exists():
            results.append(
                {
                    "script": script,
                    "ran": False,
                    "success": False,
                    "error": "Missing script file",
                }
            )
            continue
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
        )
        results.append(
            {
                "script": script,
                "ran": True,
                "success": result.returncode == 0,
                "stdout": result.stdout[-2000:],
                "stderr": result.stderr[-2000:],
                "error": None if result.returncode == 0 else f"Exit code {result.returncode}",
            }
        )
    return results


def execute_bootstrap(trigger):
    script_results = run_bootstrap_scripts()
    all_success = all(item["success"] for item in script_results)

    connection = get_db()
    mark_seed_rejected(connection)
    approved, total = get_camp_counts(connection)
    connection.commit()
    connection.close()

    BOOTSTRAP_STATUS.update(
        {
            "lastRunAt": datetime.utcnow().isoformat(),
            "trigger": trigger,
            "success": all_success,
            "scripts": script_results,
            "approvedCount": approved,
            "totalCount": total,
            "message": (
                "Live data bootstrap complete."
                if all_success
                else "Bootstrap completed with one or more script failures."
            ),
        }
    )
    return BOOTSTRAP_STATUS


def auto_bootstrap_if_seed_only():
    if os.environ.get("AUTO_BOOTSTRAP_ON_STARTUP", "true").lower() != "true":
        return

    connection = get_db()
    approved = connection.execute(
        "SELECT COUNT(*) AS count FROM camps WHERE status = 'approved'"
    ).fetchone()["count"]
    seed_approved = connection.execute(
        "SELECT COUNT(*) AS count FROM camps WHERE status = 'approved' AND source_type = 'seed'"
    ).fetchone()["count"]
    connection.close()

    # Fresh deploy heuristic: only a handful of seed records are visible.
    if approved <= 5 and seed_approved == approved and approved > 0:
        try:
            execute_bootstrap(trigger="startup_auto")
        except Exception as error:
            BOOTSTRAP_STATUS.update(
                {
                    "lastRunAt": datetime.utcnow().isoformat(),
                    "trigger": "startup_auto",
                    "success": False,
                    "scripts": [],
                    "message": f"Auto-bootstrap crashed before completion: {error}",
                }
            )
            print(f"[bootstrap] auto bootstrap failed: {error}")


@app.get("/api/admin/submissions")
def list_submissions():
    if not is_admin(request):
        return jsonify({"error": "Unauthorized"}), 401

    connection = get_db()
    rows = connection.execute(
        "SELECT * FROM camps WHERE status = 'pending_review' ORDER BY created_at ASC"
    ).fetchall()
    connection.close()
    return jsonify([row_to_camp(row) for row in rows])


@app.get("/api/admin/summary")
def admin_summary():
    if not is_admin(request):
        return jsonify({"error": "Unauthorized"}), 401

    connection = get_db()
    approved = connection.execute(
        "SELECT COUNT(*) AS count FROM camps WHERE status = 'approved'"
    ).fetchone()["count"]
    pending = connection.execute(
        "SELECT COUNT(*) AS count FROM camps WHERE status = 'pending_review'"
    ).fetchone()["count"]
    rejected = connection.execute(
        "SELECT COUNT(*) AS count FROM camps WHERE status = 'rejected'"
    ).fetchone()["count"]
    connection.close()
    return jsonify({"approved": approved, "pending": pending, "rejected": rejected})


@app.get("/api/admin/change-log")
def admin_change_log():
    if not is_admin(request):
        return jsonify({"error": "Unauthorized"}), 401

    connection = get_db()
    rows = connection.execute(
        """
        SELECT id, name, status, source_type, updated_at
        FROM camps
        ORDER BY datetime(updated_at) DESC
        LIMIT 40
        """
    ).fetchall()
    connection.close()
    return jsonify(
        [
            {
                "id": row["id"],
                "name": row["name"],
                "status": row["status"],
                "sourceType": row["source_type"],
                "updatedAt": row["updated_at"],
            }
            for row in rows
        ]
    )


@app.get("/api/admin/bootstrap-status")
def admin_bootstrap_status():
    if not is_admin(request):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(BOOTSTRAP_STATUS)


@app.post("/api/admin/submissions/<int:submission_id>/approve")
def approve_submission(submission_id):
    if not is_admin(request):
        return jsonify({"error": "Unauthorized"}), 401

    now = datetime.utcnow().isoformat()
    connection = get_db()
    cursor = connection.execute(
        "UPDATE camps SET status = 'approved', updated_at = ? WHERE id = ? AND status = 'pending_review'",
        (now, submission_id),
    )
    connection.commit()
    connection.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Submission not found"}), 404
    return jsonify({"message": "Submission approved"})


@app.post("/api/admin/submissions/<int:submission_id>/reject")
def reject_submission(submission_id):
    if not is_admin(request):
        return jsonify({"error": "Unauthorized"}), 401

    now = datetime.utcnow().isoformat()
    connection = get_db()
    cursor = connection.execute(
        "UPDATE camps SET status = 'rejected', updated_at = ? WHERE id = ? AND status = 'pending_review'",
        (now, submission_id),
    )
    connection.commit()
    connection.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Submission not found"}), 404
    return jsonify({"message": "Submission rejected"})


@app.post("/api/admin/submissions/approve-all")
def approve_all_submissions():
    if not is_admin(request):
        return jsonify({"error": "Unauthorized"}), 401

    now = datetime.utcnow().isoformat()
    connection = get_db()
    cursor = connection.execute(
        "UPDATE camps SET status = 'approved', updated_at = ? WHERE status = 'pending_review'",
        (now,),
    )
    connection.commit()
    approved, total = get_camp_counts(connection)
    connection.close()
    return jsonify(
        {
            "message": "All pending submissions approved.",
            "updatedRows": cursor.rowcount,
            "approvedCount": approved,
            "totalCount": total,
        }
    )


@app.post("/api/admin/bootstrap-live-data")
def bootstrap_live_data():
    if not is_admin(request):
        return jsonify({"error": "Unauthorized"}), 401

    status = execute_bootstrap(trigger="admin_manual")
    response_body = {
        "message": status["message"],
        "scripts": status["scripts"],
        "approvedCount": status["approvedCount"],
        "totalCount": status["totalCount"],
        "success": status["success"],
    }
    if status["success"]:
        return jsonify(response_body)
    return jsonify(response_body), 500


@app.get("/admin")
def admin_page():
    return send_from_directory(BASE_DIR, "admin.html")


init_db()
seed_db_if_empty()
auto_bootstrap_if_seed_only()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
