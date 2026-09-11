from abc import ABC, abstractmethod
from typing import Optional, Any
from pathlib import Path
import yaml
import time

from core.capture import ScreenCapture
from core.vision import VisionEngine
from core.input_controller import InputController
from core.window_manager import WindowManager
from core.state_machine import StateMachine, State, Transition, StateType


class BasePlugin(ABC):
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.game_name = self.config.get("game_name", "Unknown")

        self.capture = ScreenCapture(
            method=self.config.get("capture", {}).get("method", "auto"),
            monitor=self.config.get("capture", {}).get("monitor", 0),
        )
        self.vision = VisionEngine(
            confidence_threshold=self.config.get("vision", {}).get("confidence", 0.8)
        )
        self.input = InputController(
            human_like=self.config.get("input", {}).get("human_like", True),
        )
        self.window_manager = WindowManager()
        self.state_machine = StateMachine()

        self._game_window = None
        self._running = False
        self._loop_delay = self.config.get("loop_delay", 0.1)

        self._load_templates()
        self._setup_states()
        self._setup_transitions()

    def _load_config(self, path: str) -> dict:
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _load_templates(self):
        template_dir = Path(self.config.get("template_dir", "templates"))
        if template_dir.exists():
            self.vision.load_templates_from_dir(str(template_dir))

    @abstractmethod
    def _setup_states(self):
        pass

    @abstractmethod
    def _setup_transitions(self):
        pass

    @abstractmethod
    def get_action_for_state(self, state: str) -> Optional[dict]:
        pass

    def start(self, game_title: Optional[str] = None):
        title = game_title or self.config.get("window", {}).get("title", self.game_name)
        self._game_window = self.window_manager.find_window(title)

        if not self._game_window:
            print(f"[ERROR] Game window not found: {title}")
            return

        print(f"[INFO] Found game: {self._game_window.title}")
        self.window_manager.set_foreground(self._game_window.hwnd)
        time.sleep(0.5)

        self._running = True
        self.state_machine.start()
        self._main_loop()

    def stop(self):
        self._running = False
        self.state_machine.stop()
        print("[INFO] Agent stopped")

    def _main_loop(self):
        print(f"[INFO] Agent running - State: {self.state_machine.current_state}")
        print("[INFO] Press Ctrl+C to stop")

        while self._running:
            try:
                current = self.state_machine.update()

                if current:
                    action = self.get_action_for_state(current)
                    if action:
                        self._execute_action(action)

                time.sleep(self._loop_delay)

            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                print(f"[ERROR] {e}")
                time.sleep(1)

    def _execute_action(self, action: dict):
        action_type = action.get("type")

        if action_type == "click":
            x = action.get("x", 0)
            y = action.get("y", 0)
            if action.get("template"):
                match = self.vision.find_template(
                    self._get_screenshot(), action["template"]
                )
                if match:
                    x, y = match.center_x, match.center_y
                else:
                    return
            self.input.click(x, y)

        elif action_type == "key":
            self.input.key_press(action["key"])

        elif action_type == "wait":
            time.sleep(action.get("duration", 1))

        elif action_type == "conditional":
            if action.get("condition")():
                self._execute_action(action["then"])
            else:
                self._execute_action(action["else"])

    def _get_screenshot(self):
        if self._game_window:
            return self.capture.capture_window(self._game_window.hwnd)
        return self.capture.capture_full()

    def is_game_running(self) -> bool:
        if self._game_window:
            return self.window_manager.is_window_visible(self._game_window.hwnd)
        return False
