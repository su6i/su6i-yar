---
name: fastapi-best-practices
description: FastAPI Best Practices Technical Encyclopedia: Pydantic v2, Lifespan Events, Background Tasks, and Dependency Injection.
---

# Skill: FastAPI Best Practices (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the development of high-performance, type-safe APIs using FastAPI in the 2025 ecosystem. This document defines the standards for resource management, data validation, and asynchronous orchestration.

## 1. High-Performance Data Validation (Pydantic v2)
Leveraging the Rust-powered backend of Pydantic for maximum throughout and memory efficiency.

### 1.1 Core Architecture & Speedup
*   **Rust Mapping:** Pydantic v2 is rebuilt in Rust, providing up to 50x speedup in core validation and serialization logic.
*   **The `model_dump` Protocol:** Mandatory use of `model.model_dump(mode="json")` for consistent API serialization.
*   **Validation Modes:** Utilising `model_validate_json()` for direct, high-speed parsing of raw JSON strings bypassing Python's `json.loads`.

### 1.2 Advanced Schema Definition
```python
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Annotated

# 1.2.1 Reusable Type Annotations (2025 Standard)
class UserSchema(BaseModel):
    model_config = ConfigDict(
        extra='forbid', # Stop over-posting
        str_strip_whitespace=True
    )

    id: Annotated[int, Field(gt=0)]
    email: EmailStr
    username: Annotated[str, Field(min_length=3, max_length=50)]
```

---

## 2. Resource Lifecycle Management (Lifespan)
Standardized setup and teardown for global application resources (DB Pools, AI Models, Cache Connections).

### 2.1 Async Context Management
Replacing legacy `@app.on_event` with a unified lifespan function.
```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 2.1.1 Startup Logistics
    app.state.db_pool = await init_db_pool()
    app.state.llm_engine = await load_sota_model()
    yield # API is now ready
    # 2.1.2 Shutdown Logistics
    await app.state.db_pool.close()
```

---

## 3. Asynchronous Orchestration & Background Tasks
Balancing the Event Loop to prevent blocking and ensure sub-10ms response times.

### 3.1 Non-Blocking Execution Strategy
*   **I/O Bound (Async):** Use `async def` only with non-blocking drivers (e.g., `Motor` for MongoDB, `asyncpg` for PostgreSQL).
*   **CPU Bound (Sync):** Use standard `def`. FastAPI automatically executes these in an external thread pool to keep the event loop responsive.
*   **Background Tasks:** Offloading non-critical logic (e.g., sending emails, generating thumbnails) to `BackgroundTasks` to minimize user-perceived latency.

---

## 4. Scalable Dependency Injection (DI)
Decoupling internal logic from infrastructure using FastAPI's `Depends` system.

### 4.1 Injection Protocols
*   **Stateful Dependencies:** Accessing `app.state` via dependencies to ensure consistent resource sharing.
*   **Security Injection:** Multi-level dependency chains for OAuth2, JWT verification, and RBAC (Role-Based Access Control).
```python
async def get_db_session(request: Request):
    async with request.app.state.db_pool.acquire() as session:
        yield session

@app.get("/items")
async def read_items(db: Annotated[Session, Depends(get_db_session)]):
    return await db.fetch_all("SELECT * FROM items")
```

---

## 5. Security & Deployment Hardening
*   **Trusted Host Middleware:** Preventing HTTP Host Header attacks.
*   **CORS Configuration:** Explicitly defining allowed origins, headers, and methods (no wildcards in production).
*   **Granian (Rust Server):** Recommend deploying with **Granian** for superior performance on Linux over Uvicorn/Gunicorn.

---

## 6. Technical Appendix: Performance Benchmarking
*   **Latency Target:** P99 framework overhead < 2ms.
*   **Throughput:** Single-worker target > 5,000 requests/sec for simple GET operations on x86_64 hardware.
*   **Memory Footprint:** Application baseline (no cache) must remain < 150MB.

---

## 7. Troubleshooting & Verification
*   **Middleware Stack:** Verifying that logging and exception handling middleware don't introduce blocking calls.
*   **Auto-Docs:** Protocols for disabling `/docs` and `/redoc` in production via environment variables.

---
[Back to README](../../README.md)
