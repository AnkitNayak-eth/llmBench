# llmBench - Professional Hardware & LLM Analytics Suite

<p align="center">
  <img width="744" height="212" alt="Image" src="https://github.com/user-attachments/assets/ecf1de6c-14ae-4a12-b1b7-12382d1bab88" />
</p>

llmBench is a high-depth benchmarking tool designed to measure the raw performance of local LLM runtimes (Ollama, llama.cpp) while providing deep hardware intelligence. Unlike standard benchmarks, llmBench maps your local performance against the **LMSYS Chatbot Arena** global leaderboard using parameter-aware estimation.

![Image](https://github.com/user-attachments/assets/bb28ffe2-3740-4e97-8ebc-e4118498929d)

## Core Features

### 🔍 Deep Hardware Intelligence
Go beyond simple CPU/GPU names. llmBench performs a technical deep dive:
- **CPU Architecture**: L1/L2/L3 cache hierarchies, max clock speeds, and virtualization states.
- **Memory Subsystem**: RAM type (DDR4/DDR5), speed, slot mapping, and manufacturer details (e.g., SK Hynix).
- **GPU Analytics**: VRAM type, bus width, PCIe interface (Gen 4/5), power limits (TDP), and real-time temperatures.
- **Storage & Display**: SSD/HDD identification and display resolution.

## Operation Modes & Parametric Testing

### Mode 1: Hardware Forensic Analysis
Deep-audit of the physical stack to identify bottlenecks and provide optimized deployment recommendations.

| Category | Parameters Tested |
| :--- | :--- |
| **Processor** | Model, Topology (Cores/Threads), L1/L2/L3 Cache, Max Freq, Virtualization |
| **Memory** | Total Capacity, Type (DDR4/5), Clock Speed, Manufacturer, Part ID, Slot Count |
| **GPU/Video** | Core Name, VRAM Size & Type, Bus Width, PCIe Version, Logic/CUDA Version |
| **Thermals/Power** | GPU Idle Power, Max Power Limit (TDP), Active Thermal Reading |
| **Recommendations** | VRAM-Optimized model suggestions (Ollama & GGUF/llama.cpp) |

---

### Mode 2: LLM Performance & Global Index
Stress-testing the inference runner and mapping results to the global ecosystem.

---

## Forensic Field Dictionary

llmBench captures a high-density data stream. Here is the technical breakdown of the metrics displayed:

### Hardware Architecture
- **CPU Topology**: Distinguished count of Physical vs. Logical cores (Hyper-threading/SMT).
- **Cache Hierarchy**: Transparent L1/L2/L3 cache capacities for data-transfer bottleneck analysis.
- **Memory Hub**: Total RAM capacity, DDR generation, exact MT/s speed, and manufacturer ID.
- **GPU Interface**: Detects PCIe generation and bus width (e.g., Gen 5 x16) to verify data throughput caps.
- **VRAM Clocking**: Real-time VRAM frequency (MHz) and CUDA version detection.

### Inference Dynamics
- **Compute Intensity (GFLOPS)**: Measures the raw "thinking power" being exerted relative to the model's parameter scale.
- **Memory Bandwidth (GB/s)**: Estimated data movement speed between VRAM/RAM and the GPU/CPU cores.
- **Peak VRAM Δ**: Total memory overhead added by the model during the run (Relative).
- **Active VRAM Load**: The total, absolute system-wide VRAM usage after the model is loaded.
- **Residency Status**: Automatically detects if a model was a **"Cold Start"** (loaded off disk) or **"Stay-Resident"** (already in memory).

### Technical Latency
- **Model Load Latency**: Precise duration to move model weights from storage to active memory.
- **Context Prefill**: The speed at which the prompt is ingested before generation begins.
- **Char Throughput**: Raw character-per-second velocity for informational density.
- **TTFT (Time to First Token)**: The critical "felt latency"—how long until the first word appears.

### Efficiency & Thermals
- **Energy Footprint (KJ)**: Total energy consumed by the GPU/CPU for the specific operation.
- **Joules Per Token (J/T)**: The "Fuel Efficiency" of the model—how much energy each word costs.
- **Thermal Velocity**: The rate of temperature increase (°C/min) to detect cooling efficiency.
- **Inference Density**: Average characters per token, measuring information compression.

---

## Live Intelligence & Scraping Architecture

llmBench maintains a "zero-latency" baseline by synchronizing with the latest global research data.

### Technical Extraction Methodology
The suite utilizes a dedicated **Parallel Scraper** (`llmbench/leaderboard.py`) that performs:
- **Multi-Category Concurrency**: Uses `ThreadPoolExecutor` to simultaneously fetch 6 distinct sub-leaderboards (Coding, Math, etc.) from `arena.ai`.
- **Heuristic Regex Parsing**: Robust HTML extraction that adapts to server-rendered table changes, capturing ELO scores, error margins, and organizational metadata.
- **Smart Retries**: Built-in 429 backoff and timeout logic to ensure data availability even under high traffic.
- **Local Merging**: Aggregates multi-source data into a unified Global Index, refreshing your local baseline every time you run a benchmark.

---

## Requirements

- **Python 3.10+** (Rich, Requests, PSUtil)
- **NVIDIA GPU** & `nvidia-smi` (For power/thermal forensics)
- **Ollama** or **llama.cpp** server (Local or Remote)
- **Windows 10/11** (Optimized for deep WMI architecture detection)

## Quick Start

1. **Clone & Setup:**
   ```bash
   git clone https://github.com/your-username/llm-bench.git
   cd llm-bench
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the Suite:**
   ```bash
   python llmbench.py
   ```

## Operations Modes

- **Mode 1: Hardware Analysis**: A comprehensive audit of your physical stack with curated, optimized model recommendations for your specific VRAM/RAM profile.
- **Mode 2: Full Benchmark**: A standardized inference stress-test followed by global arena mapping and premium report generation.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Built for the high-performance AI Engineering community.*
