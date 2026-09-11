"""
Gas Station Simulator - Training Data
Real game scenarios with expected agent actions
"""

TRAINING_SCENARIOS = [
    # ============================================
    # BASIC CUSTOMER SERVICE
    # ============================================
    {
        "id": "scenario_001",
        "name": "Customer arrives at pump",
        "description": "A car pulls up to the gas pump",
        "screenshot_features": ["customer_car", "pump_handle"],
        "expected_state": "pumping_gas",
        "expected_actions": [
            {"action": "grab_handle", "target": "pump_handle"},
            {"action": "position_nozzle", "target": "customer_car", "offset": [50, 100]},
            {"action": "hold_trigger", "key": "left_mouse", "duration": 0.5},
            {"action": "monitor_speed"},
            {"action": "release_when_full"},
        ],
        "difficulty": "easy",
        "priority": 10,
    },
    {
        "id": "scenario_002",
        "name": "Pumping speed control",
        "description": "Managing the needle in the green zone during pumping",
        "screenshot_features": ["speed_meter", "pump_trigger"],
        "expected_state": "pumping_gas",
        "expected_actions": [
            {"action": "tap_shift", "key": "left_shift", "duration": 0.1},
            {"action": "observe_needle"},
            {"action": "release_shift"},
        ],
        "difficulty": "medium",
        "priority": 10,
        "tips": [
            "Tap shift for small amounts",
            "Release early - needle overshoots",
            "Green zone = perfect pumping",
        ],
    },
    {
        "id": "scenario_003",
        "name": "Customer at register",
        "description": "Customer finishes pumping and comes to pay",
        "screenshot_features": ["register_screen", "register_total"],
        "expected_state": "at_register",
        "expected_actions": [
            {"action": "scan_items", "repeat": True, "interval": 0.3},
            {"action": "check_total"},
            {"action": "take_payment", "key": "e"},
            {"action": "give_receipt", "key": "f"},
        ],
        "difficulty": "easy",
        "priority": 9,
    },
    
    # ============================================
    # CLEANING TASKS
    # ============================================
    {
        "id": "scenario_010",
        "name": "Floor needs sweeping",
        "description": "Desert sand tracked inside, floor is dirty",
        "screenshot_features": ["floor_dirt", "broom_icon"],
        "expected_state": "cleaning",
        "expected_actions": [
            {"action": "equip_broom", "target": "broom_icon"},
            {"action": "sweep_floor", "target": "floor_dirt", "drag": True},
        ],
        "difficulty": "easy",
        "priority": 6,
        "note": "Dirty floor loses customers!",
    },
    {
        "id": "scenario_011",
        "name": "Trash can full",
        "description": "Trash can overflowing with green fumes",
        "screenshot_features": ["trash_can"],
        "expected_state": "cleaning",
        "expected_actions": [
            {"action": "click_trash_can", "target": "trash_can"},
            {"action": "carry_to_dumpster"},
            {"action": "throw_trash", "key": "right_mouse"},
        ],
        "difficulty": "easy",
        "priority": 7,
        "note": "Empty before green fumes appear!",
    },
    
    # ============================================
    # DENNIS TROUBLEMAKER
    # ============================================
    {
        "id": "scenario_020",
        "name": "Dennis appears!",
        "description": "Troublemaker Dennis is spraying graffiti",
        "screenshot_features": ["dennis_icon", "graffiti"],
        "expected_state": "dealing_dennis",
        "expected_actions": [
            {"action": "grab_trash", "key": "1"},
            {"action": "throw_at_dennis", "target": "dennis_icon", "button": "right"},
        ],
        "difficulty": "easy",
        "priority": 20,
        "note": "HIGHEST PRIORITY - stop him fast!",
    },
    
    # ============================================
    # WORKSHOP REPAIRS
    # ============================================
    {
        "id": "scenario_030",
        "name": "Car needs repair",
        "description": "Customer's car is on the repair ramp",
        "screenshot_features": ["car_on_ramp", "ramp_button"],
        "expected_state": "fixing_car",
        "expected_actions": [
            {"action": "activate_ramp", "target": "ramp_button"},
            {"action": "scan_for_damage"},
            {"action": "replace_parts"},
            {"action": "paint_scratches"},
            {"action": "lower_ramp"},
        ],
        "difficulty": "hard",
        "priority": 8,
    },
    {
        "id": "scenario_031",
        "name": "Finding broken parts",
        "description": "Scanning car for red-outlined broken parts",
        "screenshot_features": ["car_on_ramp", "broken_part"],
        "expected_state": "fixing_car",
        "expected_actions": [
            {"action": "scan_cursor", "area": "car_on_ramp"},
            {"action": "click_broken_part", "target": "broken_part"},
            {"action": "replace_from_inventory"},
        ],
        "difficulty": "medium",
        "priority": 8,
        "tips": [
            "Move cursor over car to find red outlines",
            "Keep spare parts in stock",
        ],
    },
    
    # ============================================
    # DELIVERY HANDLING
    # ============================================
    {
        "id": "scenario_040",
        "name": "Delivery truck arrived",
        "description": "Supply delivery at warehouse",
        "screenshot_features": ["delivery_truck", "warehouse_door"],
        "expected_state": "receiving_delivery",
        "expected_actions": [
            {"action": "open_warehouse", "target": "warehouse_door"},
            {"action": "unload_items", "key": "e"},
            {"action": "close_warehouse"},
        ],
        "difficulty": "easy",
        "priority": 7,
        "note": "CLOSE THE DOOR after unloading!",
    },
    
    # ============================================
    # MANAGEMENT
    # ============================================
    {
        "id": "scenario_050",
        "name": "Hire employee",
        "description": "Using computer to hire staff",
        "screenshot_features": ["computer_screen", "employee_tab"],
        "expected_state": "managing",
        "expected_actions": [
            {"action": "use_computer", "target": "computer_screen"},
            {"action": "click_employee_tab", "target": "employee_tab"},
            {"action": "hire_employee", "target": "hire_button"},
        ],
        "difficulty": "easy",
        "priority": 4,
    },
    
    # ============================================
    # EMERGENCY SITUATIONS
    # ============================================
    {
        "id": "scenario_060",
        "name": "Fuel pump empty",
        "description": "Gas station running low on fuel",
        "screenshot_features": ["fuel_gauge"],
        "expected_state": "managing",
        "expected_actions": [
            {"action": "use_computer", "target": "computer_screen"},
            {"action": "order_fuel"},
        ],
        "difficulty": "medium",
        "priority": 15,
        "note": "Order fuel ASAP before customers leave!",
    },
    {
        "id": "scenario_061",
        "name": "Cars stuck in traffic",
        "description": "Customer cars getting stuck",
        "screenshot_features": ["customer_car"],
        "expected_state": "managing",
        "expected_actions": [
            {"action": "use_reset_button", "target": "reset_button"},
        ],
        "difficulty": "easy",
        "priority": 12,
        "note": "Use the big red reset button!",
    },
    {
        "id": "scenario_062",
        "name": "Party bus arrived",
        "description": "Busload of customers arriving",
        "screenshot_features": ["customer_icon", "customer_car"],
        "expected_state": "pumping_gas",
        "expected_actions": [
            {"action": "stock_shelves_quick"},
            {"action": "serve_customers"},
        ],
        "difficulty": "hard",
        "priority": 18,
        "note": "Party customers buy everything! Stock up!",
    },
    
    # ============================================
    # MULTI-TASKING SCENARIOS
    # ============================================
    {
        "id": "scenario_070",
        "name": "Customer while cleaning",
        "description": "Customer arrives while you're cleaning",
        "screenshot_features": ["customer_car", "floor_dirt"],
        "expected_state": "pumping_gas",
        "expected_actions": [
            {"action": "stop_cleaning"},
            {"action": "serve_customer_first"},
            {"action": "return_to_cleaning"},
        ],
        "difficulty": "medium",
        "priority": 10,
        "note": "Customers > Cleaning",
    },
    {
        "id": "scenario_071",
        "name": "Dennis while pumping",
        "description": "Dennis appears while pumping gas",
        "screenshot_features": ["dennis_icon", "pump_trigger"],
        "expected_state": "dealing_dennis",
        "expected_actions": [
            {"action": "release_pump"},
            {"action": "throw_at_dennis"},
            {"action": "return_to_pump"},
        ],
        "difficulty": "medium",
        "priority": 20,
        "note": "Stop pumping, deal with Dennis first!",
    },
]

