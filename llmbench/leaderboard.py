"""
Centralized data fetching for LLM rankings via arena.ai (LMSYS Arena).
Strategy:
- Scrapes the server-rendered HTML from arena.ai/leaderboard/text category sub-routes.
- Uses parallel threads to fetch Overall, Expert, Math, Coding, etc.
- Merges with a 2026 supplement for the absolute frontier.
"""

import re
import requests  # type: ignore
import time
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console  # type: ignore

console = Console()

# --- Live data sources ---
BASE_ARENA_URL = "https://arena.ai/leaderboard/text"

CATEGORIES = {
    "Overall": "",
    "Expert": "expert",
    "Math": "math",
    "Instruction Following": "instruction-following",
    "Multi-Turn": "multi-turn",
    "Coding": "coding"
}

def _scrape_single_category(cat_name, slug):
    """
    Scrapes a single category from arena.ai.
    Returns: {model_name: {"elo": int, "rank": int, "org": str}}
    """
    url = f"{BASE_ARENA_URL}/{slug}" if slug else BASE_ARENA_URL
    results = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Referer": "https://arena.ai/leaderboard"
    }

    for attempt in range(2): # Simple retry
        try:
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code == 429:
                time.sleep(2)
                continue
            r.raise_for_status()
            html = r.text
            
            # Pattern: find all <tr> contents or similar row structures
            # Flexibility for different table renderings
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
            if not rows:
                # Fallback to div-based rows if they change structure
                rows = re.findall(r'<div[^>]*role="row"[^>]*>(.*?)</div>', html, re.DOTALL)
            
            for row in rows:
                try:
                    # Model Name: look for title attribute or link text
                    name_match = re.search(r'title="([^"]+)"', row)
                    if not name_match:
                        name_match = re.search(r'href="/models/[^>]+>([^<]+)</a>', row)
                    
                    # Elo: look for a span with an Elo-like number (e.g. 1234)
                    # Often follows min-w-[178px] or similar width class
                    elo_match = re.search(r'>(\d{4})</span>', row)
                    if not elo_match:
                        elo_match = re.search(r'(\d{4})\s*±', row)
                    
                    # Rank
                    rank_match = re.search(r'font-medium">(\d+)</span>', row)
                    if not rank_match:
                        rank_match = re.search(r'<span>(\d+)</span>', row)
                    
                    # Org
                    org_match = re.search(r'class="text-text-secondary[^>]*>([^<]+)</span>', row)
                    
                    if name_match and elo_match:
                        name = name_match.group(1).strip()
                        elo = int(elo_match.group(1))
                        rank = int(rank_match.group(1)) if rank_match else 0
                        org_full = org_match.group(1).strip() if org_match else ""
                        org = org_full.split("·")[0].strip() if "·" in org_full else org_full
                        
                        results[name] = {
                            "elo": elo,
                            "rank": rank,
                            "org": org
                        }
                except Exception:
                    continue
            
            if results:
                break # Success
                
        except Exception as exc:
            if attempt == 1:
                console.print(f"[dim yellow]⚠ {cat_name} Scraping failed: {exc}[/dim yellow]")
            time.sleep(1)
        
    return cat_name, results

def fetch_llm_leaderboard():
    """
    Fetches all Arena categories in parallel and merges data.
    Returns: (list of dicts, source_label)
    """
    all_data = {} # {model_name: {cat_name: elo, "org": org, "rank": overall_rank}}
    
    # Fetch in parallel
    with ThreadPoolExecutor(max_workers=5) as executor: # Limit workers to reduce rate-limit risk
        futures = [executor.submit(_scrape_single_category, name, slug) for name, slug in CATEGORIES.items()]
        for future in futures:
            cat_name, results = future.result()
            for model_name, data in results.items():
                if model_name not in all_data:
                    all_data[model_name] = {"name": model_name, "org": data["org"], "categories": {}}
                
                all_data[model_name]["categories"][cat_name] = data["elo"]
                
                # Use "Overall" to set the primary rank/elo reference
                if cat_name == "Overall":
                    all_data[model_name]["elo"] = data["elo"]
                    all_data[model_name]["rank"] = data["rank"]
                elif "elo" not in all_data[model_name]:
                    # Use first encountered category as fallback for sorting info
                    all_data[model_name]["elo"] = data["elo"]
                    all_data[model_name]["rank"] = 999

    # Convert to list
    models = list(all_data.values())

    # Ensure everyone has an elo for sorting
    for m in models:
        if "elo" not in m:
            m["elo"] = 0

    # Sort by Overall Elo primarily
    models.sort(key=lambda x: (x.get("categories", {}).get("Overall", 0), x.get("elo", 0)), reverse=True)
    
    # Refresh ranks
    for i, m in enumerate(models):
        m["rank"] = i + 1
        
    source = "LMSYS Arena (Live Multi-Category Scrape)"
    if not models:
        source = "Offline Fallback (No live data)"

    return models, source
