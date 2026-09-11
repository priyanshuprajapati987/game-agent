# Game Agent

Generic Game Automation Agent - kisi bhi game ko automatically khelne ke liye Python-based agent.

## Features

- **Screen Capture**: DXcam (240+ FPS) ya MSS for real-time screen capture
- **Template Matching**: OpenCV-based UI element detection
- **OCR**: Game text padhne ke liye PaddleOCR
- **Input Control**: Human-like mouse/keyboard with pydirectinput
- **State Machine**: FSM-based game logic
- **Plugin System**: Har game ke liye alag plugin
- **Emergency Stop**: Ctrl+C se agent turant ruke

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Interactive menu
python main.py

# Direct game selection
python main.py --game 1          # Gas Station Simulator
python main.py --game 2          # Minecraft
python main.py --game 3          # Generic Game

# List open windows
python main.py --list

# Specify window title
python main.py --game 1 --window "My Game"
```

## Project Structure

```
game_agent/
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── core/
│   ├── __init__.py
│   ├── capture.py             # Screen capture (DXcam/mss)
│   ├── vision.py              # Template matching + image analysis
│   ├── ocr.py                 # Text extraction (PaddleOCR)
│   ├── input_controller.py    # Mouse/keyboard control
│   ├── window_manager.py      # Game window detection
│   └── state_machine.py       # FSM engine
├── plugins/
│   ├── base_plugin.py         # Plugin base class
│   ├── gas_station_sim/       # Gas Station Simulator plugin
│   ├── minecraft/             # Minecraft plugin
│   └── generic/               # Generic game plugin
└── agents/                    # Agent strategies
```

## Adding a New Game

1. `plugins/` me naya folder banao
2. `config.yaml` banao (ROIs, states, actions define karo)
3. `templates/` folder me UI elements ke screenshots daalo
4. `plugin.py` me game logic likho
5. `main.py` me plugin register karo

## Config YAML Format

```yaml
game_name: "My Game"
window:
  title: "Game Window Title"
capture:
  method: "auto"
vision:
  confidence: 0.8
input:
  human_like: true
rois:
  health_bar: {x: 50, y: 50, w: 200, h: 30}
states:
  idle:
    next: playing
  playing:
    next: game_over
```

## Safety

- **Single-player games** ke liye safe hai
- **Multiplayer me use mat karna** (cheating detect ho sakta hai)
- Human-like delays aur random clicks anti-detection ke liye
- Emergency stop: `Ctrl+C`

## License

MIT
