import sqlite3
import json

conn = sqlite3.connect('backend/data/jobs.db')
row = conn.execute("SELECT document FROM study_guides WHERE id='job_5305ef89eda44cf0a3de7098728d030d'").fetchone()

if row:
    doc = json.loads(row[0])
    print("Keys in doc:", doc.keys())
    for k in doc.keys():
        if "시스템_아키텍처" in k:
            print("--- MATCHING KEY ---:", k)
            print(doc[k][:500])
