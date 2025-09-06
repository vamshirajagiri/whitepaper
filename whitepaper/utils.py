# whitepaper/utils.py
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

LOGO = r"""
██╗    ██╗██╗  ██╗██╗████████╗██████╗  █████╗ ██████╗ ███████╗██████╗ 
██║    ██║██║  ██║██║╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
██║ █╗ ██║███████║██║   ██║   ██████╔╝███████║██████╔╝█████╗  ██████╔╝
██║███╗██║██╔══██║██║   ██║   ██╔═══╝ ██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗
╚███╔███╔╝██║  ██║██║   ██║   ██║     ██║  ██║██║     ███████╗██║  ██║
 ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝   ╚═╝   ╚═╝     ╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
"""

def print_logo():
    """Print the ASCII logo once at startup."""
    console.print(Panel.fit(LOGO, title="[bold cyan]WHITEPAPER CLI[/bold cyan]", border_style="cyan"))
    console.print("🤖 Whitepaper v1.0.0 — The Policy Analyst’s CLI Assistant\n", style="bold green")

def is_tabular(path: Path) -> bool:
    """Return True if file looks like a CSV/XLS/XLSX we should scan."""
    return path.suffix.lower() in {".csv", ".xls", ".xlsx"}
