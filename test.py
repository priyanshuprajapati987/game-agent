"""
Game Agent - Test Script
Run this to verify everything is working: python test.py
"""

import sys
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def test_header():
    console.print(Panel.fit("[bold cyan]Game Agent - System Test[/bold cyan]", border_style="cyan"))

def test_result(name, passed, detail=""):
    status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
    detail_str = f" ({detail})" if detail else ""
    console.print(f"  {status} {name}{detail_str}")
    return passed

def main():
    test_header()
    results = []
    
    console.print("\n[bold]1. Core Module Imports[/bold]")
    try:
        from core.capture import ScreenCapture
        from core.vision import VisionEngine
        from core.ocr import OCREngine
        from core.input_controller import InputController
        from core.window_manager import WindowManager
        from core.state_machine import StateMachine
        from core.offline_ai import OfflineAIEngine, ModelConfig
        from core.ai_agent import AIAgent, AgentRole, AgentTask
        from core.multi_agent import MultiAgentSpawner
        results.append(test_result("All core imports", True))
    except Exception as e:
        results.append(test_result("Core imports", False, str(e)))

    console.print("\n[bold]2. Plugin Imports[/bold]")
    try:
        from plugins.base_plugin import BasePlugin
        from plugins.gas_station_sim.plugin import GasStationPlugin
        from plugins.minecraft.plugin import MinecraftPlugin
        from plugins.generic.plugin import GenericPlugin
        results.append(test_result("All plugin imports", True))
    except Exception as e:
        results.append(test_result("Plugin imports", False, str(e)))

    console.print("\n[bold]3. StateMachine[/bold]")
    try:
        from core.state_machine import State, Transition, StateType
        sm = StateMachine()
        sm.add_state("idle", State("idle", StateType.ACTIVE))
        sm.add_state("working", State("working", StateType.ACTIVE))
        sm.add_transition(Transition("idle", "working", lambda: True))
        sm.set_initial_state("idle")
        sm.start()
        sm.update()
        results.append(test_result("StateMachine", sm.current_state == "working"))
    except Exception as e:
        results.append(test_result("StateMachine", False, str(e)))

    console.print("\n[bold]4. VisionEngine[/bold]")
    try:
        ve = VisionEngine(confidence_threshold=0.8)
        dummy = np.random.randint(0, 255, (540, 960, 3), dtype=np.uint8)
        brightness = ve.get_brightness(dummy)
        results.append(test_result("VisionEngine", brightness > 0))
    except Exception as e:
        results.append(test_result("VisionEngine", False, str(e)))

    console.print("\n[bold]5. OfflineAIEngine (CV-only)[/bold]")
    try:
        config = ModelConfig(name="test", backend="cv_only")
        ai = OfflineAIEngine(config=config)
        dummy = np.random.randint(0, 255, (540, 960, 3), dtype=np.uint8)
        result = ai.analyze_screen(dummy, task="Test")
        results.append(test_result("OfflineAIEngine", "action" in result))
    except Exception as e:
        results.append(test_result("OfflineAIEngine", False, str(e)))

    console.print("\n[bold]6. AIAgent[/bold]")
    try:
        config = ModelConfig(name="test", backend="cv_only")
        agent = AIAgent(agent_id="test", role=AgentRole.SCOUT, model_config=config)
        agent.memory.add_observation({"test": "data"})
        agent.memory.add_action({"type": "click"}, success=True)
        results.append(test_result("AIAgent", len(agent.memory.observations) == 1))
    except Exception as e:
        results.append(test_result("AIAgent", False, str(e)))

    console.print("\n[bold]7. MultiAgentSpawner[/bold]")
    try:
        config = ModelConfig(name="test", backend="cv_only")
        spawner = MultiAgentSpawner(model_config=config)
        ids = spawner.spawn_team({"scout": 1, "fighter": 1})
        results.append(test_result("MultiAgentSpawner", len(ids) == 2))
        spawner.stop_all()
    except Exception as e:
        results.append(test_result("MultiAgentSpawner", False, str(e)))

    console.print("\n[bold]8. WindowManager[/bold]")
    try:
        wm = WindowManager()
        windows = wm.get_all_windows()
        results.append(test_result("WindowManager", len(windows) > 0, f"{len(windows)} windows"))
    except Exception as e:
        results.append(test_result("WindowManager", False, str(e)))

    console.print("\n[bold]9. ScreenCapture[/bold]")
    try:
        sc = ScreenCapture(method="mss")
        results.append(test_result("ScreenCapture", True, "mss mode"))
    except Exception as e:
        results.append(test_result("ScreenCapture", False, str(e)))

    # Summary
    console.print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        console.print(f"[bold green]ALL TESTS PASSED ({passed}/{total})[/bold green]")
        console.print("[green]Game Agent is ready to use![/green]")
    else:
        console.print(f"[bold yellow]TESTS: {passed}/{total} passed[/bold yellow]")
    
    console.print("=" * 50)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
