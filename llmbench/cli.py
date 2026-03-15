from rich.console import Console  # type: ignore
from rich.table import Table  # type: ignore
import rich  # type: ignore
import rich.box
from rich.panel import Panel  # type: ignore
from rich.prompt import Prompt, Confirm  # type: ignore

from .banner import show_banner  # type: ignore
from .preflight import show_instructions  # type: ignore
from .hardware import get_hardware  # type: ignore
from .detect import detect_models, ping_ollama  # type: ignore
from .recommend import recommend_models  # type: ignore
from .benchmark import run_benchmark  # type: ignore
from .report import save_report, show_results, show_comparisons  # type: ignore

console = Console()

def start():
    """Main entry point for the benchmark"""

    show_banner()
    show_instructions()

    console.print("\n")
    mode_panel = Panel(
        "1. [bright_green]Hardware Analysis & Recommendations[/bright_green]\n"
        "2. [bright_green]Full Performance Benchmark & Global Mapping[/bright_green]",
        title="[bold]Select Operation Mode[/bold]",
        expand=False
    )
    console.print(mode_panel)
    mode = Prompt.ask("Select mode", choices=["1", "2"], default="2")

    # ------------------------------------------------
    # Scrape early if benchmark mode selected
    # ------------------------------------------------
    scraped_leaderboard = None
    llm_source = ""
    if mode == "2":
        console.print("\n[bold bright_green]Fetching latest https://arena.ai/leaderboard data...[/bold bright_green]")
        from .leaderboard import fetch_llm_leaderboard  # type: ignore
        scraped_leaderboard, llm_source = fetch_llm_leaderboard()

    # ------------------------------------------------
    # Hardware Detection
    # ------------------------------------------------

    hardware = get_hardware()

    # Create Professional Hardware Table
    hw_table = Table(title="[bold bright_cyan]ADVANCED SYSTEM HARDWARE INTELLIGENCE[/bold bright_cyan]", box=rich.box.DOUBLE_EDGE, expand=True)
    hw_table.add_column("Category", style="cyan", width=20)
    hw_table.add_column("Details", style="white")

    # Platform Info
    hw_table.add_row("SYSTEM SUMMARY", f"[white]Platform:[/white] [bright_green]{hardware.get('os', 'Unknown')} (Uptime: {hardware.get('uptime', 'N/A')})[/bright_green]\n[white]Motherboard:[/white] [bright_green]{hardware.get('motherboard', 'N/A')} ({hardware.get('chipset', 'N/A')})[/bright_green]")
    
    # CPU
    cpu_details = (
        f"[white]Model:[/white] [bright_green]{hardware.get('cpu_model', 'Unknown')}[/bright_green]\n"
        f"[white]Description:[/white] [bright_green]{hardware.get('cpu_arch_name', 'N/A')}[/bright_green]\n"
        f"[white]Topology:[/white] [bright_green]{hardware.get('cpu_physical_cores', '0')} Physical / {hardware.get('cpu_cores', '0')} Logical[/bright_green]\n"
        f"[white]Frequencies:[/white] [bright_green]{hardware.get('cpu_max_clock', 'N/A')} (Max)[/bright_green]\n"
        f"[white]Cache Tier:[/white] [bright_green]L1: {hardware.get('cpu_l1_cache', 'N/A')} | L2: {hardware.get('cpu_l2_cache', 'N/A')} | L3: {hardware.get('cpu_l3_cache', 'N/A')}[/bright_green]\n"
        f"[white]Features:[/white] [bright_green]Virtualization: {hardware.get('virtualization', 'N/A')}[/bright_green]"
    )
    hw_table.add_row("CPU ARCHITECTURE", cpu_details)

    # Memory
    mem_details = (
        f"[white]Total RAM:[/white] [bright_green]{hardware.get('ram_gb', 0)} GB {hardware.get('ram_type', '')} (@ {hardware.get('ram_speed', 'N/A')})[/bright_green]\n"
        f"[white]Modules:[/white] [bright_green]{hardware.get('ram_manufacturer', 'N/A')} ({hardware.get('ram_part', 'N/A')})[/bright_green]\n"
        f"[white]Slots:[/white] [bright_green]{hardware.get('ram_slots', 'N/A')} Physical Devices[/bright_green]"
    )
    hw_table.add_row("MEMORY SUBSYSTEM", mem_details)

    # GPU
    gpu_details = (
        f"[white]Primary GPU:[/white] [bright_green]{hardware.get('gpu', 'Unknown')}[/bright_green]\n"
        f"[white]Core Arch:[/white] [bright_green]{hardware.get('gpu_arch', 'N/A')}[/bright_green]\n"
        f"[white]Video VRAM:[/white] [bright_green]{hardware.get('vram_gb', 0)} GB {hardware.get('gpu_vram_type', 'N/A')}[/bright_green]\n"
        f"[white]Interface:[/white] [bright_green]{hardware.get('gpu_pcie', 'N/A')} ({hardware.get('gpu_bus_width', 'N/A')} Bus)[/bright_green]\n"
        f"[white]Clocking:[/white] [bright_green]Core: {hardware.get('gpu_temp', 'N/A')}C | VRAM: {hardware.get('gpu_mem_clock', 'N/A')} | CUDA: {hardware.get('gpu_cuda', 'N/A')}[/bright_green]\n"
        f"[white]Thermal/TDP:[/white] [bright_green]{hardware.get('gpu_power_limit', 'N/A')} Power Cap[/bright_green]"
    )
    hw_table.add_row("GPU (GRAPHICS)", gpu_details)

    # Storage & Display
    misc_details = (
        f"[white]Disk Drive:[/white] [bright_green]{hardware.get('storage', 'N/A')}[/bright_green]\n"
        f"[white]Resolution:[/white] [bright_green]{hardware.get('resolution', 'N/A')}[/bright_green]\n"
        f"[white]Power State:[/white] [bright_green]{hardware.get('battery', 'N/A')}[/bright_green]"
    )
    hw_table.add_row("STORAGE & DISPLAY", misc_details)

    console.print(hw_table)

    # ------------------------------------------------
    # Suggestions Engine (Production Grade)
    # ------------------------------------------------
    recs = recommend_models(hardware)
    
    if recs["ollama"] or recs["hf"]:
        console.print("\n[bold bright_green]Hardware-Optimized Model Suggestions[/bold bright_green]")
        
        # Ollama Recommendations
        if recs["ollama"]:
            ollama_table = Table(title="Ollama Registry (Ready to Run)", box=rich.box.MINIMAL, expand=True)
            ollama_table.add_column("Model Family", style="bold")
            ollama_table.add_column("Deployment Command", style="bright_green")
            for r in recs["ollama"]:
                ollama_table.add_row(r["name"], r["command"])
            console.print(ollama_table)
            
        # HF/llama.cpp Recommendations
        if recs["hf"]:
            hf_table = Table(title="HuggingFace / llama.cpp (GGUF Optimized)", box=rich.box.MINIMAL, expand=True)
            hf_table.add_column("Model Name", style="bold")
            hf_table.add_column("HuggingFace GGUF Link", style="dim")
            for r in recs["hf"]:
                hf_table.add_row(r["name"], r["link"])
            console.print(hf_table)

    if mode == "1":
        console.print("\n[bold bright_green]Hardware profiling sequence complete.[/bold bright_green]")
        return

    # ------------------------------------------------
    # LLM Benchmark Path
    # ------------------------------------------------
    from .detect import find_binary, ping_llama_cpp  # type: ignore

    is_ollama_running = ping_ollama()
    is_lcpp_running = ping_llama_cpp()
    
    models = detect_models()
    
    if not models:
        console.print("\n[yellow]No active LLM runtime (Ollama/llama.cpp) detected.[/yellow]")
        
        ollama_bin = find_binary("ollama")
        if ollama_bin:
            if Confirm.ask(f"Found local Ollama binary. Attempt to start service?"):
                import subprocess
                subprocess.Popen([ollama_bin, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                console.print("[green]Ollama service initiated. Please restart the benchmark after model loading.[/green]")
                return
        
        console.print("\nPlease start your LLM server to proceed with the performance benchmark.\n")
        return

    console.print("\n[bold bright_green]Detected Runtimes[/bold bright_green]")
    model_table = Table(box=rich.box.MINIMAL_DOUBLE_HEAD)
    model_table.add_column("ID", justify="right")
    model_table.add_column("Provider")
    model_table.add_column("Model Alias")
    
    for i, m in enumerate(models):
        source = "Ollama" if m.startswith("Ollama: ") else "llama.cpp"
        clean_name = m.replace("Ollama: ", "").replace("llama.cpp: ", "")
        model_table.add_row(str(i + 1), source, clean_name)
    console.print(model_table)
    
    choices = [str(i+1) for i in range(len(models))]
    idx_str = Prompt.ask("\nSelect target Model ID", choices=choices, default="1" if models else None)
    idx = int(idx_str) - 1
    model = models[idx]

    console.print(f"\n[bold bright_green]Executing performance stress-test on {model}...[/bold bright_green]\n")
    perf = run_benchmark(model)

    report = {
        "hardware": hardware,
        "model": model,
        "performance": perf,
        "evaluation": {}, 
    }

    # ------------------------------------------------
    # Save & Display
    # ------------------------------------------------

    save_report(report)
    show_results(report, all_models=scraped_leaderboard, show_hardware=False)
    show_comparisons(report, all_models_raw=scraped_leaderboard)

    console.print("\n[bold bright_green]Benchmark sequence finalized. View reports/ for historical data.[/bold bright_green]")


if __name__ == "__main__":
    start()