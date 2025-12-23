# 🤖 Su6i Yar - Smart AI Assistant

A powerful, intelligent Telegram bot that downloads Instagram videos, verifies factual claims, and provides multimodal educational content using Google Gemini AI.

**Rewritten from scratch for speed, stability, and ease of use.**

![Version](https://img.shields.io/badge/Version-4.4.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9+-yellow.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Key Features

### 📥 Smart Downloader
*   Automatically detects Instagram links (Posts, Reels, TV).
*   Downloads high-quality video using `yt-dlp`.
*   **Auto-Captions:** Extracts original captions and attaches them to the video.
*   **Manual Override:** `/dl` command to force download processing.
*   Handles authentication via cookies to avoid blocking.

### 🧠 Smart AI Chain (8-Layer Defense)
*   **Architecture:** Powered by **LangChain** for robust, self-healing analysis.
*   **Search Grounding:** Uses **Google Search** to verify facts in real-time.
*   **Live Model Display:** Shows exact model name (e.g., `gemini-2.0-flash`) during analysis.
*   **Fallback System:** Automatically switches models if quotas are full or APIs fail.

### 🎓 Educational Mode (/learn)
*   **Multimodal Learning:** Provides 3 nuanced variations for any word/phrase.
*   **AI Visuals:** Generates unique, relevant images for each variation using Pollinations.ai.
*   **Mini-Podcast Audio:** Sophisticated Bilingual TTS that reads the Target Sentence then the Translation with a natural delay.
*   **Triple-Format Nouns:** Strictly provides nouns as `Indefinite / Definite / Plural` (e.g., `un / le / des`).
*   **Dynamic UI:** Shows real-time progress (e.g., `1/3`) on animated Mr. Bean status GIFs.
*   **Natural Pacing:** Intelligent TTS silences instead of reading slashes for a human-like recitation.
*   **Visual Polish:** Uses language flags (🇰🇷, 🇺🇸, 🇫🇷, 🇮🇷) for a clean, professional look.

### 🔊 Voice Response (TTS)
*   **Text-to-Speech:** Convert any text to voice using `/voice` command.
*   **Multi-Language Voice:** Reply to any message with `/voice en`, `/voice fa`, etc.
*   **Translation + Voice:** Automatically translates to the target language before speaking.
*   **Powered by edge-tts:** High-quality Neural TTS voices.
+ 
+ ### 💰 Live Market Data (Currency & Gold)
+ *   **Real-time Rates:** Fetches live USD, EUR, Gold 18k, and Global Ounce rates strictly from `tgju.org`.
+ *   **Gold Parity Analysis:** Automatically calculates the theoretical price of 18k gold based on global ounce/USD parity and shows the "Market Gap" (Bobble).
+ *   **Smart Caching:** Uses a 5-minute async cache to prevent rate-limiting and ensure ultra-fast response times.

### 🔊 Audio & TTS
*   **Multi-Language Voice:** `/voice` command to read or translate & read text.
*   **Educational Audio:** `/learn` generates pronunciation for words and sample sentences.
*   **TTS Support:** `fa`, `en`, `fr`, `ko` (powered by Edge-TTS).

### 🌍 Multi-Language Support
*   Full support for **Persian (FA)** 🇮🇷, **English (EN)** 🇺🇸, **French (FR)** 🇫🇷, and **Korean (KO)** 🇰🇷.
*   Bot interface and AI responses are fully localized.

### 🔒 Privacy & Access Control
*   **Whitelist System:** Only allowed users (Admin + Whitelist) can interact with the bot.
*   **Private Mode:** Unrecognized users are blocked with a polite access denied message.
*   **Daily Quotas:** Configurable request limits for different user types.

### ⚡ Performance Optimizations
*   **Concurrent Updates:** Handles multiple users simultaneously.
*   **Parallel Fetching:** Downloads all educational slides in parallel to prevent timeouts.
*   **Staggered Requests:** Avoids rate-limiting (429) errors during image generation.

---

## 🚀 Installation

### 1. Prerequisites
*   Python 3.9 or higher.
*   `ffmpeg` (Required for video processing).
*   A Telegram Bot Token (from [@BotFather](https://t.me/BotFather)).
*   A Google Gemini API Key (from [Google AI Studio](https://aistudio.google.com/)).

### 2. Setup

Clone the repository and install dependencies:

```bash
# Clone
git clone https://github.com/su6i/su6i-yar.git
cd su6i-yar

# Install Dependencies
pip install -r requirements.txt
```

### 3. Configuration (.env)

Create a `.env` file in the root directory:

```ini
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
SETTINGS={"admin_id": your_numeric_id, "public_mode": false}
GEMINI_API_KEY=your_gemini_api_key
```

---

---

## 🎮 Usage

### 💻 Run on Personal Computer (Local Mode)

Perfect for personal use - run the bot on your laptop/desktop:

```bash
# 1. Activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the bot
python3 su6i_yar.py
```

> **Important:** The bot will only work while your computer is running. Close the terminal = bot stops.

#### 🔄 Development Mode (Auto-Restart on Changes)

```bash
./run_dev.sh
```

---

### 🖥️ Run on Server (24/7 Mode)

For always-on availability, run on a VPS (Ubuntu/Debian):

```bash
# 1. Clone and setup
git clone https://github.com/su6i/su6i-yar.git
cd su6i-yar

# 2. Setup Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies & tools
pip install -r requirements.txt
sudo apt update && sudo apt install ffmpeg -y

# 4. Create systemd service
sudo vim /etc/systemd/system/su6i-yar.service
```

Add this content (replace `/path/to/su6i-yar` and `your_user`):
```ini
[Unit]
Description=Su6i Yar Telegram Bot
After=network.target

[Service]
User=your_user
Group=your_user
WorkingDirectory=/path/to/su6i-yar
ExecStart=/path/to/su6i-yar/venv/bin/python su6i_yar.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
# 5. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable su6i-yar
sudo systemctl start su6i-yar

# 6. Check status
sudo systemctl status su6i-yar
```

### ⌨️ Menu Buttons

| Button | Function |
| :--- | :--- |
| **📊 Status** | Show your current quota and bot settings. |
| **🆘 Help** | Show the full command guide. |
| **📥 Manage Download** | Toggle Instagram Downloading On/Off. |
| **🧠 Manage AI** | Toggle Gemini Fact-Checking On/Off. |
| **💰 Currency & Gold** | Show live market rates and gold parity analysis. |
| **🇮🇷 / 🇺🇸 / 🇫🇷 / 🇰🇷** | Switch Bot Language instantly. |
| **🛑 Stop Bot** | (Admin Only) Shutdown the bot safely. |

### 🤖 Commands

| Command | Description |
| :--- | :--- |
| `/start` | Reset and open the main menu. |
| `/learn` | **Educational tutor:** 3 variations + images + audio (e.g., `/l en apple`). |
| `/voice` | Reply to message to get voice version. Supports `/v en`, `/v fa`, etc. |
| `/check` | Reply to text to Fact-Check it using search grounding. |
| `/status` | View your user type and remaining daily quota. |
| `/price`  | **Live Market:** Show currency and gold rates (alias: `/p`). |
| `/help`  | Show instructions. |
| `/detail` | Reply to analysis to get full scientific breakdown. |
| `/dl` | Force download an Instagram link (reply or arg). |
| `/stop`  | **(Admin Only)** Shutdown the bot. |

---

## 📜 License

This project is open-source and available under the MIT License.
