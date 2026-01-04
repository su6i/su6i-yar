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

# 3. Download & Setup Helper Models (Sherpa-ONNX)
echo ""
echo "🧩 Checking for Sherpa-ONNX Persian Models..."

MODEL_DIR="models"
mkdir -p "$MODEL_DIR"

# URLs
MODEL_URL="https://huggingface.co/MahtaFetrat/Mana-Persian-Piper/resolve/main/fa_IR-mana-medium.onnx"
CONFIG_URL="https://huggingface.co/MahtaFetrat/Mana-Persian-Piper/resolve/main/fa_IR-mana-medium.onnx.json"

# Files
MODEL_FILE="$MODEL_DIR/fa_IR-mana-medium.onnx"
CONFIG_FILE="$MODEL_DIR/fa_IR-mana-medium.onnx.json"
FIXED_MODEL_FILE="$MODEL_DIR/fa_IR-mana-medium-fixed.onnx"
TOKENS_FILE="$MODEL_DIR/tokens.txt"

# Download Config
if [ ! -f "$CONFIG_FILE" ]; then
    echo "📥 Downloading Config JSON..."
    curl -L "$CONFIG_URL" -o "$CONFIG_FILE"
fi

# Download Model
if [ ! -f "$MODEL_FILE" ]; then
    echo "📥 Downloading ONNX Model (60MB)..."
    curl -L "$MODEL_URL" -o "$MODEL_FILE"
fi

# Apply Metadata Fix
if [ ! -f "$FIXED_MODEL_FILE" ] && [ -f "$MODEL_FILE" ]; then
    echo "🛠️ Applying Metadata Fix..."
    
    cat <<PYEOF > fix_metadata.py
import onnx, json
model_path, config_path, output_path = "$MODEL_FILE", "$CONFIG_FILE", "$FIXED_MODEL_FILE"
with open(config_path, "r", encoding="utf-8") as f: config = json.load(f)
model = onnx.load(model_path)
meta_map = {
    "tokens": " ".join([f"{k} {v[0]}" for k, v in config.get("phoneme_id_map", {}).items() if v]),
    "config": json.dumps(config),
    "language": "fa-IR", "voice": "mana", "has_espeak": "1",
    "sample_rate": str(config.get("audio", {}).get("sample_rate", 22050)),
    "num_channels": "1", "model_type": "vits"
}
for k, v in meta_map.items():
    meta = model.metadata_props.add(); meta.key = k; meta.value = v
onnx.save(model, output_path)
PYEOF
    
    python3 fix_metadata.py
    rm fix_metadata.py
fi

# Generate Tokens
if [ ! -f "$TOKENS_FILE" ] && [ -f "$CONFIG_FILE" ]; then
    echo "📝 Generating tokens.txt..."
    cat <<PYEOF > generate_tokens.py
import json
with open("$CONFIG_FILE", "r") as f: data = json.load(f)
with open("$TOKENS_FILE", "w") as f:
    for s, ids in data.get("phoneme_id_map", {}).items():
        if ids: f.write(f"{s} {ids[0]}\n")
PYEOF
    python3 generate_tokens.py
    rm generate_tokens.py
fi
echo "✅ Models Ready."

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
