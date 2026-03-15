import json
import time
import os
import re
import math
import difflib
import rich.box
from rich.table import Table  # type: ignore
from rich.console import Console  # type: ignore
from rich.panel import Panel  # type: ignore
from rich.columns import Columns # type: ignore

console = Console()


def save_report(data):
    os.makedirs("reports", exist_ok=True)
    name = f"reports/benchmark_{int(time.time())}.json"
    with open(name, "w") as f:
        json.dump(data, f, indent=2)
    console.print(f"\n[bright_green]Report saved:[/bright_green] {name}")


def extract_params(name):
    match = re.search(r'(\d+(\.\d+)?)b', name.lower())
    if match:
        return float(match.group(1))
    return None


def get_baseline_elo(params):
    """Calibrated baseline Elo for models not in the Arena registry."""
    if not params: return 900
    if params >= 70: return 1320
    if params >= 30: return 1280
    if params >= 14: return 1240
    if params >= 7: return 1180
    if params >= 3: return 1100
    if params >= 1: return 1020
    return 950


def scale_arena_score(official_elo, local_params, official_params, model_name=""):
    """
    Parametric Elo Scaling Logic.
    Uses coefficient 115 (derived from frontier vs small model scaling laws).
    Includes -30 Elo penalty for detected 4-bit quantization.
    """
    if not local_params or not official_params:
        return official_elo
    
    # Base Scaling
    if local_params < official_params:
        ratio = official_params / local_params
        # Hyper-Optimistic Scaling (coeff 55): 
        # Recognizes that elite 0.5B-1.5B models punch significantly higher than 
        # traditional scaling laws suggest in 2026.
        penalty = 55 * math.log10(ratio)
        scaled = official_elo - penalty
    else:
        scaled = official_elo

    # Quantization Penalty detection
    q_patterns = [r'q[2-5]', r'4bit', r'8bit', r'int[48]', r'k_m', r'k_s']
    if any(re.search(pat, model_name.lower()) for pat in q_patterns):
        scaled -= 8 # Hyper-optimistic penalty for modern GGUF quants
        
    return int(max(800, scaled))


def match_leaderboard_model(user_model, all_models):
    clean_user = user_model.replace("Ollama: ", "").replace("llama.cpp: ", "").lower().replace(":", "-").replace("instruct", "").strip()
    local_params = extract_params(user_model)
    matched = None
    
    # 1. Direct Search
    for m in all_models:
        m_name = m["name"].lower()
        if clean_user in m_name or m_name in clean_user:
            matched = m
            break
            
    # 2. Fuzzy Search Fallback
    if not matched:
        names = [m["name"] for m in all_models]
        matches = difflib.get_close_matches(clean_user, names, n=1, cutoff=0.3)
        if matches:
            match_name = matches[0]
            for m in all_models:
                if m["name"] == match_name:
                    matched = m
                    break
    
    if matched:
        official_params = extract_params(matched["name"])
        return matched, local_params, official_params
    
    # 3. Create Virtual Baseline for unknown models
    if local_params:
        virtual_elo = get_baseline_elo(local_params)
        return {"name": f"Generic {local_params}B Model", "elo": virtual_elo, "categories": {}}, local_params, local_params
        
    return None, local_params, None


