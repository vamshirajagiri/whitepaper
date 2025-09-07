# whitepaper/observability/monitoring_dashboard.py
"""
Real-time Monitoring Dashboard for AI Agents
Like what you'd see in Google Cloud Console or AWS CloudWatch
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.progress import Progress, BarColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
from typing import Dict, Any, List
import time
from pathlib import Path
import json

from .agent_tracer import tracer
from .structured_logger import structured_logger

console = Console()

class MonitoringDashboard:
    """
    Enterprise monitoring dashboard for AI agent observability
    Shows real-time metrics, costs, and performance
    """
    
    def __init__(self):
        self.update_interval = 2.0  # seconds
        self.running = False
    
    def create_cost_panel(self) -> Panel:
        """Create cost tracking panel"""
        # Get cost data from recent traces
        total_cost = 0
        gpt35_calls = 0
        gpt4_calls = 0
        
        # Sample data (in production, this would come from real metrics)
        for trace_id, spans in tracer._traces.items():
            for span in spans:
                if span.cost_estimate:
                    total_cost += span.cost_estimate
                    if "gpt-3.5" in (span.model_name or ""):
                        gpt35_calls += 1
                    elif "gpt-4" in (span.model_name or ""):
                        gpt4_calls += 1
        
        cost_content = f"""
💰 Cost Optimization Dashboard
├─ Total Cost (24h): ${total_cost:.4f}
├─ GPT-3.5 Calls: {gpt35_calls} (${gpt35_calls * 0.002:.4f})
├─ GPT-4 Calls: {gpt4_calls} (${gpt4_calls * 0.03:.4f})
└─ Cost Efficiency: {((gpt35_calls / (gpt35_calls + gpt4_calls)) * 100):.1f}% on cheaper model
        """
        
        return Panel(cost_content.strip(), title="💰 Cost Tracking", border_style="green")
    
    def create_performance_panel(self) -> Panel:
        """Create performance metrics panel"""
        # Calculate performance metrics
        all_spans = [span for spans in tracer._traces.values() for span in spans]
        
        if not all_spans:
            return Panel("No performance data available", title="📊 Performance", border_style="yellow")
        
        # Calculate metrics
        successful_spans = [s for s in all_spans if s.status.value == "ok"]
        error_spans = [s for s in all_spans if s.status.value == "error"]
        durations = [s.duration_ms for s in all_spans if s.duration_ms]
        
        success_rate = len(successful_spans) / len(all_spans) if all_spans else 0
        avg_duration = sum(durations) / len(durations) if durations else 0
        p95_duration = sorted(durations)[int(len(durations) * 0.95)] if durations else 0
        
        perf_content = f"""
