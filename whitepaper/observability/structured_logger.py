# whitepaper/observability/structured_logger.py
"""
Production-Grade Structured Logging for AI Agents
Like what Google/Meta/OpenAI use for their AI systems
"""
import json
import time
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from ..agents.state import AgentType

console = Console()

class StructuredLogger:
    """
    Enterprise structured logger for AI agents
    Outputs JSON logs that can be ingested by ELK stack, Splunk, etc.
    """
    
    def __init__(self, log_level: str = "INFO"):
        # Create logs directory
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Set up structured logging
        self.logger = logging.getLogger("whitepaper.agents")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # JSON file handler for machine processing
        json_handler = logging.FileHandler(self.log_dir / "agents.jsonl")
        json_handler.setFormatter(self.JsonFormatter())
        
        # Human-readable handler for development
        human_handler = logging.FileHandler(self.log_dir / "agents.log")
        human_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        self.logger.addHandler(json_handler)
        self.logger.addHandler(human_handler)
    
    class JsonFormatter(logging.Formatter):
        """Custom formatter to output structured JSON logs"""
        
        def format(self, record):
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            
            # Add extra fields if present
            if hasattr(record, 'extra_fields'):
                log_entry.update(record.extra_fields)
            
            return json.dumps(log_entry)
    
    def log_agent_start(self, agent_type: AgentType, query: str, trace_id: str):
        """Log agent execution start"""
        extra_fields = {
            "event_type": "agent_start",
            "agent_type": agent_type.value,
            "agent_name": agent_type.name.lower(),
            "query": query,
            "trace_id": trace_id,
            "query_length": len(query),
            "query_hash": hash(query)
        }
        
        self.logger.info(
            f"Agent {agent_type.value} started processing query",
            extra={'extra_fields': extra_fields}
        )
    
    def log_agent_completion(
        self, 
        agent_type: AgentType, 
        trace_id: str,
        duration_ms: float,
        success: bool,
        token_usage: Optional[Dict[str, int]] = None,
        cost: Optional[float] = None,
        error: Optional[str] = None
    ):
        """Log agent execution completion"""
        extra_fields = {
            "event_type": "agent_completion",
            "agent_type": agent_type.value,
            "agent_name": agent_type.name.lower(),
            "trace_id": trace_id,
            "duration_ms": duration_ms,
            "success": success,
            "token_usage": token_usage or {},
            "estimated_cost": cost or 0.0,
            "error_message": error
        }
        
        level = "info" if success else "error"
        message = f"Agent {agent_type.value} completed in {duration_ms:.1f}ms"
        if not success and error:
            message += f" with error: {error[:100]}..."
        
        getattr(self.logger, level)(
            message,
            extra={'extra_fields': extra_fields}
        )
    
    def log_agent_communication(
        self,
        from_agent: AgentType,
        to_agent: AgentType,
        message_content: str,
        trace_id: str,
        message_type: str = "standard"
    ):
        """Log inter-agent communication"""
        extra_fields = {
            "event_type": "agent_communication",
            "from_agent": from_agent.value,
            "to_agent": to_agent.value,
            "message_type": message_type,
            "message_length": len(message_content),
            "message_preview": message_content[:200],
            "trace_id": trace_id
        }
        
        self.logger.info(
            f"Message from {from_agent.value} to {to_agent.value}",
            extra={'extra_fields': extra_fields}
        )
    
    def log_llm_call(
        self,
        agent_type: AgentType,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: float,
        cost: float,
        trace_id: str,
        temperature: float = 0.3
    ):
        """Log LLM API calls for cost tracking and performance"""
        extra_fields = {
            "event_type": "llm_call",
            "agent_type": agent_type.value,
            "model_name": model_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "duration_ms": duration_ms,
            "cost_usd": cost,
            "temperature": temperature,
            "trace_id": trace_id,
            "cost_per_token": cost / (prompt_tokens + completion_tokens) if (prompt_tokens + completion_tokens) > 0 else 0
        }
        
        self.logger.info(
            f"LLM call to {model_name}: {prompt_tokens + completion_tokens} tokens, ${cost:.4f}",
            extra={'extra_fields': extra_fields}
        )
    
    def log_query_classification(
        self,
        query: str,
        classification: str,
        confidence: float,
        trace_id: str
    ):
        """Log query classification results"""
        extra_fields = {
            "event_type": "query_classification",
            "query_hash": hash(query),
            "query_length": len(query),
            "classification": classification,
            "confidence": confidence,
            "trace_id": trace_id
        }
        
        self.logger.info(
            f"Query classified as '{classification}' with {confidence:.2f} confidence",
            extra={'extra_fields': extra_fields}
        )
    
    def log_error(
        self,
        agent_type: AgentType,
        error_message: str,
        trace_id: str,
        error_type: str = "unknown",
        stack_trace: Optional[str] = None
    ):
        """Log errors with context"""
        extra_fields = {
            "event_type": "agent_error",
            "agent_type": agent_type.value,
            "error_type": error_type,
            "error_message": error_message,
            "trace_id": trace_id,
            "stack_trace": stack_trace
        }
        
        self.logger.error(
            f"Error in {agent_type.value}: {error_message}",
            extra={'extra_fields': extra_fields}
        )
    
    def display_live_logs(self, trace_id: str, max_lines: int = 20):
        """Display recent logs for a trace in the terminal"""
        try:
            # Read recent logs
            log_file = self.log_dir / "agents.jsonl"
            if not log_file.exists():
                return
            
            recent_logs = []
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if log_entry.get('trace_id') == trace_id:
                            recent_logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
            
            if not recent_logs:
                return
            
            # Show last N logs
            recent_logs = recent_logs[-max_lines:]
            
            # Create table
            table = Table(title=f"Live Agent Logs (Trace: {trace_id[:8]}...)")
            table.add_column("Time", style="dim")
            table.add_column("Agent", style="cyan")
            table.add_column("Event", style="green")
            table.add_column("Details", style="white")
            
            for log in recent_logs:
                timestamp = log.get('timestamp', '')[:19]  # Remove microseconds
                agent = log.get('agent_type', 'Unknown')[:15]
                event_type = log.get('event_type', 'log')
                message = log.get('message', '')[:60]
                
                # Color code by event type
                if event_type == 'agent_error':
                    agent = f"[red]{agent}[/red]"
                    message = f"[red]{message}[/red]"
                elif event_type == 'llm_call':
                    cost = log.get('cost_usd', 0)
                    message = f"${cost:.4f} - {message}"
                
                table.add_row(timestamp, agent, event_type, message)
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error displaying logs: {e}[/red]")
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get summary statistics for a trace"""
        try:
            log_file = self.log_dir / "agents.jsonl"
            if not log_file.exists():
                return {}
            
            trace_logs = []
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if log_entry.get('trace_id') == trace_id:
                            trace_logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
            
            if not trace_logs:
                return {}
            
            # Calculate summary
            total_cost = sum(log.get('cost_usd', 0) for log in trace_logs)
            total_tokens = sum(log.get('total_tokens', 0) for log in trace_logs)
            error_count = len([log for log in trace_logs if log.get('event_type') == 'agent_error'])
            llm_calls = len([log for log in trace_logs if log.get('event_type') == 'llm_call'])
            unique_agents = len(set(log.get('agent_type') for log in trace_logs if log.get('agent_type')))
            
            start_time = min(log.get('timestamp', '') for log in trace_logs)
            end_time = max(log.get('timestamp', '') for log in trace_logs)
            
            return {
                "trace_id": trace_id,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "llm_calls": llm_calls,
                "error_count": error_count,
                "unique_agents": unique_agents,
                "start_time": start_time,
                "end_time": end_time,
                "total_events": len(trace_logs)
            }
            
        except Exception as e:
            console.print(f"[red]Error getting trace summary: {e}[/red]")
            return {}

# Global logger instance
structured_logger = StructuredLogger()
