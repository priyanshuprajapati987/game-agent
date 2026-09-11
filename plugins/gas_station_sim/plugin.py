from typing import Optional
import time
import random
from plugins.base_plugin import BasePlugin
from core.state_machine import State, Transition, StateType


class GasStationPlugin(BasePlugin):
    def __init__(self, config_path: str = "plugins/gas_station_sim/config.yaml"):
        super().__init__(config_path)
        self._customer_served = 0
        self._money_earned = 0

    def _setup_states(self):
        states = {
            "idle": State("idle", StateType.ACTIVE),
            "serving_customer": State("serving_customer", StateType.ACTIVE),
            "pumping_gas": State("pumping_gas", StateType.ACTIVE),
            "collecting_payment": State("collecting_payment", StateType.ACTIVE),
            "cleaning": State("cleaning", StateType.ACTIVE),
            "restocking": State("restocking", StateType.ACTIVE),
        }

        for name, state in states.items():
            self.state_machine.add_state(name, state)

        self.state_machine.set_initial_state("idle")

    def _setup_transitions(self):
        transitions = [
            Transition(
                from_state="idle",
                to_state="serving_customer",
                condition=self._has_customer,
                priority=10,
            ),
            Transition(
                from_state="serving_customer",
                to_state="pumping_gas",
                condition=self._customer_ready_to_pump,
                priority=5,
            ),
            Transition(
                from_state="pumping_gas",
                to_state="collecting_payment",
                condition=self._tank_full,
                priority=5,
            ),
            Transition(
                from_state="collecting_payment",
                to_state="idle",
                condition=self._payment_complete,
                priority=5,
            ),
        ]

        for t in transitions:
            self.state_machine.add_transition(t)

    def get_action_for_state(self, state: str) -> Optional[dict]:
        actions = {
            "idle": {"type": "wait", "duration": 0.5},
            "serving_customer": self._serve_customer_action(),
            "pumping_gas": self._pump_gas_action(),
            "collecting_payment": self._collect_payment_action(),
            "cleaning": {"type": "key", "key": "e"},
            "restocking": {"type": "wait", "duration": 1},
        }
        return actions.get(state)

    def _has_customer(self) -> bool:
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        match = self.vision.find_template(screenshot, "customer_icon")
        return match is not None

    def _customer_ready_to_pump(self) -> bool:
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        match = self.vision.find_template(screenshot, "fuel_prompt")
        return match is not None

    def _tank_full(self) -> bool:
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        match = self.vision.find_template(screenshot, "tank_full_indicator")
        return match is not None

    def _payment_complete(self) -> bool:
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        match = self.vision.find_template(screenshot, "payment_complete")
        return match is not None

    def _serve_customer_action(self) -> dict:
        screenshot = self._get_screenshot()
        if screenshot:
            match = self.vision.find_template(screenshot, "customer_icon")
            if match:
                return {"type": "click", "x": match.center_x, "y": match.center_y}
        return {"type": "wait", "duration": 0.2}

    def _pump_gas_action(self) -> dict:
        screenshot = self._get_screenshot()
        if screenshot:
            match = self.vision.find_template(screenshot, "fuel_pump_handle")
            if match:
                return {"type": "click", "x": match.center_x, "y": match.center_y}
        return {"type": "key", "key": "mouse_left"}

    def _collect_payment_action(self) -> dict:
        screenshot = self._get_screenshot()
        if screenshot:
            match = self.vision.find_template(screenshot, "cash_register")
            if match:
                self._customer_served += 1
                return {"type": "click", "x": match.center_x, "y": match.center_y}
        return {"type": "wait", "duration": 0.3}
