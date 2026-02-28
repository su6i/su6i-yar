import asyncio
import httpx

async def check():
    instances = [
        "https://api.cobalt.tools",
        "https://cobalt.tools",
        "https://coapi.kelig.me", 
        "https://cobalt.meowing.de",
        "https://cobalt.pub", 
        "https://api.cobalt.kwiatekmiki.pl",
        "https://cobalt.hyperr.net", 
        "https://cobalt.kuba2k2.com",
        "https://api.cobalt.tools/api/json",
        "https://api.wukko.me"
    ]
    headers = {
        "Accept": "application/json", "Content-Type": "application/json"
    }
    payload = {"url": "https://youtube.com/shorts/LrQ7NM7dAjQ"}
    
    async with httpx.AsyncClient(timeout=5, follow_redirects=True) as client:
        for url in instances:
            api_url = url if url.endswith("/api/json") else url
            try:
                resp = await client.post(api_url, json=payload, headers=headers)
                print(f"[{resp.status_code}] {url} -> {resp.text[:50]}")
            except Exception as e:
                print(f"FAILED {url}: {e}")

asyncio.run(check())
