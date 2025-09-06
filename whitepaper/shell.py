# whitepaper/shell.py
from pathlib import Path
from rich.console import Console
from .scanner import scan_files
from .etl import etl_files

console = Console()

class WhitepaperShell:
    def __init__(self):
        self.active = True
        console.print("🤖 Whitepaper Shell is ready. Type commands ('help' for list).", style="bold green")

    def run(self):
        while self.active:
            try:
                cmd = console.input("[bold cyan]whitepaper>[/bold cyan] ").strip()
                if not cmd:
                    continue
                args = cmd.split()
                command = args[0].lower()

                if command == "exit":
                    self.active = False
                    console.print("👋 Exiting Whitepaper Shell...", style="bold green")

                elif command == "scan":
                    files = args[1:] if len(args) > 1 else None
                    paths = [Path(f) for f in files] if files else list(Path(".").glob("*.csv")) + list(Path(".").glob("*.xls*"))
                    scan_files(paths)

                elif command == "etl":
                    files = args[1:] if len(args) > 1 else None
                    paths = [Path(f) for f in files] if files else list(Path(".").glob("*.csv")) + list(Path(".").glob("*.xls*"))
                    etl_files(paths)

                elif command == "help":
                    console.print("""
[bold cyan]Available commands:[/bold cyan]
  scan <file1> <file2> ...   - Scan datasets for overview
  etl <file1> <file2> ...    - Run ETL cleaning on datasets
  exit                        - Exit CLI
""")
                else:
                    console.print(f"[red]Unknown command:[/red] {command}")

            except KeyboardInterrupt:
                self.active = False
                console.print("\n👋 Exiting Whitepaper Shell...", style="bold green")

    # Provide cmdloop for compatibility with callers expecting a cmd-like API
    def cmdloop(self):
        """Compatibility alias so callers can use .cmdloop() like cmd.Cmd."""
        return self.run()
