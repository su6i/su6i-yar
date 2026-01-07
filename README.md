<div align="center">
  <img src="assets/project_logo.svg" width="350" alt="Su6i Yar Logo">
  <h1>🤖 Su6i Yar - Smart AI Assistant</h1>

  <br>
  
  <p align="center" style="white-space: nowrap;">
    <img src="https://img.shields.io/badge/Version-5.0.0-blue.svg" alt="Version">&nbsp;<img src="https://img.shields.io/badge/Python-3.12+-yellow.svg" alt="Python">&nbsp;<img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">&nbsp;<a href="https://www.linkedin.com/in/su6i/"><img src="assets/linkedin_su6i.svg" height="20" alt="LinkedIn"></a>
  </p>
</div>

A powerful, intelligent Telegram bot that downloads Instagram videos, verifies factual claims, and provides multimodal educational content using Google Gemini AI.

**Rewritten from scratch for speed, stability, and ease of use.**



## ✨ Key Features

### 📥 Smart Downloader (Triple-Fallback)
*   **Success Guarantee:** Uses a 3-stage strategy (Anonymous -> Safari Cookies -> Cobalt API) to bypass Instagram blocks.
*   **Telegram 50MB Limit Fix:** Automatically detects large files and scales resolution (1080p → 720p → 480p) to ensure the video always fits Telegram's bot limit.
*   **Auto-Captions:** Extracts original captions and attaches them to the video.
*   **Manual Override:** `/dl` command to force download processing.
*   **Hybrid Authentication:**
    *   **Local (Mac):** Seamlessly uses Safari browser cookies for personal/dev use.
    *   **Server (VPS):** Supports standard `cookies.txt` management via the included `upload_cookie.py` script.

### 🧠 Smart AI Chain (8-Layer Defense)
*   **Primary Model:** Powered by **Gemini 3 Flash Preview** for cutting-edge speed and reasoning.
*   **Architecture:** Guided by **LangChain** for robust, self-healing analysis.
*   **Search Grounding:** Uses **Google Search** to verify facts in real-time.
*   **Advanced Parsing:** Intelligently handles multimodal/grounding responses to ensure clean, formatted output.
*   **Live Model Display:** Shows exact model name (e.g., `gemini-3-flash-preview`) during analysis.
*   **Fallback System:** Automatically switches models (Pro/Flash/DeepSeek) if quotas are full or APIs fail.

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

### 🎂 Smart Birthday System (New!)
*   **Dual Calendar Support:** Automatically detects **Jalali (Solar Hijri)** vs **Gregorian** dates.
    *   Enter `1380-05-20` -> Stored as Jalali (celebrated on correct solar day).
    *   Enter `2001-08-11` -> Stored as Gregorian.
*   **Automatic Scheduler:** Checks birthdays every morning at 09:00 AM.
*   **Manual Wishes:** Generate instant birthday cards (AI Image + Text + Song) using `/birthday wish`.
*   **Smart Storage:** Data safely stored in `.storage/birthdays.json`.

### 🔒 Privacy & Access Control
*   **Whitelist System:** Only allowed users (Admin + Whitelist) can interact with the bot.
*   **Private Mode:** Unrecognized users are blocked with a polite access denied message.
*   **Daily Quotas:** Configurable request limits for different user types.

### ⚡ Performance Optimizations
*   **Concurrent Updates:** Handles multiple users simultaneously.
*   **Parallel Fetching:** Downloads all educational slides in parallel to prevent timeouts.
*   **Staggered Requests:** Avoids rate-limiting (429) errors during image generation.

### 🎨 User Experience Enhancements
*   **Countdown Timers:** Temporary messages (help, status, price) show live countdown before auto-deletion in groups.
*   **Monospace Help Menus:** Clean, consistent help formatting across all 4 languages.
*   **Smart Auto-Cleanup:** Informational messages auto-delete after 30-60s to keep group chats clean.
*   **Cookie Upload Script:** `upload_cookie.py` for easy Instagram authentication management.

---

## 🚀 Installation

### 1. Prerequisites
*   Python 3.9 or higher.
*   `ffmpeg` (Required for video processing).

*   A Telegram Bot Token (from [@BotFather](https://t.me/BotFather)).
*   A Google Gemini API Key (from [Google AI Studio](https://aistudio.google.com/)).

### 2. Setup
Run the automated installer to set up dependencies and configuration in one step:

```bash
chmod +x install.sh
./install.sh
```

Follow the on-screen prompts to enter your API keys. You will need:

| Variable | Purpose (Why do I need this?) | Where to find it |
| :--- | :--- | :--- |
| **`TELEGRAM_BOT_TOKEN`** | Connects your code to the Telegram bot so it can receive/send messages. | Start a chat with [@BotFather](https://t.me/BotFather) and send `/newbot`. |
| **`GEMINI_API_KEY`** | Powers the AI! Used for generating text, fact-checking, and translating. | Get it from [Google AI Studio](https://aistudio.google.com/). |
| **`admin_id`** | **Security:** Identifies YOU as the owner. The bot will ignore anyone else to prevent unauthorized usage. | Send a message to [@userinfobot](https://t.me/userinfobot) to see your numeric ID. |

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

#### 🔄 Development Mode (Persistence & Auto-Restart)

Run the bot with the `--dev` flag to enable development features:
- **Persistent Messages:** Status and error messages are NOT deleted, making debugging easier.
- **Auto-Restart:** Instantly reloads the bot when you save code changes.

```bash
# Easy start script (Requires nodemon or watchdog)
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
| `/dl` | Force download an Instagram link (reply or arg). **New:** Direct reply to video file to Compress & Fix. |
| `/dl` | Force download an Instagram link (reply or arg). **New:** Direct reply to video file to Compress & Fix. |
| `/birthday` | **Add:** `/birthday add @user <date>` (or Reply to user)<br>**Wish:** `/birthday wish <name> <date>` (Auto-saves)<br>**Check:** `/birthday check` |
| `/stop`  | **(Admin Only)** Shutdown the bot. |

---

## 🤝 Contributing
Contributions are welcome! Please check the issues page or submit a Pull Request.

## 📜 License

This project is open-source and available under the MIT License.
