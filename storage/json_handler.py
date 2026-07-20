import json
import os
from typing import Dict, Any

DATA_DIR = "data"
SAVE_FILE = os.path.join(DATA_DIR, "saved_guides.json")

def _ensure_dir_exists():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_data() -> Dict[str, Any]:
    """
    저장된 가이드 데이터를 불러옵니다.
    """
    _ensure_dir_exists()
    if not os.path.exists(SAVE_FILE):
        return {}
    
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}
    except Exception as e:
        print(f"Error loading data: {e}")
        return {}

def save_data(data: Dict[str, Any]) -> bool:
    """
    가이드 데이터를 JSON 파일로 저장합니다.
    """
    _ensure_dir_exists()
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        return False
