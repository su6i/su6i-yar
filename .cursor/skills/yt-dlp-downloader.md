---
name: yt-dlp-downloader
description: Best practices and known bugs for yt-dlp, specifically regarding Instagram and media extraction.
---

# Skill: yt-dlp Downloader Best Practices

[Back to README](../../README.md)

This document records essential configurations, workarounds, and CRITICAL BUGS discovered during the development of media downloaders using `yt-dlp`.

---

## ⚠️ CRITICAL BUG: Instagram Stories & `--no-playlist`

> [!IMPORTANT]
> **NEVER use the `--no-playlist` flag when downloading Instagram Stories.**

### The Issue
When requesting a specific Instagram Story URL (e.g., `https://www.instagram.com/stories/username/ID/`), passing the `--no-playlist` flag causes the `yt-dlp` extractor to return an empty result or throw a "returned nothing" warning.
- **Log Signature:** `WARNING: Extractor instagram:story returned nothing; please report this issue...`
- **Result:** The download fails even if valid cookies are provided.

### The Workaround
To successfully download a single story:
1. **Omit `--no-playlist`**: Allow `yt-dlp` to treat the story as part of the user's current story "playlist".
2. **Handle Multiple Files**: Be prepared for `yt-dlp` to download multiple files if the user has multiple active stories, or use `--match-filter` if you have the specific Story ID, but simply omitting the flag and checking the output directory is the most robust method.
3. **Cookie Requirement**: Instagram Stories *always* require cookies (`--cookies-from-browser` or `--cookies`).

---

## 🛠️ macOS Cookie Extraction (Safari)

### The Permission Issue
On macOS, `yt-dlp` often fails to read Safari cookies with an `Operation not permitted` error (CWE-281).
- **Cause**: macOS "Full Disk Access" security sandbox protects the Safari cookie database.
- **Solution**: 
    - The user must grant **Full Disk Access** to the Terminal/IDE in `System Settings > Privacy & Security`.
    - **Developer Strategy**: If Safari fails, always loop through other browsers (`chrome`, `edge`, `firefox`, `brave`) as they often have less restrictive filesystem markers or are already granted access.

---

## ⚡ Performance Optimization

- **IPv6 Force**: In some datacenters, Instagram rate-limits IPv4. Use `-6` or `--force-ipv6` as a fallback.
- **Concurrent Fragments**: For large videos, use `--concurrent-fragments 5` to speed up the download.
- **FFmpeg Integration**: Always ensure a modern `ffmpeg` is in the path to handle DASH stream merging for high-quality (1080p+) videos.

---
[Back to README](../../README.md)
