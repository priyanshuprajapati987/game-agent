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
    game_state_history: list = field(default_factory=list)

    def add_observation(self, observation: dict):
        self.observations.append({
            "timestamp": time.time(),
            **observation
        })
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
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        capture_method: str = "auto",
        human_like: bool = True,
    ):
        self.agent_id = agent_id
        self.role = role
        self.api_key = api_key
        self.model = model
        self.memory = AgentMemory()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self.capture = ScreenCapture(method=capture_method)
        self.vision = VisionEngine(confidence_threshold=0.75)
        self.input = InputController(human_like=human_like)
        self.window_manager = WindowManager()

        self._game_window = None
        self._screenshot_dir = Path("screenshots")
        self._screenshot_dir.mkdir(exist_ok=True)

        self._task_callback: Optional[Callable] = None
        self._on_action_callback: Optional[Callable] = None

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

    def screenshot_to_base64(self, screenshot: np.ndarray) -> str:
        _, buffer = cv2.imencode('.jpg', screenshot, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return base64.b64encode(buffer).decode('utf-8')

    def analyze_screen(self, screenshot: np.ndarray) -> dict:
        result = {
            "timestamp": time.time(),
            "screen_size": f"{screenshot.shape[1]}x{screenshot.shape[0]}",
            "brightness": float(np.mean(cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY))),
            "templates_found": [],
            "detected_colors": self._detect_dominant_colors(screenshot),
        }

        for name, template in self.vision._templates.items():
            match = self.vision.find_template(screenshot, name)
            if match:
                result["templates_found"].append({
                    "name": name,
                    "x": match.center_x,
                    "y": match.center_y,
                    "confidence": match.confidence,
                })

        return result

    def _detect_dominant_colors(self, screenshot: np.ndarray, n_colors: int = 3) -> list:
        small = cv2.resize(screenshot, (100, 100))
        pixels = small.reshape(-1, 3).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, n_colors, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
        colors = []
        for i, center in enumerate(centers):
            count = int(np.sum(labels == i))
            colors.append({
                "rgb": [int(c) for c in center],
                "hex": "#{:02x}{:02x}{:02x}".format(int(center[2]), int(center[1]), int(center[0])),
                "percentage": round(count / len(pixels) * 100, 1),
            })
        return colors

    def build_llm_prompt(self, task: Optional[AgentTask] = None) -> list:
        screenshot = self.take_screenshot()
        screen_analysis = self.analyze_screen(screenshot) if screenshot is not None else {}

        system_prompt = f"""You are an AI game agent with ID '{self.agent_id}' and role '{self.role.value}'.
You are playing a game and need to decide what action to take based on the current screen.

Your capabilities:
- Move mouse to any position
- Click left/right mouse button
- Press any keyboard key
- Hold keys for movement (WASD)
- Take screenshots to see the game

Current memory context: {self.memory.get_context()}

Respond with a JSON object containing:
{{
    "analysis": "Brief description of what you see on screen",
    "intent": "What you want to achieve",
    "action": {{
        "type": "click|key|hold|wait|move",
        "params": {{...}}
    }},
    "reasoning": "Why you chose this action"
}}

Action examples:
- {{"type": "click", "params": {{"x": 960, "y": 540, "button": "left"}}}}
- {{"type": "key", "params": {{"key": "e"}}}}
- {{"type": "hold", "params": {{"key": "w", "duration": 1.0}}}}
- {{"type": "wait", "params": {{"duration": 0.5}}}}"""

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        if task:
            messages.append({
                "role": "user",
                "content": f"Current task: {task.description}\n\nAnalyze the screen and decide the next action."
            })
        else:
            messages.append({
                "role": "user",
                "content": "Analyze the current game screen and decide the best action to take. What do you see? What should you do next?"
            })

        if screenshot is not None:
            b64_image = self.screenshot_to_base64(screenshot)
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
                    },
                    {
                        "type": "text",
                        "text": f"Screen analysis: {json.dumps(screen_analysis, indent=2)}"
                    }
                ]
            })

        return messages

    def parse_llm_response(self, response: str) -> Optional[dict]:
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            parsed = json.loads(response.strip())
            if "action" in parsed:
                return parsed
        except (json.JSONDecodeError, IndexError):
            pass
        return None

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

    def call_llm(self, messages: list) -> Optional[str]:
        try:
            import requests
        except ImportError:
            print("requests not installed. Run: pip install requests")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7,
        }

        api_urls = [
            "https://api.openai.com/v1/chat/completions",
            "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        ]

        for url in api_urls:
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
            except Exception:
                continue

        return None

    def _local_analyze(self, screenshot: np.ndarray) -> Optional[dict]:
        analysis = self.analyze_screen(screenshot)

        templates_found = analysis.get("templates_found", [])
        if templates_found:
            best = max(templates_found, key=lambda t: t["confidence"])
            return {
                "analysis": f"Found template: {best['name']}",
                "intent": f"Interact with {best['name']}",
                "action": {
                    "type": "click",
                    "params": {"x": best["x"], "y": best["y"], "button": "left"}
                },
                "reasoning": f"Template '{best['name']}' detected with {best['confidence']:.2f} confidence"
            }

        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            center_x, center_y = x + w // 2, y + h // 2
            return {
                "analysis": f"Detected UI element at ({center_x}, {center_y})",
                "intent": "Interact with detected element",
                "action": {
                    "type": "click",
                    "params": {"x": center_x, "y": center_y, "button": "left"}
                },
                "reasoning": "Edge detection found a UI element"
            }

        return None

    def think_and_act(self, task: Optional[AgentTask] = None) -> Optional[dict]:
        screenshot = self.take_screenshot()
        if screenshot is None:
            return None

        self.memory.add_observation({
            "screen_size": f"{screenshot.shape[1]}x{screenshot.shape[0]}",
            "role": self.role.value,
        })

        response = None
        if self.api_key:
            messages = self.build_llm_prompt(task)
            response = self.call_llm(messages)

        parsed = None
        if response:
            parsed = self.parse_llm_response(response)

        if not parsed:
            parsed = self._local_analyze(screenshot)

        if not parsed:
            parsed = {
                "analysis": "No clear action identified",
                "intent": "Explore the screen",
                "action": {"type": "wait", "params": {"duration": 1.0}},
                "reasoning": "Using fallback wait action"
            }

        success = self.execute_action(parsed.get("action", {}))
        self.memory.add_action(parsed, success)

        if self._on_action_callback:
            self._on_action_callback(self.agent_id, parsed, success)

        return parsed

    def start_continuous(self, task: Optional[AgentTask] = None, interval: float = 2.0):
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            args=(task, interval),
            daemon=True,
        )
        self._thread.start()
        print(f"[{self.agent_id}] Started continuous mode (interval={interval}s)")

    def _run_loop(self, task: Optional[AgentTask], interval: float):
        while self._running:
            try:
                result = self.think_and_act(task)
                if result:
                    print(f"[{self.agent_id}] {result.get('analysis', 'No analysis')}")
                time.sleep(interval)
            except Exception as e:
                print(f"[{self.agent_id}] Loop error: {e}")
                time.sleep(2)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print(f"[{self.agent_id}] Stopped")

    def set_callbacks(self, on_action: Optional[Callable] = None, on_task_complete: Optional[Callable] = None):
        self._on_action_callback = on_action
        self._task_callback = on_task_complete

    def save_memory(self, path: str):
        import pickle
        with open(path, 'wb') as f:
            pickle.dump(self.memory, f)

    def load_memory(self, path: str):
        import pickle
        with open(path, 'rb') as f:
            self.memory = pickle.load(f)
