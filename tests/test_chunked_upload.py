import os
import sys
import unittest
import io
import shutil
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

class TestChunkedUpload(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.upload_id = "test_upload_uuid_12345"
        self.filename = "test_meeting_audio.mp3"
        self.test_chunks_dir = f"backend/tmp/chunks/{self.upload_id}"
        self.expected_final_path = f"backend/tmp/{self.upload_id}_{self.filename}"
        
        if os.path.exists(self.test_chunks_dir):
            shutil.rmtree(self.test_chunks_dir, ignore_errors=True)
        if os.path.exists(self.expected_final_path):
            os.remove(self.expected_final_path)

    def tearDown(self):
        if os.path.exists(self.test_chunks_dir):
            shutil.rmtree(self.test_chunks_dir, ignore_errors=True)
        if os.path.exists(self.expected_final_path):
            os.remove(self.expected_final_path)

    def test_chunked_upload_and_merge(self):
        """Test sequential upload of 3 chunks and complete assembly"""
        raw_part1 = b"ABCDEFGHIJ" * 1000
        raw_part2 = b"KLMNOPQRST" * 1000
        raw_part3 = b"UVWXYZ0123" * 1000
        full_data = raw_part1 + raw_part2 + raw_part3
        
        chunks = [raw_part1, raw_part2, raw_part3]
        total_chunks = len(chunks)
        
        # 1. First chunk (0/3)
        res0 = self.client.post(
            "/api/guide/upload-chunk",
            data={
                "upload_id": self.upload_id,
                "chunk_index": 0,
                "total_chunks": total_chunks,
                "filename": self.filename
            },
            files={"chunk": ("blob", io.BytesIO(chunks[0]), "application/octet-stream")}
        )
        self.assertEqual(res0.status_code, 200)
        data0 = res0.json()
        self.assertEqual(data0["status"], "chunk_saved")
        self.assertEqual(data0["received_chunks"], 1)

        # 2. Second chunk (1/3)
        res1 = self.client.post(
            "/api/guide/upload-chunk",
            data={
                "upload_id": self.upload_id,
                "chunk_index": 1,
                "total_chunks": total_chunks,
                "filename": self.filename
            },
            files={"chunk": ("blob", io.BytesIO(chunks[1]), "application/octet-stream")}
        )
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()
        self.assertEqual(data1["status"], "chunk_saved")
        self.assertEqual(data1["received_chunks"], 2)

        # 3. Third chunk (2/3) -> Triggers assembly
        res2 = self.client.post(
            "/api/guide/upload-chunk",
            data={
                "upload_id": self.upload_id,
                "chunk_index": 2,
                "total_chunks": total_chunks,
                "filename": self.filename
            },
            files={"chunk": ("blob", io.BytesIO(chunks[2]), "application/octet-stream")}
        )
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(data2["status"], "completed")
        self.assertIn("file_path", data2)
        final_file_path = data2["file_path"]

        # 4. Verify assembled file
        self.assertTrue(os.path.exists(final_file_path))
        with open(final_file_path, "rb") as f:
            assembled_content = f.read()
        self.assertEqual(assembled_content, full_data)
        
        # 5. Verify chunk directory cleaned up
        self.assertFalse(os.path.exists(self.test_chunks_dir))

if __name__ == "__main__":
    unittest.main()