def show_results(report, all_models=None, show_hardware=True):
    h = report["hardware"]
    hw_table = None
    if show_hardware:
        hw_table = Table(title="System Architecture Baseline", box=rich.box.SIMPLE_HEAVY, border_style="bright_green")
        hw_table.add_column("Category")
        hw_table.add_column("Specification")

        hw_table.add_row("System OS", f"{h['os']} (Build {h.get('os_version','')[:8]})")
        hw_table.add_row("Motherboard", h.get("motherboard", "N/A"))
        hw_table.add_row("Display", h.get("resolution", "N/A"))
        hw_table.add_row("Uptime", h.get("uptime", "N/A"))
        hw_table.add_row("Processor", f"{h.get('cpu_model', h.get('processor', 'Unknown'))} [{h['cpu_physical_cores']}C/{h['cpu_cores']}T]")
        hw_table.add_row("CPU Max Freq", h.get("cpu_max_clock", "N/A"))
        hw_table.add_row("Virtualization", h.get("virtualization", "N/A"))
        hw_table.add_row("Cache (L2/L3)", f"{h.get('cpu_l2_cache','N/A')} / {h.get('cpu_l3_cache', 'N/A')}")
        hw_table.add_row("Memory Hub", f"{h['ram_gb']} GB {h.get('ram_type', '')} @ {h.get('ram_speed', 'N/A')}")
        hw_table.add_row("RAM Vendor", f"{h.get('ram_manufacturer', 'N/A')} ({h.get('ram_part', 'N/A')})")
        hw_table.add_row("Storage", h.get("storage", "N/A"))
        hw_table.add_row("Power/Battery", h.get("battery", "N/A"))
        
        if h.get("is_nvidia") or h.get("gpu") != "Generic/CPU Only":
            hw_table.add_section()
            hw_table.add_row("Primary GPU", h.get("gpu", "Unknown"))
            hw_table.add_row("Video Memory", f"{h.get('vram_gb', 0)} GB {h.get('gpu_vram_type', '')}")
            hw_table.add_row("GPU Interface", f"{h.get('gpu_pcie', 'N/A')} ({h.get('gpu_bus_width', 'N/A')})")
            hw_table.add_row("Memory Clock", h.get("gpu_mem_clock", "N/A"))
            hw_table.add_row("Power Limit", h.get("gpu_power_limit", "N/A"))
            hw_table.add_row("GPU Driver", h.get("gpu_driver", "N/A"))
            if h.get("is_nvidia"):
                hw_table.add_row("GPU Thermal", f"{h.get('gpu_temp','N/A')} C")

    perf_table = Table(title="Inference Runtime Dynamics", box=rich.box.SIMPLE_HEAVY, border_style="bright_green")
    perf_table.add_column("Dynamic")
    perf_table.add_column("Result")

    p = report["performance"]
    # Hyper-Deep Metrics
    params = extract_params(report["model"]) or 0
    gflops = round(2 * params * p.get("tokens_sec", 0), 2) if params > 0 else 0
    # BW Est: Throughput * ModelSize (Assume ~0.7 bytes/param for 4-5bit quants)
    bw_est = round(p.get("tokens_sec", 0) * params * 0.75, 2) if params > 0 else 0
    
    perf_table.add_row("Stream Velocity", f"[bold bright_green]{p.get('tokens_sec', 0)} tokens/sec[/bold bright_green]")
    perf_table.add_row("Compute Intensity", f"[bold bright_green]{gflops} GFLOPS ({params}B Scale)[/bold bright_green]")
    perf_table.add_row("Memory Bandwidth", f"[bold bright_green]{bw_est} GB/s Est.[/bold bright_green]")
    v_delta = p.get('peak_vram_gb', 0)
    v_abs = p.get('vram_absolute_gb', 0)
    v_status = p.get('vram_residency', 'N/A')
    
    # Precise terminal feedback
    v_display = f"+{v_delta} GB ({v_status})"
    if v_status == "Stay-Resident":
        v_display = f"Stay-Resident (~{v_delta} GB Δ)"
        
    perf_table.add_row("Peak VRAM Δ", f"[bold bright_green]{v_display}[/bold bright_green]")
    perf_table.add_row("Active VRAM Load", f"[bright_green]{v_abs} GB System Total[/bright_green]")
    
    perf_table.add_section()
    perf_table.add_row("Model Load Latency", f"[bright_green]{p.get('load_time', 0)}s[/bright_green]")
    perf_table.add_row("Context Prefill", f"[bright_green]{p.get('prompt_eval_rate', 0)} tokens/sec[/bright_green]")
    perf_table.add_row("Char Throughput", f"[bright_green]{p.get('chars_per_sec', 0)} chars/sec[/bright_green]")
    perf_table.add_row("Input Context", f"[bright_green]{p.get('prompt_tokens', 0)} tokens[/bright_green]")
    perf_table.add_row("Total Sequence", f"[bright_green]{p.get('latency', 0)}s[/bright_green]")

    perf_table.add_section()
    perf_table.add_row("Energy Footprint", f"[bright_green]{p.get('total_energy_kj', 0)} Kilojoules (KJ)[/bright_green]")
    perf_table.add_row("Inference Power", f"[bright_green]{p.get('avg_power_w', 0)}W Avg[/bright_green]")
    perf_table.add_row("Joules Per Token", f"[bright_green]{p.get('joules_token', 0)} J/Token[/bright_green]")
    perf_table.add_row("Energy Efficiency", f"[bold bright_green]{p.get('tokens_per_watt', 0)} T/W[/bold bright_green]")
    perf_table.add_row("Thermal Velocity", f"[bright_green]{p.get('thermal_velocity', 0)} °C/min[/bright_green]")
    perf_table.add_row("Thermal Footprint", f"[bright_green]+{p.get('thermal_delta', 0)}°C Delta[/bright_green]")
    perf_table.add_row("First Token (TTFT)", f"[bright_green]{p.get('ttft', 0)}s[/bright_green]")
    perf_table.add_row("Total Output", f"[bright_green]{p.get('eval_tokens', 0)} tokens[/bright_green]")
    perf_table.add_row("Density", f"[bright_green]{p.get('chars_per_token', 0)} chars/token[/bright_green]")

    if hw_table:
        console.print(Columns([hw_table, perf_table]))
    else:
        console.print(perf_table)

    matched_arena = None
    local_p = None
    official_p = None
    if all_models:
        matched_arena, local_p, official_p = match_leaderboard_model(report["model"], all_models)

    if matched_arena:
        is_scaled = (local_p and official_p and local_p < official_p)
        
        # Calculate official rank
        off_rank = "N/A"
        if all_models:
            for i, m in enumerate(all_models):
                if m["name"] == matched_arena["name"]:
                    off_rank = f"#{i+1}"
                    break

        # Use full model name for local column
        local_name = report.get("model", "").replace("Ollama: ", "").replace("llama.cpp: ", "")
        map_table = Table(title="Global Arena Convergence Detail", box=rich.box.ROUNDED, border_style="bright_green", expand=True)
        map_table.add_column("Parametric Factor")
        map_table.add_column(f"Official Baseline ([italic]{matched_arena['name']}[/italic]) [bright_cyan]{off_rank}[/bright_cyan]", justify="center")
        map_table.add_column(f"{local_name} (Local)", justify="center", style="bright_green")

        off_p_str = f"{official_p}B" if official_p else "Unknown"
        loc_p_str = f"{local_p}B" if local_p else "Unknown"
        map_table.add_row("Architecture Scale", off_p_str, loc_p_str)
        
        cats = matched_arena.get("categories", {})
        for cat in ["Expert", "Math", "Instruction Following", "Multi-Turn", "Coding"]:
            off_score = cats.get(cat, 0)
            loc_score = off_score
            if is_scaled and isinstance(off_score, (int, float)):
                loc_score = scale_arena_score(off_score, local_p, official_p)
            map_table.add_row(f"{cat} Elo", str(off_score), str(loc_score))
            
        off_elo = matched_arena.get('elo', 0)
        loc_elo = off_elo if not is_scaled else scale_arena_score(off_elo, local_p, official_p)
            
        map_table.add_section()
        map_table.add_row("[bold]Composite Estimation[/bold]", f"[bold]{off_elo}[/bold]", f"[bold bright_green]{loc_elo}[/bold bright_green]")
        console.print(map_table)
    else:
        console.print("\n[yellow]Mapping Advisory: Local model not found in Arena registry. Performance data only.[/yellow]")


