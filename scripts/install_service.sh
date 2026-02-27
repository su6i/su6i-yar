#!/bin/bash
# Install su6i-yar as a systemd service
# Run as: bash scripts/install_service.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_SRC="$SCRIPT_DIR/su6i-yar.service"
SERVICE_DST="/etc/systemd/system/su6i-yar.service"

echo "📦 Installing su6i-yar systemd service..."

# Kill any existing nohup/manual instance
if [ -f "$HOME/.su6i-yar.pid" ]; then
    OLD_PID=$(cat "$HOME/.su6i-yar.pid")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "🛑 Stopping existing process (PID $OLD_PID)..."
        kill "$OLD_PID" && sleep 2
    fi
    rm -f "$HOME/.su6i-yar.pid"
fi
pkill -f "python -m src.main" 2>/dev/null || true

# Copy service file
sudo cp "$SERVICE_SRC" "$SERVICE_DST"
sudo chmod 644 "$SERVICE_DST"

# Reload and enable
sudo systemctl daemon-reload
sudo systemctl enable su6i-yar
sudo systemctl restart su6i-yar

echo ""
echo "✅ Service installed and started!"
echo "   Status :  sudo systemctl status su6i-yar"
echo "   Logs   :  sudo journalctl -fu su6i-yar"
echo "   Or     :  tail -f ~/bot.log"
