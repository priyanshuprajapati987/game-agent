"""
Gas Station Simulator - Steam Version Plugin
App ID: 1149620
Developer: DRAGO entertainment
Platform: PC (Steam)
"""

from typing import Optional
import time
import random
from plugins.base_plugin import BasePlugin
from core.state_machine import State, Transition, StateType


class GasStationPlugin(BasePlugin):
    """
    Gas Station Simulator automation for Steam version.
    
    Controls (Steam/PC):
    - WASD: Move
    - Left Mouse: Primary action (interact, grab, pump)
    - Right Mouse: Throw, secondary action
    - E: Confirm/interact
    - F: Cancel/give receipt
    - Tab: Tool menu
    - Left Shift: Sprint / Pump speed boost
    - Space: Jump
    
    Game Loop:
    1. Customer arrives at pump
    2. Grab pump handle, position at car
    3. Hold Left Mouse to pump
    4. Use Left Shift to speed up (careful!)
    5. Customer goes to register
    6. Scan items, take payment
    7. Keep floor clean
    8. Fix cars in workshop
    9. Deal with Dennis
    """

    def __init__(self, config_path: str = "plugins/gas_station_sim/config.yaml"):
        super().__init__(config_path)
        
        # Game stats
        self._money = 0
        self._customers_served = 0
        self._floor_dirty_level = 0
        self._fuel_level = 100
        self._popularity = 1
        
        # Current task tracking
        self._current_customer = None
        self._pumping_progress = 0
        self._pump_speed = 0
        self._register_items = []
        self._dennis_active = False
        
        # Config loaded from YAML
        self.rois = self.config.get("rois", {})
        self.controls = self.config.get("controls", {})
        self.pumping_config = self.config.get("pumping_minigame", {})

    def _setup_states(self):
        """Setup all game states"""
        states = {
            "idle": State("idle", StateType.ACTIVE),
            "customer_at_pump": State("customer_at_pump", StateType.ACTIVE),
            "pumping_gas": State("pumping_gas", StateType.ACTIVE),
            "customer_at_register": State("customer_at_register", StateType.ACTIVE),
            "at_register": State("at_register", StateType.ACTIVE),
            "car_in_workshop": State("car_in_workshop", StateType.ACTIVE),
            "fixing_car": State("fixing_car", StateType.ACTIVE),
            "floor_dirty": State("floor_dirty", StateType.ACTIVE),
            "cleaning": State("cleaning", StateType.ACTIVE),
            "dennis_active": State("dennis_active", StateType.ACTIVE),
            "dealing_dennis": State("dealing_dennis", StateType.ACTIVE),
            "delivery_arrived": State("delivery_arrived", StateType.ACTIVE),
            "receiving_delivery": State("receiving_delivery", StateType.ACTIVE),
            "fuel_low": State("fuel_low", StateType.ACTIVE),
            "ordering_fuel": State("ordering_fuel", StateType.ACTIVE),
        }

        for name, state in states.items():
            self.state_machine.add_state(name, state)

        self.state_machine.set_initial_state("idle")

    def _setup_transitions(self):
        """Setup state transitions based on game conditions"""
        transitions = [
            # ============================================
            # CRITICAL PRIORITY (20) - DENNIS
            # ============================================
            Transition(
                from_state="idle",
                to_state="dennis_active",
                condition=self._dennis_detected,
                priority=20,
            ),
            Transition(
                from_state="cleaning",
                to_state="dennis_active",
                condition=self._dennis_detected,
                priority=20,
            ),
            Transition(
                from_state="at_register",
                to_state="dennis_active",
                condition=self._dennis_detected,
                priority=20,
            ),
            
            # ============================================
            # HIGH PRIORITY (15) - FUEL LOW
            # ============================================
            Transition(
                from_state="idle",
                to_state="fuel_low",
                condition=self._fuel_is_low,
                priority=15,
            ),
            
            # ============================================
            # MEDIUM-HIGH PRIORITY (10) - CUSTOMERS
            # ============================================
            Transition(
                from_state="idle",
                to_state="customer_at_pump",
                condition=self._customer_at_pump,
                priority=10,
            ),
            Transition(
                from_state="cleaning",
                to_state="customer_at_pump",
                condition=self._customer_at_pump,
                priority=10,
            ),
            
            # ============================================
            # MEDIUM PRIORITY (9) - REGISTER
            # ============================================
            Transition(
                from_state="pumping_gas",
                to_state="customer_at_register",
                condition=self._pump_complete,
                priority=9,
            ),
            Transition(
                from_state="idle",
                to_state="customer_at_register",
                condition=self._customer_at_register,
                priority=9,
            ),
            
            # ============================================
            # MEDIUM PRIORITY (8) - WORKSHOP
            # ============================================
            Transition(
                from_state="idle",
                to_state="car_in_workshop",
                condition=self._car_in_workshop,
                priority=8,
            ),
            
            # ============================================
            # MEDIUM PRIORITY (7) - DELIVERY
            # ============================================
            Transition(
                from_state="idle",
                to_state="delivery_arrived",
                condition=self._delivery_arrived,
                priority=7,
            ),
            
            # ============================================
            # LOW-MEDIUM PRIORITY (6) - CLEANING
            # ============================================
            Transition(
                from_state="idle",
                to_state="floor_dirty",
                condition=self._floor_needs_cleaning,
                priority=6,
            ),
            
            # ============================================
            # STATE COMPLETION TRANSITIONS
            # ============================================
            Transition(
                from_state="pumping_gas",
                to_state="idle",
                condition=lambda: self._pumping_progress >= 100,
                priority=5,
            ),
            Transition(
                from_state="at_register",
                to_state="idle",
                condition=self._payment_complete,
                priority=5,
            ),
            Transition(
                from_state="fixing_car",
                to_state="idle",
                condition=self._repair_complete,
                priority=5,
            ),
            Transition(
                from_state="cleaning",
                to_state="idle",
                condition=lambda: self._floor_dirty_level < 20,
                priority=5,
            ),
            Transition(
                from_state="dealing_dennis",
                to_state="idle",
                condition=lambda: not self._dennis_active,
                priority=5,
            ),
            Transition(
                from_state="receiving_delivery",
                to_state="idle",
                condition=self._delivery_complete,
                priority=5,
            ),
            Transition(
                from_state="ordering_fuel",
                to_state="idle",
                condition=lambda: self._fuel_level > 50,
                priority=5,
            ),
        ]

        for t in transitions:
            self.state_machine.add_transition(t)

    def get_action_for_state(self, state: str) -> Optional[dict]:
        """Get action based on current state"""
        actions = {
            "idle": self._idle_action(),
            "customer_at_pump": self._approach_pump_action(),
            "pumping_gas": self._pumping_action(),
            "customer_at_register": self._approach_register_action(),
            "at_register": self._register_action(),
            "car_in_workshop": self._approach_workshop_action(),
            "fixing_car": self._workshop_action(),
            "floor_dirty": self._equip_broom_action(),
            "cleaning": self._cleaning_action(),
            "dennis_active": self._spot_dennis_action(),
            "dealing_dennis": self._dennis_action(),
            "delivery_arrived": self._go_to_warehouse_action(),
            "receiving_delivery": self._delivery_action(),
            "fuel_low": self._go_to_computer_action(),
            "ordering_fuel": self._order_fuel_action(),
        }
        return actions.get(state)

    # ============================================
    # CONDITION CHECKERS
    # ============================================

    def _customer_at_pump(self) -> bool:
        """Check if customer is waiting at gas pump"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        
        # Check for customer car
        match = self.vision.find_template(screenshot, "customer_car_1")
        if match:
            self._current_customer = {"car": match, "pump": 1}
            return True
        
        match = self.vision.find_template(screenshot, "customer_car_2")
        if match:
            self._current_customer = {"car": match, "pump": 2}
            return True
        
        # Check customer indicator icon
        match = self.vision.find_template(screenshot, "customer_indicator")
        return match is not None

    def _customer_at_register(self) -> bool:
        """Check if customer is at checkout"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        
        match = self.vision.find_template(screenshot, "register_screen")
        return match is not None

    def _pump_complete(self) -> bool:
        """Check if pumping is complete"""
        return self._pumping_progress >= 100

    def _floor_needs_cleaning(self) -> bool:
        """Check if floor is dirty"""
        return self._floor_dirty_level > 50

    def _dennis_detected(self) -> bool:
        """Check if Dennis is causing trouble"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        
        # Check for Dennis character
        match = self.vision.find_template(screenshot, "dennis_location")
        if match:
            self._dennis_active = True
            return True
        
        # Check for graffiti
        match = self.vision.find_template(screenshot, "graffiti_on_wall")
        if match:
            self._dennis_active = True
            return True
        
        return False

    def _car_in_workshop(self) -> bool:
        """Check if car needs repair"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        
        match = self.vision.find_template(screenshot, "car_on_ramp")
        return match is not None

    def _delivery_arrived(self) -> bool:
        """Check if delivery truck arrived"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        
        match = self.vision.find_template(screenshot, "delivery_truck")
        return match is not None

    def _fuel_is_low(self) -> bool:
        """Check if fuel is low"""
        return self._fuel_level < 30

    def _payment_complete(self) -> bool:
        """Check if payment was processed"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        
        # Look for receipt or completion indicator
        match = self.vision.find_template(screenshot, "receipt_button")
        return match is not None

    def _repair_complete(self) -> bool:
        """Check if car repair is complete"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        
        # Car should be gone from ramp
        match = self.vision.find_template(screenshot, "car_on_ramp")
        return match is None

    def _delivery_complete(self) -> bool:
        """Check if delivery unloading is complete"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        
        # No more boxes to unload
        match = self.vision.find_template(screenshot, "delivery_box")
        return match is None

    # ============================================
    # ACTION EXECUTORS
    # ============================================

    def _idle_action(self) -> dict:
        """Look around for tasks"""
        # Check for email notifications
        screenshot = self._get_screenshot()
        if screenshot:
            email_match = self.vision.find_template(screenshot, "email_notification")
            if email_match:
                return {"type": "click", "x": email_match.center_x, "y": email_match.center_y}
        
        return {"type": "wait", "duration": 0.5}

    def _approach_pump_action(self) -> dict:
        """Walk to customer at pump"""
        if self._current_customer:
            car = self._current_customer["car"]
            # Move towards the car
            return {
                "type": "move_to",
                "x": car.center_x,
                "y": car.center_y + 100
            }
        return {"type": "wait", "duration": 0.3}

    def _pumping_action(self) -> dict:
        """Handle gas pumping minigame"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return {"type": "wait", "duration": 0.2}
        
        # Step 1: Grab pump handle (Left Mouse)
        if self._pumping_progress == 0:
            match = self.vision.find_template(screenshot, "pump_handle")
            if match:
                self._pumping_progress = 10
                return {"type": "click", "x": match.center_x, "y": match.center_y}
        
        # Step 2: Position nozzle at car fuel tank
        elif self._pumping_progress == 10:
            if self._current_customer:
                car = self._current_customer["car"]
                self._pumping_progress = 20
                # Click near fuel tank (offset from car center)
                return {
                    "type": "click", 
                    "x": car.center_x + 50, 
                    "y": car.center_y + 100
                }
        
        # Step 3: Start pumping - hold Left Mouse
        elif self._pumping_progress == 20:
            self._pumping_progress = 30
            return {"type": "hold", "key": "left_mouse", "duration": 0.5}
        
        # Step 4: Monitor speed needle
        elif self._pumping_progress == 30:
            match = self.vision.find_template(screenshot, "pumping_speed_meter")
            if match:
                # Check if needle is in green zone
                green_zone = self.rois.get("green_zone", {})
                if green_zone:
                    in_green = self.vision.check_region_color(
                        screenshot,
                        (green_zone["x"], green_zone["y"], green_zone["w"], green_zone["h"]),
                        target_color=(0, 200, 0),
                        tolerance=50,
                    )
                    
                    if in_green:
                        # In green zone - safe to speed up
                        return {"type": "hold", "key": "left_shift", "duration": 0.2}
                    else:
                        # Not in green - release and wait
                        self._pumping_progress = 40
                        return {"type": "wait", "duration": 0.3}
            
            # Default: keep pumping
            return {"type": "hold", "key": "left_mouse", "duration": 0.1}
        
        # Step 5: Check if tank is full
        elif self._pumping_progress == 40:
            match = self.vision.find_template(screenshot, "fuel_gauge_car")
            if match:
                # Tank full - release and finish
                self._pumping_progress = 100
                self._customers_served += 1
                return {"type": "release", "key": "left_mouse"}
        
        return {"type": "wait", "duration": 0.2}

    def _approach_register_action(self) -> dict:
        """Walk to register"""
        screenshot = self._get_screenshot()
        if screenshot:
            match = self.vision.find_template(screenshot, "register_screen")
            if match:
                return {"type": "move_to", "x": match.center_x, "y": match.center_y}
        return {"type": "wait", "duration": 0.3}

    def _register_action(self) -> dict:
        """Handle checkout/register"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return {"type": "wait", "duration": 0.2}
        
        # Scan items (Left Click on register screen)
        match = self.vision.find_template(screenshot, "register_items")
        if match:
            return {
                "type": "click",
                "x": match.center_x + random.randint(-20, 20),
                "y": match.center_y + random.randint(-20, 20)
            }
        
        # Check for total - take payment (E key)
        match = self.vision.find_template(screenshot, "register_total")
        if match:
            return {"type": "key", "key": "e"}
        
        # Give receipt (F key)
        match = self.vision.find_template(screenshot, "receipt_button")
        if match:
            return {"type": "key", "key": "f"}
        
        return {"type": "wait", "duration": 0.3}

    def _approach_workshop_action(self) -> dict:
        """Walk to workshop"""
        screenshot = self._get_screenshot()
        if screenshot:
            match = self.vision.find_template(screenshot, "workshop_area")
            if match:
                return {"type": "move_to", "x": match.center_x, "y": match.center_y}
        return {"type": "wait", "duration": 0.3}

    def _workshop_action(self) -> dict:
        """Handle car repairs"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return {"type": "wait", "duration": 0.2}
        
        # Activate ramp (Left Click)
        match = self.vision.find_template(screenshot, "ramp_button")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}
        
        # Look for broken parts (red outline)
        match = self.vision.find_template(screenshot, "broken_part_highlight")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}
        
        # Paint scratches (drag motion)
        match = self.vision.find_template(screenshot, "car_on_ramp")
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

    def _equip_broom_action(self) -> dict:
        """Equip the broom"""
        screenshot = self._get_screenshot()
        if screenshot:
            match = self.vision.find_template(screenshot, "broom_location")
            if match:
                return {"type": "click", "x": match.center_x, "y": match.center_y}
        return {"type": "wait", "duration": 0.2}

    def _cleaning_action(self) -> dict:
        """Handle cleaning tasks"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return {"type": "wait", "duration": 0.2}
        
        # Check for full trash cans first
        match = self.vision.find_template(screenshot, "trash_can_1")
        if match:
            self._floor_dirty_level = max(0, self._floor_dirty_level - 30)
            return {"type": "click", "x": match.center_x, "y": match.center_y}
        
        match = self.vision.find_template(screenshot, "trash_can_2")
        if match:
            self._floor_dirty_level = max(0, self._floor_dirty_level - 30)
            return {"type": "click", "x": match.center_x, "y": match.center_y}
        
        # Sweep the floor (drag motion)
        for area in self.rois.get("floor_dirt_areas", []):
            match = self.vision.find_template(screenshot, "floor_dirt_areas")
            if match:
                self._floor_dirty_level = max(0, self._floor_dirty_level - 10)
                return {
                    "type": "drag",
                    "start_x": area["x"],
                    "start_y": area["y"],
                    "end_x": area["x"] + area["w"],
                    "end_y": area["y"],
                    "duration": 0.5
                }
        
        # Floor is clean
        self._floor_dirty_level = 0
        return {"type": "wait", "duration": 0.5}

    def _spot_dennis_action(self) -> dict:
        """Look for Dennis"""
        screenshot = self._get_screenshot()
        if screenshot:
            match = self.vision.find_template(screenshot, "dennis_location")
            if match:
                return {"type": "move_to", "x": match.center_x, "y": match.center_y}
        return {"type": "wait", "duration": 0.2}

    def _dennis_action(self) -> dict:
        """Chase away Dennis - throw trash at him!"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return {"type": "wait", "duration": 0.2}
        
        # Find Dennis
        match = self.vision.find_template(screenshot, "dennis_location")
        if match:
            # Right-click to throw trash at him
            return {
                "type": "click",
                "x": match.center_x,
                "y": match.center_y,
                "button": "right"
            }
        
        # Dennis gone
        self._dennis_active = False
        return {"type": "wait", "duration": 0.5}

    def _go_to_warehouse_action(self) -> dict:
        """Walk to warehouse"""
        screenshot = self._get_screenshot()
        if screenshot:
            match = self.vision.find_template(screenshot, "warehouse_door")
            if match:
                return {"type": "move_to", "x": match.center_x, "y": match.center_y}
        return {"type": "wait", "duration": 0.3}

    def _delivery_action(self) -> dict:
        """Handle delivery truck"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return {"type": "wait", "duration": 0.2}
        
        # Open warehouse door (Left Click)
        match = self.vision.find_template(screenshot, "warehouse_door")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}
        
        # Unload boxes (E key)
        match = self.vision.find_template(screenshot, "delivery_box")
        if match:
            return {"type": "key", "key": "e"}
        
        return {"type": "wait", "duration": 0.5}

    def _go_to_computer_action(self) -> dict:
        """Walk to management computer"""
        screenshot = self._get_screenshot()
        if screenshot:
            match = self.vision.find_template(screenshot, "computer_desk")
            if match:
                return {"type": "move_to", "x": match.center_x, "y": match.center_y}
        return {"type": "wait", "duration": 0.3}

    def _order_fuel_action(self) -> dict:
        """Use computer to order fuel"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return {"type": "wait", "duration": 0.2}
        
        # Click on computer screen
        match = self.vision.find_template(screenshot, "computer_screen")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}
        
        # Click order tab
        match = self.vision.find_template(screenshot, "order_tab")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}
        
        return {"type": "key", "key": "e"}

    # ============================================
    # HELPER METHODS
    # ============================================

    def is_station_open(self) -> bool:
        """Check if station is open"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return True
        
        match = self.vision.find_template(screenshot, "open_close_sign")
        return match is not None

    def toggle_station(self):
        """Toggle station open/closed"""
        screenshot = self._get_screenshot()
        if screenshot:
            match = self.vision.find_template(screenshot, "open_close_sign")
            if match:
                self.input.click(match.center_x, match.center_y)

    def use_reset_button(self):
        """Use the BIG RED RESET button"""
        screenshot = self._get_screenshot()
        if screenshot:
            match = self.vision.find_template(screenshot, "reset_button_big")
            if match:
                self.input.click(match.center_x, match.center_y)

    def update_fuel_level(self, level: int):
        """Update internal fuel level tracking"""
        self._fuel_level = max(0, min(100, level))
