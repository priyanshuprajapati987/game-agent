import sys
import time
import signal
import argparse
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

from core import ScreenCapture, VisionEngine, InputController, WindowManager
from core.ai_agent import AIAgent, AgentRole, AgentTask
from core.multi_agent import MultiAgentSpawner
from core.offline_ai import OfflineAIEngine, ModelConfig
from plugins.gas_station_sim.plugin import GasStationPlugin
from plugins.minecraft.plugin import MinecraftPlugin
from plugins.generic.plugin import GenericPlugin

console = Console()

PLUGINS = {
    "1": ("Gas Station Simulator", GasStationPlugin),
    "2": ("Minecraft", MinecraftPlugin),
    "3": ("Generic Game", GenericPlugin),
}

agent = None
spawner = None


def signal_handler(sig, frame):
    global agent, spawner
    console.print("\n[yellow]Emergency stop triggered![/yellow]")
    if spawner:
        spawner.stop_all()
    if agent:
        agent.stop()
    sys.exit(0)


def show_banner():
    banner = """
  ____   ___   ____ _   _ ______     __
 / ___| / _ \ / ___| | | |  _ \ \   / /
| |  _|| | | | |   | |_| | | | \ \ / /
| |_| || |_| | |___|  _  | |_| |\ V /
 \____| \___/ \____|_| |_|____/  \_/

    Generic Game Automation Agent
    OFFLINE MODE - No API Key Required
    Press Ctrl+C to stop
    """
    console.print(Panel(banner.strip(), style="bold cyan"))


def show_menu():
    table = Table(title="Select Mode", show_header=True)
    table.add_column("Number", style="cyan")
    table.add_column("Mode", style="green")
    table.add_column("Description", style="white")

    table.add_row("1", "Rule-Based Agent", "Traditional state machine (no AI)")
    table.add_row("2", "AI Single Agent", "One AI agent with offline model")
    table.add_row("3", "AI Multi-Agent", "Multiple AI agents parallel tasks")
    table.add_row("4", "List Windows", "Show all open windows")

    console.print(table)


