# Game Agent

Generic Game Automation Agent - Offline AI-powered agent jo bina API key ke kisi bhi game ko automatically khel sake.

## Features

- **Fully Offline** - Koi API key nahi chahiye, sab local run hota hai
- **Multiple Backends** - CV Only, Ollama, LLaMA.cpp, Transformers
- **AI-Powered** - Screenshot se game samajhta hai aur decisions leta hai
- **Multi-Agent** - Parallel tasks ke liye multiple agents
- **Auto-Learn** - Agent khud se seekhta hai
- **Human-Like** - Anti-detection delays aur random clicks

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
python main.py
```

## Modes

### 1. Rule-Based (No AI)
```bash
python main.py --mode rule
```

### 2. AI Single Agent
```bash
python main.py --mode ai
```

### 3. Multi-Agent
```bash
python main.py --mode multi
```

## AI Backends

| Backend | Description | Install |
|---------|-------------|---------|
| **CV Only** | Pure OpenCV (fast, no LLM) | Already installed |
| **Ollama** | Local LLM server | [ollama.com](https://ollama.com) |
| **LLaMA.cpp** | Direct .gguf model | `pip install llama-cpp-python` |
| **Transformers** | HuggingFace models | `pip install transformers torch` |

### CV Only Mode (Default)
- Koi model nahi chahiye
- Template matching + edge detection se kaam karta hai
- Fast hai but limited intelligence

### Ollama Mode (Recommended)
```bash
# Install Ollama
# Windows: https://ollama.com/download

# Start Ollama
ollama serve

# Pull a model
ollama pull llava:7b      # Vision + Language
ollama pull llama3:8b     # Language only
ollama pull mistral:7b    # Language only

# Run game agent
python main.py --mode ai
```

### LLaMA.cpp Mode
```bash
pip install llama-cpp-python

# Download .gguf model from HuggingFace
# Then run agent and provide path
```

### Transformers Mode
```bash
pip install transformers torch

# Uses any HuggingFace model
```

## Model Recommendations

| Use Case | Model | Size |
|----------|-------|------|
| Vision + Text | llava:7b | 4GB |
| Fast Text | mistral:7b | 4GB |
| Best Quality | llama3:8b | 5GB |
| Lightweight | phi3:3.8b | 2GB |
| CV Only | None | 0GB |

## Multi-Agent Team

| Role | Description |
|------|-------------|
| scout | Game explore karta hai |
| fighter | Combat handle karta hai |
| farmer | Resources collect karta hai |
| builder | Structures build karta hai |
| crafter | Items craft karta hai |
| explorer | Naye areas discover karta hai |

```bash
# Example: 3 agents team
python main.py --mode multi
# Select: scout x1, fighter x1, farmer x1
```

## Multi-Agent Commands

| Command | Description |
|---------|-------------|
| `status` | Sab agents ki status |
| `pause` | Sab agents pause |
| `resume` | Sab agents resume |
| `stop` | Sab agents stop |
| `Ctrl+C` | Emergency stop |

## Project Structure

```
game_agent/
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── core/
│   ├── __init__.py
│   ├── capture.py             # Screen capture
│   ├── vision.py              # Template matching
│   ├── ocr.py                 # Text extraction
│   ├── input_controller.py    # Mouse/keyboard
│   ├── window_manager.py      # Window detection
│   ├── state_machine.py       # FSM engine
│   ├── ai_agent.py            # AI agent
│   ├── multi_agent.py         # Multi-agent spawner
│   └── offline_ai.py          # Offline AI engine
├── plugins/
│   ├── base_plugin.py
│   ├── gas_station_sim/
│   ├── minecraft/
│   └── generic/
└── screenshots/               # Auto-saved screenshots
```

## How It Works

```
Screenshot → AI Analyze → Decide Action → Execute → Learn
   (240fps)   (Local)     (CV/LLM)     (Input)   (Memory)
```

1. **Screenshot** leta hai (DXcam 240 FPS)
2. **AI** analyze karta hai (CV Only / Ollama / LLaMA)
3. **Action** decide karta hai
4. **Execute** karta hai game me
5. **Learn** karta hai patterns

## Safety

- **Single-player games** ke liye safe
- **Multiplayer me use mat karna**
- Human-like delays se anti-detection
- Emergency stop: `Ctrl+C`

## License

MIT
