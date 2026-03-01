---
description: How to deploy Su6i Yar's Downloader on Datacenters (Hetzner, AWS) without Anti-Bot Blocks
---

# Bypassing Datacenter IP Blocks (YouTube & Anti-Bot Walls)

When deploying bot scrapers or downloaders (like `yt-dlp`) on Datacenter IPs (such as Hetzner, DigitalOcean, or AWS), services like YouTube enforce strict "Proof of Origin" (PO Token) blocks. Even with perfectly valid user cookies, the bot will hit a "Sign in to confirm you're not a bot" wall.

This workflow outlines the failed strategies and the ultimate successful strategy for bypassing these blocks.

## ❌ Failed Strategies

1. **Explicit Cookies Only**: Passing `cookies.txt` directly to `yt-dlp` works on local residential IPs (like your home Mac), but immediately fails on Datacenter IPs due to IP reputation.
2. **Anonymous Downloading**: Bypassing cookies entirely fails because YouTube now requires PO Tokens for almost all video extraction from unknown IPs.
3. **Forcing IPv6**: Using `--force-ipv6` in `yt-dlp` sometimes bypasses IPv4 bans, but Hetzner's IPv6 ranges are also heavily blacklisted by YouTube.
4. **Mobile Client Fallbacks (iOS/Android)**: Setting `--extractor-args "youtube:player_client=ios,android"` used to work, but YouTube recently enforced PO Tokens on mobile APIs as well.
5. **MWEB (Mobile Web) Fallback**: Setting `--extractor-args "youtube:player_client=mweb"` works temporarily for low-resolution (360p) anonymous downloads, but fails when high-quality or age-restricted videos require authenticated cookies.

## ✅ Successful Strategy: Cloudflare WARP (SOCKS5 Proxy Mode)

The most robust, free, and permanent solution is to tunnel the `yt-dlp` traffic through **Cloudflare WARP**, effectively masking the Datacenter IP behind Cloudflare's massive consumer proxy network (acting as a residential IP).

> [!IMPORTANT]
> To prevent WARP from breaking existing server routing or VPNs (like Hiddify), we **do not** run WARP in full VPN mode. Instead, we run it in **Proxy Mode** on a silent local port (`40000`).

### Installation on Ubuntu (x86_64 / amd64)

```bash
# 1. Add Cloudflare Repo
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | sudo gpg --yes --dearmor --output /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg && echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflare-client.list

# 2. Update and Install
sudo apt-get update && sudo apt-get install cloudflare-warp -y
```

### Installation on Ubuntu (ARM64 / aarch64)

> [!WARNING]
> Cloudflare often lags behind in releasing ARM64 packages for the latest Ubuntu versions (e.g., `noble` 24.04). If the standard installation fails with a `404 Not Found` for the `noble` repo, you must force the package manager to download the `jammy` (22.04) version, which is perfectly compatible.

```bash
# Force the 'jammy' repository instead of standard $(lsb_release -cs)
echo "deb [arch=arm64 signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ jammy main" | sudo tee /etc/apt/sources.list.d/cloudflare-client.list

sudo apt-get update
sudo apt-get install cloudflare-warp -y
```

### Configuration (SOCKS5 Proxy Mode)

Regardless of the architecture, run these exact commands (updated for the 2024+ WARP CLI syntax):

```bash
# 1. Register the device
warp-cli --accept-tos registration new

# 2. Set mode to proxy ONLY (does not route entire server traffic)
warp-cli --accept-tos mode proxy

# 3. Set the local port
warp-cli --accept-tos proxy port 40000

# 4. Connect
warp-cli --accept-tos connect
```

### Integrating with `yt-dlp` (Python)

Inside your Python download logic, inject the SOCKS5 proxy string into the `yt-dlp` base command. Ensure you bind it to `127.0.0.1`.

```python
    # Route strict sites through WARP SOCKS5 proxy to avoid Datacenter IP bans
    if platform in ["youtube", "instagram"]:
        yt_extra_args.extend(["--proxy", "socks5://127.0.0.1:40000"])
        
    if platform == "youtube":
        yt_extra_args.extend([
            "--remote-components", "ejs:github",
            "--extractor-args", "youtube:player_client=ios,android,default"
        ])
```

This ensures that only YouTube and Instagram traffic requested by the bot passes through Cloudflare, bypassing Datacenter tracking entirely!
