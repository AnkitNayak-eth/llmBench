import psutil  # type: ignore
import platform
import sys
import os
import subprocess
import json
import re
from .gpu import get_gpu  # type: ignore


def get_hardware():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    cpu_freq = psutil.cpu_freq()
    gpu = get_gpu()
    
    hw_info = {
        "os": f"{platform.system()} {platform.release()}",
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version.split()[0],
        
        "cpu_cores": psutil.cpu_count(),
        "cpu_physical_cores": psutil.cpu_count(logical=False),
        "cpu_usage_pct": psutil.cpu_percent(interval=0.1),
        "cpu_freq": round(cpu_freq.max, 2) if cpu_freq else 0,
        
        "ram_gb": round(mem.total / 1e9, 2),
        "ram_available_gb": round(mem.available / 1e9, 2),
        "ram_usage_pct": mem.percent,
        
        "swap_total_gb": round(swap.total / 1e9, 2),
        "swap_usage_pct": swap.percent,
        
        "gpu": gpu["gpu"],
        "vram_gb": gpu["vram_gb"],
        "gpu_driver": gpu.get("driver", "N/A"),
        "gpu_temp": gpu.get("temp", "N/A"),
        "is_nvidia": gpu.get("is_nvidia", False),
        
        "motherboard": "N/A",
        "cpu_model": platform.processor(),
        "cpu_l1_cache": "N/A",
        "cpu_l2_cache": "N/A",
        "cpu_l3_cache": "N/A",
        "cpu_max_clock": "N/A",
        "ram_speed": "N/A",
        "ram_type": "N/A",
        "ram_manufacturer": "N/A",
        "ram_part": "N/A",
        "ram_slots": "N/A",
        "storage": "N/A",
        "resolution": "N/A",
        "uptime": "N/A",
        "cpu_arch_name": "N/A",
        "gpu_arch": "N/A",
        "gpu_bus_width": "N/A",
        "gpu_vram_type": "N/A",
        "gpu_pcie": "N/A",
        "gpu_power_limit": "N/A",
        "gpu_cuda": "N/A",
        "battery": "N/A",
        "chipset": "N/A",
        "virtualization": "N/A"
    }

    if os.name == 'nt':
        try:
            ps_base = ["powershell", "-NoProfile", "-Command", 
                "Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer, Product, Chipset | ConvertTo-Json -Compress; " +
                "Get-CimInstance Win32_Processor | Select-Object Name, L1CacheSize, L2CacheSize, L3CacheSize, MaxClockSpeed, VirtualizationFirmwareEnabled, Description | ConvertTo-Json -Compress; " +
                "(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime | Select-Object Days, Hours, Minutes | ConvertTo-Json -Compress"
            ]
            res_base = subprocess.run(ps_base, capture_output=True, text=True)
            if res_base.returncode == 0 and res_base.stdout:
                outputs = res_base.stdout.strip().split("\n")
                if len(outputs) >= 1:
                    try:
                        mb = json.loads(outputs[0])
                        hw_info["motherboard"] = f"{mb.get('Manufacturer', '').strip()} {mb.get('Product', '').strip()}".strip() or "N/A"
                        hw_info["chipset"] = mb.get('Chipset', 'Unknown')
                    except: pass
                if len(outputs) >= 2:
                    try:
                        cpu = json.loads(outputs[1])
                        if isinstance(cpu, list): cpu = cpu[0]
                        hw_info["cpu_model"] = cpu.get('Name', platform.processor()).strip()
                        l1 = cpu.get('L1CacheSize', 0)
                        l2 = cpu.get('L2CacheSize', 0)
                        l3 = cpu.get('L3CacheSize', 0)
                        if l1: hw_info["cpu_l1_cache"] = f"{round(l1/1024, 1)} MB" if l1 > 2000 else f"{l1} KB"
                        if l2: hw_info["cpu_l2_cache"] = f"{round(l2/1024, 1)} MB"
                        if l3: hw_info["cpu_l3_cache"] = f"{round(l3/1024, 1)} MB"
                        hw_info["cpu_max_clock"] = f"{cpu.get('MaxClockSpeed', 0)} MHz"
                        hw_info["virtualization"] = "Enabled" if cpu.get('VirtualizationFirmwareEnabled') else "Disabled"
                        hw_info["cpu_arch_name"] = cpu.get('Description', 'Unknown')
                    except: pass
                if len(outputs) >= 3:
                    try:
                        up = json.loads(outputs[2])
                        hw_info["uptime"] = f"{up.get('Days')}d {up.get('Hours')}h {up.get('Minutes')}m"
                    except: pass

            ps_ram = ["powershell", "-NoProfile", "-Command", 
                "Get-CimInstance Win32_PhysicalMemory | Select-Object Speed, SMBIOSMemoryType, Manufacturer, PartNumber | ConvertTo-Json -Compress; " +
                "Get-CimInstance Win32_PhysicalMemoryArray | Select-Object MemoryDevices | ConvertTo-Json -Compress"
            ]
            res_ram = subprocess.run(ps_ram, capture_output=True, text=True)
            if res_ram.returncode == 0 and res_ram.stdout:
                outputs = res_ram.stdout.strip().split("\n")
                if len(outputs) >= 1:
                    data = json.loads(outputs[0])
                    types = {26: "DDR4", 30: "LPDDR4", 34: "DDR5"}
                    if isinstance(data, list):
                        hw_info["ram_speed"] = f"{max([d.get('Speed', 0) for d in data])} MHz"
                        hw_info["ram_type"] = types.get(data[0].get('SMBIOSMemoryType', 0), "Unknown")
                        hw_info["ram_manufacturer"] = data[0].get('Manufacturer', 'Unknown').strip()
                        hw_info["ram_part"] = data[0].get('PartNumber', 'Unknown').strip()
                    elif isinstance(data, dict):
                        hw_info["ram_speed"] = f"{data.get('Speed', 0)} MHz"
                        hw_info["ram_type"] = types.get(data.get('SMBIOSMemoryType', 0), "Unknown")
                        hw_info["ram_manufacturer"] = data.get('Manufacturer', 'Unknown').strip()
                        hw_info["ram_part"] = data.get('PartNumber', 'Unknown').strip()
                if len(outputs) >= 2:
                    try:
                        slot_data = json.loads(outputs[1])
                        hw_info["ram_slots"] = slot_data.get('MemoryDevices', 'N/A')
                    except: pass

            if hw_info.get("is_nvidia"):
                try:
                    nv_path = r"C:\Windows\System32\nvidia-smi.exe"
                    res_nv = subprocess.run([nv_path, "-q"], capture_output=True, text=True)
                    if res_nv.returncode == 0:
                        out = res_nv.stdout
                        bus = re.search(r"Bus Width\s+:\s+(\d+\s+bit)", out)
                        if bus: hw_info["gpu_bus_width"] = bus.group(1)
                        mem_clk = re.search(r"Memory\s+:\s+(\d+\s+MHz)", out)
                        if mem_clk: hw_info["gpu_mem_clock"] = mem_clk.group(1)
                        pwr = re.search(r"Current Power Limit\s+:\s+([\d\.]+)\s+W", out)
                        if pwr: hw_info["gpu_power_limit"] = f"{pwr.group(1)}W"
                        cuda = re.search(r"CUDA Version\s+:\s+([\d\.]+)", out)
                        if cuda: hw_info["gpu_cuda"] = cuda.group(1)
                        
                        # VRAM Type heuristic
                        if "GDDR6" in out: hw_info["gpu_vram_type"] = "GDDR6"
                        elif "GDDR5" in out: hw_info["gpu_vram_type"] = "GDDR5"
                        
                    # PCIe info via query
                    res_pcie = subprocess.run([nv_path, "--query-gpu=pcie.link.width.max,pcie.link.gen.max", "--format=csv,noheader,nounits"], capture_output=True, text=True)
                    if res_pcie.returncode == 0:
                        p = [x.strip() for x in res_pcie.stdout.split(",")]
                        if len(p) >= 2: hw_info["gpu_pcie"] = f"Gen {p[1]} x{p[0]}"
                except: pass

            ps_misc = ["powershell", "-NoProfile", "-Command", 
                "Get-PhysicalDisk | Select-Object FriendlyName, MediaType, Size | ConvertTo-Json -Compress; " +
                "Get-CimInstance Win32_VideoController | Select-Object CurrentHorizontalResolution, CurrentVerticalResolution, VideoProcessor | ConvertTo-Json -Compress; " +
                "Get-CimInstance Win32_Battery | Select-Object EstimatedChargeRemaining | ConvertTo-Json -Compress"
            ]
            res_misc = subprocess.run(ps_misc, capture_output=True, text=True)
            if res_misc.returncode == 0 and res_misc.stdout:
                outputs = res_misc.stdout.strip().split("\n")
                if len(outputs) >= 1:
                    try:
                        d = json.loads(outputs[0])
                        if isinstance(d, list): d = d[0]
                        hw_info["storage"] = f"{d.get('FriendlyName')} ({round(d.get('Size',0)/1e9)}GB {d.get('MediaType')})"
                    except: pass
                if len(outputs) >= 2:
                    try:
                        v = json.loads(outputs[1])
                        if isinstance(v, list): v = next((x for x in v if x.get('CurrentHorizontalResolution')), v[0])
                        hw_info["resolution"] = f"{v.get('CurrentHorizontalResolution')}x{v.get('CurrentVerticalResolution')}"
                        if not hw_info.get("gpu_arch") or hw_info["gpu_arch"] == "Unknown":
                            hw_info["gpu_arch"] = v.get('VideoProcessor', 'Unknown')
                    except: pass
                if len(outputs) >= 3:
                    try:
                        b = json.loads(outputs[2])
                        hw_info["battery"] = f"{b.get('EstimatedChargeRemaining')}% Charge"
                    except: pass
                    
        except Exception:
            pass

    return hw_info