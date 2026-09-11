import base64
import json
import time
import threading
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import cv2
import numpy as np

from .capture import ScreenCapture
from .vision import VisionEngine
from .input_controller import InputController
from .window_manager import WindowManager
from .offline_ai import OfflineAIEngine, ModelConfig


class AgentRole(Enum):
    SCOUT = "scout"
    FIGHTER = "fighter"
    FARMER = "farmer"
    BUILDER = "builder"
    CRAFTER = "crafter"
    EXPLORER = "explorer"
    MANAGER = "manager"


@dataclass
class AgentTask:
    task_id: str
    description: str
    priority: int = 5
    status: str = "pending"
    result: Any = None
    assigned_agent: Optional[str] = None


@dataclass
class AgentMemory:
    observations: list = field(default_factory=list)
    actions_taken: list = field(default_factory=list)
    successful_patterns: list = field(default_factory=list)
    failed_patterns: list = field(default_factory=list)

    def add_observation(self, observation: dict):
        self.observations.append({"timestamp": time.time(), **observation})
        if len(self.observations) > 100:
            self.observations = self.observations[-100:]

    def add_action(self, action: dict, success: bool):
        entry = {"timestamp": time.time(), "action": action, "success": success}
        self.actions_taken.append(entry)
        if success:
            self.successful_patterns.append(action)
        else:
            self.failed_patterns.append(action)
        if len(self.actions_taken) > 200:
            self.actions_taken = self.actions_taken[-200:]

    def get_context(self) -> str:
        recent = self.observations[-5:]
        recent_actions = self.actions_taken[-5:]
        return json.dumps({
            "recent_observations": recent,
            "recent_actions": recent_actions,
            "success_count": len(self.successful_patterns),
            "fail_count": len(self.failed_patterns),
        }, indent=2)


class AIAgent:
    def __init__(
        self,
        agent_id: str,
        role: AgentRole = AgentRole.SCOUT,
        model_config: Optional[ModelConfig] = None,
        capture_method: str = "auto",
        human_like: bool = True,
    ):
        self.agent_id = agent_id
        self.role = role
        self.memory = AgentMemory()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self.capture = ScreenCapture(method=capture_method)
        self.vision = VisionEngine(confidence_threshold=0.75)
        self.input = InputController(human_like=human_like)
        self.window_manager = WindowManager()

        self._game_window = None
        self._on_action_callback: Optional[Callable] = None

        if model_config is None:
            model_config = ModelConfig(name="default", backend="cv_only")
        self.ai = OfflineAIEngine(config=model_config)

    def attach_to_game(self, window_title: str) -> bool:
        self._game_window = self.window_manager.find_window(window_title)
        if self._game_window:
            self.window_manager.set_foreground(self._game_window.hwnd)
            time.sleep(0.3)
            print(f"[{self.agent_id}] Attached to: {self._game_window.title}")
            return True
        print(f"[{self.agent_id}] Game not found: {window_title}")
        return False

    def take_screenshot(self) -> Optional[np.ndarray]:
        if self._game_window:
            return self.capture.capture_window(self._game_window.hwnd)
        return self.capture.capture_full()

    def think_and_act(self, task: Optional[AgentTask] = None) -> Optional[dict]:
        screenshot = self.take_screenshot()
        if screenshot is None:
            return None

        self.memory.add_observation({
            "screen_size": f"{screenshot.shape[1]}x{screenshot.shape[0]}",
            "role": self.role.value,
        })

        task_desc = task.description if task else "Explore the game"
        result = self.ai.analyze_screen(screenshot, task=task_desc)

        success = self.execute_action(result.get("action", {}))
        self.memory.add_action(result, success)

        if self._on_action_callback:
            self._on_action_callback(self.agent_id, result, success)

        return result

    def execute_action(self, action: dict) -> bool:
        try:
            action_type = action.get("type")
            params = action.get("params", {})

            if action_type == "click":
                self.input.click(
                    x=params.get("x"),
                    y=params.get("y"),
                    button=params.get("button", "left"),
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
            elif action_type == "wait":
                time.sleep(params.get("duration", 1.0))
                return True
            elif action_type == "move":
                self.input.move_to(params["x"], params["y"])
                return True
        except Exception as e:
            print(f"[{self.agent_id}] Action error: {e}")
        return False

    def start_continuous(self, task: Optional[AgentTask] = None, interval: float = 2.0):
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            args=(task, interval),
            daemon=True,
        )
        self._thread.start()
        backend = self.ai.get_backend_info()["backend"]
        print(f"[{self.agent_id}] Started ({backend} mode, interval={interval}s)")

    def _run_loop(self, task: Optional[AgentTask], interval: float):
        while self._running:
            try:
                result = self.think_and_act(task)
                if result:
                    analysis = result.get('analysis', 'N/A')[:60]
                    action_type = result.get('action', {}).get('type', 'N/A')
                    print(f"[{self.agent_id}] {action_type}: {analysis}")
                time.sleep(interval)
            except Exception as e:
                print(f"[{self.agent_id}] Loop error: {e}")
                time.sleep(2)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print(f"[{self.agent_id}] Stopped")

    def set_callbacks(self, on_action: Optional[Callable] = None):
        self._on_action_callback = on_action

    def save_memory(self, path: str):
        import pickle
        with open(path, 'wb') as f:
            pickle.dump(self.memory, f)

    def load_memory(self, path: str):
        import pickle
        with open(path, 'rb') as f:
            self.memory = pickle.load(f)
