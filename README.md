# 🤖 Su6i Yar - Smart AI Assistant

A powerful, intelligent Telegram bot that downloads Instagram videos and verifies factual claims using Google Gemini AI.
**Rewritten from scratch for speed, stability, and ease of use.**

![Version](https://img.shields.io/badge/Version-3.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9+-yellow.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Key Features

### 📥 Smart Downloader
*   Automatically detects Instagram links (Posts, Reels, TV).
*   Downloads high-quality video using `yt-dlp`.
*   Handles authentication via cookies to avoid blocking.

### 🧠 Smart AI Chain (8-Layer Defense)
*   **Architecture:** Powered by **LangChain** for robust, self-healing analysis.
*   **Search Grounding:** Uses **Google Search** to verify facts in real-time.
*   **Live Model Display:** Shows exact model name (e.g., `gemini-2.5-flash`) during analysis.
*   **Fallback System:** Automatically switches models if quotas are full or APIs fail:
    1.  Gemini 2.5 Pro (Global Search)
    2.  Gemini 1.5 Pro
    3.  Gemini 2.5 Flash
    4.  Gemini 2.0 Flash
    5.  Gemini 2.5 Flash-lite
    6.  Gemini 1.5 Flash
    7.  Gemini 1.5 Flash-8B
    8.  **DeepSeek** (Failsafe Backup)

### 📊 Summary + Detail View
*   **Summary First:** AI provides a concise comparison table with claims vs research findings.
*   **Detail on Demand:** Reply with `/detail` to get full scientific analysis with references.
*   **Smart Chunking:** Long responses are split by paragraphs, not mid-sentence.

### 🔊 Voice Response (TTS)
*   **Text-to-Speech:** Convert any text to voice using `/voice` command.
*   **Multi-Language Voice:** Reply to any message with `/voice en`, `/voice fa`, etc.
*   **Translation + Voice:** Automatically translates to target language before speaking.
*   **Powered by edge-tts:** High-quality Neural TTS voices.

### 🌍 Multi-Language Support
*   Full support for **Persian (FA)** 🇮🇷, **English (EN)** 🇺🇸, **French (FR)** 🇫🇷, and **Korean (KO)** 🇰🇷.
*   AI responses are fully localized (labels, examples, conclusions).
*   Instantly switch languages via the bot menu.

### ⚡ Interactive Menu
*   Fast, button-based interface for easy control.
*   Toggle Download/AI features On/Off with one click.
*   Status message replies directly to user's text.

### 🎨 Clean Logging
*   Colored console output (Green=INFO, Yellow=WARNING, Red=ERROR).
*   Filters verbose httpx and google_genai logs for cleaner output.

### ⚙️ Server Optimizations
*   **Concurrent Updates:** Handle multiple users simultaneously.
*   **Rate Limiting:** Prevents spam (5 sec cooldown per user).
*   **Auto-Restart (Dev):** Use `./run_dev.sh` for auto-reload on file changes.

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
git clone https://github.com/your-username/su6i-yar.git
cd su6i-yar

# Install Dependencies
pip install -r requirements.txt
# OR with uv
uv pip install -r requirements.txt
```

### 3. Configuration (.env)

Create a `.env` file in the root directory:

```ini
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_numeric_admin_id

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# DeepSeek AI (Optional Fallback)
DEEPSEEK_API_KEY=your_deepseek_key

# Instagram (Optional but Recommended for Reels)
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password
```

> **Note:** To get your `TELEGRAM_CHAT_ID`, send a message to `@userinfobot` on Telegram.

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

This will automatically restart the bot whenever you edit the code.

---

### 🖥️ Run on Server (24/7 Mode)

For always-on availability, run on a VPS (Ubuntu/Debian):

```bash
# 1. Clone and setup
git clone https://github.com/su6i/su6i-yar.git
cd su6i-yar

# 2. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Create .env file
vim .env
# Add your tokens (TELEGRAM_BOT_TOKEN, GEMINI_API_KEY, etc.)

# 4. Create systemd service
sudo vim /etc/systemd/system/su6i-yar.service
```

Add this content:
```text
[Unit]
Description=Su6i Yar Telegram Bot
After=network.target

[Service]
User=your_username
WorkingDirectory=/home/your_username/su6i-yar
ExecStart=/home/your_username/su6i-yar/venv/bin/python3 su6i_yar.py
Restart=always
RestartSec=10
Environment=PATH=/home/your_username/su6i-yar/venv/bin

[Install]
WantedBy=multi-user.target
```

Then:
```bash
# 3. Enable and start
sudo systemctl enable su6i-yar
sudo systemctl start su6i-yar

# 4. Check status
sudo systemctl status su6i-yar
```

---

### 📱 In Telegram

1.  **Start:** Send `/start` to see the welcome menu.
2.  **Download:** Paste any Instagram link. The bot will download and send the video.
3.  **Fact-Check:** Send any text (longer than 50 chars). The bot will analyze it with Gemini.
4.  **Detail View:** Reply to any AI analysis with `/detail` to get the full scientific breakdown.
5.  **Settings:** Use the menu buttons to toggle features or change language.

### ⌨️ Menu Buttons

The bot is primarily controlled via the interactive keyboard:

| Button | Function |
| :--- | :--- |
| **📊 Status** | Show current settings (AI/Download status). |
| **🆘 Help** | Show instructions. |
| **🔊 Voice** | Get voice version of last analysis. |
| **📥 Toggle Download** | Turn Instagram Downloading On/Off. |
| **🧠 Toggle AI** | Turn Gemini Fact-Checking On/Off. |
| **🇮🇷 / 🇺🇸 / 🇫🇷 / 🇰🇷** | Switch Bot Language instantly. |
| **🛑 Stop Bot** | (Admin Only) Shutdown the bot. |

### 🤖 Commands

| Command | Description |
| :--- | :--- |
| `/start` | Open the main menu. |
| `/status` | View current settings. |
| `/help`  | Show help instructions. |
| `/check` | Reply to text to Fact-Check it. |
| `/detail` | Reply to AI analysis to get full scientific details. |
| `/voice` | Reply to any message to get voice version. |
| `/voice en` | Translate to English and speak. |
| `/voice fa` | Translate to Persian and speak. |
| `/voice fr` | Translate to French and speak. |
| `/voice ko` | Translate to Korean and speak. |
| `/toggle_dl` | Toggle Download ON/OFF. |
| `/toggle_fc` | Toggle AI ON/OFF. |
| `/close` | Close/Remove the menu keyboard. |
| `/stop`  | **(Admin Only)** Shutdown the bot safely. |

---

## 📋 AI Analysis Format

### Summary (Default)
```
🧠 Analysis by gemini-2.5-flash

Overall Status: ⚠️

Comparison Table:
━━━━━━━━━━━━━━
▫️ Text Claim: 17%
▫️ Research Papers: 17.1%
▫️ Research Findings: Research confirms this amount
▫️ Status: ✅
━━━━━━━━━━━━━━

Conclusion:
[2-3 sentence summary]

💡 For full analysis:
Reply to this message with /detail
```

### Detail View (On Demand)
Full scientific analysis with:
- Detailed explanations for each claim
- Academic references with DOI/URLs
- Biological/technical mechanisms

---

## 🛠️ Troubleshooting

*   **Bot doesn't reply?**
    *   Check your terminal logs.
    *   Ensure your `TELEGRAM_BOT_TOKEN` is correct.
*   **Download fails?**
    *   Instagram blocks are common. Ensure `cookies.txt` is updated or credentials in `.env` are valid.
    *   Try updating yt-dlp: `pip install -U yt-dlp`.
*   **Menu stuck?**
    *   Send `/close` to remove the old menu, then `/start` again.
*   **AI response in wrong language?**
    *   Switch language using the menu buttons (🇮🇷/🇺🇸/🇫🇷).

---

## 📜 License

This project is open-source and available under the MIT License.
