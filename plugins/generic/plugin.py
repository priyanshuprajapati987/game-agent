from typing import Optional
from ..base_plugin import BasePlugin
from ...core.state_machine import State, Transition, StateType


class GenericPlugin(BasePlugin):
    def __init__(self, config_path: str = "plugins/generic/config.yaml"):
        super().__init__(config_path)

    def _setup_states(self):
        states = {
            "idle": State("idle", StateType.ACTIVE),
            "playing": State("playing", StateType.ACTIVE),
            "paused": State("paused", StateType.ACTIVE),
            "menu": State("menu", StateType.ACTIVE),
            "game_over": State("game_over", StateType.TERMINAL),
        }

        for name, state in states.items():
            self.state_machine.add_state(name, state)

        self.state_machine.set_initial_state("idle")

    def _setup_transitions(self):
        transitions = [
            Transition(
                from_state="idle",
                to_state="menu",
                condition=self._in_menu,
                priority=10,
            ),
            Transition(
                from_state="menu",
                to_state="playing",
                condition=self._in_game,
                priority=5,
            ),
            Transition(
                from_state="playing",
                to_state="paused",
                condition=self._is_paused,
                priority=8,
            ),
            Transition(
                from_state="paused",
                to_state="playing",
                condition=lambda: not self._is_paused(),
                priority=5,
            ),
            Transition(
                from_state="playing",
                to_state="game_over",
                condition=self._is_game_over,
                priority=20,
            ),
        ]

        for t in transitions:
            self.state_machine.add_transition(t)

    def get_action_for_state(self, state: str) -> Optional[dict]:
        actions = {
            "idle": {"type": "wait", "duration": 1},
            "menu": self._menu_action(),
            "playing": self._playing_action(),
            "paused": self._paused_action(),
            "game_over": self._game_over_action(),
        }
        return actions.get(state)

    def _in_menu(self) -> bool:
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        return (
            self.vision.find_template(screenshot, "play_button") is not None
            or self.vision.find_template(screenshot, "start_button") is not None
        )

    def _in_game(self) -> bool:
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        return self.vision.find_template(screenshot, "game_hud") is not None

    def _is_paused(self) -> bool:
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        return self.vision.find_template(screenshot, "pause_menu") is not None

    def _is_game_over(self) -> bool:
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        return (
            self.vision.find_template(screenshot, "game_over") is not None
            or self.vision.find_template(screenshot, "you_died") is not None
        )

    def _menu_action(self) -> dict:
        screenshot = self._get_screenshot()
        if screenshot:
            match = self.vision.find_template(screenshot, "play_button")
            if not match:
                match = self.vision.find_template(screenshot, "start_button")
            if match:
                return {"type": "click", "x": match.center_x, "y": match.center_y}
        return {"type": "wait", "duration": 0.5}

    def _playing_action(self) -> dict:
        return {"type": "wait", "duration": 0.1}

    def _paused_action(self) -> dict:
        return {"type": "key", "key": "escape"}

    def _game_over_action(self) -> dict:
        screenshot = self._get_screenshot()
        if screenshot:
            match = self.vision.find_template(screenshot, "restart_button")
            if match:
                return {"type": "click", "x": match.center_x, "y": match.center_y}
        return {"type": "key", "key": "enter"}
