# Game Agent

Generic Game Automation Agent - AI-powered agent jo kisi bhi game ko automatically khel sake. Single-player games ke liye.

## Features

- **AI-Powered**: LLM (GPT-4o) se screen samajhta hai aur decisions leta hai
- **Auto-Learn**: Agent khud se seekhta hai kya kaam karta hai, kya nahi
- **Multi-Agent**: Alag alag tasks ke liye parallel agents spawn kar sakte ho
- **Screen Capture**: DXcam (240+ FPS) real-time capture
- **Template Matching**: OpenCV-based UI element detection
- **Human-Like**: Random delays aur clicks se detection avoid hota hai
- **Emergency Stop**: Ctrl+C se sab agents ruk jayenge

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Interactive menu
python main.py

# Direct mode selection
python main.py --mode rule    # Rule-based (no AI)
python main.py --mode ai      # Single AI agent
python main.py --mode multi   # Multi-agent mode
python main.py --list         # List open windows
```

## Modes

### 1. Rule-Based Agent
Traditional state machine - predefined rules se game khelta hai. AI ki zaroorat nahi.

```bash
python main.py --mode rule
```

### 2. AI Single Agent
Ek AI agent jo screenshot leta hai, LLM se samajhta hai, aur action leta hai. Khud se seekhta hai.

```bash
python main.py --mode ai
```

**Setup API Key:**
```bash
# Option 1: Environment variable
set OPENAI_API_KEY=sk-your-key-here

# Option 2: .env file
echo OPENAI_API_KEY=sk-your-key-here > .env
```

### 3. Multi-Agent Mode
Multiple agents parallel me kaam karte hain. Har agent ka ek role hota hai:

| Role | Description |
|------|-------------|
| scout | Game explore karta hai, info gather karta hai |
| fighter | Combat situations handle karta hai |
| farmer | Resources collect karta hai |
| builder | Structures build karta hai |
| crafter | Items craft karta hai |
| explorer | Naye areas discover karta hai |

```bash
python main.py --mode multi
```

## Multi-Agent Commands

| Command | Description |
|---------|-------------|
| `status` | Sab agents ki status dikhata hai |
| `pause` | Sab agents ko pause karta hai |
| `resume` | Sab agents ko resume karta hai |
| `stop` | Sab agents ko stop karta hai |
| `Ctrl+C` | Emergency stop |

## Agent Roles & Team Example

```bash
# Team composition
Scout: 1 agent
Fighter: 2 agents
Farmer: 1 agent
Builder: 1 agent

# Total: 5 agents running parallel
```

## Project Structure

```
game_agent/
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── core/
│   ├── __init__.py
│   ├── capture.py             # Screen capture (DXcam/mss)
│   ├── vision.py              # Template matching (OpenCV)
│   ├── ocr.py                 # Text extraction (PaddleOCR)
│   ├── input_controller.py    # Mouse/keyboard control
│   ├── window_manager.py      # Game window detection
│   ├── state_machine.py       # FSM engine
│   ├── ai_agent.py            # AI-powered agent (LLM + Vision)
│   └── multi_agent.py         # Multi-agent spawner
├── plugins/
│   ├── base_plugin.py         # Plugin base class
│   ├── gas_station_sim/       # Gas Station Simulator
│   ├── minecraft/             # Minecraft
│   └── generic/               # Generic game plugin
└── agents/                    # Agent strategies
```

## How AI Agent Works

```
Screenshot → Analyze → LLM Decision → Execute Action → Learn
    ↓           ↓           ↓              ↓           ↓
  DXcam     Vision     GPT-4o         pydirect    Memory
  240fps    Engine     Response       input       Update
```

1. **Screenshot** leta hai game ki (240 FPS)
2. **Analyze** karta hai - templates, colors, UI elements
3. **LLM** ko bhejta hai with screen analysis
4. **Action** leta hai LLM se - click, key press, etc.
5. **Execute** karta hai action game me
6. **Learn** karta hai - kya successful raha, kya fail hua

## Multi-Agent Architecture

```
         ┌─────────────┐
         │   Spawner    │
         │  (Manager)   │
         └──────┬───────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│ Scout │  │Fighter│  │Farmer │
│ Agent │  │ Agent │  │ Agent │
└───┬───┘  └───┬───┘  └───┬───┘
    │           │           │
    └───────────┼───────────┘
                │
         ┌──────▼──────┐
         │  Game Window │
         │  (Shared)    │
         └─────────────┘
```

- Har agent alag role play karta hai
- Same game window share karte hain
- Parallel me kaam karte hain
- Individual memory rakhte hain

## Safety

- **Single-player games** ke liye safe
- **Multiplayer me use mat karna** (cheating)
- Human-like delays se anti-detection
- Emergency stop: `Ctrl+C`

## License

MIT
