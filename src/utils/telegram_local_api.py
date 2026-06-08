import asyncio
import os
import shutil
import socket
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Optional

from telegram import Bot

from src.core.logger import logger


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _can_use_local_for_size(file_size_bytes: int) -> bool:
    if not _env_bool("TELEGRAM_LOCAL_BOTAPI_AUTOSTART", default=True):
        return False
    threshold_mb = float(os.getenv("TELEGRAM_LOCAL_BOTAPI_THRESHOLD_MB", "48"))
    return file_size_bytes >= int(threshold_mb * 1024 * 1024)


def _is_port_open(host: str, port: int, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


async def _wait_port(host: str, port: int, timeout_sec: float = 6.0) -> bool:
    step = 0.15
    loops = int(timeout_sec / step)
    for _ in range(max(1, loops)):
        if _is_port_open(host, port):
            return True
        await asyncio.sleep(step)
    return False


async def _start_local_botapi() -> tuple[Optional[asyncio.subprocess.Process], Optional[str], bool]:
    """
    Returns: (process, base_url, started_by_us)
    - If an instance is already running on target port, process is None and started_by_us is False.
    - If startup fails, returns (None, None, False).
    """
    host = os.getenv("TELEGRAM_LOCAL_BOTAPI_HOST", "127.0.0.1")
    port = int(os.getenv("TELEGRAM_LOCAL_BOTAPI_PORT", "8081"))
    base_url = os.getenv("TELEGRAM_LOCAL_BOTAPI_URL", f"http://{host}:{port}").rstrip("/")

    if _is_port_open(host, port):
        logger.info("📡 Local Bot API already running; reusing existing instance.")
        return None, base_url, False

    api_id = (os.getenv("TELEGRAM_LOCAL_BOTAPI_API_ID") or os.getenv("TG_API_ID") or "").strip()
    api_hash = (os.getenv("TELEGRAM_LOCAL_BOTAPI_API_HASH") or os.getenv("TG_API_HASH") or "").strip()
    if not api_id or not api_hash:
        logger.warning("⚠️ Local Bot API autostart skipped: API_ID/API_HASH missing.")
        return None, None, False

    mode = os.getenv("TELEGRAM_LOCAL_BOTAPI_MODE", "auto").strip().lower()
    binary = os.getenv("TELEGRAM_LOCAL_BOTAPI_BIN", "telegram-bot-api").strip()
    binary_path = shutil.which(binary) or (binary if Path(binary).exists() else None)

    data_dir = Path(os.getenv("TELEGRAM_LOCAL_BOTAPI_DATA_DIR", str(Path.home() / ".su6i-yar" / "botapi-local")))
    data_dir.mkdir(parents=True, exist_ok=True)

    cmd = None
    if mode in {"auto", "native"} and binary_path:
        cmd = [
            str(binary_path),
            "--local",
            "--http-port",
            str(port),
            "--api-id",
            api_id,
            "--api-hash",
            api_hash,
            "--dir",
            str(data_dir),
        ]

    if cmd is None and mode in {"auto", "docker"}:
        docker_bin = shutil.which("docker")
        if docker_bin:
            image = os.getenv("TELEGRAM_LOCAL_BOTAPI_DOCKER_IMAGE", "aiogram/telegram-bot-api:latest").strip()
            container_name = f"su6i-botapi-{port}-{uuid.uuid4().hex[:8]}"
            cmd = [
                docker_bin,
                "run",
                "--rm",
                "--name",
                container_name,
                "-p",
                f"{port}:{port}",
                "-v",
                f"{data_dir}:/var/lib/telegram-bot-api",
                image,
                "--local",
                "--http-port",
                str(port),
                "--api-id",
                api_id,
                "--api-hash",
                api_hash,
                "--dir",
                "/var/lib/telegram-bot-api",
            ]

    if cmd is None:
        logger.warning("⚠️ Local Bot API autostart skipped: no native binary and no docker runtime available.")
        return None, None, False

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except Exception as e:
        logger.warning(f"⚠️ Local Bot API failed to spawn: {e}")
        return None, None, False

    ok = await _wait_port(host, port, timeout_sec=8.0)
    if not ok:
        logger.warning("⚠️ Local Bot API autostart timed out; falling back to cloud bot API.")
        try:
            proc.terminate()
            await asyncio.wait_for(proc.wait(), timeout=2.0)
        except Exception:
            pass
        return None, None, False

    logger.info(f"✅ Local Bot API started on {base_url}")
    return proc, base_url, True


async def _stop_local_botapi(proc: Optional[asyncio.subprocess.Process]) -> None:
    if not proc:
        return
    try:
        proc.terminate()
        await asyncio.wait_for(proc.wait(), timeout=3.0)
        logger.info("🛑 Local Bot API stopped after upload.")
    except Exception:
        try:
            proc.kill()
            await proc.wait()
        except Exception:
            pass


@asynccontextmanager
async def maybe_local_upload_bot(primary_bot: Bot, file_size_bytes: int) -> AsyncIterator[Bot]:
    """
    Yield local Bot API Bot for large files when available, otherwise yield primary bot.
    Automatically starts/stops local server only when needed.
    """
    if not _can_use_local_for_size(file_size_bytes):
        yield primary_bot
        return

    proc, base_url, started_by_us = await _start_local_botapi()
    if not base_url:
        yield primary_bot
        return

    token = getattr(primary_bot, "token", None) or getattr(primary_bot, "_token", None)
    if not token:
        logger.warning("⚠️ Could not read bot token from runtime bot object; using cloud bot API.")
        if started_by_us:
            await _stop_local_botapi(proc)
        yield primary_bot
        return

    local_bot = Bot(
        token=token,
        base_url=f"{base_url}/bot",
        base_file_url=f"{base_url}/file/bot",
    )

    try:
        logger.info("📦 Using Local Bot API for large upload.")
        yield local_bot
    finally:
        try:
            await local_bot.shutdown()
        except Exception:
            pass
        if started_by_us:
            await _stop_local_botapi(proc)
