import threading
import time
import uuid
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, field
from queue import Queue, PriorityQueue
from enum import Enum

from .ai_agent import AIAgent, AgentRole, AgentTask


class SpawnerStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class AgentInfo:
    agent_id: str
    role: AgentRole
    status: str = "idle"
    current_task: Optional[str] = None
    actions_completed: int = 0
    success_rate: float = 0.0


class MultiAgentSpawner:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        capture_method: str = "auto",
        human_like: bool = True,
    ):
        self.api_key = api_key
        self.model = model
        self.capture_method = capture_method
        self.human_like = human_like

        self._agents: Dict[str, AIAgent] = {}
        self._agent_info: Dict[str, AgentInfo] = {}
        self._task_queue = Queue()
        self._status = SpawnerStatus.IDLE
        self._spawner_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        self._game_window_title: Optional[str] = None
        self._on_agent_action: Optional[Callable] = None
        self._on_task_complete: Optional[Callable] = None
        self._on_agent_error: Optional[Callable] = None

    def set_game_window(self, title: str):
        self._game_window_title = title

    def set_callbacks(
        self,
        on_agent_action: Optional[Callable] = None,
        on_task_complete: Optional[Callable] = None,
        on_agent_error: Optional[Callable] = None,
    ):
        self._on_agent_action = on_agent_action
        self._on_task_complete = on_task_complete
        self._on_agent_error = on_agent_error

    def spawn_agent(
        self,
        role: AgentRole,
        agent_id: Optional[str] = None,
    ) -> Optional[str]:
        if agent_id is None:
            agent_id = f"agent_{role.value}_{uuid.uuid4().hex[:6]}"

        with self._lock:
            if agent_id in self._agents:
                print(f"[Spawner] Agent {agent_id} already exists")
                return None

            agent = AIAgent(
                agent_id=agent_id,
                role=role,
                api_key=self.api_key,
                model=self.model,
                capture_method=self.capture_method,
                human_like=self.human_like,
            )

            if self._game_window_title:
                success = agent.attach_to_game(self._game_window_title)
                if not success:
                    print(f"[Spawner] Failed to attach {agent_id} to game")
                    return None

            agent.set_callbacks(
                on_action=self._handle_agent_action,
                on_task_complete=self._handle_task_complete,
            )

            self._agents[agent_id] = agent
            self._agent_info[agent_id] = AgentInfo(
                agent_id=agent_id,
                role=role,
            )

            print(f"[Spawner] Spawned {role.value} agent: {agent_id}")
            return agent_id

    def spawn_multiple(self, roles: List[AgentRole]) -> List[str]:
        agent_ids = []
        for role in roles:
            agent_id = self.spawn_agent(role)
            if agent_id:
                agent_ids.append(agent_id)
        return agent_ids

    def spawn_team(self, team_config: Dict[str, int]) -> List[str]:
        agent_ids = []
        for role_str, count in team_config.items():
            try:
                role = AgentRole(role_str)
                for _ in range(count):
                    agent_id = self.spawn_agent(role)
                    if agent_id:
                        agent_ids.append(agent_id)
            except ValueError:
                print(f"[Spawner] Unknown role: {role_str}")
        return agent_ids

    def assign_task(self, agent_id: str, task: AgentTask) -> bool:
        with self._lock:
            if agent_id not in self._agents:
                print(f"[Spawner] Agent {agent_id} not found")
                return False

            agent = self._agents[agent_id]
            task.assigned_agent = agent_id
            task.status = "assigned"
            self._agent_info[agent_id].current_task = task.task_id

            print(f"[Spawner] Task '{task.description}' assigned to {agent_id}")
            return True

    def broadcast_task(self, task: AgentTask) -> List[str]:
        assigned = []
        with self._lock:
            for agent_id, agent in self._agents.items():
                if self._agent_info[agent_id].current_task is None:
                    task_copy = AgentTask(
                        task_id=task.task_id,
                        description=task.description,
                        priority=task.priority,
                        assigned_agent=agent_id,
                    )
                    self.assign_task(agent_id, task_copy)
                    assigned.append(agent_id)
        return assigned

    def start_agent(self, agent_id: str, interval: float = 2.0):
        with self._lock:
            if agent_id in self._agents:
                agent = self._agents[agent_id]
                task = None
                if self._agent_info[agent_id].current_task:
                    task = AgentTask(
                        task_id=self._agent_info[agent_id].current_task,
                        description="Execute assigned task",
                    )
                agent.start_continuous(task=task, interval=interval)
                self._agent_info[agent_id].status = "running"

    def start_all(self, interval: float = 2.0):
        with self._lock:
            self._status = SpawnerStatus.RUNNING
            for agent_id in self._agents:
                self.start_agent(agent_id, interval)

    def stop_agent(self, agent_id: str):
        with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].stop()
                self._agent_info[agent_id].status = "stopped"

    def stop_all(self):
        with self._lock:
            self._status = SpawnerStatus.STOPPED
            for agent_id in self._agents:
                self._agents[agent_id].stop()
                self._agent_info[agent_id].status = "stopped"

    def pause_all(self):
        with self._lock:
            self._status = SpawnerStatus.PAUSED
            for agent_id in self._agents:
                self._agents[agent_id].stop()
                self._agent_info[agent_id].status = "paused"

    def resume_all(self, interval: float = 2.0):
        with self._lock:
            self._status = SpawnerStatus.RUNNING
            for agent_id in self._agents:
                if self._agent_info[agent_id].status == "paused":
                    self.start_agent(agent_id, interval)

    def remove_agent(self, agent_id: str):
        with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].stop()
                del self._agents[agent_id]
                del self._agent_info[agent_id]
                print(f"[Spawner] Removed agent: {agent_id}")

    def get_agent(self, agent_id: str) -> Optional[AIAgent]:
        return self._agents.get(agent_id)

    def get_status(self) -> Dict[str, AgentInfo]:
        return self._agent_info.copy()

    def get_agent_count(self) -> int:
        return len(self._agents)

    def get_running_count(self) -> int:
        return sum(1 for info in self._agent_info.values() if info.status == "running")

    def _handle_agent_action(self, agent_id: str, action: dict, success: bool):
        with self._lock:
            if agent_id in self._agent_info:
                self._agent_info[agent_id].actions_completed += 1

        if self._on_agent_action:
            self._on_agent_action(agent_id, action, success)

    def _handle_task_complete(self, agent_id: str, result: any):
        with self._lock:
            if agent_id in self._agent_info:
                self._agent_info[agent_id].current_task = None

        if self._on_task_complete:
            self._on_task_complete(agent_id, result)

    def print_status(self):
        print("\n" + "=" * 60)
        print("MULTI-AGENT STATUS")
        print("=" * 60)
        print(f"Total Agents: {self.get_agent_count()}")
        print(f"Running: {self.get_running_count()}")
        print(f"Status: {self._status.value}")
        print("-" * 60)
        for agent_id, info in self._agent_info.items():
            print(f"  {agent_id}:")
            print(f"    Role: {info.role.value}")
            print(f"    Status: {info.status}")
            print(f"    Task: {info.current_task or 'None'}")
            print(f"    Actions: {info.actions_completed}")
        print("=" * 60 + "\n")

    def save_all_memory(self, directory: str):
        from pathlib import Path
        Path(directory).mkdir(parents=True, exist_ok=True)
        for agent_id, agent in self._agents.items():
            path = f"{directory}/{agent_id}_memory.pkl"
            agent.save_memory(path)
            print(f"[Spawner] Saved memory for {agent_id}")
