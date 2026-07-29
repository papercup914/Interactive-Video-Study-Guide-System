import json
import sys

def main():
    try:
        with open('backend/data/saved_guides.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Determine if data is a list or dict
        if isinstance(data, list):
            latest = data[-1]
        elif isinstance(data, dict):
            latest = list(data.values())[-1]
        else:
            print("Unknown JSON format")
            return
            
        with open('scratch/latest_guide.txt', 'w', encoding='utf-8') as f:
            f.write(json.dumps(latest, ensure_ascii=False, indent=2))
            
        print("Successfully extracted to scratch/latest_guide.txt")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
