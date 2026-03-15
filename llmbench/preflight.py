from rich import print  # type: ignore
from rich.panel import Panel  # type: ignore
import sys

def show_instructions():

    instructions = """
[bold bright_green]Benchmarking Environment Checklist:[/bold bright_green]

1. [bold]LLM Engine:[/bold] Ensure [bright_green]Ollama[/bright_green] or [bright_green]llama.cpp[/bright_green] is active and model is loaded.
2. [bold]Memory:[/bold] For accurate results, close all RAM-intensive applications.
3. [bold]Thermal/Power:[/bold] Plug in your laptop to prevent CPU/GPU throttling.
4. [bold]Connectivity:[/bold] [bold red]Internet Required[/bold red]. llmBench synchronizes with 
   the [underline]LMSYS Chatbot Arena[/underline] leaderboard for global ranking mapping.

[italic dim]This suite runs a standardized inference stress-test to measure raw hardware speed 
and then performs 'Parameter-Aware Estimation' to map your local model against 
300+ frontier LLMs on the global leaderboard.[/italic dim]

[dim]Methodology: Real-Time Performance + Logarithmic Arena Score Approximation[/dim]
"""
    
    print(Panel(instructions, title="[bold bright_green]llmBench — Professional Edition[/bold bright_green]", border_style="bright_green", expand=False))