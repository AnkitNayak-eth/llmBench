# 🚀 llmBench — Professional Hardware & LLM Analytics Suite

llmBench is a high-depth benchmarking tool designed to measure the raw performance of local LLM runtimes (Ollama, llama.cpp) while providing deep hardware intelligence. Unlike standard benchmarks, llmBench maps your local performance against the **LMSYS Chatbot Arena** global leaderboard using parameter-aware estimation.

![llmBench Banner](https://raw.githubusercontent.com/user-attachments/assets/6e22f03b-c290-4e1e-a698-c9c0f993f773)

## ✨ Core Features

### 🔍 Deep Hardware Intelligence
Go beyond simple CPU/GPU names. llmBench performs a technical deep dive:
- **CPU Architecture**: L1/L2/L3 cache hierarchies, max clock speeds, and virtualization states.
- **Memory Subsystem**: RAM type (DDR4/DDR5), speed, slot mapping, and manufacturer details (e.g., SK Hynix).
- **GPU Analytics**: VRAM type, bus width, PCIe interface (Gen 4/5), power limits (TDP), and real-time temperatures.
- **Storage & Display**: SSD/HDD identification and display resolution.

### ⚡ Advanced Performance Stress-Test
Capture the true efficiency of your model runs:
- **Tokens per Second**: Real-time stream and generation velocity.
- **Energy Efficiency**: Tokens per Watt (T/W) calculation via real-time GPU power monitoring.
- **Thermal Footprint**: Measured temperature delta (°C) across inference runs.
- **Peak VRAM Δ**: Accurate tracking of memory allocation overhead.

### 🏆 Global Arena Mapping
llmBench synchronizes with the **LMSYS Chatbot Arena** to provide:
- **Elo Approximation**: Standardized mapping of your local model against 300+ frontier models (Claude 3.5, Gemini 1.5, GPT-4o).
- **Global Percentile**: See exactly where your hardware/model combination stands in the global rankings.
- **Category Scoring**: Expert-level breakdown across Coding, Math, and Instruction Following.

## 🛠️ Requirements

- **Python 3.10+**
- **NVIDIA GPU** (for deep power/thermal metrics)
- **Ollama** or **llama.cpp** server running locally
- **Windows 10/11** (Optimized for PowerShell & WMI)

## 🚀 Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/llm-bench.git
   cd llm-bench
   ```

2. **Setup virtual environment:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the suite:**
   ```bash
   python llmbench.py
   ```

## 📊 Operations Modes

- **Mode 1: Hardware Analysis**: A comprehensive audit of your physical stack with optimized model recommendations.
- **Mode 2: Full Benchmark**: A standardized inference stress-test followed by global arena mapping and report generation.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Built for the AI Engineering community.*
