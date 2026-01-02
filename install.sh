#!/bin/bash

echo "🤖 Su6i Yar Installer"
echo "======================"

# 1. Environment Setup
if [[ ! -d "venv" ]]; then
    echo "📦 Creating Virtual Environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# 2. Dependencies
echo "📥 Installing Dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies Installed."

# 3. Configuration
echo ""
echo "🔧 Configuration (.env)"
echo "-----------------------"
echo "We need to set up your API keys."
echo ""

read -p "1. Enter TELEGRAM_BOT_TOKEN: " token
read -p "2. Enter GEMINI_API_KEY: " gemini
read -p "3. Enter Your Numeric Admin ID (e.g. 12345678): " admin_id

cat <<EOF > .env
TELEGRAM_BOT_TOKEN=$token
GEMINI_API_KEY=$gemini
SETTINGS={"admin_id": ${admin_id:-0}, "public_mode": false}
EOF

echo ""
echo "✅ Configuration saved to .env"
echo "------------------------------"
echo "🎉 Setup Complete! Run: './run_dev.sh' or 'python3 su6i_yar.py'"
