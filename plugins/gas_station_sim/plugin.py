"""
Gas Station Simulator - Real Game Plugin
Based on actual game mechanics and UI elements
"""

from typing import Optional
import time
import random
from plugins.base_plugin import BasePlugin
from core.state_machine import State, Transition, StateType


class GasStationPlugin(BasePlugin):
    """
    Gas Station Simulator automation plugin.
    
    Game States:
    - IDLE: Not doing anything
    - PUMPING_GAS: Filling customer's car
    - AT_REGISTER: Taking payment
    - CLEANING: Sweeping/emptying trash
    - FIXING_CAR: Workshop repairs
    - DEALING_DENNIS: Chasing troublemaker
    - STOCKING: Filling shelves
    - MANAGING: Using computer/employees
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
        self._register_items = []
        self._dennis_active = False
        
        # Config loaded from YAML
        self.rois = self.config.get("rois", {})
        self.game_states = self.config.get("game_states", {})
        self.actions = self.config.get("actions", {})

    def _setup_states(self):
        """Setup all game states with priorities"""
        states = {
            "idle": State("idle", StateType.ACTIVE),
            "pumping_gas": State("pumping_gas", StateType.ACTIVE),
            "at_register": State("at_register", StateType.ACTIVE),
            "cleaning": State("cleaning", StateType.ACTIVE),
            "fixing_car": State("fixing_car", StateType.ACTIVE),
            "dealing_dennis": State("dealing_dennis", StateType.ACTIVE),
            "stocking": State("stocking", StateType.ACTIVE),
            "managing": State("managing", StateType.ACTIVE),
            "receiving_delivery": State("receiving_delivery", StateType.ACTIVE),
        }

        for name, state in states.items():
            self.state_machine.add_state(name, state)

        self.state_machine.set_initial_state("idle")

    def _setup_transitions(self):
        """Setup state transitions based on game conditions"""
        transitions = [
            # Dennis has highest priority - deal with him first
            Transition(
                from_state="idle",
                to_state="dealing_dennis",
                condition=self._dennis_detected,
                priority=20,
            ),
            Transition(
                from_state="cleaning",
                to_state="dealing_dennis",
                condition=self._dennis_detected,
                priority=20,
            ),
            Transition(
                from_state="stocking",
                to_state="dealing_dennis",
                condition=self._dennis_detected,
                priority=20,
            ),
            
            # Customer at pump - serve them
            Transition(
                from_state="idle",
                to_state="pumping_gas",
                condition=self._customer_at_pump,
                priority=10,
            ),
            Transition(
                from_state="cleaning",
                to_state="pumping_gas",
                condition=self._customer_at_pump,
                priority=10,
            ),
            
            # Customer at register
            Transition(
                from_state="pumping_gas",
                to_state="at_register",
                condition=self._pump_complete,
                priority=9,
            ),
            Transition(
                from_state="idle",
                to_state="at_register",
                condition=self._customer_at_register,
                priority=9,
            ),
            
            # Car in workshop
            Transition(
                from_state="idle",
                to_state="fixing_car",
                condition=self._car_in_workshop,
                priority=8,
            ),
            
            # Floor dirty - clean it
            Transition(
                from_state="idle",
                to_state="cleaning",
                condition=self._floor_needs_cleaning,
                priority=6,
            ),
            
            # Delivery arrived
            Transition(
                from_state="idle",
                to_state="receiving_delivery",
                condition=self._delivery_arrived,
                priority=7,
            ),
            
            # Go back to idle after tasks
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
        ]

        for t in transitions:
            self.state_machine.add_transition(t)

    def get_action_for_state(self, state: str) -> Optional[dict]:
        """Get the action to perform based on current state"""
        actions = {
            "idle": self._idle_action(),
            "pumping_gas": self._pumping_action(),
            "at_register": self._register_action(),
            "cleaning": self._cleaning_action(),
            "fixing_car": self._workshop_action(),
            "dealing_dennis": self._dennis_action(),
            "stocking": self._stocking_action(),
            "receiving_delivery": self._delivery_action(),
            "managing": self._managing_action(),
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
        
        # Check for customer car at pump
        match = self.vision.find_template(screenshot, "customer_car")
        if match:
            self._current_customer = match
            return True
        
        # Check for customer indicator
        match = self.vision.find_template(screenshot, "customer_icon")
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
        
        match = self.vision.find_template(screenshot, "dennis_icon")
        if match:
            self._dennis_active = True
            return True
        
        # Check for graffiti
        match = self.vision.find_template(screenshot, "graffiti")
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

    def _payment_complete(self) -> bool:
        """Check if payment was processed"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return False
        
        match = self.vision.find_template(screenshot, "payment_complete")
        return match is not None

    # ============================================
    # ACTION EXECUTORS
    # ============================================

    def _idle_action(self) -> dict:
        """Look around for customers or tasks"""
        # Check for email notifications
        screenshot = self._get_screenshot()
        if screenshot:
            email_match = self.vision.find_template(screenshot, "email_icon")
            if email_match:
                return {"type": "click", "x": email_match.center_x, "y": email_match.center_y}
        
        return {"type": "wait", "duration": 0.5}

    def _pumping_action(self) -> dict:
        """Handle gas pumping minigame"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return {"type": "wait", "duration": 0.2}
        
        # Step 1: Grab pump handle
        if self._pumping_progress == 0:
            match = self.vision.find_template(screenshot, "pump_handle")
            if match:
                self._pumping_progress = 10
                return {"type": "click", "x": match.center_x, "y": match.center_y}
        
        # Step 2: Position nozzle at car
        elif self._pumping_progress == 10:
            match = self.vision.find_template(screenshot, "customer_car")
            if match:
                # Click near fuel tank (offset from car center)
                self._pumping_progress = 20
                return {
                    "type": "click", 
                    "x": match.center_x + 50, 
                    "y": match.center_y + 100
                }
        
        # Step 3: Start pumping (hold trigger)
        elif self._pumping_progress == 20:
            self._pumping_progress = 30
            return {"type": "hold", "key": "left_mouse", "duration": 0.5}
        
        # Step 4: Monitor and control speed
        elif self._pumping_progress == 30:
            # Check speed meter
            match = self.vision.find_template(screenshot, "speed_meter")
            if match:
                # Analyze needle position
                roi = self.rois.get("needle_green_zone", {})
                if roi:
                    in_green = self.vision.check_region_color(
                        screenshot,
                        (roi["x"], roi["y"], roi["w"], roi["h"]),
                        target_color=(0, 200, 0),
                        tolerance=50,
                    )
                    if in_green:
                        # In green zone - keep pumping
                        return {"type": "hold", "key": "left_shift", "duration": 0.2}
                    else:
                        # Not in green - release and wait
                        self._pumping_progress = 40
                        return {"type": "wait", "duration": 0.3}
            
            # Default: keep pumping
            return {"type": "hold", "key": "left_mouse", "duration": 0.1}
        
        # Step 5: Check if done
        elif self._pumping_progress == 40:
            match = self.vision.find_template(screenshot, "fuel_gauge")
            if match:
                # Check if tank is full
                self._pumping_progress = 100
                self._customers_served += 1
                return {"type": "release", "key": "left_mouse"}
        
        return {"type": "wait", "duration": 0.2}

    def _register_action(self) -> dict:
        """Handle checkout/register"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return {"type": "wait", "duration": 0.2}
        
        # Scan items
        match = self.vision.find_template(screenshot, "register_screen")
        if match:
            # Click to scan
            return {
                "type": "click",
                "x": match.center_x + random.randint(-20, 20),
                "y": match.center_y + random.randint(-20, 20)
            }
        
        # Check for total
        match = self.vision.find_template(screenshot, "register_total")
        if match:
            # Take payment
            return {"type": "key", "key": "e"}
        
        # Give receipt
        match = self.vision.find_template(screenshot, "payment_complete")
        if match:
            return {"type": "key", "key": "f"}
        
        return {"type": "wait", "duration": 0.3}

    def _cleaning_action(self) -> dict:
        """Handle cleaning tasks"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return {"type": "wait", "duration": 0.2}
        
        # Check for full trash cans first
        match = self.vision.find_template(screenshot, "trash_can")
        if match:
            # Click to empty
            self._floor_dirty_level = max(0, self._floor_dirty_level - 30)
            return {"type": "click", "x": match.center_x, "y": match.center_y}
        
        # Sweep the floor
        match = self.vision.find_template(screenshot, "floor_dirt")
        if match:
            # Drag broom across dirty area
            self._floor_dirty_level = max(0, self._floor_dirty_level - 10)
            return {
                "type": "drag",
                "start_x": match.center_x - 200,
                "start_y": match.center_y,
                "end_x": match.center_x + 200,
                "end_y": match.center_y,
                "duration": 0.5
            }
        
        # Floor is clean
        self._floor_dirty_level = 0
        return {"type": "wait", "duration": 0.5}

    def _workshop_action(self) -> dict:
        """Handle car repairs"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return {"type": "wait", "duration": 0.2}
        
        # Check if ramp is up
        match = self.vision.find_template(screenshot, "ramp_button")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}
        
        # Look for broken parts
        match = self.vision.find_template(screenshot, "broken_part")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}
        
        # Paint scratches
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

    def _dennis_action(self) -> dict:
        """Chase away Dennis"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return {"type": "wait", "duration": 0.2}
        
        # Find Dennis
        match = self.vision.find_template(screenshot, "dennis_icon")
        if match:
            # Throw trash at him
            return {
                "type": "click",
                "x": match.center_x,
                "y": match.center_y,
                "button": "right"
            }
        
        # Dennis gone
        self._dennis_active = False
        return {"type": "wait", "duration": 0.5}

    def _stocking_action(self) -> dict:
        """Stock shelves with products"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return {"type": "wait", "duration": 0.2}
        
        # Click on empty shelf spots
        return {"type": "key", "key": "e"}

    def _delivery_action(self) -> dict:
        """Handle delivery truck"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return {"type": "wait", "duration": 0.2}
        
        # Open warehouse door
        match = self.vision.find_template(screenshot, "warehouse_door")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}
        
        # Unload items
        return {"type": "key", "key": "e"}

    def _managing_action(self) -> dict:
        """Use management computer"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return {"type": "wait", "duration": 0.2}
        
        match = self.vision.find_template(screenshot, "computer_screen")
        if match:
            return {"type": "click", "x": match.center_x, "y": match.center_y}
        
        return {"type": "wait", "duration": 0.5}

    # ============================================
    # CUSTOMER FLOW TRACKING
    # ============================================

    def track_customer_flow(self):
        """Track customer arrival and service"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return
        
        # Update dirty level based on customer count
        if self._current_customer:
            self._floor_dirty_level = min(100, self._floor_dirty_level + 2)

    def update_game_stats(self):
        """Update internal game statistics"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return
        
        # Read money display
        roi = self.rois.get("money_display")
        if roi:
            text = self.ocr.read_number(
                screenshot,
                roi=(roi["x"], roi["y"], roi["w"], roi["h"])
            )
            if text is not None:
                self._money = int(text)

    # ============================================
    # HELPER METHODS
    # ============================================

    def is_open(self) -> bool:
        """Check if station is open"""
        screenshot = self._get_screenshot()
        if screenshot is None:
            return True
        
        match = self.vision.find_template(screenshot, "open_sign")
        return match is not None

    def toggle_station(self):
        """Toggle station open/closed"""
        screenshot = self._get_screenshot()
        if screenshot:
            match = self.vision.find_template(screenshot, "open_sign")
            if match:
                self.input.click(match.center_x, match.center_y)

    def use_reset_button(self):
        """Use the big red reset button"""
        screenshot = self._get_screenshot()
        if screenshot:
            match = self.vision.find_template(screenshot, "reset_button")
            if match:
                self.input.click(match.center_x, match.center_y)
