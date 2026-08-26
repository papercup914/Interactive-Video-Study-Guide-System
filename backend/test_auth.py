import os
import asyncio
import jwt
import time
from fastapi.security import HTTPAuthorizationCredentials
from backend.auth import get_current_user
from fastapi import HTTPException

async def run_tests():
    print("[RUN] Running Backend Auth Unit Tests...")
    test_secret = "super-secret-jwt-key-for-unit-testing-purposes-12345"
    os.environ["SUPABASE_JWT_SECRET"] = test_secret
    os.environ["APP_ENV"] = "production"
    os.environ["DISABLE_AUTH"] = "false"

    # Test 1: Valid JWT Token
    valid_payload = {
        "sub": "user-uuid-1234-5678",
        "email": "student@example.com",
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
        "aud": "authenticated"
    }
    valid_token = jwt.encode(valid_payload, test_secret, algorithm="HS256")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=valid_token)
    
    user = await get_current_user(creds)
    assert user["id"] == "user-uuid-1234-5678", f"Expected user-uuid-1234-5678, got {user['id']}"
    assert user["email"] == "student@example.com", f"Expected student@example.com, got {user['email']}"
    print("  [PASS] Test 1: Valid JWT verified successfully")

    # Test 2: Expired JWT Token
    expired_payload = {
        "sub": "user-uuid-1234-5678",
        "email": "student@example.com",
        "exp": int(time.time()) - 3600,
    }
    expired_token = jwt.encode(expired_payload, test_secret, algorithm="HS256")
    expired_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token)
    
    try:
        await get_current_user(expired_creds)
        assert False, "Expired token should raise HTTPException"
    except HTTPException as e:
        assert e.status_code == 401
        print("  [PASS] Test 2: Expired JWT correctly rejected with 401")

    # Test 3: Invalid Secret Signature
    wrong_token = jwt.encode(valid_payload, "wrong-secret-key", algorithm="HS256")
    wrong_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=wrong_token)
    
    try:
        await get_current_user(wrong_creds)
        assert False, "Invalid signature should raise HTTPException"
    except HTTPException as e:
        assert e.status_code == 401
        print("  [PASS] Test 3: Invalid signature correctly rejected with 401")

    # Test 4: Missing Credentials in Production
    try:
        await get_current_user(None)
        assert False, "Missing credentials in production should raise HTTPException"
    except HTTPException as e:
        assert e.status_code == 401
        print("  [PASS] Test 4: Missing credentials correctly rejected with 401")

    # Test 5: Dev mode / DISABLE_AUTH fallback
    os.environ["APP_ENV"] = "dev"
    os.environ["DISABLE_AUTH"] = "true"
    dev_user = await get_current_user(None)
    assert dev_user["is_dev"] is True
    print("  [PASS] Test 5: Dev mode fallback user successfully returned")

    print("\n[SUCCESS] ALL AUTH TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(run_tests())
