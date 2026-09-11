"""
Generic Game Agent - Works with ANY game
No templates needed - AI vision handles everything

Uses: LLaVA (Local AI) or Pure CV Fallback
"""

import json
import time
import threading
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import cv2
import numpy as np

from core.capture import ScreenCapture
from core.vision import VisionEngine
from core.input_controller import InputController
from core.window_manager import WindowManager
from core.offline_ai import OfflineAIEngine, ModelConfig


class AgentRole(Enum):
    EXPLORER = "explorer"
    FIGHTER = "fighter"
    FARMER = "farmer"
    BUILDER = "builder"
    CRAFTER = "crafter"
    MINER = "miner"
    HUNTER = "hunter"
    CUSTOM = "custom"


@dataclass
class GameMemory:
    """Agent yaad rakhta hai kya kiya"""
    observations: list = field(default_factory=list)
    actions: list = field(default_factory=list)
    discoveries: list = field(default_factory=list)
    mistakes: list = field(default_factory=list)
    
    def remember(self, observation: str, action: str, result: str):
        self.observations.append({"obs": observation, "time": time.time()})
        self.actions.append({"action": action, "result": result, "time": time.time()})
        
        if len(self.observations) > 50:
            self.observations = self.observations[-50:]
        if len(self.actions) > 50:
            self.actions = self.actions[-50:]
    
    def get_context(self) -> str:
        recent = self.actions[-5:]
        return "\n".join([f"- {a['action']} -> {a['result']}" for a in recent])


class GenericGameAgent:
    """
    EK AGENT JO KISI BHI GAME ME KHEL SAKTA HAI
    
    - Koi templates nahi
    - Koi coordinates nahi
    - Sirf AI vision + screenshots
    - Natural language instructions
    """
    
    def __init__(
        self,
        agent_id: str = "main_agent",
        role: AgentRole = AgentRole.EXPLORER,
        model_config: Optional[ModelConfig] = None,
    ):
        self.agent_id = agent_id
        self.role = role
        self.memory = GameMemory()
        self._running = False
        
        # Core systems
        self.capture = ScreenCapture(method="auto")
        self.input = InputController(human_like=True)
        self.window_manager = WindowManager()
        self.vision = VisionEngine(confidence_threshold=0.7)
        
        # AI Brain
        if model_config is None:
            model_config = ModelConfig(name="cv_only", backend="cv_only")
        self.ai = OfflineAIEngine(config=model_config)
        
        self._game_window = None
        self._current_task = ""
        self._on_action: Optional[Callable] = None

    def attach(self, window_title: str) -> bool:
        """Game se connect ho"""
        self._game_window = self.window_manager.find_window(window_title)
        if self._game_window:
            self.window_manager.set_foreground(self._game_window.hwnd)
            time.sleep(0.3)
            print(f"[{self.agent_id}] Connected to: {self._game_window.title}")
            return True
        print(f"[{self.agent_id}] Game not found: {window_title}")
        return False

    def screenshot(self) -> Optional[np.ndarray]:
        """Screen ka photo lo"""
        if self._game_window:
            return self.capture.capture_window(self._game_window.hwnd)
        return self.capture.capture_full()

    def think(self, task: str = "") -> dict:
        """
        SOCHO - Screenshot dekho, samjho, action decide karo
        
        Ye har frame hota hai:
        1. Screenshot lo
        2. AI ko bhejo
        3. Action wapas aao
        """
        screen = self.screenshot()
        if screen is None:
            return {"action": "wait", "reason": "no screen"}
        
        # AI se pucho
        task_to_use = task or self._current_task or "Explore and find something to do"
        result = self.ai.analyze_screen(screen, task=task_to_use)
        
        # Memory me save
        self.memory.remember(
            observation=result.get("analysis", ""),
            action=str(result.get("action", {})),
            result="pending"
        )
        
        return result

    def act(self, action: dict) -> bool:
        """KARO - Action execute karo"""
        try:
            action_type = action.get("type")
            params = action.get("params", {})
            
            if action_type == "click":
                self.input.click(
                    x=params.get("x"),
                    y=params.get("y"),
                    button=params.get("button", "left")
                )
                return True
            
            elif action_type == "key":
                self.input.key_press(params["key"])
                return True
            
            elif action_type == "hold":
                self.input.key_down(params["key"])
                time.sleep(params.get("duration", 0.5))
                self.input.key_up(params["key"])
                return True
            
            elif action_type == "move":
                self.input.move_to(params["x"], params["y"])
                return True
            
            elif action_type == "wait":
                time.sleep(params.get("duration", 1.0))
                return True
            
            elif action_type == "drag":
                self.input.drag(
                    params["start_x"], params["start_y"],
                    params["end_x"], params["end_y"],
                    duration=params.get("duration", 0.5)
                )
                return True
                
        except Exception as e:
            print(f"[{self.agent_id}] Action error: {e}")
        return False

    def run_once(self, task: str = "") -> dict:
        """Ek baar socho aur karo"""
        result = self.think(task)
        success = self.act(result.get("action", {}))
        return {"thought": result, "success": success}

    def run_continuous(self, task: str = "", interval: float = 2.0):
        """Lagatar chalte raho"""
        self._running = True
        self._current_task = task
        
        print(f"\n[{self.agent_id}] STARTED")
        print(f"[{self.agent_id}] Role: {self.role.value}")
        print(f"[{self.agent_id}] Task: {task or 'Free play'}")
        print(f"[{self.agent_id}] Press Ctrl+C to stop\n")
        
        while self._running:
            try:
                result = self.run_once(task)
                
                thought = result["thought"]
                analysis = thought.get("analysis", "N/A")[:60]
                action_type = thought.get("action", {}).get("type", "?")
                
                print(f"[{self.agent_id}] {action_type}: {analysis}")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[{self.agent_id}] Error: {e}")
                time.sleep(2)
        
        self.stop()

    def stop(self):
        self._running = False
        print(f"[{self.agent_id}] STOPPED")

    def set_task(self, task: str):
        """Naya task do"""
        self._current_task = task
        print(f"[{self.agent_id}] New task: {task}")

    def get_status(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "task": self._current_task,
            "actions_done": len(self.memory.actions),
            "running": self._running,
        }


