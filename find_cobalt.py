import asyncio
import httpx
import json

async def find_working_cobalt():
    headers = {"Accept": "application/json"}
    
    # 1. Fetch live instances from the registry
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        try:
            resp = await client.get("https://instances.cobalt.best/api/instances")
            instances_data = resp.json()
            # Filter instances that are online, trust >= 0
            live_urls = [inst["api"] for inst in instances_data if inst.get("version") and float(inst["version"].split(".")[0]) >= 10]
            print(f"Found {len(live_urls)} live v10 instances.")
        except Exception as e:
            print(f"Failed to fetch registry: {e}")
            return
            
    # 2. Test them with our YT video
    payload = {"url": "https://youtube.com/shorts/LrQ7NM7dAjQ"}
    req_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    
    working = []
    async with httpx.AsyncClient(timeout=5, follow_redirects=True) as client:
        for api_url in live_urls[:15]: # Test top 15
            if api_url == "https://api.cobalt.tools": continue # Official is strict
            try:
                # Cobalt v10 uses POST to '/'
                url_path = api_url.rstrip("/") + "/"
                resp = await client.post(url_path, json=payload, headers=req_headers)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    dl_url = data.get("url")
                    if dl_url:
                        print(f"✅ WORKING: {api_url}")
                        working.append(api_url)
                    else:
                        print(f"❌ Returned 200 but no URL: {api_url} -> {data}")
                else:
                    print(f"❌ HTTP {resp.status_code}: {api_url}")
            except Exception as e:
                print(f"❌ ERROR {api_url}: {type(e).__name__}")
                
    print(f"\nDiscovered {len(working)} working instances:\n" + json.dumps(working, indent=2))

asyncio.run(find_working_cobalt())
