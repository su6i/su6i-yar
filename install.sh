#!/bin/bash

echo "🤖 Su6i Yar Installer"
echo "======================"

# 0. Fix Locale (Prevent Perl Warnings)
export LC_ALL=C.UTF-8
export LC_CTYPE=C.UTF-8
export LANG=C.UTF-8

# 1. Environment Setup
if [[ ! -d "venv" ]]; then
    echo "📦 Creating Virtual Environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# 2. Dependencies
echo "📥 Installing Dependencies..."
pip install -r requirements.txt
echo "✅ Python Dependencies Installed."

# 2.1 System Dependencies Check (espeak-ng)
if ! command -v espeak-ng &> /dev/null; then
    echo "⚠️  [WARNING] 'espeak-ng' is NOT installed!"
    echo "   Sherpa-ONNX (Model 2) requires it for Persian TTS."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]] && command -v apt-get &> /dev/null; then
        echo "🔄 Attempting to install 'espeak-ng' locally (requires sudo)..."
        if sudo apt-get install -y espeak-ng; then
            echo "✅ 'espeak-ng' installed successfully!"
        else
            echo "❌ Automatic installation failed."
            echo "   👉 Please run manually: sudo apt install espeak-ng"
        fi
    else
         echo "   👉 Please install 'espeak-ng' manually for your OS."
         echo "      (Linux: sudo apt install espeak-ng | Mac: brew install espeak-ng)"
    fi
    echo ""
fi

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
# Force regeneration to ensure 'n_speakers' and other metadata is up to date
if [ -f "$MODEL_FILE" ]; then
    echo "🛠️ Applying Metadata Fix..."
    
    # Try to remove old file, handle permissions if needed
    if [ -f "$FIXED_MODEL_FILE" ]; then
        rm -f "$FIXED_MODEL_FILE" || sudo rm -f "$FIXED_MODEL_FILE"
    fi
    
    if [ -f "$FIXED_MODEL_FILE" ]; then
         echo "❌ Error: Could not delete old fixed model (Permission Denied?)."
         echo "   Try running: sudo rm $FIXED_MODEL_FILE"
         exit 1
    fi
    
    cat <<PYEOF > fix_metadata.py
import onnx, json
import sys

try:
    model_path, config_path, output_path = "$MODEL_FILE", "$CONFIG_FILE", "$FIXED_MODEL_FILE"
    with open(config_path, "r", encoding="utf-8") as f: config = json.load(f)
    model = onnx.load(model_path)
    meta_map = {
        "tokens": " ".join([f"{k} {v[0]}" for k, v in config.get("phoneme_id_map", {}).items() if v]),
        "config": json.dumps(config),
        "language": "fa-IR", "voice": "mana", "has_espeak": "0",
        "sample_rate": str(config.get("audio", {}).get("sample_rate", 22050)),
        "num_channels": "1", "model_type": "vits",
        "n_speakers": "1",
        "comment": "Fixed by Su6i Yar Installer v2",
        "version": "1"
    }
    for k, v in meta_map.items():
        meta = model.metadata_props.add(); meta.key = k; meta.value = v
    onnx.save(model, output_path)
    print("   -> fix_metadata.py executed successfully")
except Exception as e:
    print(f"   -> Error in Python script: {e}")
    sys.exit(1)
PYEOF
    
    # Use venv python to ensure 'onnx' library is available
    if ./venv/bin/python fix_metadata.py; then
        echo "   -> Metadata patched."
    else
        echo "❌ Python script failed to fix metadata!"
        exit 1
    fi
    rm fix_metadata.py
    
    if [ ! -f "$FIXED_MODEL_FILE" ]; then
        echo "❌ Output file $FIXED_MODEL_FILE was NOT created!"
        exit 1
    fi
else
    echo "❌ Error: Original model file $MODEL_FILE not found!"
    exit 1
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
    ./venv/bin/python generate_tokens.py
    rm generate_tokens.py
fi

# Generate Lexicon (Persian IPA Mapping)
if [ ! -f "$MODEL_DIR/lexicon.txt" ]; then
    echo "📝 Generating Persian Lexicon (IPA)..."
    cat <<PYEOF > generate_lexicon.py
import json

# Persian Character to IPA Map (Standard VITS/Espeak approximation)
persian_phoneme_map = {
    "آ": "ʔɒː", "ا": "ʔ", "ب": "b", "پ": "p", "ت": "t",
    "ث": "s", "ج": "dʒ", "چ": "tʃ", "ح": "h", "خ": "x",
    "د": "d", "ذ": "z", "ر": "ɾ", "ز": "z", "ژ": "ʒ",
    "س": "s", "ش": "ʃ", "ص": "s", "ض": "z", "ط": "t",
    "ظ": "z", "ع": "ʔ", "غ": "ɣ", "ف": "f", "ق": "ɢ",
    "ک": "k", "گ": "ɡ", "ل": "l", "م": "m", "ن": "n",
    "و": "v", "ه": "h", "ی": "j", " ": " "
}

with open("$MODEL_DIR/lexicon.txt", "w", encoding="utf-8") as f:
    for char, phoneme in persian_phoneme_map.items():
        # IMPORTANT: Phonemes must be space-separated for Sherpa (e.g. "ʔ ɒ ː")
        spaced_phoneme = " ".join(list(phoneme))
        f.write(f"{char} {spaced_phoneme}\n")
PYEOF
    ./venv/bin/python generate_lexicon.py
    rm generate_lexicon.py
    echo "   -> Created models/lexicon.txt"
fi
echo "✅ Models Ready."

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
