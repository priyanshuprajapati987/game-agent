import sys
import time
import signal
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt

from core import ScreenCapture, VisionEngine, InputController, WindowManager
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


def signal_handler(sig, frame):
    global agent
    console.print("\n[yellow]Emergency stop triggered![/yellow]")
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
    Press Ctrl+C to stop
    """
    console.print(Panel(banner.strip(), style="bold cyan"))


def show_menu():
    table = Table(title="Select Game Plugin", show_header=True)
    table.add_column("Number", style="cyan")
    table.add_column("Game", style="green")
    table.add_column("Description", style="white")

    table.add_row("1", "Gas Station Simulator", "Automate gas pumping, customer service")
    table.add_row("2", "Minecraft", "Mining, crafting, basic automation")
    table.add_row("3", "Generic Game", "Template-based for any game")
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


def main():
    global agent

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    show_banner()

    parser = argparse.ArgumentParser(description="Game Agent")
    parser.add_argument("--game", type=str, help="Game plugin to use (1, 2, or 3)")
    parser.add_argument("--window", type=str, help="Game window title")
    parser.add_argument("--list", action="store_true", help="List open windows")
    args = parser.parse_args()

    if args.list:
        list_windows()
        return

    if args.game:
        choice = args.game
    else:
        show_menu()
        choice = Prompt.ask("\nSelect game", choices=["1", "2", "3", "4"])

    if choice == "4":
        list_windows()
        return

    if choice not in PLUGINS:
        console.print("[red]Invalid choice![/red]")
        return

    game_name, plugin_class = PLUGINS[choice]
    console.print(f"\n[green]Starting {game_name} agent...[/green]")

    try:
        agent = plugin_class()

        window_title = args.window or agent.config.get("window", {}).get("title")
        if not window_title:
            window_title = Prompt.ask("Enter game window title (or leave blank for auto-detect)")

        agent.start(game_title=window_title if window_title else None)

    except FileNotFoundError as e:
        console.print(f"[red]Config error: {e}[/red]")
        console.print("[yellow]Make sure you're running from the project root directory[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if agent:
            agent.stop()


if __name__ == "__main__":
    main()
