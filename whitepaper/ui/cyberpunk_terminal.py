# whitepaper/ui/cyberpunk_terminal.py
"""
🔥 CYBERPUNK FUTURISTIC TERMINAL INTERFACE 🔥
West Coast Tech Aesthetic - Blade Runner meets Silicon Valley
"""
import time
import random
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.columns import Columns
from rich.align import Align
from typing import List, Optional
import threading

console = Console()

class CyberpunkTerminal:
    """
    Futuristic hacker terminal with sick aesthetics
    Think Matrix meets West Coast tech vibes
    """
    
    def __init__(self):
        self.neon_colors = [
            "bright_cyan", "bright_magenta", "bright_green", 
            "bright_yellow", "bright_blue", "bright_red"
        ]
        self.glitch_chars = ["█", "▓", "▒", "░", "▄", "▀", "▌", "▐"]
        
    def glitch_text(self, text: str, intensity: float = 0.1) -> str:
        """Add glitch effect to text"""
        if random.random() > intensity:
            return text
        
        glitched = ""
        for char in text:
            if random.random() < 0.1:
                glitched += random.choice(self.glitch_chars)
            else:
                glitched += char
        return glitched
    
    def neural_loading(self, message: str, duration: float = 2.0):
        """Sick neural network loading animation"""
        frames = [
            "⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"
        ]
        
        end_time = time.time() + duration
        i = 0
        
        while time.time() < end_time:
            frame = frames[i % len(frames)]
            color = random.choice(self.neon_colors)
            
            # Add some glitch effect occasionally
            display_msg = self.glitch_text(message) if random.random() < 0.1 else message
            
            console.print(f"[{color}]{frame}[/{color}] {display_msg}", end="\r")
            time.sleep(0.1)
            i += 1
        
        console.print(f"[bright_green]✓[/bright_green] {message}")
    
    def matrix_cascade(self, lines: int = 3):
        """Matrix-style cascading effect"""
        matrix_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        
        for _ in range(lines):
            line = ""
            for _ in range(60):
                if random.random() < 0.7:
                    char = random.choice(matrix_chars)
                    color = "bright_green" if random.random() < 0.8 else "green"
                    line += f"[{color}]{char}[/{color}]"
                else:
                    line += " "
            
            console.print(line)
            time.sleep(0.05)
    
    def cyber_panel(self, title: str, content: str, style: str = "bright_cyan"):
        """Futuristic panel with cyber aesthetics"""
        # Add some glitch to title occasionally
        display_title = self.glitch_text(title) if random.random() < 0.05 else title
        
        panel = Panel(
            content,
            title=f"[{style}]▸ {display_title}[/{style}]",
            border_style=style,
            title_align="left"
        )
        console.print(panel)
    
    def agent_activation(self, agent_name: str, action: str):
        """Sick agent activation message"""
        activations = {
            "user_facing": "🧠 Neural Interface",
            "query_checker": "🛡️ Security Protocols", 
            "supervisor": "⚡ Quantum Router",
            "dataset_handler": "📡 Data Streams",
            "web_searcher": "🌐 Network Crawler",
            "analysis_stats": "🔥 Deep Analytics Engine",
            "analysis_viz": "🎨 Visualization Matrix",
            "analysis_insights": "💎 Intelligence Core",
            "checker": "✨ Quality Nexus"
        }
        
        cyber_name = activations.get(agent_name.lower().replace(" ", "_"), f"🤖 {agent_name}")
        
        # Futuristic action descriptions
        action_map = {
            "started": "INITIALIZED",
            "processing": "PROCESSING", 
            "completed": "COMPLETE",
            "forwarding": "ROUTING",
            "analyzing": "ANALYZING",
            "generating": "GENERATING"
        }
        
        cyber_action = action_map.get(action.lower(), action.upper())
        
        # Random neon color
        color = random.choice(["bright_cyan", "bright_magenta", "bright_green"])
        
        # Add occasional glitch effect
        if random.random() < 0.05:
            cyber_name = self.glitch_text(cyber_name, 0.3)
        
        console.print(f"[{color}]▸ {cyber_name}[/{color}] [dim]{cyber_action}[/dim]")
    
    def data_stream_effect(self, data_type: str, count: int):
        """Matrix-style data streaming effect"""
        colors = ["bright_green", "green", "dim green"]
        
        stream_text = Text()
        stream_text.append(f"▸ Data Stream [{data_type}] ", style="bright_cyan")
        
        for i in range(count):
            color = random.choice(colors)
            char = random.choice("█▓▒░")
            stream_text.append(char, style=color)
        
        stream_text.append(f" [{count} packets]", style="dim")
        console.print(stream_text)
    
    def neural_progress(self, message: str, total_steps: int = 100):
        """Futuristic progress bar with neural network vibes"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[bright_cyan]{task.description}"),
            BarColumn(bar_width=40, style="bright_cyan", complete_style="bright_green"),
            TextColumn("{task.percentage:>3.0f}%"),
            console=console,
            transient=True
        ) as progress:
            
            task = progress.add_task(f"▸ {message}", total=total_steps)
            
            for i in range(total_steps):
                # Simulate processing with variable speed
                time.sleep(random.uniform(0.02, 0.1))
                progress.update(task, advance=1)
                
                # Add occasional glitch effect
                if random.random() < 0.05:
                    progress.update(task, description=f"▸ {self.glitch_text(message, 0.2)}")
                    time.sleep(0.1)
                    progress.update(task, description=f"▸ {message}")
    
    def system_status(self, agents_active: int, cost: float, duration: float):
        """Cyberpunk system status display"""
        status_text = Text()
        
        # System header with glitch effect
        header = "NEURAL NEXUS STATUS"
        if random.random() < 0.1:
            header = self.glitch_text(header, 0.2)
        
        status_content = f"""
