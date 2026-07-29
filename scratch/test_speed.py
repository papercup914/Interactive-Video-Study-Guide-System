import sys
import os
import asyncio
import time
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")
sys.path.append(os.path.abspath('.'))

from backend.routers.guide import GuideRequest, _generate_guide_task
from backend.services.job_manager import get_job, create_job

async def test_speed(url, provider):
    job_id = f"test_{provider.replace('/', '_')}_{int(time.time())}"
    print(f"\n=================================")
    print(f"--- Testing {provider} ---")
    print(f"=================================\n")
    
    request = GuideRequest(
        url=url,
        provider=provider,
        length_preset="Auto",
        analogy_preset="Auto"
    )
    
    create_job(job_id)
    
    start = time.time()
    await _generate_guide_task(job_id, request)
    end = time.time()
    
    job = get_job(job_id)
    duration = end - start
    
    if job and job.get("status") == "completed":
        print(f"\n>>> [{provider}] Success!")
        print(f">>> Time taken: {duration:.2f} seconds")
        if job.get("document"):
            print(f">>> Chapters generated: {len(job['document'])}")
    else:
        print(f"\n>>> [{provider}] Failed or incomplete.")
        print(f">>> Job info: {job}")
        
    return duration

async def main():
    url = "https://youtu.be/uhOxZFUEs6o"
    providers = [
        "cerebras/gpt-oss-120b",
        "nvidia/nemotron-3-ultra-550b-a55b"
    ]
    
    results = {}
    for p in providers:
        duration = await test_speed(url, p)
        results[p] = duration
        
    print("\n\n=================================")
    print("--- Speed Test Results ---")
    for p, d in results.items():
        print(f"{p}: {d:.2f} seconds")
    print("=================================\n")

if __name__ == "__main__":
    asyncio.run(main())
