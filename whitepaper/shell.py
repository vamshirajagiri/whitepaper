# whitepaper/shell.py
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from .scanner import scan_files
from .etl import etl_files
from .simple_agents import Simple4AgentSystem

console = Console()

class WhitepaperShell:
    def __init__(self):
        self.active = True
        self.agent_system = Simple4AgentSystem()
        console.print("🚀 Whitepaper - Simple 4-Agent Policy Analysis CLI", style="bold cyan")
        console.print("💡 Type commands or natural language queries\n", style="dim")

    def _get_all_datasets(self):
        """Get all available datasets"""
        datasets = {}
        raw_files = list(Path(".").glob("*.csv")) + list(Path(".").glob("*.xls*"))
        datasets['raw'] = [f for f in raw_files if not f.name.endswith('_cleaned.csv')]
        
        cleaned_dir = Path("cleaned-dataset")
        if cleaned_dir.exists():
            datasets['cleaned'] = list(cleaned_dir.glob("*_cleaned*.csv"))
        else:
            datasets['cleaned'] = []
        return datasets

    def _is_command(self, text: str) -> bool:
        """Check if input is a command"""
        commands = ['scan', 'etl', 'help', 'exit', 'list', 'status']
        first_word = text.strip().split()[0].lower() if text.strip() else ""
        return first_word in commands

    def _initialize_agent(self):
        """Initialize the Simple 4-Agent system"""
        # Agent system is already initialized in __init__
        console.print("[green]✅ Simple 4-Agent System ready![/green]")

    def _handle_command(self, cmd: str):
        """Handle CLI commands"""
        args = cmd.split()
        command = args[0].lower()

        if command == "exit":
            self.active = False
            console.print("👋 Goodbye!", style="bold green")
        
        elif command == "list":
            datasets = self._get_all_datasets()
            raw_count = len(datasets['raw'])
            cleaned_count = len(datasets['cleaned'])
            
            console.print("[green]📊 Available Datasets:[/green]")
            if raw_count > 0:
                console.print(f"\n[yellow]📁 Raw ({raw_count}):[/yellow]")
                for file in datasets['raw']:
                    console.print(f"  • {file.name}")
            
            if cleaned_count > 0:
                console.print(f"\n[green]✨ Cleaned ({cleaned_count}):[/green]")
                for file in datasets['cleaned']:
                    console.print(f"  • {file.name}")
            
            console.print(f"\n[blue]💡 Total: {raw_count + cleaned_count} datasets[/blue]")

        elif command == "scan":
            datasets = self._get_all_datasets()
            paths = datasets['raw'] + datasets['cleaned']
            if paths:
                console.print(f"[blue]🔎 Indexing {len(paths)} files into vector database...[/blue]")
                result = self.agent_system.handle_input("scan")
                console.print(f"[green]✅ {result}[/green]")
            else:
                console.print("[yellow]⚠️ No files found[/yellow]")

        elif command == "etl":
            datasets = self._get_all_datasets()
            paths = datasets['raw']
            if paths:
                console.print(f"[blue]🔧 Running ETL on {len(paths)} files...[/blue]")
                etl_files(paths)
            else:
                console.print("[yellow]⚠️ No raw files to process[/yellow]")

        elif command == "status":
            datasets = self._get_all_datasets()
            agent_status = "✅ Ready"
            
            # Get reports directory info
            reports_path = Path("reports")
            reports_count = len(list(reports_path.glob("*.txt"))) if reports_path.exists() else 0
            
            status = f"""
🤖 Simple 4-Agent System: {agent_status}
📊 Raw Datasets: {len(datasets['raw'])}
✨ Cleaned Datasets: {len(datasets['cleaned'])}
📁 Reports Generated: {reports_count}
🔍 Vector DB: Available for queries
"""
            console.print(Panel(status.strip(), title="Simple 4-Agent System Status", border_style="blue"))

        elif command == "help":
            help_text = """
[bold cyan]Commands:[/bold cyan]
  list                  - Show available datasets
  scan                  - Index datasets into vector database
  etl                   - Clean raw datasets
  status                - Show system status
  help                  - Show this help
  exit                  - Exit

[bold green]Natural Language Queries:[/bold green]
  Ask questions about your data and get AI-powered analysis!
  Examples:
    "What trends do you see in the agricultural data?"
    "Analyze the healthcare spending patterns"
    "What policy recommendations do you have?"
    
[bold yellow]Reports:[/bold yellow]
  Analysis results and policy recommendations are saved
  automatically in the 'reports/' directory
"""
            console.print(Panel(help_text.strip(), title="Simple 4-Agent System Help", border_style="cyan"))

        else:
            console.print(f"[red]Unknown command: {command}[/red]")

    def _handle_natural_language(self, query: str):
        """Handle natural language queries"""
        console.print("[blue]🚀 Processing with Simple 4-Agent System...[/blue]")
        try:
            result = self.agent_system.handle_input(query)
            if result:
                console.print("\n" + "="*80, style="bold cyan")
                console.print("[bold cyan]🎯 AGENT ANALYSIS RESULTS[/bold cyan]")
                console.print("="*80, style="bold cyan")
                console.print(f"\n{result}\n")
                console.print("="*80, style="dim")
            else:
                console.print("[red]❌ No results returned[/red]")
        except Exception as e:
            console.print(f"[red]❌ Analysis failed: {e}[/red]")

    def run(self):
        """Main CLI loop"""
        console.print("🎯 Ready for your questions and commands!")
        console.print("[dim]Type 'help' for available commands\n")
        
        while self.active:
            try:
                user_input = console.input("[bold cyan]whitepaper>[/bold cyan] ").strip()
                
                if not user_input:
                    continue
                
                if self._is_command(user_input):
                    self._handle_command(user_input)
                else:
                    self._handle_natural_language(user_input)
                    
            except KeyboardInterrupt:
                self.active = False
                console.print("\n👋 Goodbye!", style="bold green")
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")

    def cmdloop(self):
        """Compatibility method"""
        return self.run()