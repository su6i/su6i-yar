#!/bin/bash

# Directory for models
MODEL_DIR="models"
mkdir -p "$MODEL_DIR"

echo "🚀 Checking for Sherpa-ONNX Persian Models..."

# URLs (Hugging Face)
MODEL_URL="https://huggingface.co/MahtaFetrat/Mana-Persian-Piper/resolve/main/fa_IR-mana-medium.onnx"
CONFIG_URL="https://huggingface.co/MahtaFetrat/Mana-Persian-Piper/resolve/main/fa_IR-mana-medium.onnx.json"

# Filenames
MODEL_FILE="$MODEL_DIR/fa_IR-mana-medium.onnx"
CONFIG_FILE="$MODEL_DIR/fa_IR-mana-medium.onnx.json"
FIXED_MODEL_FILE="$MODEL_DIR/fa_IR-mana-medium-fixed.onnx"

# 1. Download Config
if [ ! -f "$CONFIG_FILE" ]; then
    echo "📥 Downloading Config JSON..."
    curl -L "$CONFIG_URL" -o "$CONFIG_FILE"
else
    echo "✅ Config JSON found."
fi

# 2. Download Model
if [ ! -f "$MODEL_FILE" ]; then
    echo "📥 Downloading ONNX Model (60MB)..."
    curl -L "$MODEL_URL" -o "$MODEL_FILE"
else
    echo "✅ ONNX Model found."
fi

# 3. Apply Metadata Fix (Required for Sherpa-ONNX)
if [ ! -f "$FIXED_MODEL_FILE" ]; then
    echo "🛠️ Applying Metadata Fix (Adding phoneme_id_map and config)..."
    
    # Create temporary python script
    cat <<EOF > fix_metadata.py
import onnx
import json
import os

model_path = "$MODEL_FILE"
config_path = "$CONFIG_FILE"
output_path = "$FIXED_MODEL_FILE"

print(f"Reading config from {config_path}...")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

print(f"Loading model from {model_path}...")
model = onnx.load(model_path)

# Meta 1: phoneme_id_map (tokens)
phoneme_id_map = config.get("phoneme_id_map", {})
tokens_str = " ".join([f"{k} {v[0]}" for k, v in phoneme_id_map.items() if v])

# Meta 2: config (JSON string)
config_str = json.dumps(config)

meta_map = {
    "tokens": tokens_str,
    "config": config_str,
    "language": "fa-IR",
    "voice": "mana",
    "has_espeak": "1",
    "sample_rate": str(config.get("audio", {}).get("sample_rate", 22050)),
    "num_channels": "1",
    "model_type": "vits"
}

# Add/Update Metadata
for key, value in meta_map.items():
    meta = model.metadata_props.add()
    meta.key = key
    meta.value = value

print(f"Saving fixed model to {output_path}...")
onnx.save(model, output_path)
print("✅ Metadata fixed!")
EOF
    
    # Run the script
    python3 fix_metadata.py
    rm fix_metadata.py
else
    echo "✅ Fixed Model already exists."
fi

# 4. Generate tokens.txt
TOKENS_FILE="$MODEL_DIR/tokens.txt"
if [ ! -f "$TOKENS_FILE" ]; then
    echo "📝 Generating tokens.txt..."
    cat <<EOF > generate_tokens.py
import json
with open("$CONFIG_FILE", "r", encoding="utf-8") as f:
    data = json.load(f)
id_map = data.get("phoneme_id_map", {})
with open("$TOKENS_FILE", "w", encoding="utf-8") as f:
    for symbol, ids in id_map.items():
        if ids:
            f.write(f"{symbol} {ids[0]}\n")
EOF
    python3 generate_tokens.py
    rm generate_tokens.py
    echo "✅ tokens.txt created."
fi

echo "🎉 All Done! Models are ready."
