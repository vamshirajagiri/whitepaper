# whitepaper/shell.py
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from .scanner import scan_files
from .etl import etl_files
from .agent import WhitepaperMultiAgent
from .agents import HubSpokeSystem
from .ui.cyberpunk_terminal import cyber_terminal

console = Console()

class WhitepaperShell:
    def __init__(self, use_hub_spoke=True):
        self.active = True
        self.agent = None
        self.hub_spoke_system = None
        self.use_hub_spoke = use_hub_spoke
        self.cleaned_datasets_available = False
        # Cyberpunk neural network introduction
        if use_hub_spoke:
            cyber_terminal.matrix_intro()
        else:
            console.print("🤖 Legacy 3-Agent System Ready", style="bold green")
            console.print("💡 Type natural language queries or use commands like 'scan dataset.csv'\n", style="dim")

    def _check_cleaned_datasets(self):
        """Check if cleaned datasets are available"""
        cleaned_dir = Path("cleaned-dataset")
        if cleaned_dir.exists():
            # Look for both old and new naming patterns
            csv_files = list(cleaned_dir.glob("*_cleaned*.csv"))
            self.cleaned_datasets_available = len(csv_files) > 0
            return len(csv_files)
        return 0

    def _get_all_datasets(self):
        """Get all available datasets (both raw and cleaned)"""
        datasets = {}

        # Get raw datasets from current directory
        raw_files = list(Path(".").glob("*.csv")) + list(Path(".").glob("*.xls*"))
        datasets['raw'] = [f for f in raw_files if not f.name.endswith('_cleaned.csv')]

        # Get cleaned datasets
        cleaned_dir = Path("cleaned-dataset")
        if cleaned_dir.exists():
            # Look for both old and new naming patterns
            cleaned_files = list(cleaned_dir.glob("*_cleaned*.csv"))
            datasets['cleaned'] = cleaned_files
        else:
            datasets['cleaned'] = []

        return datasets

    def _find_dataset_file(self, filename: str):
        """Find a dataset file in both current directory and cleaned-dataset directory"""
        # First check current directory
        current_file = Path(filename)
        if current_file.exists():
            return current_file

        # Then check cleaned-dataset directory
        cleaned_dir = Path("cleaned-dataset")
        if cleaned_dir.exists():
            cleaned_file = cleaned_dir / filename
            if cleaned_file.exists():
                return cleaned_file

        # Try to find by partial name match
        datasets = self._get_all_datasets()
        for file_path in datasets['raw'] + datasets['cleaned']:
            if filename.lower() in file_path.name.lower():
                return file_path

        return None

    def _get_user_confirmation(self, message: str) -> bool:
        """Get yes/no confirmation from user"""
        while True:
            response = console.input(f"[yellow]{message} (y/n): [/yellow]").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                console.print("[red]Please answer 'y' or 'n'[/red]")

    def _is_command(self, text: str) -> bool:
        """Check if input is a command or natural language query"""
        commands = ['scan', 'etl', 'help', 'exit', 'list', 'datasets', 'status', 'toggle', 'demo', 'monitor', 'logs', 'traces', 'performance', 'agents']
        first_word = text.strip().split()[0].lower() if text.strip() else ""
        return first_word in commands or text.strip().endswith('.csv') or text.strip().endswith('.xls') or text.strip().endswith('.xlsx')


    def _initialize_agent(self):
        """Initialize the AI agent system"""
        if self.use_hub_spoke and not self.hub_spoke_system:
            console.print("[green]🚀 Initializing 9-Agent Hub-Spoke System...[/green]")
            try:
                self.hub_spoke_system = HubSpokeSystem()
                console.print("[green]✅ Hub-Spoke System ready![/green]")
            except Exception as e:
                console.print(f"[red]❌ Failed to initialize Hub-Spoke System: {e}[/red]")
                console.print("[yellow]💡 Falling back to legacy system...[/yellow]")
                self.use_hub_spoke = False
                self._initialize_legacy_agent()
        elif not self.use_hub_spoke and not self.agent:
            self._initialize_legacy_agent()
    
    def _initialize_legacy_agent(self):
        """Initialize legacy 3-agent system"""
        console.print("[green]🤖 Initializing Legacy Multi-Agent System...[/green]")
        try:
            self.agent = WhitepaperMultiAgent()
            console.print("[green]✅ Legacy AI Agent ready![/green]")
        except Exception as e:
            console.print(f"[red]❌ Failed to initialize AI Agent: {e}[/red]")
            console.print("[yellow]💡 You can still use basic commands[/yellow]")

    def _handle_command(self, cmd: str):
        """Handle traditional CLI commands"""
        args = cmd.split()
        command = args[0].lower()

        if command == "exit":
            self.active = False
            console.print("👋 Exiting Whitepaper Terminal...", style="bold green")

        elif command == "scan":
            files = args[1:] if len(args) > 1 else None
            if files:
                # Find files in both current and cleaned directories
                paths = []
                for filename in files:
                    file_path = self._find_dataset_file(filename)
                    if file_path:
                        paths.append(file_path)
                    else:
                        console.print(f"[red]❌ File not found: {filename}[/red]")
            else:
                # Scan all available datasets
                datasets = self._get_all_datasets()
                paths = datasets['raw'] + datasets['cleaned']

            if paths:
                console.print(f"[blue]🔎 Scanning {len(paths)} files...[/blue]")
                scan_files(paths)
                self._check_cleaned_datasets()  # Update availability
            else:
                console.print("[yellow]⚠️ No CSV/Excel files found[/yellow]")

        elif command == "etl":
            # Check for overwrite flag
            overwrite = False
            files = []

            for arg in args[1:]:
                if arg == "--overwrite":
                    overwrite = True
                else:
                    files.append(arg)

            if files:
                # Find files in both current and cleaned directories
                paths = []
                for filename in files:
                    file_path = self._find_dataset_file(filename)
                    if file_path:
                        paths.append(file_path)
                    else:
                        console.print(f"[red]❌ File not found: {filename}[/red]")
            else:
                # Run ETL on all raw datasets (not cleaned ones)
                datasets = self._get_all_datasets()
                paths = datasets['raw']

            if paths:
                mode = "overwrite" if overwrite else "hash-based"
                console.print(f"[blue]🔧 Running ETL on {len(paths)} files (mode: {mode})...[/blue]")
                etl_files(paths, overwrite=overwrite)
                self._check_cleaned_datasets()  # Update availability
            else:
                console.print("[yellow]⚠️ No raw CSV/Excel files found to process[/yellow]")

        elif command == "list" or command == "datasets":
            datasets = self._get_all_datasets()
            raw_count = len(datasets['raw'])
            cleaned_count = len(datasets['cleaned'])

            if raw_count > 0 or cleaned_count > 0:
                console.print("[green]📊 Available Datasets:[/green]")

                if raw_count > 0:
                    console.print(f"\n[yellow]📁 Raw Datasets ({raw_count}):[/yellow]")
                    for file in datasets['raw']:
                        console.print(f"  • {file.name}")

                if cleaned_count > 0:
                    console.print(f"\n[green]✨ Cleaned Datasets ({cleaned_count}):[/green]")
                    for file in datasets['cleaned']:
                        console.print(f"  • {file.name}")

                console.print(f"\n[blue]💡 Total: {raw_count + cleaned_count} datasets available[/blue]")
            else:
                console.print("[yellow]📭 No datasets found. Add CSV/Excel files to current directory.[/yellow]")

        elif command == "demo":
            console.print("[green]🚀 Launching Multi-Agent Demo System...[/green]")
            try:
                import sys
                import asyncio
                from pathlib import Path
                
                # Add project root to path
                project_root = Path(__file__).parent.parent
                sys.path.insert(0, str(project_root))
                
                from demo_agent_system import demo_main
                asyncio.run(demo_main())
            except ImportError as e:
                console.print(f"[red]❌ Demo system not available: {e}[/red]")
                console.print("[yellow]Run: pip install rich langchain-openai[/yellow]")
            except Exception as e:
                console.print(f"[red]❌ Demo error: {e}[/red]")

        elif command == "status":
            cleaned_count = self._check_cleaned_datasets()
            
            # Enhanced status with hub-spoke info
            agent_status = "❌ Not initialized"
            if self.use_hub_spoke and self.hub_spoke_system:
                agent_status = "✅ 9-Agent Hub-Spoke Ready"
            elif self.agent:
                agent_status = "✅ Legacy 3-Agent Ready"
            
            status_info = f"""
🤖 AI Agent System: {agent_status}
📊 Cleaned Datasets: {cleaned_count} available
💾 Vector DB: {'✅ Ready' if (self.agent and hasattr(self.agent, 'vectorstore') and self.agent.vectorstore) else '❌ Not indexed'}
🚀 Hub-Spoke Mode: {'✅ Active' if self.use_hub_spoke else '❌ Legacy Mode'}
            """
            console.print(Panel(status_info.strip(), title="System Status", border_style="blue"))

        elif command == "toggle":
            # Toggle between hub-spoke and legacy mode
            self.use_hub_spoke = not self.use_hub_spoke
            mode = "9-Agent Hub-Spoke" if self.use_hub_spoke else "Legacy 3-Agent"
            console.print(f"[green]✅ Switched to {mode} system[/green]")
            console.print(f"[yellow]💡 Your next query will use the {mode} system[/yellow]")
            
            # Reset agents to force re-initialization
            self.agent = None
            self.hub_spoke_system = None
        
        elif command == "monitor":
            console.print("[bright_cyan]▸ Neural Nexus Monitoring Dashboard[/bright_cyan]")
            console.print("[dim]Real-time monitoring would show here...[/dim]")
            console.print("[yellow]💡 Full monitoring dashboard coming soon![/yellow]")
        
        elif command == "logs":
            console.print("[bright_cyan]▸ Neural Network Logs[/bright_cyan]") 
            console.print("[dim]Agent communication logs would show here...[/dim]")
            console.print("[yellow]💡 Structured logging system coming soon![/yellow]")
        
        elif command == "traces":
            console.print("[bright_cyan]▸ Quantum Trace Analysis[/bright_cyan]")
            console.print("[dim]Distributed traces would show here...[/dim]")
            console.print("[yellow]💡 Trace analysis system coming soon![/yellow]")
        
        elif command == "help":
            help_text = """
[bold cyan]Available Commands:[/bold cyan]
  scan <file1> <file2> ...    - Scan datasets for overview (works with raw/cleaned)
  etl <file1> <file2> ...     - Run ETL cleaning on datasets (hash-based caching)
  etl --overwrite <files>     - Run ETL with overwrite mode (keeps latest version)
  list / datasets             - List all available datasets (raw + cleaned)
  status                      - Show system status (including hub-spoke mode)
  toggle                      - Switch between 9-Agent Hub-Spoke & Legacy systems
  
[bold magenta]Cyberpunk Observability:[/bold magenta]
  monitor                     - Neural Nexus monitoring dashboard ⚡
  logs                        - Agent communication logs 📋
  traces                      - Quantum trace analysis 🔍
  
  demo                        - Launch Multi-Agent Demo System 🚀
  help                        - Show this help
  exit                        - Exit terminal

[bold green]ETL Features:[/bold green]
  • Hash-based caching prevents duplicate processing
  • Unique cleaned files for each dataset version
  • Skip ETL if no changes detected
  • Use --overwrite to keep only latest cleaned version

[bold green]🤖 AI Agent Features:[/bold green]
  • 9-Agent Hub-Spoke: Cost-optimized (GPT-3.5 routing + GPT-4 analysis)
  • Cyberpunk neural network interface with Matrix-style effects
  • Real-time agent communication: 🧠 Neural Interface, ⚡ Quantum Router
  • Query validation & professional rejection system
  • Auto-selects datasets and web search based on query
  • Legacy 3-Agent system available as fallback

[bold green]Natural Language Queries:[/bold green]
  • "Analyze agricultural trends and provide policy recommendations"
  • "What are the consumption patterns in the dataset?"
  • "Give me insights about economic indicators"
  • "Show me correlations in the data"

[bold yellow]💡 Tip:[/bold yellow] Just type your questions naturally - the AI will understand!
            """
            console.print(Panel(help_text.strip(), title="Whitepaper Help", border_style="cyan"))

        else:
            console.print(f"[red]Unknown command:[/red] {command}")
            console.print("[dim]Type 'help' for available commands[/dim]")

    def _handle_natural_language(self, query: str):
        """Handle natural language queries with AI agent system"""
        self._initialize_agent()

        if self.use_hub_spoke and self.hub_spoke_system:
            console.print("[blue]🚀 Processing with 9-Agent Hub-Spoke System...[/blue]")
            try:
                # Use the new hub-spoke system
                result = self.hub_spoke_system.analyze_query(query)
                if result:
                    # Display the final response with enhanced formatting
                    console.print("\n" + "="*70, style="bold cyan")
                    console.print("[bold cyan]🎯 HUB-SPOKE ANALYSIS RESULTS[/bold cyan]")
                    console.print("="*70, style="bold cyan")
                    console.print(f"\n{result}\n")
                    console.print("="*70, style="dim")
                else:
                    console.print("[red]❌ Hub-Spoke analysis failed to produce results[/red]")
            except Exception as e:
                console.print(f"[red]❌ Hub-Spoke Analysis failed: {e}[/red]")
                console.print("[yellow]💡 Falling back to legacy system...[/yellow]")
                self.use_hub_spoke = False
                self._handle_natural_language(query)  # Retry with legacy
        elif self.agent:
            console.print("[blue]🤖 Processing with Legacy Multi-Agent System...[/blue]")
            try:
                # Use the legacy system
                result = self.agent.analyze_policy_query(query)
                if result:
                    console.print("\n" + "="*60, style="bold green")
                    console.print("[bold green]🎯 LEGACY ANALYSIS RESULTS[/bold green]")
                    console.print("="*60, style="bold green")
                    console.print(f"\n{result}\n")
                    console.print("="*60, style="dim")
                else:
                    console.print("[red]❌ Analysis failed to produce results[/red]")
            except Exception as e:
                console.print(f"[red]❌ AI Analysis failed: {e}[/red]")
                console.print("[yellow]💡 Try using basic commands instead[/yellow]")
        else:
            console.print("[red]❌ AI Agent not available. Check your OpenAI API key.[/red]")

    def run(self):
        """Main CLI loop with intelligent command/natural language detection"""
        # Initial setup flow
        console.print("\n" + "="*60, style="bold cyan")

        # Step 1: Ask about scanning
        if self._get_user_confirmation("🔎 Should I scan the available datasets first?"):
            console.print("[green]📊 Starting dataset scan...[/green]")
            scan_files(list(Path(".").glob("*.csv")) + list(Path(".").glob("*.xls*")))

        # Step 2: Ask about ETL
        if self._get_user_confirmation("🔧 Should I run ETL preprocessing on the datasets?"):
            console.print("[green]⚙️ Starting ETL pipeline...[/green]")
            etl_files(list(Path(".").glob("*.csv")) + list(Path(".").glob("*.xls*")))

        # Check cleaned datasets
        cleaned_count = self._check_cleaned_datasets()
        if cleaned_count > 0:
            console.print(f"[green]✅ {cleaned_count} cleaned datasets ready for analysis![/green]")
        else:
            console.print("[yellow]⚠️ No cleaned datasets found. You can still scan and process data.[/yellow]")

        console.print("\n" + "="*60, style="bold cyan")
        console.print("[bold green]🎯 Ready for your commands or questions![/bold green]")
        console.print("[dim]Type 'help' for available commands or ask questions naturally[/dim]\n")

        # Main interaction loop
        while self.active:
            try:
                user_input = console.input("[bold cyan]whitepaper>[/bold cyan] ").strip()

                if not user_input:
                    continue

                # Intelligent routing: command vs natural language
                if self._is_command(user_input):
                    self._handle_command(user_input)
                else:
                    self._handle_natural_language(user_input)

            except KeyboardInterrupt:
                self.active = False
                console.print("\n👋 Exiting Whitepaper Terminal...", style="bold green")
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")

    # Provide cmdloop for compatibility with callers expecting a cmd-like API
    def cmdloop(self):
        """Compatibility alias so callers can use .cmdloop() like cmd.Cmd."""
        return self.run()
