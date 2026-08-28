import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.services.job_manager import (
    create_batch_job,
    get_batch_job,
    update_batch_job_status,
    create_batch_video_items,
    get_batch_video_items,
    update_batch_video_item,
    upsert_study_guide_from_sync,
    get_all_presets_for_video,
    save_study_guide
)
from backend.services.batch_collector import is_shorts_video

class TestBatchPreGeneration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        os.environ["ADMIN_SYNC_SECRET"] = "test_secret_sync_key_1234"

    def test_shorts_detection(self):
        """쇼츠 판별 로직 검증"""
        # Duration <= 60
        self.assertTrue(is_shorts_video({"duration": 45, "title": "Regular Title"}))
        self.assertTrue(is_shorts_video({"duration": "59", "title": "Regular Title"}))
        # Title with #shorts
        self.assertTrue(is_shorts_video({"duration": 120, "title": "Cool Demo #shorts"}))
        # URL with /shorts/
        self.assertTrue(is_shorts_video({"duration": 150, "url": "https://youtube.com/shorts/abc1234"}))
        # Normal long video
        self.assertFalse(is_shorts_video({"duration": 650, "title": "Comprehensive AI Tutorial", "url": "https://youtube.com/watch?v=abc1234"}))

    def test_batch_job_lifecycle_in_db(self):
        """배치 작업 생성, 영상 아이템 추가, 상태 갱신 라이프사이클 테스트"""
        import uuid
        batch_id = f"test_batch_db_{uuid.uuid4().hex[:8]}"
        job = create_batch_job(

            batch_id=batch_id,
            url="https://youtube.com/playlist?list=PLtest",
            title="테스트 재생목록",
            provider="Google Gemini",
            max_limit=10,
            exclude_shorts=True,
            force_refresh=False
        )
        self.assertIsNotNone(job)
        self.assertEqual(job["id"], batch_id)
        self.assertEqual(job["status"], "pending")

        # 비디오 아이템 추가
        videos = [
            {"id": "vid001", "title": "Video 1", "duration": "10:00", "url": "https://youtube.com/watch?v=vid001"},
            {"id": "vid002", "title": "Video 2", "duration": "15:30", "url": "https://youtube.com/watch?v=vid002"}
        ]
        items = create_batch_video_items(batch_id, videos)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["video_id"], "vid001")

        # 비디오 아이템 상태 갱신
        target_id = items[0]["id"]
        update_batch_video_item(target_id, status="completed", presets_generated=9)
        updated_items = get_batch_video_items(batch_id)
        target_item = next((it for it in updated_items if it["id"] == target_id), None)
        self.assertIsNotNone(target_item)
        self.assertEqual(target_item["status"], "completed")
        self.assertEqual(target_item["presets_generated"], 9)


        # 배치 전체 상태 갱신
        update_batch_job_status(batch_id, status="completed", total=2, completed=1, skipped=1, failed=0)
        fetched_batch = get_batch_job(batch_id)
        self.assertEqual(fetched_batch["status"], "completed")
        self.assertEqual(fetched_batch["completed_videos"], 1)

    def test_sync_endpoint_security(self):
        """운영 서버 동기화 엔드포인트(POST /api/admin/sync-guide)의 보안 인증 및 데이터 등록 테스트"""
        # 1. 키 누락 시 403
        payload = {
            "batch_id": "test_batch_sec",
            "video_id": "test_sec_vid",
            "video_url": "https://youtube.com/watch?v=test_sec_vid",
            "guides": []
        }
        res_no_key = self.client.post("/api/admin/sync-guide", json=payload)
        self.assertEqual(res_no_key.status_code, 403)

        # 2. 잘못된 키 시 403
        res_wrong_key = self.client.post(
            "/api/admin/sync-guide",
            json=payload,
            headers={"X-Admin-Sync-Key": "wrong_key_xyz"}
        )
        self.assertEqual(res_wrong_key.status_code, 403)

        # 3. 올바른 키 시 200 OK 및 DB 등록
        guide_data = {
            "id": "guide_test_sec_normal_rich",
            "url": "https://youtube.com/watch?v=test_sec_vid",
            "title": "동기화된 테스트 영상",
            "image_url": "https://img.youtube.com/vi/test_sec_vid/0.jpg",
            "provider": "Google Gemini",
            "document": {"1. 서론": "서론 내용입니다."},
            "length_preset": "적당한 설명",
            "analogy_preset": "풍부한 비유",
            "generation_time_sec": 42
        }
        payload_valid = {
            "batch_id": "test_batch_sec",
            "video_id": "test_sec_vid",
            "video_url": "https://youtube.com/watch?v=test_sec_vid",
            "guides": [guide_data]
        }
        res_valid = self.client.post(
            "/api/admin/sync-guide",
            json=payload_valid,
            headers={"X-Admin-Sync-Key": "test_secret_sync_key_1234"}
        )
        self.assertEqual(res_valid.status_code, 200)
        data = res_valid.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["synced_count"], 1)

        # DB 조회 검증
        presets = get_all_presets_for_video("https://youtube.com/watch?v=test_sec_vid")
        self.assertGreaterEqual(len(presets), 1)
        self.assertEqual(presets[0]["title"], "동기화된 테스트 영상")

    @patch("backend.services.batch_collector.collect_videos_from_source")
    def test_batch_api_endpoints(self, mock_collect):
        """FastAPI 배치 관리 라우트 (start, get, list, cancel) 통합 테스트"""
        mock_collect.return_value = ("테스트 플레이리스트", [
            {"id": "demo001", "title": "Demo 1", "duration": "5:00", "url": "https://youtube.com/watch?v=demo001"}
        ])
        
        # Start batch
        start_res = self.client.post(
            "/api/admin/batch/start",
            json={
                "url": "https://youtube.com/playlist?list=PLdemo123",
                "provider": "Google Gemini",
                "max_limit": 5,
                "exclude_shorts": True,
                "force_refresh": False
            }
        )
        self.assertEqual(start_res.status_code, 200)
        start_data = start_res.json()
        self.assertEqual(start_data["status"], "success")
        batch_id = start_data["batch_id"]

        # Get batch detail
        detail_res = self.client.get(f"/api/admin/batch/{batch_id}")
        self.assertEqual(detail_res.status_code, 200)
        detail_data = detail_res.json()
        self.assertEqual(detail_data["batch"]["id"], batch_id)

        # List batches
        list_res = self.client.get("/api/admin/batch/list/all")
        self.assertEqual(list_res.status_code, 200)
        list_data = list_res.json()
        batch_ids = [b["id"] for b in list_data["batches"]]
        self.assertIn(batch_id, batch_ids)

        # Cancel batch
        cancel_res = self.client.post(f"/api/admin/batch/{batch_id}/cancel")
        self.assertEqual(cancel_res.status_code, 200)
        cancel_data = cancel_res.json()
        self.assertEqual(cancel_data["status"], "success")

    def test_process_audio_signature(self):
        """process_audio 시그니처(3개 인자 수용) 및 존재하지 않는 파일 예외 검증"""
        from backend.services.llm import process_audio
        # 파일이 없을 때 적절한 ValueError 발생
        with self.assertRaises(ValueError):
            process_audio("non_existent_audio.mp3", "Google Gemini", url_hash="test_hash_123")

    def test_batch_start_with_remote_config(self):
        """운영 서버 URL 및 시크릿 키가 포함된 배치 시작 테스트"""
        start_res = self.client.post(
            "/api/admin/batch/start",
            json={
                "url": "https://youtube.com/playlist?list=PLremote123",
                "provider": "Google Gemini",
                "max_limit": 5,
                "exclude_shorts": True,
                "force_refresh": False,
                "remote_url": "http://13.209.73.143:8000",
                "sync_key": "test_secret_key"
            }
        )
        self.assertEqual(start_res.status_code, 200)
        batch_id = start_res.json()["batch_id"]
        
        detail = get_batch_job(batch_id)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["remote_url"], "http://13.209.73.143:8000")
        self.assertEqual(detail["sync_key"], "test_secret_key")

if __name__ == "__main__":
    unittest.main()
