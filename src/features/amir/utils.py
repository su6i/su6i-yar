"""
Amir CLI bridge for su6i-yar.
Wraps shell commands and handles temp-file lifecycle.
"""
import os
import re
import uuid
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from src.core.config import TEMP_DIR
from src.core.logger import logger

# ── Path resolution ──────────────────────────────────────────────────────────
# Priority: AMIR_PATH env var → sibling repo → fallback to PATH
_AMIR_PATH = os.getenv(
    "AMIR_PATH",
    str(Path(__file__).resolve().parents[4] / "amir-cli" / "amir"),
)


def amir_path() -> str:
    return _AMIR_PATH


def _tmp(suffix: str) -> str:
    """Return a unique temp file path inside TEMP_DIR."""
    return os.path.join(TEMP_DIR, f"amir_{uuid.uuid4().hex}{suffix}")


# ── Intent detection ─────────────────────────────────────────────────────────

_PDF_KEYWORDS = re.compile(
    r"pdf|پی.?دی.?اف|پی‌دی‌اف|تبدیل به پی|a4|کارت.?ملی|شناسنامه|سند|مدرک|print", re.I
)
_RESIZE_KEYWORDS = re.compile(
    r"resize|ریسایز|تغییر.?اندازه|کوچک|compress|فشرده|بزرگ", re.I
)
_QR_KEYWORDS = re.compile(r"qr|کیو.?آر|کد.?کیو", re.I)
_WATERMARK_KEYWORDS = re.compile(r"watermark|واترمارک", re.I)


def detect_photo_intent(caption: str) -> Optional[str]:
    """
    Returns one of: 'pdf' | 'resize' | 'watermark' | None
    based on the Telegram message caption.
    """
    if not caption:
        return None
    c = caption.strip()
    if _PDF_KEYWORDS.search(c):
        return "pdf"
    if _WATERMARK_KEYWORDS.search(c):
        return "watermark"
    if _RESIZE_KEYWORDS.search(c):
        return "resize"
    return None


# ── CLI runners ──────────────────────────────────────────────────────────────

def _run(args: list[str], timeout: int = 60) -> tuple[int, str]:
    """Run amir with given args; return (exit_code, combined_output)."""
    cmd = ["bash", amir_path(), "--no-venv"] + args
    logger.info(f"[amir] Running: {' '.join(cmd)}")
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=TEMP_DIR,
        )
        output = (proc.stdout + proc.stderr).strip()
        return proc.returncode, output
    except subprocess.TimeoutExpired:
        return 1, "⏱ Timeout: عملیات بیش از حد طول کشید."
    except FileNotFoundError:
        return 1, f"❌ amir CLI پیدا نشد: {amir_path()}"
    except Exception as e:
        return 1, f"❌ خطا: {e}"


def run_pdf(input_path: str) -> tuple[int, str, Optional[str]]:
    """
    Convert an image file to PDF.
    Returns (exit_code, message, output_pdf_path_or_None).
    """
    output = _tmp(".pdf")
    code, out = _run(["pdf", input_path, "-o", output])
    if code == 0 and os.path.isfile(output):
        return 0, "✅ PDF ساخته شد.", output
    # Fallback: try via ImageMagick directly if amir pdf failed
    try:
        import shutil
        if shutil.which("magick") or shutil.which("convert"):
            convert_cmd = "magick" if shutil.which("magick") else "convert"
            r = subprocess.run(
                [convert_cmd, input_path, output],
                capture_output=True, timeout=30
            )
            if r.returncode == 0 and os.path.isfile(output):
                return 0, "✅ PDF ساخته شد.", output
    except Exception:
        pass
    return 1, f"❌ تبدیل به PDF ناموفق بود.\n{out}", None


def run_qr(text: str) -> tuple[int, str, Optional[str]]:
    """
    Generate a QR code PNG for text.
    Returns (exit_code, message, output_png_path_or_None).
    """
    output = _tmp(".png")
    code, out = _run(["qr", text, output])
    if code == 0 and os.path.isfile(output):
        return 0, "✅ QR code آماده است.", output
    # Fallback: qrencode directly
    try:
        import shutil
        if shutil.which("qrencode"):
            r = subprocess.run(
                ["qrencode", "-o", output, "-s", "10", text],
                capture_output=True, timeout=15
            )
            if r.returncode == 0 and os.path.isfile(output):
                return 0, "✅ QR code آماده است.", output
    except Exception:
        pass
    return 1, f"❌ ساخت QR ناموفق بود.\n{out}", None


