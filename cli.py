# subtrace/cli.py

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text

console = Console()


BANNER = r"""
 ███████╗██╗   ██╗██████╗ ████████╗██████╗  █████╗  ██████╗███████╗
 ██╔════╝██║   ██║██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██╔════╝
 ███████╗██║   ██║██████╔╝   ██║   ██████╔╝███████║██║     █████╗
 ╚════██║██║   ██║██╔══██╗   ██║   ██╔══██╗██╔══██║██║     ██╔══╝
 ███████║╚██████╔╝██████╔╝   ██║   ██║  ██║██║  ██║╚██████╗███████╗
 ╚══════╝ ╚═════╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝
"""


def show_banner():
    console.clear()

    console.print(
        Panel.fit(
            Text(BANNER, style="bold green"),
            border_style="green",
            title="Subtrace v2",
        )
    )


def build_menu():
    table = Table(title="Attack Surface Mapper")

    table.add_column("#", style="cyan", no_wrap=True)
    table.add_column("Action", style="green")

    table.add_row("1", "Passive Discovery")
    table.add_row("2", "Live Crawling")
    table.add_row("3", "Playwright SPA Scan")
    table.add_row("4", "Historical URL Analysis")
    table.add_row("5", "Technology Fingerprinting")
    table.add_row("6", "Risk Analysis")
    table.add_row("7", "Run Full Pipeline")
    table.add_row("8", "Export Reports")
    table.add_row("9", "Settings")
    table.add_row("0", "Exit")

    console.print(table)


def handle_choice(choice: str):
    if choice == "1":
        console.print("[cyan]Starting passive discovery...[/cyan]")

    elif choice == "2":
        console.print("[cyan]Starting crawler...[/cyan]")

    elif choice == "3":
        console.print("[cyan]Launching Playwright scan...[/cyan]")

    elif choice == "4":
        console.print("[cyan]Analyzing historical URLs...[/cyan]")

    elif choice == "5":
        console.print("[cyan]Running technology fingerprinting...[/cyan]")

    elif choice == "6":
        console.print("[cyan]Executing risk analysis...[/cyan]")

    elif choice == "7":
        console.print("[bold green]Running full Subtrace pipeline...[/bold green]")

    elif choice == "8":
        console.print("[green]Export manager opened.[/green]")

    elif choice == "9":
        console.print("[yellow]Settings panel coming soon.[/yellow]")

    elif choice == "0":
        return False

    else:
        console.print("[red]Invalid selection.[/red]")

    return True


def launch_cli():
    show_banner()

    running = True

    while running:
        build_menu()

        choice = Prompt.ask(
            "[bold green]Select option[/bold green]"
        )

        running = handle_choice(choice)
