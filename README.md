# 🤖 Smart InstaBot (AI Powered)

A powerful, intelligent Telegram bot that downloads Instagram videos and verifies factual claims using Google Gemini AI.
**Rewritten from scratch for speed, stability, and ease of use.**

![Version](https://img.shields.io/badge/Version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9+-yellow.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Key Features

*   **📥 Smart Downloader:**
    *   Automatically detects Instagram links (Posts, Reels, TV).
    *   Downloads high-quality video using `yt-dlp`.
    *   Handles authentication via cookies to avoid blocking.
*   **🧠 Smart AI Chain (8-Layer Defense):**
    *   **Architecture:** Powered by **LangChain** for robust, self-healing analysis.
    *   **Search Grounding:** Uses **Google Search** to verify facts in real-time (with Gemini 2.5 Pro).
    *   **Fallback Sytem:** Automatically switches models if quotas are full or APIs fail:
        1.  Gemini 2.5 Pro (Global Search)
        2.  Gemini 1.5 Pro
        3.  Gemini 2.5 Flash
        4.  Gemini 2.0 Flash
        5.  Gemini 2.5 Flash-lite
        6.  Gemini 1.5 Flash
        7.  Gemini 1.5 Flash-8B
        8.  **DeepSeek** (Failsafe Backup)
*   **🌍 Multi-Language Support:**
    *   Full support for **Persian (FA)** 🇮🇷, **English (EN)** 🇺🇸, and **French (FR)** 🇫🇷.
    *   Instantly switch languages via the bot menu.
*   **⚡ Interactive Menu:**
    *   Fast, button-based interface for easy control.
    *   Toggle Download/AI features On/Off with one click.

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
git clone https://github.com/your-username/smart-insta-dl.git
cd smart-insta-dl

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

Run the bot:

```bash
python3 smart_insta_dl.py
```

### 📱 In Telegram

1.  **Start:** Send `/start` to see the welcome menu.
2.  **Download:** Paste any Instagram link. The bot will download and send the video.
3.  **Fact-Check:** Send any text (longer than 50 chars). The bot will analyze it with Gemini.
4.  **Settings:** Use the menu buttons to toggle features or change language.

### ⌨️ Menu Buttons

The bot is primarily controlled via the interactive keyboard:

| Button | Function |
| :--- | :--- |
| **📊 Status** | Show current settings (AI/Download status). |
| **🆘 Help** | Show instructions. |
| **📥 Toggle Download** | Turn Instagram Downloading On/Off. |
| **🧠 Toggle AI** | Turn Gemini Fact-Checking On/Off. |
| **🇮🇷 / 🇺🇸 / 🇫🇷** | Switch Bot Language instantly. |
| **🛑 Stop Bot** | (Admin Only) Shutdown the bot. |

### 🤖 Commands

| Command | Description |
| :--- | :--- |
| `/start` | Open the main menu. |
| `/status` | View current settings. |
| `/help`  | Show help instructions. |
| `/check` | Reply to text to Fact-Check it. |
| `/toggle_dl` | Toggle Download ON/OFF. |
| `/toggle_fc` | Toggle AI ON/OFF. |
| `/close` | Close/Remove the menu keyboard. |
| `/stop`  | **(Admin Only)** Shutdown the bot safely. |

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

---

## 📜 License

This project is open-source and available under the MIT License.