def run_pass(length: int = 16) -> tuple[int, str]:
    """
    Generate a password of given length.
    Returns (exit_code, password_or_error).
    """
    # amir pass writes to clipboard + echoes; parse the echo
    code, out = _run(["pass", str(length)])
    # Output: "🔑 Password (16 chars) copied: XYZ123..."
    match = re.search(r"copied:\s*(.+)$", out, re.M)
    if match:
        return 0, match.group(1).strip()
    # Fallback: generate locally
    import secrets, string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+"
    pwd = "".join(secrets.choice(alphabet) for _ in range(length))
    return 0, pwd


def run_weather(city: str = "Tehran") -> tuple[int, str]:
    """
    Get weather text for a city via wttr.in.
    Returns (exit_code, weather_text).
    """
    code, out = _run(["weather", city])
    if out:
        return code, out
    # Direct fallback
    try:
        import urllib.request
        with urllib.request.urlopen(
            f"https://wttr.in/{city}?0m2t", timeout=10
        ) as r:
            return 0, r.read().decode("utf-8")
    except Exception as e:
        return 1, f"❌ دریافت آب‌وهوا ناموفق بود: {e}"


def run_resize(input_path: str, size: str = "1080") -> tuple[int, str, Optional[str]]:
    """
    Resize image using amir img resize.
    size can be '1080', '1240x1753' (A4), etc.
    Returns (exit_code, message, output_path_or_None).
    """
    output = _tmp(Path(input_path).suffix or ".jpg")
    code, out = _run(["img", "resize", input_path, size, "-o", output])
    if code == 0 and os.path.isfile(output):
        return 0, f"✅ تصویر ریسایز شد ({size}).", output
    return 1, f"❌ ریسایز ناموفق.\n{out}", None


def run_stack(image_paths: list[str], a4: bool = True) -> tuple[int, str, Optional[str]]:
    """
    Stack multiple images vertically (side-by-side on one A4 page).
    Uses 'amir img stack' then 'amir pdf' to produce a final PDF.
    Returns (exit_code, message, output_pdf_or_None).
    """
    if len(image_paths) < 2:
        return 1, "❌ حداقل ۲ تصویر نیاز است.", None

    stacked = _tmp(".jpg")
    stack_args = ["img", "stack"] + image_paths + ["-o", stacked]
    if a4:
        stack_args += ["-p", "a4"]
    code, out = _run(stack_args, timeout=60)

    if code != 0 or not os.path.isfile(stacked):
        # Fallback: use ImageMagick append directly
        try:
            import shutil
            magick = shutil.which("magick") or shutil.which("convert")
            if magick:
                r = subprocess.run(
                    [magick] + image_paths + ["-append", stacked],  # vertical stack
                    capture_output=True, timeout=30
                )
                if r.returncode != 0 or not os.path.isfile(stacked):
                    return 1, f"❌ ترکیب تصاویر ناموفق.\n{out}", None
            else:
                return 1, f"❌ ترکیب تصاویر ناموفق.\n{out}", None
        except Exception as e:
            return 1, f"❌ خطا در ترکیب: {e}", None

    # Convert stacked image → PDF
    output_pdf = _tmp(".pdf")
    code2, out2 = _run(["pdf", stacked, "-o", output_pdf], timeout=60)
    cleanup(stacked)
    if code2 == 0 and os.path.isfile(output_pdf):
        return 0, "✅ PDF آماده است.", output_pdf

    # Fallback: magick to PDF
    try:
        import shutil
        magick = shutil.which("magick") or shutil.which("convert")
        if magick:
            r = subprocess.run(
                [magick, stacked, output_pdf],
                capture_output=True, timeout=30
            )
            if r.returncode == 0 and os.path.isfile(output_pdf):
                return 0, "✅ PDF آماده است.", output_pdf
    except Exception:
        pass
    return 1, f"❌ ساخت PDF ناموفق.\n{out2}", None


def cleanup(*paths: str) -> None:
    """Remove temp files safely."""
    for p in paths:
        try:
            if p and os.path.isfile(p):
                os.unlink(p)
        except Exception:
            pass
