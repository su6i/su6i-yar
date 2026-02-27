#!/bin/bash

echo "🤖 Su6i Yar Installer"
echo "======================"

# 0. Fix Locale (Prevent Perl Warnings)
export LC_ALL=C.UTF-8
export LC_CTYPE=C.UTF-8
export LANG=C.UTF-8

# 1. Environment Setup (UV Optimized)
if command -v uv &> /dev/null; then
    echo "⚡ Using 'uv' for fast & space-efficient installation..."
    if [[ ! -d ".venv" ]]; then
        uv venv .venv
    fi
    source .venv/bin/activate
    uv pip install -r requirements.txt
else
    echo "⚠️ 'uv' not found. Fallback to standard python venv (Slower/More Disk Usage)."
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -r requirements.txt
fi

echo "✅ Python Dependencies Installed."

# 2.1 System Dependencies Check (espeak-ng) - REMOVED (Not needed for Model 1/3)


# 3. Sherpa-ONNX Models - REMOVED


# 3. Configuration
echo ""
echo "🔧 Configuration (.env)"
echo "-----------------------"

ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    touch "$ENV_FILE"
fi

# Function to check and prompt for a specific key
check_and_prompt() {
    local key=$1
    local prompt_text=$2
    
    # Check if key exists and is not empty in .env
    if grep -q "^${key}=" "$ENV_FILE"; then
        echo "✅ Found $key"
    else
        echo "⚠️  Missing $key"
        read -p "$prompt_text: " user_value
        
        # Determine strict formatting for SETTINGS json
        if [ "$key" == "SETTINGS" ]; then
             echo "${key}=${user_value}" >> "$ENV_FILE"
        else
             echo "${key}=${user_value}" >> "$ENV_FILE"
        fi
        echo "   Saved $key to $ENV_FILE"
    fi
}

check_and_prompt "TELEGRAM_BOT_TOKEN" "1. Enter TELEGRAM_BOT_TOKEN"
check_and_prompt "GEMINI_API_KEY" "2. Enter GEMINI_API_KEY"

# Special handling for SETTINGS to preserve JSON structure if missing
if grep -q "^SETTINGS=" "$ENV_FILE"; then
    echo "✅ Found SETTINGS"
else
    echo "⚠️  Missing SETTINGS"
    read -p "3. Enter Your Numeric Admin ID (e.g. 12345678): " admin_id
    # Default to 0 if empty
    safe_admin_id=${admin_id:-0}
    echo "SETTINGS={\"admin_id\": $safe_admin_id, \"public_mode\": false}" >> "$ENV_FILE"
    echo "   Saved SETTINGS to $ENV_FILE"
fi

echo ""
echo "✅ Configuration Check Complete."
echo "------------------------------"

# 4. Auto-Restart Service (Server Mode)
if command -v systemctl >/dev/null 2>&1; then
    SERVICE_NAME="su6i-yar"
    if systemctl list-units --full -all | grep -Fq "$SERVICE_NAME.service"; then
        echo "🔄 Detected Systemd Service: $SERVICE_NAME"
        echo "   Restarting service to apply changes..."
        sudo systemctl restart $SERVICE_NAME
        echo "✅ Service Restarted!"
    fi
fi

# 5. Verification
echo ""
echo "🧪 Running Verification Tests..."
chmod +x run_tests.sh
if ./run_tests.sh; then
    echo ""
    echo "🎉 Setup & Verification Complete! System is ready."
    echo "   Run: './run_dev.sh' or 'python3 su6i_yar.py'"
else
    echo ""
    echo "❌ Setup Finished, but Verification FAILED."
    echo "   Please check the logs above before running the bot."
    exit 1
fi