[bright_cyan]▸ Agents Online:[/bright_cyan] [bright_green]{agents_active}[/bright_green]
[bright_cyan]▸ Processing Cost:[/bright_cyan] [bright_yellow]${cost:.4f}[/bright_yellow]
[bright_cyan]▸ Neural Time:[/bright_cyan] [bright_magenta]{duration:.1f}s[/bright_magenta]
[bright_cyan]▸ Status:[/bright_cyan] [bright_green]OPTIMAL[/bright_green]
        """
        
        self.cyber_panel(header, status_content.strip(), "bright_cyan")
    
    def matrix_intro(self):
        """Professional intro with matrix effect"""
        intro_text = [
            "[bright_green]WHITEPAPER CLI[/bright_green]",
            "[bright_cyan]▸ 9-Agent System Ready[/bright_cyan]",
            "[bright_magenta]▸ Multi-Agent Analysis Active[/bright_magenta]",
            "[bright_yellow]▸ Ready for Deep Analysis[/bright_yellow]"
        ]
        
        # Matrix cascade effect
        self.matrix_cascade(2)
        
        for line in intro_text:
            console.print(line)
            time.sleep(0.3)
        
        console.print()
    
    def glitch_banner(self, text: str):
        """Sick glitch banner effect"""
        banner = Panel(
            Align.center(f"[bright_white]{text}[/bright_white]"),
            style="bright_red",
            title="[bright_red]▸ SYSTEM ALERT",
            title_align="left"
        )
        
        # Flash effect
        for _ in range(3):
            console.print(banner)
            time.sleep(0.1)
            console.clear()
            time.sleep(0.05)
        
        console.print(banner)
    
    def neural_shutdown(self):
        """Cool shutdown sequence"""
        shutdown_msgs = [
            "Neural pathways disconnecting...",
            "Quantum states collapsing...", 
            "Memory cores powering down...",
            "System hibernation initiated..."
        ]
        
        for msg in shutdown_msgs:
            self.neural_loading(msg, 1.0)
            time.sleep(0.2)
        
        console.print("[bright_red]▸ NEURAL NEXUS OFFLINE[/bright_red]")

# Global cyberpunk terminal instance
cyber_terminal = CyberpunkTerminal()
