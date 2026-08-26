import httpx
import os
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

QA_API_BASE_URL = os.getenv("QA_API_BASE_URL", "http://localhost:8000")

semaphore = asyncio.Semaphore(3)

class RateLimitError(Exception):
    pass

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(RateLimitError)
)
async def fetch_with_backoff(client: httpx.AsyncClient, method: str, url: str, **kwargs):
    async with semaphore:
        response = await client.request(method, url, **kwargs)
        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        response.raise_for_status()
        return response

class QAHttpClient:
    def __init__(self):
        # Asymmetric timeout: Connect 5s, Read 120s
        timeout = httpx.Timeout(120.0, connect=5.0)
        self.client = httpx.AsyncClient(base_url=QA_API_BASE_URL, timeout=timeout)
    
    async def ping_health(self):
        try:
            # Check server status
            response = await self.client.get("/health")
            response.raise_for_status()
            return True
        except httpx.ConnectError:
            return False
        except Exception as e:
            print(f"Health check failed: {e}")
            return False

    async def get_guide(self, job_id: str):
        response = await self.client.get(f"/api/guide/result/{job_id}")
        response.raise_for_status()
        return response.json()

    async def chat(self, payload: dict, correlation_id: str):
        headers = {
            "X-QA-Test-Mode": "true",
            "X-Correlation-ID": correlation_id
        }
        return await fetch_with_backoff(self.client, "POST", "/api/discussion/chat", json=payload, headers=headers)
    
    async def close(self):
        await self.client.aclose()
