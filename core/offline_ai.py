import json
import time
import base64
import subprocess
import threading
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class ModelConfig:
    name: str
    backend: str  # "ollama", "llama_cpp", "transformers", "cv_only"
    model_path: Optional[str] = None
    vision_model_path: Optional[str] = None
    device: str = "cpu"  # "cpu", "cuda", "mps"
    n_ctx: int = 2048
    n_threads: int = 4
    temperature: float = 0.7
    max_tokens: int = 500


class OfflineAIEngine:
    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig(name="default", backend="cv_only")
        self._llm = None
        self._vision_model = None
        self._ollama_available = False
        self._init_backend()

    def _init_backend(self):
        if self.config.backend == "ollama":
            self._init_ollama()
        elif self.config.backend == "llama_cpp":
            self._init_llama_cpp()
        elif self.config.backend == "transformers":
            self._init_transformers()
        else:
            print("[OfflineAI] Using CV-only mode (no LLM)")

    def _init_ollama(self):
        try:
            import requests
            resp = requests.get("http://localhost:11434/api/tags", timeout=5)
            if resp.status_code == 200:
                self._ollama_available = True
                models = resp.json().get("models", [])
                print(f"[OfflineAI] Ollama connected! Available models: {[m['name'] for m in models]}")
            else:
                print("[OfflineAI] Ollama not running. Start with: ollama serve")
                self.config.backend = "cv_only"
        except Exception:
            print("[OfflineAI] Ollama not found. Install: https://ollama.com")
            print("[OfflineAI] Falling back to CV-only mode")
            self.config.backend = "cv_only"

    def _init_llama_cpp(self):
        try:
            from llama_cpp import Llama
            if self.config.model_path and Path(self.config.model_path).exists():
                self._llm = Llama(
                    model_path=self.config.model_path,
                    n_ctx=self.config.n_ctx,
                    n_threads=self.config.n_threads,
                    verbose=False,
                )
                print(f"[OfflineAI] Loaded model: {self.config.model_path}")
            else:
                print("[OfflineAI] Model file not found!")
                self.config.backend = "cv_only"
        except ImportError:
            print("[OfflineAI] llama-cpp-python not installed. Run: pip install llama-cpp-python")
            self.config.backend = "cv_only"

    def _init_transformers(self):
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            if self.config.model_path:
                print(f"[OfflineAI] Loading transformers model: {self.config.model_path}")
                self._tokenizer = AutoTokenizer.from_pretrained(self.config.model_path)
                self._llm = AutoModelForCausalLM.from_pretrained(
                    self.config.model_path,
                    device_map="auto" if self.config.device != "cpu" else None,
                )
                print("[OfflineAI] Model loaded!")
            else:
                self.config.backend = "cv_only"
        except ImportError:
            print("[OfflineAI] transformers not installed. Run: pip install transformers torch")
            self.config.backend = "cv_only"

    def generate_response(self, prompt: str, image: Optional[np.ndarray] = None) -> str:
        if self.config.backend == "ollama":
            return self._ollama_generate(prompt, image)
        elif self.config.backend == "llama_cpp":
            return self._llama_cpp_generate(prompt)
        elif self.config.backend == "transformers":
            return self._transformers_generate(prompt)
        else:
            return self._cv_analyze(image) if image is not None else "{}"

    def _ollama_generate(self, prompt: str, image: Optional[np.ndarray] = None) -> str:
        try:
            import requests

            messages = [
                {
                    "role": "system",
                    "content": """You are a game AI agent. Analyze the game screen and decide the next action.
Respond ONLY with a JSON object:
{
    "analysis": "what you see",
    "intent": "what to achieve",
    "action": {"type": "click|key|hold|wait", "params": {"x": 0, "y": 0, "key": "", "duration": 0}},
    "reasoning": "why"
}"""
                },
                {"role": "user", "content": prompt}
            ]

            payload = {
                "model": self.config.name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                }
            }

            if image is not None:
                b64 = self._image_to_base64(image)
                payload["images"] = [b64]

            resp = requests.post(
                "http://localhost:11434/api/chat",
                json=payload,
                timeout=60,
            )

            if resp.status_code == 200:
                return resp.json().get("message", {}).get("content", "")
            else:
                print(f"[OfflineAI] Ollama error: {resp.status_code}")
                return ""

        except Exception as e:
            print(f"[OfflineAI] Ollama error: {e}")
            return ""

    def _llama_cpp_generate(self, prompt: str) -> str:
        try:
            output = self._llm(
                prompt,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                stop=["</s>", "\n\n"],
            )
            return output["choices"][0]["text"]
        except Exception as e:
            print(f"[OfflineAI] Llama.cpp error: {e}")
            return ""

    def _transformers_generate(self, prompt: str) -> str:
        try:
            inputs = self._tokenizer(prompt, return_tensors="pt")
            if self.config.device != "cpu":
                inputs = {k: v.to(self.config.device) for k, v in inputs.items()}

            outputs = self._llm.generate(
                **inputs,
                max_new_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                do_sample=True,
            )
            return self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            print(f"[OfflineAI] Transformers error: {e}")
            return ""

    def _cv_analyze(self, image: np.ndarray) -> str:
        analysis = {
            "analysis": "",
            "intent": "explore",
            "action": {"type": "wait", "params": {"duration": 1.0}},
            "reasoning": "CV-only mode - using visual analysis"
        }

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        brightness = np.mean(gray)

        analysis["analysis"] = f"Screen {width}x{height}, brightness: {brightness:.0f}"

        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            cx, cy = x + w // 2, y + h // 2

            aspect = w / h if h > 0 else 1

            if aspect > 3:
                elem_type = "button/bar"
            elif 0.8 < aspect < 1.2:
                elem_type = "icon/element"
            else:
                elem_type = "panel/area"

            analysis["analysis"] += f" | Found {elem_type} at ({cx},{cy}) size {w}x{h}"
            analysis["action"] = {"type": "click", "params": {"x": cx, "y": cy, "button": "left"}}
            analysis["reasoning"] = f"Detected {elem_type} via edge detection"

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_red = np.array([0, 100, 100])
        upper_red = np.array([10, 255, 255])
        red_mask = cv2.inRange(hsv, lower_red, upper_red)
        red_pixels = np.sum(red_mask > 0)

        lower_green = np.array([40, 100, 100])
        upper_green = np.array([80, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        green_pixels = np.sum(green_mask > 0)

        if red_pixels > 500:
            analysis["analysis"] += " | RED alert detected!"
            analysis["intent"] = "investigate danger"
        elif green_pixels > 500:
            analysis["analysis"] += " | GREEN indicator found"
            analysis["intent"] = "interact with element"

        center_region = gray[height//4:3*height//4, width//4:3*width//4]
        center_brightness = np.mean(center_region)

        if center_brightness > brightness + 20:
            analysis["analysis"] += " | Bright center detected"
            analysis["reasoning"] += " - bright area likely interactive"

        return json.dumps(analysis)

    def _image_to_base64(self, image: np.ndarray) -> str:
        _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return base64.b64encode(buffer).decode('utf-8')

    def analyze_screen(self, image: np.ndarray, task: str = "") -> dict:
        prompt = f"""Current task: {task if task else "Explore the game and decide what to do"}

Look at this game screenshot and tell me:
1. What do you see on the screen?
2. What should the agent do next?
3. What specific action to take (click position, key press, etc)?

Respond with JSON:"""

        response = self.generate_response(prompt, image)

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

        fallback = self._cv_analyze(image)
        return json.loads(fallback)

    def is_available(self) -> bool:
        return self.config.backend != "cv_only"

    def get_backend_info(self) -> dict:
        return {
            "backend": self.config.backend,
            "model": self.config.name,
            "available": self.is_available(),
            "device": self.config.device,
        }
