# whitepaper/shell.py
import cmd
from pathlib import Path
from .utils import console, is_tabular
from .scanner import scan_files

class WhitepaperShell(cmd.Cmd):
    intro = "Type 'help' to see available commands. Type 'exit' to quit."
    prompt = "whitepaper > "

    def do_scan(self, arg: str):
        """Scan datasets.
Usage:
  scan                -> scans all CSV/XLS/XLSX files in cwd
  scan file1 file2    -> scans only provided files (relative or absolute)"""
        args = arg.split()
        paths = []
        if args:
            for a in args:
                p = Path(a)
                if not p.exists():
                    console.print(f"[yellow]⚠ {a} does not exist; skipping.")
                    continue
                if not is_tabular(p):
                    console.print(f"[yellow]⚠ {a} is not .csv/.xls/.xlsx; skipping.")
                    continue
                paths.append(p)
        else:
            cwd = Path.cwd()
            paths = sorted([f for f in cwd.glob("*.csv")] + [f for f in cwd.glob("*.xls")] + [f for f in cwd.glob("*.xlsx")])

        if not paths:
            console.print("[yellow]No dataset files found to scan (CSV/XLS/XLSX)")
            return

        console.print(f"📂 Found {len(paths)} file(s) to scan.")
        scan_files(paths)

    def do_list(self, arg: str):
        """List CSV/XLS/XLSX files in current folder."""
        p = Path.cwd()
        files = sorted([f for f in p.glob("*.csv")] + [f for f in p.glob("*.xls")] + [f for f in p.glob("*.xlsx")])
        if not files:
            console.print("[yellow]No dataset files found in current folder.")
            return
        for f in files:
            console.print(f" • {f.name}")

    def do_clear(self, arg: str):
        """Clear the screen."""
        console.clear()

    def do_exit(self, arg: str):
        """Exit whitepaper shell and return to normal terminal."""
        console.print("👋 Goodbye! Returning control to terminal.")
        return True

    def do_quit(self, arg: str):
        """Alias for exit"""
        return self.do_exit(arg)

    def emptyline(self):
        # don't repeat last command on empty line
        pass
