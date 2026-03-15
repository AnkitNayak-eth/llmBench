import requests
import re

def estimate_size(name):
    """Parses model name to estimate parameter size in Billions."""
    name = name.lower()
    match = re.search(r'(\d+(\.\d+)?)b', name)
    if match:
        return float(match.group(1))
    
    # Common special cases
    if "70b" in name: return 70
    if "34b" in name: return 34
    if "13b" in name: return 13
    if "8b" in name: return 8
    if "7b" in name: return 7
    if "3b" in name: return 3
    if "1.5b" in name: return 1.5
    if "0.5b" in name: return 0.5
    
    return None


def recommend_models(hw):
    """
    Returns separate recommendations for Ollama and HF/llama.cpp
    based on the system's VRAM and RAM profile.
    """
    ram = hw["ram_gb"]
    vram = hw["vram_gb"]
    
    # We aim for models that fit comfortably in memory 
    # (assuming 4-bit quantization, ~0.7-0.8 GB per Billion parameters)
    memory_limit = vram if vram > 0 else (ram * 0.7)
    
    # 1. Ollama Recommendations (Top popular models)
    # We use a curated list of reliable Ollama models that scale well
    ollama_candidates = [
        {"name": "Llama 3.1 8B", "id": "llama3.1", "size": 8},
        {"name": "Mistral Nemo 12B", "id": "mistral-nemo", "size": 12},
        {"name": "Gemma 2 9B", "id": "gemma2", "size": 9},
        {"name": "Qwen 2.5 7B", "id": "qwen2.5", "size": 7},
        {"name": "Phi-3 Mini 3.8B", "id": "phi3", "size": 3.8},
        {"name": "Qwen 2.5 0.5B", "id": "qwen2.5:0.5b", "size": 0.5},
        {"name": "Llama 3.2 3B", "id": "llama3.2", "size": 3},
        {"name": "Mistral 7B", "id": "mistral", "size": 7},
    ]
    
    ollama_results = []
    for c in ollama_candidates:
        if c["size"] * 0.8 <= memory_limit:
            ollama_results.append({
                "name": c["name"],
                "command": f"ollama run {c['id']}"
            })
            
    # 2. HF/llama.cpp Recommendations (Latest GGUFs)
    # Fetching from HF API for dynamic suggestions
    url = "https://huggingface.co/api/models"
    params = {
        "pipeline_tag": "text-generation",
        "search": "GGUF",
        "sort": "downloads",
        "direction": -1,
        "limit": 100
    }
    
    hf_results = []
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            for m in r.json():
                name = m["id"]
                size = estimate_size(name)
                
                if size and (size * 0.8 <= memory_limit):
                    hf_results.append({
                        "name": name.split('/')[-1],
                        "link": f"https://huggingface.co/{name}"
                    })
                if len(hf_results) >= 8:
                    break
    except:
        pass # Fallback to static if offline
        
    return {
        "ollama": ollama_results[:8],
        "hf": hf_results[:8]
    }