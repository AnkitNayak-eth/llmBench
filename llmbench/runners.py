import requests  # type: ignore

def run_ollama(model, prompt):
    """Single-turn generation for Ollama."""
    # Strip the prefix if present
    if model.startswith("Ollama: "):
        model = model.replace("Ollama: ", "")
        
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )
    return r.json()

def run_chat_ollama(model, messages):
    """Multi-turn chat for Ollama."""
    if model.startswith("Ollama: "):
        model = model.replace("Ollama: ", "")
        
    r = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False
        }
    )
    return r.json()

def run_llama_cpp(model, prompt):
    """Single-turn generation for llama.cpp."""
    # llama.cpp server usually uses /completion or /v1/chat/completions
    try:
        r = requests.post(
            "http://localhost:8080/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            },
            timeout=120
        )
        if r.status_code == 200:
            res = r.json()
            return {"response": res["choices"][0]["message"]["content"]}
    except:
        pass
        
    # Fallback to native /completion
    r = requests.post(
        "http://localhost:8080/completion",
        json={
            "prompt": prompt,
            "stream": False
        }
    )
    res = r.json()
    return {"response": res["content"]}

def run_chat_llama_cpp(model, messages):
    """Multi-turn chat for llama.cpp."""
    r = requests.post(
        "http://localhost:8080/v1/chat/completions",
        json={
            "messages": messages,
            "stream": False
        }
    )
    res = r.json()
    return {"message": res["choices"][0]["message"]}

def run_inference(model, prompt):
    """Generic inference wrapper."""
    if model.startswith("Ollama: "):
        return run_ollama(model, prompt)
    elif model.startswith("llama.cpp: "):
        return run_llama_cpp(model, prompt)
    return run_ollama(model, prompt) # Default to Ollama if no prefix

def run_chat(model, messages):
    """Generic chat wrapper."""
    if model.startswith("Ollama: "):
        return run_chat_ollama(model, messages)
    elif model.startswith("llama.cpp: "):
        return run_chat_llama_cpp(model, messages)
    return run_chat_ollama(model, messages)