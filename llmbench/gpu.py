import subprocess
import os
import shutil
import json
import re

def get_gpu():
    """
    Super-robust GPU detection.
    """
    # 1. Try nvidia-smi (Most accurate for NVIDIA)
    nv_path = shutil.which("nvidia-smi") or r"C:\Windows\System32\nvidia-smi.exe"

    # Try simple first to increase reliability
    try:
        cmd = [nv_path, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout:
            parts = [p.strip() for p in res.stdout.split(",")]
            if len(parts) >= 2:
                vram = round(float(parts[1]) / 1024, 2)
                return {
                    "gpu": parts[0],
                    "vram_gb": vram,
                    "driver": parts[2] if len(parts) > 2 else "N/A",
                    "is_nvidia": True,
                    "source": "nvidia-smi"
                }
    except Exception:
        pass

    # 2. PowerShell Fallback (CIM)
    if os.name == 'nt':
        try:
            # We fetch more fields to be safe
            ps_cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion | ConvertTo-Json -Compress"]
            res = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=10)
            
            if res.returncode == 0 and res.stdout:
                # Handle cases where PS might print extra stuff
                match = re.search(r'\[.*\]|\{.*\}', res.stdout.replace('\n', ''))
                if match:
                    data = json.loads(match.group(0))
                    if isinstance(data, dict): data = [data]
                    
                    best_gpu = None
                    for entry in data:
                        name = entry.get("Name", "Unknown GPU")
                        ram = entry.get("AdapterRAM", 0) or 0
                        # Handle 32-bit signed overflow
                        if ram < 0: ram = 4294967296 + ram
                        
                        vram_gb = round(abs(ram) / (1024**3), 2)
                        
                        # Hack for Laptop 4GB/8GB reporting issues in WMI
                        if "RTX 5060" in name and vram_gb < 4.1:
                            vram_gb = 8.0

                        is_discrete = any(x in name.lower() for x in ["nvidia", "amd", "radeon", "geforce", "rtx", "arc", "quadro"])
                        
                        current = {
                            "gpu": name,
                            "vram_gb": vram_gb,
                            "driver": entry.get("DriverVersion", "N/A"),
                            "is_nvidia": "nvidia" in name.lower(),
                            "source": "cim"
                        }
                        
                        if best_gpu is None:
                            best_gpu = current
                        elif is_discrete and not any(x in best_gpu["gpu"].lower() for x in ["nvidia", "amd", "rtx"]):
                            best_gpu = current
                        elif is_discrete and vram_gb > best_gpu["vram_gb"]:
                            best_gpu = current
                    
                    if best_gpu:
                        return best_gpu
        except Exception:
            pass

    return {
        "gpu": "Generic/CPU Only",
        "vram_gb": 0,
        "driver": "N/A",
        "is_nvidia": False,
        "source": "none"
    }

def get_gpu_vram_usage():
    try:
        nv_path = shutil.which("nvidia-smi") or r"C:\Windows\System32\nvidia-smi.exe"
        cmd = [nv_path, "--query-gpu=memory.used", "--format=csv,noheader,nounits"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return round(float(res.stdout.split("\n")[0]) / 1024, 2)
    except:
        pass
    return 0


def get_gpu_temp():
    try:
        nv_path = shutil.which("nvidia-smi") or r"C:\Windows\System32\nvidia-smi.exe"
        cmd = [nv_path, "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return float(res.stdout.strip())
    except:
        pass
    return 0


def get_gpu_power():
    try:
        nv_path = shutil.which("nvidia-smi") or r"C:\Windows\System32\nvidia-smi.exe"
        cmd = [nv_path, "--query-gpu=power.draw", "--format=csv,noheader,nounits"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return float(res.stdout.strip())
    except:
        pass
    return 0