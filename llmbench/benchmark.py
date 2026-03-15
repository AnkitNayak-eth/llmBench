import time
from .runners import run_inference as run_ollama  # type: ignore
from .gpu import get_gpu_vram_usage, get_gpu_temp, get_gpu_power # type: ignore

def run_benchmark(model):
    """
    Enhanced single-prompt benchmark. 
    Captures peak VRAM and detailed performance metrics.
    """
    prompt = "Write a comprehensive technical overview of Large Language Models, covering architecture, training, and inference optimization."
    
    start_vram = get_gpu_vram_usage()
    start_temp = get_gpu_temp()
    start_pwr = get_gpu_power()
    start_time = time.time()
    
    try:
        out = run_ollama(model, prompt)
    except Exception as e:
        return {"error": str(e)}
        
    end_time = time.time()
    end_vram = get_gpu_vram_usage()
    end_temp = get_gpu_temp()
    end_pwr = get_gpu_power()
    
    latency = end_time - start_time
    vram_delta = round(max(0, end_vram - start_vram), 2)
    response_text = out.get("response") or out.get("content") or ""
    
    prompt_eval_duration = out.get("prompt_eval_duration", 0) / 1e9
    eval_duration = out.get("eval_duration", 0) / 1e9
    eval_count = out.get("eval_count", 0)
    prompt_eval_count = out.get("prompt_eval_count", 0)
    load_duration = out.get("load_duration", 0) / 1e9
    total_duration = out.get("total_duration", 0) / 1e9
    
    # Residency Detection
    # If the VRAM delta is zero, the model was already in the GPU memory.
    if vram_delta < 0.02:
        residency_status = "Stay-Resident"
    elif load_duration > 1.0:
        residency_status = "Cold Start"
    else:
        residency_status = "Dynamic"
    
    temp_delta = round(max(0, end_temp - start_temp), 1)
    avg_pwr = round((start_pwr + end_pwr) / 2, 2)
    
    if eval_count == 0:
        eval_count = len(response_text.split())
    if prompt_eval_count == 0:
        prompt_eval_count = len(prompt.split())
        
    if eval_duration > 0:
        tokens_sec = eval_count / eval_duration
    else:
        tokens_sec = eval_count / latency if latency > 0 else 0
        
    prompt_eval_rate = prompt_eval_count / prompt_eval_duration if prompt_eval_duration > 0 else 0
    generation_eval_rate = eval_count / eval_duration if eval_duration > 0 else 0

    # Efficiency Calculations
    tokens_per_watt = round(tokens_sec / avg_pwr, 4) if avg_pwr > 0 else 0
    joules_per_token = round(avg_pwr / tokens_sec, 2) if tokens_sec > 0 else 0
    total_energy_kj = round((avg_pwr * latency) / 1000, 3)
    
    # Thermal Velocity (°C/min)
    thermal_velocity = round(temp_delta / (latency / 60), 2) if latency > 0 else 0

    output_chars = len(response_text)
    chars_per_token = output_chars / eval_count if eval_count > 0 else 0
    chars_per_sec = output_chars / latency if latency > 0 else 0

    return {
        "latency": round(latency, 2),
        "tokens_sec": round(tokens_sec, 2),
        "ttft": round(prompt_eval_duration, 2),
        "total_duration": round(total_duration, 2),
        "eval_duration": round(eval_duration, 2),
        "load_time": round(load_duration, 2),
        "prompt_tokens": prompt_eval_count,
        "eval_tokens": eval_count,
        "prompt_eval_rate": round(prompt_eval_rate, 2),
        "generation_eval_rate": round(generation_eval_rate, 2),
        "output_chars": output_chars,
        "chars_per_token": round(chars_per_token, 2),
        "chars_per_sec": round(chars_per_sec, 2),
        "peak_vram_gb": vram_delta,
        "vram_absolute_gb": end_vram,
        "vram_residency": residency_status,
        "thermal_delta": temp_delta,
        "thermal_velocity": thermal_velocity,
        "avg_power_w": avg_pwr,
        "total_energy_kj": total_energy_kj,
        "joules_token": joules_per_token,
        "tokens_per_watt": tokens_per_watt,
        "response_preview": response_text[:100] + "..."
    }