# Future Tasks & Deferred Scope

## Automated AI Persona QA System (v2.0 / Deferred)
- **Celery / Async Queue Integration (Option C)**: The current CLI is synchronous and processes one guide at a time. Once the core evaluation framework is stable, migrate it to an asynchronous queue (e.g., Celery or FastAPI Background Tasks) to allow bulk testing of 100+ guides simultaneously.

## Immediate Implementation Tasks (QA Harness)
- **Pre-flight & Connection Handling**: Implement `/api/health` ping before test execution. Catch `httpx.ConnectError`.
- **Asymmetric Timeouts**: Configure HTTP client with `timeout=httpx.Timeout(120.0, connect=5.0)`.
- **Backend Protection Header**: Inject `X-QA-Test-Mode: true` in all requests. Update backend to mock/rollback database saves when this header is present.
- **Observability Headers**: Inject `X-Correlation-ID` (UUID) into requests. Catch `httpx.HTTPStatusError` and log the UUID.
- **Concurrency & Backoff**: Add `asyncio.Semaphore(3)` and `@retry` with exponential backoff for 429 status codes.