# ============================================
# ACTION PATTERNS (learned from gameplay)
# ============================================

ACTION_PATTERNS = {
    "pumping_gas": {
        "pattern": "grab -> position -> hold -> monitor -> release",
        "timing": {
            "grab_to_position": 0.5,
            "position_to_hold": 0.3,
            "hold_duration": "variable",
            "monitor_interval": 0.1,
        },
        "success_criteria": "fuel_gauge shows full",
        "failure_indicators": ["overshoot", "fuel_spill"],
    },
    
    "at_register": {
        "pattern": "scan -> total -> pay -> receipt",
        "timing": {
            "scan_interval": 0.3,
            "pay_delay": 0.5,
            "receipt_delay": 0.3,
        },
        "success_criteria": "payment_complete visible",
    },
    
    "cleaning": {
        "pattern": "equip -> sweep -> empty_trash -> dump",
        "timing": {
            "sweep_drag": 0.5,
            "empty_trash": 1.0,
            "carry_to_dumpster": 2.0,
        },
        "success_criteria": "dirt_meter below 20",
    },
    
    "fixing_car": {
        "pattern": "ramp_up -> scan -> replace -> paint -> ramp_down",
        "timing": {
            "ramp_activate": 1.0,
            "scan_duration": 2.0,
            "replace_part": 0.5,
            "paint_scratch": 2.0,
        },
        "success_criteria": "car leaves repaired",
    },
}

