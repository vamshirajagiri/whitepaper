#!/usr/bin/env python3
"""
Simple test for the three-agent system
"""

from whitepaper.agent import ThreeAgentSystem
from rich.console import Console

console = Console()

def simple_test():
    """Simple test without full workflow"""
    console.print("\n[bold cyan]🧪 Simple Three-Agent Test[/bold cyan]\n")

    # Test basic functionality
    agent = ThreeAgentSystem()

    # Test greeting
    console.print("[green]Test 1: Greeting[/green]")
    result = agent.process_query("hello")
    console.print(f"Response: {result}")

    # Test status
    console.print("\n[green]Test 2: Status[/green]")
    result = agent.process_query("status")
    console.print(f"Response: {result}")

    # Test help
    console.print("\n[green]Test 3: Help[/green]")
    result = agent.process_query("help")
    console.print(f"Response: {result[:200]}...")

    console.print("\n[bold cyan]✅ Simple Tests Completed![/bold cyan]")

if __name__ == "__main__":
    simple_test()
