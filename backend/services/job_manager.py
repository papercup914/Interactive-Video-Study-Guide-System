import sqlite3
import json
import os
from typing import Dict, Any
from datetime import datetime

DB_PATH = "backend/data/jobs.db"

def _get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    # check_same_thread=False allows FastAPI's threadpool to share the connection
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def _init_db():
    conn = _get_conn()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            status TEXT,
            progress TEXT,
            document TEXT,
            url TEXT,
            title TEXT,
            error TEXT,
            created_at TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS job_checkpoints (
            job_id TEXT,
            section_title TEXT,
            content TEXT,
            created_at TEXT,
            PRIMARY KEY (job_id, section_title)
        )
    ''')
    conn.commit()
    conn.close()

# Initialize on import
_init_db()

def create_job(job_id: str) -> None:
    conn = _get_conn()
    created_at = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO jobs (id, status, progress, created_at) VALUES (?, ?, ?, ?)",
        (job_id, "pending", "", created_at)
    )
    conn.commit()
    conn.close()

def update_job_status(job_id: str, status: str, progress: str = "") -> None:
    conn = _get_conn()
    if progress:
        conn.execute("UPDATE jobs SET status = ?, progress = ? WHERE id = ?", (status, progress, job_id))
    else:
        conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
    conn.commit()
    conn.close()

def finish_job(job_id: str, document: Dict[str, str], url: str = None, title: str = None) -> None:
    conn = _get_conn()
    doc_json = json.dumps(document, ensure_ascii=False)
    conn.execute(
        "UPDATE jobs SET status = ?, progress = ?, document = ?, url = ?, title = ? WHERE id = ?",
        ("completed", "100%", doc_json, url, title, job_id)
    )
    conn.commit()
    conn.close()

def fail_job(job_id: str, error_message: str) -> None:
    conn = _get_conn()
    conn.execute("UPDATE jobs SET status = ?, error = ? WHERE id = ?", ("failed", error_message, job_id))
    conn.commit()
    conn.close()
    
    os.makedirs("backend/data", exist_ok=True)
    with open("backend/data/last_error.txt", "w", encoding="utf-8") as f:
        f.write(f"Job: {job_id}\nError: {error_message}")

def get_job(job_id: str) -> Dict[str, Any]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    
    if not row:
        return None
        
    job = dict(row)
    if job.get("document"):
        try:
            job["document"] = json.loads(job["document"])
        except:
            job["document"] = {}
    return job

def cancel_job(job_id: str) -> None:
    conn = _get_conn()
    conn.execute("UPDATE jobs SET status = ?, progress = ? WHERE id = ?", ("cancelled", "작업이 중단되었습니다.", job_id))
    conn.commit()
    conn.close()

def save_chapter_checkpoint(job_id: str, section_title: str, content: str) -> None:
    conn = _get_conn()
    created_at = datetime.now().isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO job_checkpoints (job_id, section_title, content, created_at) VALUES (?, ?, ?, ?)",
        (job_id, section_title, content, created_at)
    )
    conn.commit()
    conn.close()

def get_completed_chapters(job_id: str) -> Dict[str, str]:
    conn = _get_conn()
    rows = conn.execute("SELECT section_title, content FROM job_checkpoints WHERE job_id = ?", (job_id,)).fetchall()
    conn.close()
    return {row["section_title"]: row["content"] for row in rows}

