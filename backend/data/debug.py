import sqlite3
import json
conn = sqlite3.connect('backend/data/jobs.db')
row = conn.execute("SELECT document FROM study_guides WHERE id='job_5305ef89eda44cf0a3de7098728d030d'").fetchone()
doc = json.loads(row[0])
for key, value in doc.items():
    if "<feynman>" in value:
        print("FOUND IN:", key)
        idx = value.find("<feynman>")
        end_idx = value.find("</feynman>")
        print(repr(value[idx:end_idx+10]))
