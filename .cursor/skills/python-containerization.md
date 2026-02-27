---
name: python-containerization
description: Python Containerization Technical Encyclopedia: Multi-Stage Docker, Distroless Images, 'uv' Integration, and Security Hardening.
---

# Skill: Python Containerization (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the efficient, secure, and reproducible containerization of Python applications in the 2025 ecosystem. This document defines the standards for Dockerfile optimization, multi-stage building, and production-grade image hardening.

---

## 1. Multi-Stage Docker Architecture
Minimalizing the final image size by separating the build environment from the runtime environment.

### 1.1 The "Builder" Pattern Standard
*   **Stage 1 (Build):** Installing heavy dependencies (compilers, git, dev-libraries) and generating bytecode or building C-extensions.
*   **Stage 2 (Runtime):** Copying only the necessary artifacts (e.g., `site-packages`) into a lean base image (e.g., `python:3.12-slim`).

### 1.2 Implementation Protocol (`uv` + Docker)
```dockerfile
# 1.2.1 Stage 1: Build
FROM ghcr.io/astral-sh/uv:latest AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev # Install only production deps

# 1.2.2 Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY src/ ./src/
USER 1000:1000 # 1.2.3 Mandatory Non-Root User Standard
CMD ["python", "-m", "project_name.main"]
```

---

## 2. Advanced Image Optimization & Security
Reducing the "Attack Surface" and improving pull/push performance via layer management.

### 2.1 Layer Squashing & Caching
*   **Protocol:** Ordering `COPY` commands from least-frequently changed to most-frequently changed (e.g., `pyproject.toml` before `src/`).
*   **Protocol:** Combining `RUN` commands where possible to minimize the number of underlying filesystem layers.

### 2.2 Image Hardening (Security Standards)
*   **Distroless Images:** Utilizing `gcr.io/distroless/python3` for maximum security (removes shell, package manager, and standard tools).
*   **Read-Only Filesystems:** Running containers with `--read-only` flag to prevent unauthorized writes at runtime.
*   **Secret Management:** Never using `ENV` for passwords; utilizing Docker Secrets or K8s Secret mounting.

---

## 3. High-Performance Container Orchestration (2025)
*   **Memory Management:** Setting `PYTHONMALLOC=malloc` in containers to reduce fragmentation in high-concurrency scenarios.
*   **Signal Handling:** Ensuring the application correctly handles `SIGTERM` for graceful shutdown in Kubernetes.
*   **Health Checks:** Implementing `/healthz` endpoints and configuring `HEALTHCHECK` instructions in the Dockerfile.

---

## 4. Technical Appendix: Comprehensive Docker CLI Reference
| Command | Primary Use Case | Standard |
| :--- | :--- | :--- |
| `docker build --no-cache` | Force a clean rebuild for debugging | Development |
| `docker image prune -a` | Clean up unused images and free disk space | Maintenance |
| `docker exec -it <id> /bin/bash`| Enter container for inspection | Troubleshooting |
| `docker stats` | Real-time CPU/RAM monitoring per container | Monitoring |

---

## 5. Industrial Case Study: Optimizing an ML Inference Image
**Objective:** Reducing a 5GB PyTorch image to < 1.5GB.
1.  **Stage Separation:** Compiling custom CUDA kernels in the builder stage.
2.  **Pruning:** Removing `.pyc`, `tests`, `docs`, and `examples` from `site-packages` before copying to the runtime stage.
3.  **Base Selection:** Moving from `python:3.12-full` to `python:3.12-slim`.
4.  **PIP Caching:** Utilizing `mount=type=cache` during the build to speed up repeated dependency installations.

---

## 6. Glossary of Containerization Terms
*   **Image:** A read-only template with instructions for creating a Docker container.
*   **Container:** A runnable instance of an image.
*   **Entrypoint:** The command that is always executed when the container starts.
*   **Layer:** A cached filesystem change resulting from a `RUN`, `COPY`, or `ADD` command in a Dockerfile.

---

## 7. Mathematical Foundations: Layer Hashing
*   **Content Hash:** How Docker determines if a layer can be reused based on the hash of the files being copied.
*   **Delta Compression:** The algorithm used by registries to transmit only the changes between image versions.

---

## 8. Troubleshooting & Performance Verification
*   **Zombie Processes:** Using `tini` or a similar init-system as an entrypoint to manage child processes correctly.
*   **Permission Denied:** Fixing common uid/gid mismatch issues between host and container.
*   **Large Image Size:** Utilizing `dive` to inspect layer-by-layer size contributions.

---

## 9. Appendix: Container Orchestration Integration
*   **Docker Compose:** Standard for local multi-container development.
*   **Container Registries:** Protocols for pushing/pulling from AWS ECR, GCP GCR, and GitHub GHCR.

---

## 10. Benchmarks & Performance Standards (2025)
*   **Image Size:** Target < 500MB for standard web apps; < 2GB for ML apps.
*   **Build Time:** Target < 2m for warm-cache builds.
*   **Layer Count:** Target < 15 layers for a production image.

---
[Back to README](../../README.md)
