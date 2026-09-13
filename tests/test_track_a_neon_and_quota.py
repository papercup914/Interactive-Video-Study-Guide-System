import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.data.database import engine, SessionLocal
from backend.data.models import Base, Job, StudyGuide, UserUsage
from backend.services.job_manager import (
    init_db_schema,
    create_job,
    get_job,
    check_and_increment_quota,
    get_user_daily_usage,
)

def run_track_a_tests():
    print("=== [Track A Verification] Starting Neon PostgreSQL & Quota Test ===")
    
    print(f"[1/5] Checking DB connection: {engine.url.render_as_string(hide_password=True)}")
    with engine.connect() as conn:
        result = conn.execute(__import__("sqlalchemy").text("SELECT 1")).scalar()
        print(f"      Connection OK: SELECT 1 => {result}")
        
    print("[2/5] Initializing database schema (idempotent)...")
    init_db_schema()
    print("      Schema initialized successfully.")
    
    test_job_id = f"test_job_{int(datetime.now().timestamp())}"
    test_user_id = f"test_user_{int(datetime.now().timestamp())}"
    print(f"[3/5] Testing create_job with user_id: {test_job_id} / {test_user_id}")
    create_job(test_job_id, user_id=test_user_id)
    
    with SessionLocal() as db:
        saved_job = db.query(Job).filter(Job.id == test_job_id).first()
        assert saved_job is not None, "Job was not saved to DB"
        assert saved_job.user_id == test_user_id, f"Expected user_id={test_user_id}, got {saved_job.user_id}"
        print(f"      Job verification OK: job.id={saved_job.id}, job.user_id={saved_job.user_id}")
        
    print(f"[4/5] Testing daily quota for user: {test_user_id} (limit=3)")
    
    allowed, used, max_lim = check_and_increment_quota(test_user_id, max_daily=3)
    assert allowed is True and used == 1, f"1st call failed: allowed={allowed}, used={used}"
    print(f"      Try 1: allowed={allowed}, used={used}/{max_lim}")
    
    allowed, used, max_lim = check_and_increment_quota(test_user_id, max_daily=3)
    assert allowed is True and used == 2, f"2nd call failed: allowed={allowed}, used={used}"
    print(f"      Try 2: allowed={allowed}, used={used}/{max_lim}")
    
    allowed, used, max_lim = check_and_increment_quota(test_user_id, max_daily=3)
    assert allowed is True and used == 3, f"3rd call failed: allowed={allowed}, used={used}"
    print(f"      Try 3: allowed={allowed}, used={used}/{max_lim}")
    
    allowed, used, max_lim = check_and_increment_quota(test_user_id, max_daily=3)
    assert allowed is False and used == 3, f"4th call should be BLOCKED: allowed={allowed}, used={used}"
    print(f"      Try 4 (Quota Exceeded): allowed={allowed}, used={used}/{max_lim} => BLOCKED AS EXPECTED!")
    
    usage_info = get_user_daily_usage(test_user_id, max_daily=3)
    assert usage_info["used"] == 3 and usage_info["remaining"] == 0
    print(f"      Usage status query: {usage_info}")
    
    print("[5/5] Cleaning up test data...")
    with SessionLocal() as db:
        db.query(Job).filter(Job.id == test_job_id).delete()
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        db.query(UserUsage).filter(UserUsage.id == f"{test_user_id}:{date_str}").delete()
        db.commit()
    print("      Cleanup complete.")
    
    print("\n[SUCCESS] === ALL TRACK A TESTS PASSED PERFECTLY! ===")

if __name__ == "__main__":
    run_track_a_tests()
