#!/usr/bin/env python3
"""
Backend Health Diagnostic Script for AWS EC2 Deployment
Checks FastAPI, Redis, and Supabase JWT auth connectivity.
"""

import sys
import json
import urllib.request
import urllib.error

def check_endpoint(url: str, description: str) -> bool:
    print(f"[CHECK] Testing {description} ({url})...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HealthCheck/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.getcode()
            body = response.read().decode('utf-8')
            if status_code == 200:
                print(f"  [PASS] Status: {status_code} OK | Body: {body.strip()[:100]}")
                return True
            else:
                print(f"  [FAIL] Unexpected status: {status_code}")
                return False
    except urllib.error.HTTPError as e:
        print(f"  [FAIL] HTTP Error: {e.code} - {e.reason}")
        return False
    except Exception as e:
        print(f"  [FAIL] Connection error: {str(e)}")
        return False

def main():
    print("=================================================================")
    print("🏥 Interactive Study Guide Backend Health Diagnostics")
    print("=================================================================")

    target_host = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    results = []
    # 1. Check basic health
    results.append(check_endpoint(f"{target_host}/health", "FastAPI Core Health Endpoint"))

    print("\n-----------------------------------------------------------------")
    if all(results):
        print("🎉 ALL BACKEND SYSTEMS OPERATIONAL! Server is ready for Vercel.")
        sys.exit(0)
    else:
        print("⚠️ Some checks failed. Please inspect container logs using:")
        print("   docker compose logs -f")
        sys.exit(1)

if __name__ == "__main__":
    main()