def list_windows():
    try:
        wm = WindowManager()
        windows = wm.get_all_windows()
        table = Table(title="Open Windows", show_header=True)
        table.add_column("HWND", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Class", style="white")

        for w in windows[:30]:
            table.add_row(str(w.hwnd), w.title[:50], w.class_name)

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def select_model() -> ModelConfig:
    console.print("\n[bold cyan]Select AI Backend[/bold cyan]\n")

    table = Table(show_header=True)
    table.add_column("Number", style="cyan")
    table.add_column("Backend", style="green")
    table.add_column("Description", style="white")
    table.add_column("Install", style="dim")

    table.add_row("1", "CV Only", "Pure OpenCV (no LLM, fast)", "Already installed")
    table.add_row("2", "Ollama", "Local LLM via Ollama", "ollama.com")
    table.add_row("3", "LLaMA.cpp", "Direct .gguf model loading", "pip install llama-cpp-python")
    table.add_row("4", "Transformers", "HuggingFace models", "pip install transformers torch")

    console.print(table)

    choice = Prompt.ask("\nSelect backend", choices=["1", "2", "3", "4"], default="1")

    if choice == "1":
        return ModelConfig(name="cv_only", backend="cv_only")

    elif choice == "2":
        model_name = Prompt.ask("Ollama model name", default="llava:7b")
        console.print(f"[dim]Make sure Ollama is running: ollama serve[/dim]")
        return ModelConfig(name=model_name, backend="ollama")

    elif choice == "3":
        model_path = Prompt.ask("Model file path (.gguf)")
        if not Path(model_path).exists():
            console.print(f"[red]File not found: {model_path}[/red]")
            return ModelConfig(name="cv_only", backend="cv_only")
        n_ctx = int(Prompt.ask("Context size", default="2048"))
        n_threads = int(Prompt.ask("CPU threads", default="4"))
        return ModelConfig(
            name=Path(model_path).stem,
            backend="llama_cpp",
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
        )

    elif choice == "4":
        model_path = Prompt.ask("HuggingFace model ID or local path")
        device = Prompt.ask("Device", choices=["cpu", "cuda", "mps"], default="cpu")
        return ModelConfig(
            name=model_path.split("/")[-1],
            backend="transformers",
            model_path=model_path,
            device=device,
        )

    return ModelConfig(name="cv_only", backend="cv_only")


def run_rule_based():
    global agent

    console.print("\n[bold]Select Game Plugin[/bold]\n")
    table = Table(show_header=True)
    table.add_column("Number", style="cyan")
    table.add_column("Game", style="green")
    table.add_row("1", "Gas Station Simulator")
    table.add_row("2", "Minecraft")
    table.add_row("3", "Generic Game")
    console.print(table)

    choice = Prompt.ask("\nSelect game", choices=["1", "2", "3"])

    if choice not in PLUGINS:
        console.print("[red]Invalid choice![/red]")
        return

    game_name, plugin_class = PLUGINS[choice]
    console.print(f"\n[green]Starting {game_name} agent...[/green]")

    try:
        agent = plugin_class()
        window_title = Prompt.ask("Enter game window title (or blank for auto)")
        agent.start(game_title=window_title if window_title else None)
    except FileNotFoundError as e:
        console.print(f"[red]Config error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if agent:
            agent.stop()


def run_ai_single():
    global agent

    model_config = select_model()
    console.print(f"\n[dim]Backend: {model_config.backend} | Model: {model_config.name}[/dim]")

    window_title = Prompt.ask("Game window title")

    agent_id = Prompt.ask("Agent ID", default="main_agent")
    role_str = Prompt.ask(
        "Agent role",
        choices=["scout", "fighter", "farmer", "builder", "crafter", "explorer"],
        default="scout",
    )

    role = AgentRole(role_str)
    agent = AIAgent(
        agent_id=agent_id,
        role=role,
        model_config=model_config,
    )

    if not agent.attach_to_game(window_title):
        console.print("[red]Could not find game window![/red]")
        return

    task_desc = Prompt.ask("Task description (or blank for free play)", default="")
    task = None
    if task_desc:
        task = AgentTask(task_id="main_task", description=task_desc)

    interval = float(Prompt.ask("Action interval (seconds)", default="2.0"))

    console.print(f"\n[green]AI Agent '{agent_id}' ({role.value}) started![/green]")
    console.print(f"[dim]Backend: {model_config.backend} | Interval: {interval}s[/dim]")
    console.print("[yellow]Press Ctrl+C to stop\n[/yellow]")

    agent.start_continuous(task=task, interval=interval)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.stop()
        console.print("\n[green]Agent stopped.[/green]")


def run_ai_multi():
    global spawner

    model_config = select_model()
    console.print(f"\n[dim]Backend: {model_config.backend} | Model: {model_config.name}[/dim]")

    window_title = Prompt.ask("Game window title")

    spawner = MultiAgentSpawner(model_config=model_config)
    spawner.set_game_window(window_title)

    console.print("\n[bold]Spawn Agents[/bold]")
    console.print("Roles: scout, fighter, farmer, builder, crafter, explorer")

    team_config = {}
    while True:
        role = Prompt.ask("\nAgent role (or 'done' to finish)", default="done")
        if role == "done":
            break
        try:
            AgentRole(role)
            count = int(Prompt.ask(f"How many {role} agents?", default="1"))
            team_config[role] = count
        except ValueError:
            console.print(f"[red]Unknown role: {role}[/red]")

    if not team_config:
        team_config = {"scout": 1, "fighter": 1}

    console.print(f"\n[dim]Spawning team: {team_config}[/dim]")
    agent_ids = spawner.spawn_team(team_config)

    if not agent_ids:
        console.print("[red]No agents spawned![/red]")
        return

    task_desc = Prompt.ask("\nGlobal task for all agents", default="Explore the game and complete objectives")
    interval = float(Prompt.ask("Action interval (seconds)", default="3.0"))

    for agent_id in agent_ids:
        task = AgentTask(task_id=f"task_{agent_id}", description=task_desc)
        spawner.assign_task(agent_id, task)

    console.print(f"\n[green]Starting {len(agent_ids)} agents...[/green]")
    spawner.start_all(interval=interval)

    def on_action(agent_id, action, success):
        status = "[green]OK[/green]" if success else "[red]FAIL[/red]"
        analysis = action.get("analysis", "N/A")[:50]
        console.print(f"  {status} {agent_id}: {analysis}")

    spawner.set_callbacks(on_agent_action=on_action)

    console.print("[yellow]Commands: status | pause | resume | stop | Ctrl+C[/yellow]\n")

    try:
        while True:
            user_input = input()
            cmd = user_input.strip().lower()
            if cmd == "status":
                spawner.print_status()
            elif cmd == "stop":
                spawner.stop_all()
                break
            elif cmd == "pause":
                spawner.pause_all()
                console.print("[yellow]All agents paused[/yellow]")
            elif cmd == "resume":
                spawner.resume_all(interval)
                console.print("[green]All agents resumed[/green]")
    except KeyboardInterrupt:
        pass
    finally:
        spawner.stop_all()
        spawner.save_all_memory("agent_memory")
        console.print("\n[green]All agents stopped. Memory saved.[/green]")


def main():
    global agent, spawner

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    show_banner()

    parser = argparse.ArgumentParser(description="Game Agent - Offline Mode")
    parser.add_argument("--mode", type=str, help="Mode: rule, ai, multi")
    parser.add_argument("--list", action="store_true", help="List open windows")
    args = parser.parse_args()

    if args.list:
        list_windows()
        return

    if args.mode:
        mode = args.mode
    else:
        show_menu()
        mode = Prompt.ask("\nSelect mode", choices=["1", "2", "3", "4"])

    if mode == "4":
        list_windows()
    elif mode == "1":
        run_rule_based()
    elif mode == "2":
        run_ai_single()
    elif mode == "3":
        run_ai_multi()
    else:
        console.print("[red]Invalid mode![/red]")


if __name__ == "__main__":
    main()
