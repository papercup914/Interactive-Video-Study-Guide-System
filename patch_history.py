import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from backend.services.evaluator import evaluate_learning_profile

def patch_json():
    with open("backend/data/saved_guides.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for item in data["history"]:
        if "notes" in item and len(item["notes"]) > 0:
            print(f"Evaluating {len(item['notes'])} notes for '{item['title']}'...")
            profile = {"total_questions": 0, "average_score": 0.0, "type_counts": {}, "recent_advice": ""}
            for note in item["notes"]:
                res = evaluate_learning_profile(note.get("question", ""), note.get("answer", ""))
                
                total = profile["total_questions"]
                current_avg = profile["average_score"]
                new_score = res.get("score", 5)
                new_type = res.get("type", "기타")
                
                profile["average_score"] = round(((current_avg * total) + new_score) / (total + 1), 1)
                profile["total_questions"] = total + 1
                
                type_counts = profile.get("type_counts", {})
                type_counts[new_type] = type_counts.get(new_type, 0) + 1
                profile["type_counts"] = type_counts
                profile["recent_advice"] = res.get("advice", "")
                
            item["learning_profile"] = profile
            
    with open("backend/data/saved_guides.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    patch_json()
    print("Patched successfully!")
