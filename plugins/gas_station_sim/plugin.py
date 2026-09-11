"""
Gas Station Simulator - Steam Version
Template Matching Based (No Hardcoded Coordinates)
"""

from typing import Optional
import time
import random
from plugins.base_plugin import BasePlugin
from core.state_machine import State, Transition, StateType


class GasStationPlugin(BasePlugin):
    """
    Agent dhundega ki kahan hai - coordinates nahi chahiye.
    Template matching se screen pe search karega.
    """

    def __init__(self, config_path: str = "plugins/gas_station_sim/config.yaml"):
        super().__init__(config_path)
        
        # Game stats
        self._money = 0
        self._customers_served = 0
        self._floor_dirty = False
        self._fuel_level = 100
        self._dennis_active = False
        self._pumping_progress = 0

    def _setup_states(self):
        states = {
            "idle": State("idle", StateType.ACTIVE),
            "customer_waiting": State("customer_waiting", StateType.ACTIVE),
            "pumping_gas": State("pumping_gas", StateType.ACTIVE),
            "customer_paying": State("customer_paying", StateType.ACTIVE),
            "taking_payment": State("taking_payment", StateType.ACTIVE),
            "car_repair": State("car_repair", StateType.ACTIVE),
            "fixing_car": State("fixing_car", StateType.ACTIVE),
            "floor_dirty": State("floor_dirty", StateType.ACTIVE),
            "cleaning": State("cleaning", StateType.ACTIVE),
            "dennis_here": State("dennis_here", StateType.ACTIVE),
            "chasing_dennis": State("chasing_dennis", StateType.ACTIVE),
            "delivery_truck": State("delivery_truck", StateType.ACTIVE),
            "unloading": State("unloading", StateType.ACTIVE),
            "fuel_empty": State("fuel_empty", StateType.ACTIVE),
            "ordering": State("ordering", StateType.ACTIVE),
        }
        for name, state in states.items():
            self.state_machine.add_state(name, state)
        self.state_machine.set_initial_state("idle")

    def _setup_transitions(self):
        transitions = [
            # DENNIS = HIGHEST PRIORITY
            Transition("idle", "dennis_here", self._see_dennis, 20),
            Transition("cleaning", "dennis_here", self._see_dennis, 20),
            Transition("taking_payment", "dennis_here", self._see_dennis, 20),
            
            # FUEL EMPTY
            Transition("idle", "fuel_empty", self._fuel_out, 15),
            
            # CUSTOMER AT PUMP
            Transition("idle", "customer_waiting", self._see_customer, 10),
            Transition("cleaning", "customer_waiting", self._see_customer, 10),
            
            # PUMPING DONE -> REGISTER
            Transition("pumping_gas", "customer_paying", self._pump_done, 9),
            Transition("idle", "customer_paying", self._see_at_register, 9),
            
            # CAR IN WORKSHOP
            Transition("idle", "car_repair", self._see_car_repair, 8),
            
            # DELIVERY
            Transition("idle", "delivery_truck", self._see_delivery, 7),
            
            # DIRTY FLOOR
            Transition("idle", "floor_dirty", self._see_dirty, 6),
            
            # GO BACK TO IDLE
            Transition("taking_payment", "idle", self._payment_done, 5),
            Transition("fixing_car", "idle", self._repair_done, 5),
            Transition("cleaning", "idle", self._floor_clean, 5),
            Transition("chasing_dennis", "idle", self._dennis_gone, 5),
            Transition("unloading", "idle", self._unload_done, 5),
            Transition("ordering", "idle", lambda: True, 5),
        ]
        for t in transitions:
            self.state_machine.add_transition(t)

    def get_action_for_state(self, state: str) -> Optional[dict]:
        actions = {
            "idle": self._do_idle,
            "customer_waiting": self._do_go_to_customer,
            "pumping_gas": self._do_pumping,
            "customer_paying": self._do_go_to_register,
            "taking_payment": self._do_register,
            "car_repair": self._do_go_to_workshop,
            "fixing_car": self._do_repair,
            "floor_dirty": self._do_go_clean,
            "cleaning": self._do_clean,
            "dennis_here": self._do_spot_dennis,
            "chasing_dennis": self._do_throw_trash,
            "delivery_truck": self._do_go_warehouse,
            "unloading": self._do_unload,
            "fuel_empty": self._do_go_computer,
            "ordering": self._do_order_fuel,
        }
        func = actions.get(state)
        return func() if func else None

    # ============================================
    # CONDITION CHECKERS (Template Search)
    # ============================================

    def _see_dennis(self) -> bool:
        s = self._get_screenshot()
        if s is None: return False
        if self.vision.find_template(s, "dennis"):
            self._dennis_active = True
            return True
        if self.vision.find_template(s, "graffiti"):
            self._dennis_active = True
            return True
        return False

    def _fuel_out(self) -> bool:
        return self._fuel_level < 20

    def _see_customer(self) -> bool:
        s = self._get_screenshot()
        if s is None: return False
        return self.vision.find_template(s, "customer_car") is not None

    def _pump_done(self) -> bool:
        return self._pumping_progress >= 100

    def _see_at_register(self) -> bool:
        s = self._get_screenshot()
        if s is None: return False
        return self.vision.find_template(s, "register_screen") is not None

    def _see_car_repair(self) -> bool:
        s = self._get_screenshot()
        if s is None: return False
        return self.vision.find_template(s, "car_on_ramp") is not None

    def _see_delivery(self) -> bool:
        s = self._get_screenshot()
        if s is None: return False
        return self.vision.find_template(s, "delivery_truck") is not None

    def _see_dirty(self) -> bool:
        s = self._get_screenshot()
        if s is None: return False
        return self.vision.find_template(s, "dirty_floor") is not None

    def _payment_done(self) -> bool:
        s = self._get_screenshot()
        if s is None: return False
        return self.vision.find_template(s, "receipt") is not None

    def _repair_done(self) -> bool:
        s = self._get_screenshot()
        if s is None: return False
        return self.vision.find_template(s, "car_on_ramp") is None

    def _floor_clean(self) -> bool:
        s = self._get_screenshot()
        if s is None: return False
        return self.vision.find_template(s, "dirty_floor") is None

    def _dennis_gone(self) -> bool:
        s = self._get_screenshot()
        if s is None: return True
        if self.vision.find_template(s, "dennis") is None:
            self._dennis_active = False
            return True
        return False

    def _unload_done(self) -> bool:
        s = self._get_screenshot()
        if s is None: return False
        return self.vision.find_template(s, "delivery_box") is None

    # ============================================
    # ACTION EXECUTORS (Template Search)
    # ============================================

    def _do_idle(self) -> dict:
        return {"type": "wait", "duration": 0.5}

    def _do_go_to_customer(self) -> dict:
        s = self._get_screenshot()
        if s:
            match = self.vision.find_template(s, "customer_car")
            if match:
                return {"type": "move_to", "x": match.center_x, "y": match.center_y}
        return {"type": "wait", "duration": 0.3}

    def _do_pumping(self) -> dict:
        s = self._get_screenshot()
        if s is None:
            return {"type": "wait", "duration": 0.2}

        # Step 1: Grab handle
        if self._pumping_progress == 0:
            match = self.vision.find_template(s, "pump_handle")
            if match:
                self._pumping_progress = 25
                return {"type": "click", "x": match.center_x, "y": match.center_y}

        # Step 2: Position at car
        elif self._pumping_progress == 25:
            match = self.vision.find_template(s, "customer_car")
            if match:
                self._pumping_progress = 50
                return {"type": "click", "x": match.center_x, "y": match.center_y}

        # Step 3: Hold trigger
        elif self._pumping_progress == 50:
            self._pumping_progress = 75
            return {"type": "hold", "key": "left_mouse", "duration": 0.5}

        # Step 4: Watch speed, boost if in green
        elif self._pumping_progress == 75:
            match = self.vision.find_template(s, "green_zone")
            if match:
                return {"type": "hold", "key": "left_shift", "duration": 0.2}
            self._pumping_progress = 100
            return {"type": "release", "key": "left_mouse"}

        return {"type": "wait", "duration": 0.2}

    def _do_go_to_register(self) -> dict:
        s = self._get_screenshot()
        if s:
            match = self.vision.find_template(s, "register_screen")
            if match:
                return {"type": "move_to", "x": match.center_x, "y": match.center_y}
        return {"type": "wait", "duration": 0.3}

    def _do_register(self) -> dict:
        s = self._get_screenshot()
        if s is None:
            return {"type": "wait", "duration": 0.2}

        # Scan items
        match = self.vision.find_template(s, "register_items")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}

        # Take payment
        match = self.vision.find_template(s, "total_amount")
        if match:
            return {"type": "key", "key": "e"}

        # Give receipt
        match = self.vision.find_template(s, "payment_button")
        if match:
            return {"type": "key", "key": "f"}

        return {"type": "wait", "duration": 0.3}

    def _do_go_to_workshop(self) -> dict:
        s = self._get_screenshot()
        if s:
            match = self.vision.find_template(s, "workshop")
            if match:
                return {"type": "move_to", "x": match.center_x, "y": match.center_y}
        return {"type": "wait", "duration": 0.3}

    def _do_repair(self) -> dict:
        s = self._get_screenshot()
        if s is None:
            return {"type": "wait", "duration": 0.2}

        # Activate ramp
        match = self.vision.find_template(s, "ramp_button")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}

        # Find broken part
        match = self.vision.find_template(s, "broken_part")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}

        # Paint scratches
        match = self.vision.find_template(s, "car_on_ramp")
        if match:
            return {
                "type": "drag",
                "start_x": match.x + 50,
                "start_y": match.y + 50,
                "end_x": match.x + match.width - 50,
                "end_y": match.y + match.height - 50,
                "duration": 2.0
            }

        return {"type": "wait", "duration": 0.5}

    def _do_go_clean(self) -> dict:
        s = self._get_screenshot()
        if s:
            match = self.vision.find_template(s, "broom")
            if match:
                return {"type": "click", "x": match.center_x, "y": match.center_y}
        return {"type": "wait", "duration": 0.2}

    def _do_clean(self) -> dict:
        s = self._get_screenshot()
        if s is None:
            return {"type": "wait", "duration": 0.2}

        # Empty trash
        match = self.vision.find_template(s, "trash_full")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}

        match = self.vision.find_template(s, "trash_can")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}

        # Sweep floor
        match = self.vision.find_template(s, "dirty_floor")
        if match:
            return {
                "type": "drag",
                "start_x": match.x,
                "start_y": match.y,
                "end_x": match.x + match.width,
                "end_y": match.y,
                "duration": 0.5
            }

        return {"type": "wait", "duration": 0.3}

    def _do_spot_dennis(self) -> dict:
        s = self._get_screenshot()
        if s:
            match = self.vision.find_template(s, "dennis")
            if match:
                return {"type": "move_to", "x": match.center_x, "y": match.center_y}
        return {"type": "wait", "duration": 0.2}

    def _do_throw_trash(self) -> dict:
        s = self._get_screenshot()
        if s is None:
            return {"type": "wait", "duration": 0.2}

        match = self.vision.find_template(s, "dennis")
        if match:
            # RIGHT CLICK to throw!
            return {"type": "click", "x": match.center_x, "y": match.center_y, "button": "right"}

        self._dennis_active = False
        return {"type": "wait", "duration": 0.5}

    def _do_go_warehouse(self) -> dict:
        s = self._get_screenshot()
        if s:
            match = self.vision.find_template(s, "warehouse_door")
            if match:
                return {"type": "move_to", "x": match.center_x, "y": match.center_y}
        return {"type": "wait", "duration": 0.3}

    def _do_unload(self) -> dict:
        s = self._get_screenshot()
        if s is None:
            return {"type": "wait", "duration": 0.2}

        match = self.vision.find_template(s, "warehouse_door")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}

        match = self.vision.find_template(s, "delivery_box")
        if match:
            return {"type": "key", "key": "e"}

        return {"type": "wait", "duration": 0.5}

    def _do_go_computer(self) -> dict:
        s = self._get_screenshot()
        if s:
            match = self.vision.find_template(s, "computer")
            if match:
                return {"type": "move_to", "x": match.center_x, "y": match.center_y}
        return {"type": "wait", "duration": 0.3}

    def _do_order_fuel(self) -> dict:
        s = self._get_screenshot()
        if s is None:
            return {"type": "wait", "duration": 0.2}

        match = self.vision.find_template(s, "computer")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}

        match = self.vision.find_template(s, "order_tab")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}

        return {"type": "key", "key": "e"}
