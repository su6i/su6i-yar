# 📸 Smart Insta DL (All-in-One Downloader)

A powerful tool to download Instagram videos (Reels, Posts). It works in two modes:
1.  **Server Mode 🤖**: Runs as a Telegram Bot, monitoring chats for links.
2.  **CLI Mode 💻**: Runs as a command-line tool to download a single link instantly.

**✨ Key Feature: Auto-Healing Auth**
No need to manually manage cookies! If Instagram asks for login, the bot automatically launches a headless browser, logs in using your credentials, updates the session, and resumes the download.

## 🚀 Features

-   **Unified Script**: One file (`smart_insta_dl.py`) for everything.
-   **Auto-Login**: Detects auth failures and refreshes cookies automatically (Headless Selenium).
-   **Smart Download**: Uses `yt-dlp` for best quality.
-   **Optimized**: Converts/Compresses videos for Telegram compatibility.
-   **Server Ready**: Headless mode enabled by default for Linux/VPS environments.

## 🛠️ Setup

1.  **Clone & Install**:
    ```bash
    git clone https://github.com/YOUR_USERNAME/smart-insta-dl.git
    cd smart-insta-dl
    pip install -r requirements.txt
    ```

2.  **Configuration (`.env`)**:
    Create a `.env` file with your details:
    ```env
    # Telegram Bot Token (Required for Server Mode)
    TELEGRAM_BOT_TOKEN=12345678:AAE_xXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx
    
    # Target Chat ID (Required for CLI upload & Admin checks)
    TELEGRAM_CHAT_ID=123456789
    
    # Instagram Credentials (Required for Auto-Login)
    INSTAGRAM_USERNAME=your_username
    INSTAGRAM_PASSWORD=your_password
    ```

3.  **System Requirements**:
    -   `ffmpeg` installed:
        -   **Linux**: `sudo apt install ffmpeg`
        -   **macOS**: `brew install ffmpeg`
        -   **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.
    -   Google Chrome (for Selenium auto-login)

## 🏃 Usage

### 1️⃣ CLI Mode (Command Line)
Download a video instantly. It saves the video + caption locally and sends a copy to your Telegram "Saved Messages" (if `TELEGRAM_CHAT_ID` is set).

```bash
# Syntax
python smart_insta_dl.py <INSTAGRAM_URL>

# Example
python smart_insta_dl.py https://www.instagram.com/reel/Cs123456/
```

### 2️⃣ Server Mode (Telegram Bot)
Ideal for running on a VPS or keeping it open in the background.

1. **Start the Bot:**
   ```bash
   python smart_insta_dl.py --server
   ```
   You will see a log: `🤖 Bot started! Monitoring messages...`.
   
   > **To Stop the Bot:** Press `Ctrl + C` in the terminal.

2. **Use it in Telegram:**
   - Open your bot (e.g., **`@My_Personal_Assistant_Bot`**).
   - Click **Start**.
   - **Send an Instagram link** to the chat.
   - The bot will download and reply with the video. 🚀

   *Note: In this mode, the terminal just shows logs. All interaction happens in Telegram.*

### 3️⃣ Using in Groups & Channels
To have the bot auto-download links sent by **others** in a group:

1. **Add the bot** to your Group or Channel.
2. **Promote it to Admin** (Required to see messages).
   - *Why?* Telegram bots by default cannot see messages in groups due to privacy settings. Making it an Admin allows it to read links sent by members.
3. **That's it!** Any Instagram link sent in the group will be auto-replied to with the video.

## 🧠 Smart Features (Gemini AI)
The bot uses **Google Gemini AI** to fact-check scientific claims in captions!

### 🌍 Multi-Language Support
The bot speaks **English (Default), Persian (Farsi), and French**.
- It analyzes text in the selected language.
- It replies with "Thinking..." and results in that language.
- Change it with: `/set_lang fa`

### 👮‍♂️ Admin Alerts
Errors (API limits, network issues) are **hidden** from group chats to prevent spam. Instead, they are sent privately to the **Bot Owner** (Admin).
- Claim ownership with: `/set_admin`

### 🤖 How to use Fact-Checking:

1.  **Automatic (Private Chat):**
    -   Send any text longer than **50 characters** (default) to the bot in private.
    -   It will automatically analyze it.

2.  **Manual (Groups & Any Chat):**
    -   **Reply** to any message (text or caption) with **`/check`**.
    -   The bot will reads that specific message and analyze it.

---

## 🎮 Bot Commands Guide

| Command | Description |
| :--- | :--- |
| **`/start`** | Show welcome message and quick guide. |
| **`/help`** | Show the full list of commands. |
| **`/status`** | View settings (DL/FC status, Lang, Min Length). |
| **`/set_lang [code]`** | Set language: `fa` (Persian), `en` (English), `fr` (French). |
| **`/set_admin`** | **(Important)** Set YOURSELF as the Admin to receive error logs. |
| **`/stop_bot`** | **(Admin Only)** Stop and shutdown the bot remotely. |
| **`/toggle_dl`** | Enable/Disable video downloading. |
| **`/toggle_fc`** | Enable/Disable Fact-Checking. |
| **`/toggle_fc 100`** | Set minimum text length to 100 chars (and enable FC). |
| **`/check`** | (Reply to a message) Force analyze the text/caption. |

---

### 🔧 Troubleshooting
-   **Cookies**: The bot auto-heals `cookies.txt`. If downloads fail, wait a few seconds for it to login.
-   **No Reply in Group?**: Check if the bot is Admin. If it still fails silently, it likely hit an API error (check your DM if you are the Admin!).

## 📂 File Structure
-   `smart_insta_dl.py`: The main brain.
-   `requirements.txt`: Python dependencies.
-   `cookies.txt`: Auto-generated session file.
-   `instagram_videos_temp/`: Temporary download folder.