# ============================================
# MULTI-GAME MANAGER
# ============================================

class GameSession:
    """Ek game session"""
    def __init__(self, game_name: str, window_title: str):
        self.game_name = game_name
        self.window_title = window_title
        self.agent = GenericGameAgent(agent_id=f"{game_name}_agent")
        self.connected = False
    
    def start(self, task: str = ""):
        if self.agent.attach(self.window_title):
            self.connected = True
            self.agent.run_continuous(task=task)


class MultiGameManager:
    """
    100 GAMES KHELNE KA MANAGER
    
    Example:
        manager = MultiGameManager()
        manager.add_game("Minecraft", "Minecraft")
        manager.add_game("GTA", "Grand Theft Auto")
        manager.start_all()
    """
    
    def __init__(self):
        self.games: List[GameSession] = []
        self._running = False
    
    def add_game(self, game_name: str, window_title: str, task: str = ""):
        session = GameSession(game_name, window_title)
        session._task = task
        self.games.append(session)
        print(f"Added: {game_name}")
    
    def start_all(self):
        """Sab games me agents chalu karo"""
        print(f"\nStarting {len(self.games)} game agents...\n")
        
        threads = []
        for session in self.games:
            t = threading.Thread(
                target=session.start,
                args=(session._task,),
                daemon=True
            )
            threads.append(t)
            t.start()
            time.sleep(1)
        
        print("\nAll agents running! Press Ctrl+C to stop.\n")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_all()
    
    def stop_all(self):
        for session in self.games:
            session.agent.stop()
        print("\nAll agents stopped.")


# ============================================
# QUICK START FUNCTIONS
# ============================================

def play_game(game_title: str, task: str = "", mode: str = "cv"):
    """
    Ek game khelo
    
    Usage:
        play_game("Minecraft", "Mine diamonds")
        play_game("Gas Station Simulator", "Serve customers")
        play_game("Cyberpunk 2077", "Complete the mission")
    """
    config = ModelConfig(
        name="llava:7b" if mode == "ollama" else "cv_only",
        backend="ollama" if mode == "ollama" else "cv_only"
    )
    
    agent = GenericGameAgent(model_config=config)
    
    if agent.attach(game_title):
        agent.run_continuous(task=task)
    else:
        print(f"Game not found: {game_title}")
        print("Make sure the game is running!")


def play_multiple(games: Dict[str, str], mode: str = "cv"):
    """
    Multiple games ek saath khelo
    
    Usage:
        play_multiple({
            "Minecraft": "Mine diamonds",
            "Gas Station Simulator": "Serve customers",
            "Stardew Valley": "Farm crops"
        })
    """
    manager = MultiGameManager()
    
    for game_title, task in games.items():
        manager.add_game(game_title, game_title, task)
    
    manager.start_all()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("\nGeneric Game Agent - Play ANY game!\n")
        print("Usage:")
        print('  python generic_agent.py "Game Title" "Task"')
        print('  python generic_agent.py "Minecraft" "Mine diamonds"')
        print('  python generic_agent.py "GTA V" "Drive around"')
        sys.exit(0)
    
    game = sys.argv[1]
    task = sys.argv[2] if len(sys.argv) > 2 else ""
    
    play_game(game, task)
