# whitepaper/utils.py
import hashlib
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

LOGO = r"""
██╗    ██╗██╗  ██╗██╗████████╗███████╗██████╗  █████╗ ██████╗ ███████╗██████╗
██║    ██║██║  ██║██║╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
██║ █╗ ██║███████║██║   ██║   █████╗  ██████╔╝███████║██████╔╝█████╗  ██████╔╝
██║███╗██║██╔══██║██║   ██║   ██╔══╝  ██╔═══╝ ██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗
╚███╔███╔╝██║  ██║██║   ██║   ███████╗██║     ██║  ██║██║     ███████╗██║  ██║
 ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝   ╚═╝   ╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
"""

def print_logo():
    """Print the ASCII logo once at startup."""
    console.print(Panel.fit(LOGO, title="[bold cyan]WHITEPAPER CLI[/bold cyan]", border_style="cyan"))
    console.print("🤖 Whitepaper v1.0.0 — The Policy Analyst’s CLI Assistant\n", style="bold green")

def is_tabular(path: Path) -> bool:
    """Return True if file looks like a CSV/XLS/XLSX we should scan."""
    return path.suffix.lower() in {".csv", ".xls", ".xlsx"}

def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate hash of a file using specified algorithm (md5 or sha256)."""
    hash_func = hashlib.md5() if algorithm == "md5" else hashlib.sha256()

    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()

def extract_hash_from_filename(filename: str) -> str:
    """Extract hash from cleaned filename like 'population_cleaned_ab12cd34.csv'."""
    if "_cleaned_" in filename:
        parts = filename.split("_cleaned_")
        if len(parts) == 2:
            hash_part = parts[1].split(".")[0]  # Remove extension
            return hash_part
    return None
