"""
Game Agent - Play ANY Game!
No templates needed - AI Vision handles everything
"""

import sys
import time
import signal
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from core.generic_agent import GenericGameAgent, MultiGameManager, play_game, AgentRole
from core.offline_ai import ModelConfig

console = Console()


def signal_handler(sig, frame):
    console.print("\n[yellow]Stopping...[/yellow]")
    sys.exit(0)


def show_banner():
    banner = """
  ____   ___   ____ _   _ ______     __
 / ___| / _ \ / ___| | | |  _ \ \   / /
| |  _|| | | | |   | |_| | | | \ \ / /
| |_| || |_| | |___|  _  | |_| |\ V /
 \____| \___/ \____|_| |_|____/  \_/

    GENERIC GAME AGENT
    Play ANY Game - No Templates Needed!
    """
    console.print(Panel(banner.strip(), style="bold cyan"))


def select_backend():
    table = Table(title="AI Backend", show_header=True)
    table.add_column("Num", style="cyan")
    table.add_column("Backend", style="green")
    table.add_column("Description", style="white")
    
    table.add_row("1", "CV Only", "Fast, no AI model needed")
    table.add_row("2", "Ollama", "Local AI (llava:7b recommended)")
    
    console.print(table)
    
    choice = Prompt.ask("Select", choices=["1", "2"], default="1")
    
    if choice == "2":
        model = Prompt.ask("Model name", default="llava:7b")
        return ModelConfig(name=model, backend="ollama")
    else:
        return ModelConfig(name="cv_only", backend="cv_only")


def main():
    signal.signal(signal.SIGINT, signal_handler)
    show_banner()
    
    console.print("[bold]What do you want to do?[/bold]\n")
    
    table = Table(show_header=True)
    table.add_column("Num", style="cyan")
    table.add_column("Mode", style="green")
    table.add_column("Description", style="white")
    
    table.add_row("1", "Play One Game", "Agent plays one game")
    table.add_row("2", "Play Multiple Games", "Agents play many games")
    table.add_row("3", "Quick Start", "Just type game name")
    
    console.print(table)
    
    choice = Prompt.ask("\nSelect", choices=["1", "2", "3"])
    
    config = select_backend()
    
    if choice == "1":
        single_game(config)
    elif choice == "2":
        multi_game(config)
    elif choice == "3":
        quick_start(config)


def single_game(config):
    game = Prompt.ask("\nGame name (as it appears in window title)")
    task = Prompt.ask("Task for agent (or blank for free play)", default="")
    
    agent = GenericGameAgent(model_config=config)
    
    if agent.attach(game):
        agent.run_continuous(task=task)
    else:
        console.print("[red]Game not found![/red]")
        console.print("[dim]Make sure game is running and window title matches[/dim]")


def multi_game(config):
    console.print("\n[bold]Add games (type 'done' when finished):[/bold]\n")
    
    games = {}
    while True:
        game = Prompt.ask("Game name (or 'done')")
        if game.lower() == "done":
            break
        task = Prompt.ask(f"Task for {game}", default="Play the game")
        games[game] = task
    
    if not games:
        games = {"Minecraft": "Mine diamonds", "GTA V": "Drive around"}
    
    console.print(f"\n[dim]Starting {len(games)} agents...[/dim]\n")
    
    manager = MultiGameManager()
    for game, task in games.items():
        manager.add_game(game, game, task)
    
    manager.start_all()


def quick_start(config):
    console.print("\n[bold]Quick Start - Just type what you want![/bold]\n")
    console.print("[dim]Examples:[/dim]")
    console.print('  "Minecraft - mine diamonds"')
    console.print('  "GTA V - drive around"')
    console.print('  "Stardew Valley - farm crops"')
    console.print('  "Gas Station Simulator - serve customers"\n')
    
    query = Prompt.ask("What game and task?")
    
    if " - " in query:
        game, task = query.split(" - ", 1)
    else:
        game = query
        task = "Play the game"
    
    play_game(game, task, mode="ollama" if config.backend == "ollama" else "cv")


if __name__ == "__main__":
    main()
