#!/bin/bash
# 🚀 Smart Entry Point for Su6i Yar

# ── Single-instance lock (pgrep-based — survives exec) ───────
if pgrep -f "python.*src\.main" > /dev/null 2>&1; then
    EXISTING=$(pgrep -f "python.*src\.main" | tr '\n' ' ')
    echo "⚠️  Already running (PID $EXISTING). Run: pkill -f src.main"
    exit 1
fi
# ─────────────────────────────────────────────────────────────

# Check/Create Env File
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating default..."
    touch .env
    echo "Please add your keys to .env file."
fi

# 1. Environment & Dependencies (Self-Healing)
echo "🔍 Checking environment..."

if command -v uv &> /dev/null; then
    if [ ! -d ".venv" ]; then
        echo "⚡ Creating optimized environment (uv)..."
        uv venv .venv
    fi
    source .venv/bin/activate
    echo "📥 Syncing dependencies..."
    # --frozen: never modify uv.lock, install exactly what's locked
    uv sync --frozen > /dev/null 2>&1 || uv pip install -r requirements.txt > /dev/null 2>&1
    # Always use latest yt-dlp (YouTube breaks with old versions)
    uv pip install --upgrade yt-dlp > /dev/null 2>&1
    
    # Ensure Playwright browsers + system deps are installed
    if [ ! -f ".venv/.playwright_installed" ]; then
        echo "🌐 Installing browser binaries (Playwright)..."
        playwright install chromium
        echo "📦 Installing Playwright system dependencies..."
        sudo playwright install-deps chromium 2>/dev/null || \
            sudo apt-get install -y libnspr4 libnss3 2>/dev/null || true
        touch .venv/.playwright_installed
    fi
else
    # Fallback to standard pip
    if [ ! -d "venv" ]; then
        echo "📦 Creating standard venv..."
        python3 -m venv venv
    fi
    source venv/bin/activate
    
    # Check if we need to install deps (simple marker check)
    if [ ! -f "venv/.installed" ]; then
        echo "📥 Installing dependencies (pip)..."
        pip install -r requirements.txt
        echo "🌐 Installing browser binaries (Playwright)..."
        playwright install chromium
        touch venv/.installed
    fi
fi

# 2. YouTube Cookies check
if [ ! -f "cookies.txt" ]; then
    echo ""
    echo "⚠️  cookies.txt not found — YouTube may block downloads."
    echo "   روی مک خودت اجرا کن:"
    echo "   yt-dlp --cookies-from-browser chrome --cookies /tmp/yt_cookies.txt 'https://youtube.com'"
    echo "   scp /tmp/yt_cookies.txt su6i@89.167.55.129:~/su6i-yar/cookies.txt"
    echo ""
fi

# 3. Check Suno Cookie (Headless friendly)
if [ ! -f .storage/suno_cookie.json ]; then
     # Only launch if we have a display (not SSH) and not strictly headless
     if [[ -n "$DISPLAY" ]] || [[ "$OSTYPE" == "darwin"* ]]; then
         echo "🍪 No Suno Cookie found. Attempting interactive login..."
         # Use python -m to run setup
         python -m src.setup_suno
     fi
fi

# 3. Execution Router
if [[ "$1" == "--dev" ]]; then
    ./scripts/run_dev.sh
    exit 0
elif [[ "$1" == "--test" ]]; then
    ./scripts/run_tests.sh
    exit 0
fi

# 4. Production Run
echo "🚀 Launching Su6i Yar..."
exec python -m src.main "$@"
