import subprocess
import os
import shutil
import json
import re

def _run_nvidia_smi(query_fields):
    """Internal helper for robust nvidia-smi calls."""
    paths = [
        shutil.which("nvidia-smi"),
        r"C:\Windows\System32\nvidia-smi.exe",
        r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe"
    ]
    
    for nv_path in paths:
        if not nv_path or not os.path.exists(nv_path): continue
        try:
            cmd = [nv_path, f"--query-gpu={query_fields}", "--format=csv,noheader,nounits"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout:
                return res.stdout.strip()
        except:
            continue
    return None

def get_gpu():
    """Super-robust GPU detection."""
    raw = _run_nvidia_smi("name,memory.total,driver_version")
    if raw:
        parts = [p.strip() for p in raw.split(",")]
        if len(parts) >= 2:
            vram = round(float(parts[1]) / 1024, 2)
            return {
                "gpu": parts[0],
                "vram_gb": vram,
                "driver": parts[2] if len(parts) > 2 else "N/A",
                "is_nvidia": True,
                "source": "nvidia-smi"
            }

    # 2. PowerShell Fallback (CIM)
    if os.name == 'nt':
        try:
            ps_cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion | ConvertTo-Json -Compress"]
            res = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=10)
            
            if res.returncode == 0 and res.stdout:
                match = re.search(r'\[.*\]|\{.*\}', res.stdout.replace('\n', ''))
                if match:
                    data = json.loads(match.group(0))
                    if isinstance(data, dict): data = [data]
                    
                    best_gpu = None
                    for entry in data:
                        name = entry.get("Name", "Unknown GPU")
                        ram = entry.get("AdapterRAM", 0) or 0
                        if ram < 0: ram = 4294967296 + ram
                        vram_gb = round(abs(ram) / (1024**3), 2)
                        
                        if "RTX 5060" in name and vram_gb < 4.1: vram_gb = 8.0

                        is_discrete = any(x in name.lower() for x in ["nvidia", "amd", "radeon", "geforce", "rtx", "arc", "quadro"])
                        current = {
                            "gpu": name, "vram_gb": vram_gb, "driver": entry.get("DriverVersion", "N/A"),
                            "is_nvidia": "nvidia" in name.lower(), "source": "cim"
                        }
                        if best_gpu is None or (is_discrete and vram_gb > best_gpu["vram_gb"]):
                            best_gpu = current
                    
                    if best_gpu: return best_gpu
        except Exception: pass

    return {"gpu": "Generic/CPU Only", "vram_gb": 0, "driver": "N/A", "is_nvidia": False, "source": "none"}

def get_gpu_vram_usage():
    res = _run_nvidia_smi("memory.used")
    if res:
        try:
            return round(float(res.split("\n")[0]) / 1024, 2)
        except: pass
    return 0

def get_gpu_temp():
    res = _run_nvidia_smi("temperature.gpu")
    if res:
        try: return float(res.strip())
        except: pass
    return 0

def get_gpu_power():
    res = _run_nvidia_smi("power.draw")
    if res:
        try: return float(res.strip())
        except: pass
    return 0