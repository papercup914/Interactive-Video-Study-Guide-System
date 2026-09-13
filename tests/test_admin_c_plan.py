import os
import sys
import unittest
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.data.database import SessionLocal
from backend.data.models import Job, StudyGuide, UserUsage
from backend.services.job_manager import (
    create_job,
    update_job_status,
    fail_job,
    get_admin_jobs,
    retry_job,
    delete_job,
    get_all_user_usages,
    reset_user_quota,
    get_admin_study_guides,
    delete_study_guide,
    check_and_increment_quota
)

class TestAdminCPlan(unittest.TestCase):
    def setUp(self):
        self.test_job_id = f"test_job_{int(datetime.now().timestamp())}"
        self.test_user_id = f"test_user_{int(datetime.now().timestamp())}"
        self.test_guide_id = f"test_guide_{int(datetime.now().timestamp())}"

    def tearDown(self):
        delete_job(self.test_job_id)
        delete_study_guide(self.test_guide_id)
        with SessionLocal() as db:
            db.query(UserUsage).filter(UserUsage.user_id == self.test_user_id).delete()
            db.commit()

    def test_job_lifecycle_and_admin_actions(self):
        """Job 생성 -> 실패 상태 전환 -> 관리자 목록 조회 -> 재시도 -> 삭제 검증"""
        # 1. Job 생성
        create_job(self.test_job_id, user_id=self.test_user_id)
        with SessionLocal() as db:
            j = db.query(Job).filter(Job.id == self.test_job_id).first()
            j.url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            j.title = "Rick Astley - Never Gonna Give You Up"
            db.commit()

        # 2. fail_job 호출
        fail_job(self.test_job_id, "Test timeout error in LLM")

        # 3. get_admin_jobs 조회
        res = get_admin_jobs(limit=10, status="failed", search=self.test_job_id)
        self.assertGreaterEqual(res["total"], 1)
        found = any(item["id"] == self.test_job_id for item in res["items"])
        self.assertTrue(found, "생성된 실패 작업이 관리자 목록에 포함되어야 함")

        # 4. retry_job 호출
        retry_info = retry_job(self.test_job_id)
        self.assertIsNotNone(retry_info)
        self.assertEqual(retry_info["status"], "pending")
        self.assertEqual(retry_info["url"], "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        # 5. delete_job 호출
        del_res = delete_job(self.test_job_id)
        self.assertTrue(del_res)
        with SessionLocal() as db:
            j_after = db.query(Job).filter(Job.id == self.test_job_id).first()
            self.assertIsNone(j_after, "Job이 삭제되어야 함")

    def test_quota_reset(self):
        """유저 쿼터 소진 후 관리자 원클릭 리셋 검증"""
        # 1. 쿼터 3회 모두 소진
        for _ in range(3):
            allowed, count, max_q = check_and_increment_quota(self.test_user_id, max_daily=3)
        self.assertEqual(count, 3)

        # 4회차 시도 시 거절 확인
        allowed4, count4, _ = check_and_increment_quota(self.test_user_id, max_daily=3)
        self.assertFalse(allowed4)
        self.assertEqual(count4, 3)

        # 2. 관리자 get_all_user_usages 조회
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        usages = get_all_user_usages(target_date=today_str)
        user_usage = next((u for u in usages if u["user_id"] == self.test_user_id), None)
        self.assertIsNotNone(user_usage)
        self.assertEqual(user_usage["generation_count"], 3)

        # 3. reset_user_quota 호출
        reset_res = reset_user_quota(self.test_user_id, target_date=today_str)
        self.assertTrue(reset_res)

        # 4. 쿼터가 0으로 리셋되었는지 확인하고 다시 1회 허용되는지 검증
        allowed_again, count_again, _ = check_and_increment_quota(self.test_user_id, max_daily=3)
        self.assertTrue(allowed_again, "리셋 후 다시 생성이 허용되어야 함")
        self.assertEqual(count_again, 1)

    def test_admin_api_secret_check(self):
        """관리자 시크릿 키 검증 엔드포인트 테스트"""
        from backend.routers.admin import check_admin_secret
        from fastapi import HTTPException

        # 유효하지 않은 키
        with self.assertRaises(HTTPException):
            check_admin_secret("invalid-secret-key")

        # 올바른 기본 키
        expected = os.getenv("ADMIN_SECRET_KEY", "studyguide-admin-2026").strip()
        self.assertTrue(check_admin_secret(expected))

if __name__ == "__main__":
    unittest.main()
