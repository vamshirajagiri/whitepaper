# whitepaper/hub_spoke_shell.py
"""
Enhanced Shell with Hub-Spoke Integration
Google-style incremental rollout with feature flags
"""
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
import time

from .shell import WhitepaperShell
from .observability.monitoring_dashboard import monitoring_dashboard
from .observability.structured_logger import structured_logger
from .observability.agent_tracer import tracer

console = Console()

class HubSpokeShell(WhitepaperShell):
    """
    Enhanced shell with 9-Agent Hub-Spoke system
    Inherits all existing functionality with seamless upgrade
    """
    
    def __init__(self, force_hub_spoke=True):
        # Initialize with hub-spoke enabled by default
        super().__init__(use_hub_spoke=force_hub_spoke)
        
        # Enhanced welcome message
        self._display_enhanced_welcome()
        
    def _display_enhanced_welcome(self):
        """Display enhanced welcome with hub-spoke features"""
        welcome_text = Text()
        welcome_text.append("🚀 Whitepaper ", style="bold cyan")
        welcome_text.append("9-Agent Hub-Spoke System", style="bold yellow")
        
        features = [
            "💰 Cost-Optimized: GPT-3.5 routing + GPT-4 analysis",
            "🔄 Real-time agent communication",
            "🔍 Smart query validation",
            "🌐 Web search integration", 
            "📊 Advanced data processing",
            "✅ Quality assurance pipeline"
        ]
        
        panel_content = "\n".join(features)
        
        console.print(Panel(
            panel_content,
            title="✨ Enhanced Features",
            border_style="green",
            title_align="center"
        ))
        
        console.print("\n[bold green]Ready for natural language queries or commands![/bold green]")
        console.print("[dim]Type 'help' for commands or 'toggle' to switch systems[/dim]\n")
    
    def cmdloop(self):
        """Enhanced command loop with streaming support"""
        try:
            while self.active:
                try:
                    # Enhanced prompt with system indicator
                    system_indicator = "🎯" if self.use_hub_spoke else "🤖"
                    user_input = console.input(f"[bold cyan]{system_indicator} whitepaper>[/bold cyan] ").strip()
                    
                    if not user_input:
                        continue
                        
                    # Process input with enhanced detection
                    if self._is_command(user_input):
                        self._handle_command(user_input)
                    else:
                        # Natural language with enhanced streaming
                        self._handle_natural_language_enhanced(user_input)
                        
                except KeyboardInterrupt:
                    console.print("\n[yellow]Use 'exit' to quit gracefully[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                    
        except KeyboardInterrupt:
            console.print("\n[green]👋 Goodbye![/green]")
    
    def _handle_natural_language_enhanced(self, query: str):
        """Enhanced natural language handling with streaming"""
        if self.use_hub_spoke:
            # Show real-time processing
            with console.status("[bold blue]🚀 Initializing Hub-Spoke System...", spinner="dots"):
                self._initialize_agent()
            
            if self.hub_spoke_system:
                console.print(f"[cyan]🎯 Query: {query}[/cyan]")
                console.print("[dim]Watch the agents communicate in real-time...[/dim]\n")
                
                try:
                    # The hub-spoke system will stream agent communications automatically
                    result = self.hub_spoke_system.analyze_query(query)
                    
                    if result:
                        self._display_enhanced_results(result)
                    else:
                        console.print("[red]❌ Analysis did not produce results[/red]")
                        
                except Exception as e:
                    console.print(f"[red]❌ Hub-Spoke system error: {e}[/red]")
                    console.print("[yellow]💡 Falling back to legacy system...[/yellow]")
                    self.use_hub_spoke = False
                    self._handle_natural_language_enhanced(query)
            else:
                console.print("[red]❌ Failed to initialize hub-spoke system[/red]")
        else:
            # Use legacy system
            self._handle_natural_language(query)
    
    def _display_enhanced_results(self, result: str):
        """Enhanced result display with better formatting"""
        console.print("\n" + "═"*80, style="bold cyan")
        console.print("[bold cyan]🎯 HUB-SPOKE ANALYSIS COMPLETE[/bold cyan]", justify="center")
        console.print("═"*80, style="bold cyan")
        
        # Display the result with nice formatting
        console.print(f"\n{result}\n")
        
        # Add completion footer
        console.print("═"*80, style="dim")
        console.print("[green]✅ Analysis completed successfully[/green]", justify="center")
        console.print("═"*80, style="dim")
        
    def _handle_command(self, cmd: str):
        """Enhanced command handling with additional features"""
        args = cmd.split()
        command = args[0].lower()
        
        if command == "performance":
            # Show system performance metrics
            self._show_performance_metrics()
        elif command == "agents":
            # Show agent status
            self._show_agent_status()
        elif command == "monitor":
            # Show monitoring dashboard
            self._show_monitoring_dashboard()
        elif command == "logs":
            # Show recent logs
            self._show_recent_logs()
        elif command == "traces":
            # Show recent traces
            self._show_recent_traces()
        else:
            # Use parent class method for existing commands
            super()._handle_command(cmd)
    
    def _show_performance_metrics(self):
        """Display system performance metrics"""
        if self.hub_spoke_system:
            status = self.hub_spoke_system.get_agent_status()
            metrics = f"""
🚀 9-Agent Hub-Spoke System:
   Agents Initialized: {status['agents_initialized']}
   Workflow Compiled: {'✅' if status['workflow_compiled'] else '❌'}
   
💰 Cost Optimization:
   GPT-3.5 Agents: 6 (routing, conversation, utilities)
   GPT-4 Agents: 3 (analysis, insights, quality check)
   
🎯 Available Agents:
{chr(10).join(['   • ' + agent for agent in status['available_agents']])}
            """
        else:
            metrics = "❌ Hub-Spoke system not initialized"
            
        console.print(Panel(metrics.strip(), title="System Performance", border_style="blue"))
    
    def _show_agent_status(self):
        """Show detailed agent status"""
        if self.hub_spoke_system:
            console.print("[green]🎯 9-Agent Hub-Spoke System Status:[/green]")
            console.print("  1. 👤 User Facing - GPT-3.5 (Conversation)")
            console.print("  2. 🔍 Query Checker - GPT-3.5 (Validation)")  
            console.print("  3. 🎯 Supervisor - GPT-3.5 (Hub Orchestration)")
            console.print("  4. 📊 Dataset Handler - GPT-3.5 (Data Processing)")
            console.print("  5. 🌐 Web Searcher - GPT-3.5 (External Context)")
            console.print("  6. 📈 Stats Analyst - GPT-4 (Statistical Analysis)")
            console.print("  7. 📊 Visualization - GPT-4 (Charts & Graphs)")
            console.print("  8. 💡 Insights - GPT-4 (Strategic Recommendations)")
            console.print("  9. ✅ Quality Checker - GPT-4 (Final Review)")
        else:
            console.print("[yellow]🤖 Legacy 3-Agent system active[/yellow]")
    
    def _show_monitoring_dashboard(self):
        """Show real-time monitoring dashboard"""
        console.print("[green]📈 Launching Real-time Monitoring Dashboard...[/green]")
        monitoring_dashboard.show_dashboard(duration_seconds=60)
    
    def _show_recent_logs(self):
        """Show recent structured logs"""
        console.print("[green]📋 Recent Agent Logs:[/green]")
        
        # Show logs for recent traces
        recent_traces = list(tracer._traces.keys())[-3:]  # Last 3 traces
        for trace_id in recent_traces:
            console.print(f"\n[cyan]Trace: {trace_id[:8]}...[/cyan]")
            structured_logger.display_live_logs(trace_id, max_lines=10)
    
    def _show_recent_traces(self):
        """Show recent trace analysis"""
        console.print("[green]🔍 Recent Trace Analysis:[/green]")
        
        recent_traces = list(tracer._traces.keys())[-5:]  # Last 5 traces
        for trace_id in recent_traces:
            trace_summary = structured_logger.get_trace_summary(trace_id)
            if trace_summary:
                console.print(f"\n[cyan]Trace {trace_id[:8]}...:[/cyan]")
                console.print(f"  Cost: ${trace_summary.get('total_cost', 0):.4f}")
                console.print(f"  Tokens: {trace_summary.get('total_tokens', 0)}")
                console.print(f"  Agents: {trace_summary.get('unique_agents', 0)}")
                console.print(f"  Errors: {trace_summary.get('error_count', 0)}")

# Create the enhanced shell instance
def create_enhanced_shell():
    """Factory function for creating enhanced shell"""
    return HubSpokeShell(force_hub_spoke=True)
