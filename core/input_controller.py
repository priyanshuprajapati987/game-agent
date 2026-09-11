import random
import time
from typing import Optional, Tuple
from dataclasses import dataclass

try:
    import pydirectinput
    pydirectinput.FAILSAFE = False
    HAS_PYDIRECTINPUT = True
except ImportError:
    HAS_PYDIRECTINPUT = False

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False


@dataclass
class HumanLikeConfig:
    click_variance: int = 5
    delay_mean: float = 0.15
    delay_std: float = 0.05
    move_duration_mean: float = 0.25
    move_duration_std: float = 0.08


class InputController:
    def __init__(self, human_like: bool = True, config: Optional[HumanLikeConfig] = None):
        self.human_like = human_like
        self.config = config or HumanLikeConfig()
        self._backend = self._init_backend()

    def _init_backend(self):
        if HAS_PYDIRECTINPUT:
            return "pydirectinput"
        elif HAS_PYAUTOGUI:
            return "pyautogui"
        else:
            raise ImportError("No input library available. Install pydirectinput-rgx or pyautogui.")

    def click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        clicks: int = 1,
    ):
        if self.human_like and x is not None and y is not None:
            x += random.randint(-self.config.click_variance, self.config.click_variance)
            y += random.randint(-self.config.click_variance, self.config.click_variance)

        self._natural_delay()

        if self._backend == "pydirectinput":
            if x is not None and y is not None:
                pydirectinput.click(x, y, clicks=clicks, button=button)
            else:
                pydirectinput.click(clicks=clicks, button=button)
        else:
            if x is not None and y is not None:
                pyautogui.click(x, y, clicks=clicks, button=button)
            else:
                pyautogui.click(clicks=clicks, button=button)

    def move_to(self, x: int, y: int, duration: Optional[float] = None):
        if duration is None and self.human_like:
            duration = max(
                0.05,
                random.gauss(self.config.move_duration_mean, self.config.move_duration_std),
            )

        if self._backend == "pydirectinput":
            if duration:
                pydirectinput.moveTo(x, y, duration=duration)
            else:
                pydirectinput.moveTo(x, y)
        else:
            if duration:
                pyautogui.moveTo(x, y, duration=duration)
            else:
                pyautogui.moveTo(x, y)

    def drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: float = 0.5,
        button: str = "left",
    ):
        if self.human_like:
            start_x += random.randint(-3, 3)
            start_y += random.randint(-3, 3)
            end_x += random.randint(-3, 3)
            end_y += random.randint(-3, 3)

        self._natural_delay()

        if self._backend == "pydirectinput":
            pydirectinput.moveTo(start_x, start_y)
            pydirectinput.mouseDown(button=button)
            pydirectinput.moveTo(end_x, end_y, duration=duration)
            pydirectinput.mouseUp(button=button)
        else:
            pyautogui.moveTo(start_x, start_y)
            pyautogui.mouseDown(button=button)
            pyautogui.moveTo(end_x, end_y, duration=duration)
            pyautogui.mouseUp(button=button)

    def scroll(self, amount: int, x: Optional[int] = None, y: Optional[int] = None):
        self._natural_delay()
        if self._backend == "pydirectinput":
            pydirectinput.scroll(amount, x=x, y=y)
        else:
            pyautogui.scroll(amount, x=x, y=y)

    def key_press(self, key: str):
        self._natural_delay()
        if self._backend == "pydirectinput":
            pydirectinput.press(key)
        else:
            pyautogui.press(key)

    def key_down(self, key: str):
        if self._backend == "pydirectinput":
            pydirectinput.keyDown(key)
        else:
            pyautogui.keyDown(key)

    def key_up(self, key: str):
        if self._backend == "pydirectinput":
            pydirectinput.keyUp(key)
        else:
            pyautogui.keyUp(key)

    def hotkey(self, *keys: str):
        self._natural_delay()
        if self._backend == "pydirectinput":
            pydirectinput.hotkey(*keys)
        else:
            pyautogui.hotkey(*keys)

    def type_text(self, text: str, interval: float = 0.05):
        self._natural_delay()
        if self._backend == "pydirectinput":
            pydirectinput.typewrite(text, interval=interval)
        else:
            pyautogui.typewrite(text, interval=interval)

    def _natural_delay(self):
        if self.human_like:
            delay = max(0.01, random.gauss(self.config.delay_mean, self.config.delay_std))
            time.sleep(delay)

    def get_mouse_position(self) -> Tuple[int, int]:
        if self._backend == "pydirectinput":
            pos = pydirectinput.position()
            return (pos[0], pos[1])
        else:
            pos = pyautogui.position()
            return (pos[0], pos[1])
