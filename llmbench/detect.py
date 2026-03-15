import requests  # type: ignore
import shutil
import os

def detect_ollama():
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        models = r.json().get("models", [])
        return [m["name"] for m in models]
    except:
        return []

def ping_ollama():
    try:
        r = requests.get("http://localhost:11434/", timeout=2)
        return r.status_code == 200
    except:
        return False

def detect_llama_cpp():
    """Detect models from a running llama.cpp server (default port 8080)."""
    try:
        # llama.cpp server often has /props or /health
        # Some users use openai-compatible /v1/models
        r = requests.get("http://localhost:8080/v1/models", timeout=2)
        if r.status_code == 200:
            models = r.json().get("data", [])
            return [m["id"] for m in models]
        
        # Fallback to llama.cpp specific /props if OpenAI API not enabled
        r = requests.get("http://localhost:8080/props", timeout=2)
        if r.status_code == 200:
            return ["llama.cpp-server"] # llama.cpp doesn't always list name clearly in /props
            
    except:
        pass
    return []

def ping_llama_cpp():
    try:
        r = requests.get("http://localhost:8080/health", timeout=2)
        return r.status_code == 200
    except:
        try:
            r = requests.get("http://localhost:8080/", timeout=2)
            return r.status_code == 200
        except:
            return False

def find_binary(name):
    """Check if a binary exists in PATH or common locations."""
    path = shutil.which(name)
    if path:
        return path
    
    # Windows specific common spots
    if os.name == 'nt':
        if name == 'ollama':
            local_appdata = os.environ.get('LOCALAPPDATA', '')
            alt_path = os.path.join(local_appdata, 'Ollama', 'ollama.exe')
            if os.path.exists(alt_path):
                return alt_path
    
    return None

def detect_models():
    models = []
    
    # Check Ollama
    ollama_models = detect_ollama()
    for m in ollama_models:
        models.append(f"Ollama: {m}")
        
    # Check llama.cpp
    lcpp_models = detect_llama_cpp()
    for m in lcpp_models:
        models.append(f"llama.cpp: {m}")

    return list(set(models))