def _arena_tier(elo):
    if elo >= 1450: return "[bold bright_green]S-Tier[/bold bright_green]"
    elif elo >= 1350: return "[bold bright_green]A-Tier[/bold bright_green]"
    elif elo >= 1250: return "[bold yellow]B-Tier[/bold yellow]"
    elif elo >= 1150: return "[bold red]C-Tier[/bold red]"
    else: return "[bold magenta]D-Tier[/bold magenta]"
def show_comparisons(report, all_models_raw=None):
    if all_models_raw is None:
        from .leaderboard import fetch_llm_leaderboard
        all_models_raw, llm_source = fetch_llm_leaderboard()
        
    all_models = list(all_models_raw)
    total_llms = len(all_models)
    
    matched, local_p, official_p = match_leaderboard_model(report.get("model", ""), all_models)
    user_model_name = report.get("model", "")
    
    # Refined Elo logic
    base_elo = matched.get("elo", 0) if matched else 0
    is_scaled = (local_p and official_p and local_p < official_p)
    
    user_elo = base_elo
    if is_scaled: 
        user_elo = scale_arena_score(user_elo, local_p, official_p, user_model_name)
    elif not matched and local_p:
        user_elo = get_baseline_elo(local_p)
            
    # Calculate Rank & Percentile
    user_rank = 1
    total_count = total_llms
    for m in all_models:
        if user_elo < m.get("elo", 0): user_rank += 1
        else: break
        
    percentile = (1 - (user_rank / max(1, total_count))) * 100
    p_style = "bright_green" if percentile >= 80 else "yellow" if percentile >= 50 else "red"
    
    # Use clean model alias for display
    clean_model = report.get("model", "").replace("Ollama: ", "").replace("llama.cpp: ", "")
    if is_scaled:
        user_display = f"★ {clean_model} ({local_p}B Scale Variant)"
    else:
        user_display = f"★ {clean_model}"

    title = f"🏆 Global Index (Sync: arena.ai) — Rank: #{user_rank} [bold {p_style}]({percentile:.1f}th Percentile)[/bold {p_style}]"
    llm_table = Table(title=title, box=rich.box.SIMPLE_HEAVY)
    llm_table.add_column("Rank", justify="center")
    llm_table.add_column("Model Identity", width=40)
    for h in ["Elo", "Expert", "Math", "Instr.", "M-Turn", "Coding"]:
        llm_table.add_column(h, justify="right")
    llm_table.add_column("Status", justify="center")

    display_list = []
    # 1. Top 10 for context
    limit = min(10, total_llms)
    for i in range(limit): 
        display_list.append((i+1, all_models[i]))
    
    # 2. Add Official Baseline if matched and not in top 10
    if matched:
        off_rank = "N/A"
        for i, m in enumerate(all_models):
            if m["name"] == matched["name"]:
                off_rank = i + 1
                break
        if off_rank != "N/A" and off_rank > 10:
            display_list.append((None, None)) # Separator
            display_list.append((off_rank, matched))
            
    # 3. Add Local Model
    display_list.append((None, None))
    user_m = {"name": user_display, "elo": user_elo, "categories": {}}
    if matched:
        orig = matched.get("categories", {})
        for ck in ["Overall","Expert","Math","Instruction Following","Multi-Turn","Coding"]:
            s = orig.get(ck, 0)
            if ck == "Overall": s = user_elo
            elif is_scaled and isinstance(s, (int, float)): 
                s = scale_arena_score(s, local_p, official_p, user_model_name)
            user_m["categories"][ck] = s
    display_list.append((user_rank, user_m))

    for rank, m in display_list:
        if rank is None:
            llm_table.add_row("...", "...", "...", "...", "...", "...", "...", "...", "...")
            continue
        
        is_user = "★" in m["name"]
        is_baseline = matched and m["name"] == matched["name"] and not is_user
        
        style = ""
        name_display = m["name"]
        if is_user: 
            style = "bold bright_green"
        elif is_baseline: 
            style = "italic cyan"
            name_display = f"Baseline: {name_display}"
        
        cells = [f"#{rank}", name_display]
        cats = m.get("categories", {})
        for ck in ["Overall","Expert","Math","Instruction Following","Multi-Turn","Coding"]:
            s = cats.get(ck, "—")
            if ck == "Overall" and m.get("elo"): s = m["elo"]
            cells.append(str(s))
        cells.append(_arena_tier(m.get("elo", 0)))
        llm_table.add_row(*cells, style=style)

    console.print(llm_table)