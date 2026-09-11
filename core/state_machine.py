from typing import Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import time


class StateType(Enum):
    ACTIVE = "active"
    TRANSITION = "transition"
    TERMINAL = "terminal"


@dataclass
class State:
    name: str
    state_type: StateType = StateType.ACTIVE
    on_enter: Optional[Callable] = None
    on_exit: Optional[Callable] = None
    on_update: Optional[Callable] = None
    data: dict = field(default_factory=dict)


@dataclass
class Transition:
    from_state: str
    to_state: str
    condition: Callable[[], bool]
    priority: int = 0


class StateMachine:
    def __init__(self):
        self._states: dict[str, State] = {}
        self._transitions: list[Transition] = []
        self._current_state: Optional[str] = None
        self._previous_state: Optional[str] = None
        self._state_time: float = 0
        self._running: bool = False
        self._state_history: list[tuple[str, float]] = []

    def add_state(self, name: str, state: State):
        self._states[name] = state

    def add_transition(self, transition: Transition):
        self._transitions.append(transition)
        self._transitions.sort(key=lambda t: t.priority, reverse=True)

    def set_initial_state(self, state_name: str):
        if state_name not in self._states:
            raise ValueError(f"State '{state_name}' not found")
        self._current_state = state_name

    def start(self):
        if self._current_state is None:
            raise RuntimeError("No initial state set")
        self._running = True
        self._state_time = time.time()
        state = self._states[self._current_state]
        if state.on_enter:
            state.on_enter()

    def stop(self):
        self._running = False

    def update(self) -> Optional[str]:
        if not self._running or self._current_state is None:
            return None

        state = self._states[self._current_state]

        if state.on_update:
            state.on_update()

        for transition in self._transitions:
            if transition.from_state == self._current_state:
                if transition.condition():
                    return self._transition_to(transition.to_state)

        return self._current_state

    def force_transition(self, to_state: str) -> bool:
        if to_state not in self._states:
            return False
        if self._current_state:
            self._transition_to(to_state)
            return True
        return False

    def _transition_to(self, to_state: str) -> str:
        old_state = self._states[self._current_state]
        if old_state.on_exit:
            old_state.on_exit()

        elapsed = time.time() - self._state_time
        self._state_history.append((self._current_state, elapsed))

        self._previous_state = self._current_state
        self._current_state = to_state
        self._state_time = time.time()

        new_state = self._states[self._current_state]
        if new_state.on_enter:
            new_state.on_enter()

        return self._current_state

    @property
    def current_state(self) -> Optional[str]:
        return self._current_state

    @property
    def previous_state(self) -> Optional[str]:
        return self._previous_state

    @property
    def state_elapsed(self) -> float:
        return time.time() - self._state_time

    @property
    def is_running(self) -> bool:
        return self._running

    def get_state_data(self, state_name: str) -> dict:
        return self._states[state_name].data

    def set_state_data(self, state_name: str, key: str, value: Any):
        self._states[state_name].data[key] = value

    def get_history(self) -> list[tuple[str, float]]:
        return self._state_history.copy()

    def clear_history(self):
        self._state_history.clear()

    def register_actions(self, state_name: str, on_enter=None, on_exit=None, on_update=None):
        if state_name in self._states:
            state = self._states[state_name]
            if on_enter:
                state.on_enter = on_enter
            if on_exit:
                state.on_exit = on_exit
            if on_update:
                state.on_update = on_update