📊 Performance Metrics (24h)
├─ Success Rate: {success_rate * 100:.1f}%
├─ Error Rate: {len(error_spans) / len(all_spans) * 100:.1f}%
├─ Avg Response Time: {avg_duration:.0f}ms
├─ P95 Response Time: {p95_duration:.0f}ms
└─ Total Queries: {len(set(s.trace_id for s in all_spans))}
        """
        
        return Panel(perf_content.strip(), title="📊 Performance", border_style="blue")
    
    def create_agent_status_table(self) -> Table:
        """Create agent status table"""
        table = Table(title="🤖 Agent Status & Performance")
        table.add_column("Agent", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Calls", justify="right")
        table.add_column("Avg Duration", justify="right")
        table.add_column("Success Rate", justify="right")
        table.add_column("Cost", justify="right")
        
        # Group spans by agent
        agent_metrics = {}
        for spans in tracer._traces.values():
            for span in spans:
                agent_name = span.agent_name
                if agent_name not in agent_metrics:
                    agent_metrics[agent_name] = {
                        'calls': 0, 'durations': [], 'successes': 0, 'costs': []
                    }
                
                agent_metrics[agent_name]['calls'] += 1
                if span.duration_ms:
                    agent_metrics[agent_name]['durations'].append(span.duration_ms)
                if span.status.value == "ok":
                    agent_metrics[agent_name]['successes'] += 1
                if span.cost_estimate:
                    agent_metrics[agent_name]['costs'].append(span.cost_estimate)
        
        # Add rows to table
        for agent_name, metrics in agent_metrics.items():
            calls = metrics['calls']
            avg_duration = sum(metrics['durations']) / len(metrics['durations']) if metrics['durations'] else 0
            success_rate = metrics['successes'] / calls if calls > 0 else 0
            total_cost = sum(metrics['costs'])
            
            # Status indicator
            if success_rate >= 0.95:
                status = "🟢 Healthy"
            elif success_rate >= 0.8:
                status = "🟡 Warning"
            else:
                status = "🔴 Critical"
            
            table.add_row(
                agent_name,
                status,
                str(calls),
                f"{avg_duration:.0f}ms",
                f"{success_rate * 100:.1f}%",
                f"${total_cost:.4f}"
            )
        
        return table
    
    def create_recent_traces_table(self) -> Table:
        """Create recent traces table"""
        table = Table(title="🔍 Recent Traces")
        table.add_column("Trace ID", style="dim")
        table.add_column("Query Preview", style="white")
        table.add_column("Duration", justify="right")
        table.add_column("Cost", justify="right")
        table.add_column("Status", justify="center")
        table.add_column("Agents", justify="right")
        
        # Get recent traces (last 10)
        recent_traces = list(tracer._traces.items())[-10:]
        
        for trace_id, spans in recent_traces:
            if not spans:
                continue
                
            # Get trace summary
            first_span = spans[0]
            query_preview = (first_span.input_data or {}).get('query', 'Unknown')[:30] + "..."
            total_duration = max(s.duration_ms or 0 for s in spans)
            total_cost = sum(s.cost_estimate or 0 for s in spans)
            has_errors = any(s.status.value == "error" for s in spans)
            agent_count = len(set(s.agent_name for s in spans))
            
            status = "🔴 Error" if has_errors else "🟢 Success"
            
            table.add_row(
                trace_id[:8] + "...",
                query_preview,
                f"{total_duration:.0f}ms",
                f"${total_cost:.4f}",
                status,
                str(agent_count)
            )
        
        return table
    
    def create_error_analysis_panel(self) -> Panel:
        """Create error analysis panel"""
        # Get recent errors
        all_spans = [span for spans in tracer._traces.values() for span in spans]
        error_spans = [s for s in all_spans if s.status.value == "error"]
        
        if not error_spans:
            error_content = "🟢 No recent errors detected"
        else:
            # Count error types
            error_types = {}
            for span in error_spans[-10:]:  # Last 10 errors
                error_msg = span.error_message or "Unknown error"
                error_key = error_msg[:50]  # First 50 chars
                error_types[error_key] = error_types.get(error_key, 0) + 1
            
            error_content = "🔴 Recent Errors:\\n"
            for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                error_content += f"├─ {count}x: {error}\\n"
        
        return Panel(error_content, title="🚨 Error Analysis", border_style="red")
    
    def create_live_dashboard_layout(self) -> Layout:
        """Create the full dashboard layout"""
        layout = Layout()
        
        # Split into top and bottom
        layout.split_column(
            Layout(name="top", ratio=1),
            Layout(name="bottom", ratio=2)
        )
        
        # Split top into metrics
        layout["top"].split_row(
            Layout(self.create_cost_panel(), name="cost"),
            Layout(self.create_performance_panel(), name="performance")
        )
        
        # Split bottom into tables
        layout["bottom"].split_row(
            Layout(self.create_agent_status_table(), name="agents"),
            Layout(name="right")
        )
        
        # Split right section
        layout["right"].split_column(
            Layout(self.create_recent_traces_table(), name="traces"),
            Layout(self.create_error_analysis_panel(), name="errors")
        )
        
        return layout
    
    def show_dashboard(self, duration_seconds: int = 30):
        """Show live updating dashboard"""
        console.print("🚀 Starting Real-time Agent Monitoring Dashboard...")
        console.print(f"📊 Updating every {self.update_interval}s for {duration_seconds}s")
        console.print("Press Ctrl+C to stop\\n")
        
        try:
            with Live(self.create_live_dashboard_layout(), refresh_per_second=1/self.update_interval) as live:
                start_time = time.time()
                
                while time.time() - start_time < duration_seconds:
                    time.sleep(self.update_interval)
                    live.update(self.create_live_dashboard_layout())
                    
        except KeyboardInterrupt:
            console.print("\\n[yellow]Dashboard stopped by user[/yellow]")
    
    def show_trace_details(self, trace_id: str):
        """Show detailed trace analysis"""
        trace_data = tracer.export_trace(trace_id)
        if not trace_data:
            console.print(f"[red]Trace {trace_id} not found[/red]")
            return
        
        # Create detailed trace panel
        trace_summary = f"""
🔍 Trace Analysis: {trace_id}

📊 Summary:
├─ Total Duration: {trace_data['total_duration_ms']:.0f}ms
├─ Total Cost: ${trace_data['total_cost']:.4f}
├─ Agent Count: {trace_data['agent_count']}
├─ Error Count: {trace_data['error_count']}
└─ Status: {'🟢 Success' if trace_data['error_count'] == 0 else '🔴 Errors'}

🤖 Agent Flow:
        """
        
        # Show agent execution flow
        for i, span_tree in enumerate(trace_data['spans']):
            span = span_tree['span']
            trace_summary += f"├─ {i+1}. {span['agent_name']} ({span.get('duration_ms', 0):.0f}ms)\\n"
            
            # Show children
            for child in span_tree.get('children', []):
                child_span = child['span']
                trace_summary += f"│  └─ {child_span['agent_name']} ({child_span.get('duration_ms', 0):.0f}ms)\\n"
        
        console.print(Panel(trace_summary, title="🔍 Detailed Trace Analysis", border_style="cyan"))
        
        # Show structured logs for this trace
        structured_logger.display_live_logs(trace_id)

# Create global dashboard instance
monitoring_dashboard = MonitoringDashboard()
