from typing import Optional
import time
import random
from ..base_plugin import BasePlugin
from ...core.state_machine import State, Transition, StateType


class MinecraftPlugin(BasePlugin):
    def __init__(self, config_path: str = "plugins/minecraft/config.yaml"):
        super().__init__(config_path)
        self._inventory_full = False
        self._health_low = False
        self._mining = False

    def _setup_states(self):
        states = {
            "idle": State("idle", StateType.ACTIVE),
            "mining": State("mining", StateType.ACTIVE),
            "walking": State("walking", StateType.ACTIVE),
            "crafting": State("crafting", StateType.ACTIVE),
            "combat": State("combat", StateType.ACTIVE),
            "food": State("food", StateType.ACTIVE),
            "inventory_full": State("inventory_full", StateType.ACTIVE),
        }

        for name, state in states.items():
            self.state_machine.add_state(name, state)

        self.state_machine.set_initial_state("idle")

    def _setup_transitions(self):
        transitions = [
            Transition(
                from_state="idle",
                to_state="mining",
                condition=lambda: not self._inventory_full and not self._health_low,
                priority=10,
            ),
            Transition(
                from_state="mining",
                to_state="inventory_full",
                condition=lambda: self._inventory_full,
                priority=15,
            ),
            Transition(
                from_state="mining",
                to_state="combat",
                condition=self._enemy_nearby,
                priority=20,
            ),
            Transition(
                from_state="mining",
                to_state="food",
                condition=lambda: self._health_low,
                priority=18,
            ),
            Transition(
                from_state="inventory_full",
                to_state="crafting",
                condition=lambda: True,
                priority=5,
            ),
            Transition(
                from_state="combat",
                to_state="mining",
                condition=lambda: not self._enemy_nearby(),
                priority=5,
            ),
        ]

        for t in transitions:
            self.state_machine.add_transition(t)

    def get_action_for_state(self, state: str) -> Optional[dict]:
        actions = {
            "idle": {"type": "key", "key": "w"},
            "mining": self._mining_action(),
            "walking": self._walking_action(),
            "crafting": self._crafting_action(),
            "combat": self._combat_action(),
            "food": self._eat_food_action(),
            "inventory_full": self._manage_inventory_action(),
        }
        return actions.get(state)

    def _enemy_nearby(self) -> bool:
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        match = self.vision.find_template(screenshot, "enemy_indicator")
        return match is not None

    def _mining_action(self) -> dict:
        return {"type": "mouse_hold", "button": "left", "duration": 0.5}

    def _walking_action(self) -> dict:
        return {"type": "key", "key": "w"}

    def _crafting_action(self) -> dict:
        return {"type": "key", "key": "e"}

    def _combat_action(self) -> dict:
        return {"type": "click", "x": 960, "y": 540}

    def _eat_food_action(self) -> dict:
        return {"type": "key", "key": "1"}

    def _manage_inventory_action(self) -> dict:
        self._inventory_full = False
        return {"type": "key", "key": "e"}