# ============================================
# GAME TIPS (for agent learning)
# ============================================

GAME_TIPS = [
    "Floor cleanliness directly affects customer satisfaction",
    "Empty trash cans BEFORE they show green fumes",
    "Pump speed: tap shift for small amounts, release early for large",
    "Dennis always appears when you're busiest - keep trash ready",
    "Warehouse doors MUST be closed after delivery",
    "Party bus = stock everything, they buy it all",
    "Use reset button for stuck cars/trucks",
    "Close station when doing maintenance",
    "Keep variety of products for better popularity",
    "Order car parts in advance for workshop",
    "Employees work 8-hour shifts then go to trailers",
    "Pay employees before assigning tasks",
    "Big red reset button fixes many stuck situations",
]

# ============================================
# VISUAL RECOGNITION PATTERNS
# ============================================

VISUAL_PATTERNS = {
    "customer_waiting": {
        "templates": ["customer_icon", "customer_arrow"],
        "location": "top_right",
        "color": "yellow/orange indicator",
    },
    
    "pump_active": {
        "templates": ["pump_handle", "pump_trigger"],
        "location": "center",
        "state": "handle grabbed = pumping",
    },
    
    "register_ready": {
        "templates": ["register_screen", "register_total"],
        "location": "center_left",
        "state": "total visible = ready to pay",
    },
    
    "trash_full": {
        "templates": ["trash_can"],
        "location": "center_left",
        "state": "green fumes = overflow",
    },
    
    "dennis_threat": {
        "templates": ["dennis_icon", "graffiti"],
        "location": "anywhere",
        "state": "spraying = active threat",
    },
    
    "car_repair": {
        "templates": ["car_on_ramp", "broken_part"],
        "location": "workshop",
        "state": "red outline = broken part",
    },
}
