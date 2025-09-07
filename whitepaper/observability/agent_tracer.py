# whitepaper/observability/agent_tracer.py
"""
Distributed Tracing for AI Agents
Similar to OpenTelemetry but specialized for multi-agent systems
"""
import time
import uuid
import json
from typing import Dict, List, Optional, Any, ContextManager
from dataclasses import dataclass, field, asdict
from contextlib import contextmanager
from enum import Enum
import threading
from pathlib import Path

class SpanStatus(Enum):
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"

@dataclass
class TraceContext:
    """Trace context that flows through all agents"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create_root(cls) -> 'TraceContext':
        """Create a root trace context"""
        trace_id = str(uuid.uuid4())
        return cls(trace_id=trace_id, span_id=str(uuid.uuid4()))
    
    def create_child(self) -> 'TraceContext':
        """Create a child span context"""
        return TraceContext(
            trace_id=self.trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=self.span_id,
            baggage=self.baggage.copy()
        )

@dataclass
class AgentSpan:
    """Individual agent execution span - like Jaeger/Zipkin spans"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    agent_name: str
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status: SpanStatus = SpanStatus.UNSET
    
    # Agent-specific attributes
    model_name: Optional[str] = None
    model_provider: str = "openai"
    token_usage: Dict[str, int] = field(default_factory=dict)
    cost_estimate: Optional[float] = None
    
    # LLM attributes
    prompt_tokens: int = 0
    completion_tokens: int = 0
    temperature: float = 0.3
    
    # Execution details
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Agent communication
    messages_sent: List[Dict[str, Any]] = field(default_factory=list)
    messages_received: List[Dict[str, Any]] = field(default_factory=list)
    
    # Custom tags and logs
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def finish(self, status: SpanStatus = SpanStatus.OK, error: Optional[str] = None):
        """Finish the span"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status
        if error:
            self.error_message = error
            self.status = SpanStatus.ERROR
    
    def add_tag(self, key: str, value: str):
        """Add a tag to the span"""
        self.tags[key] = value
    
    def add_log(self, message: str, level: str = "info", **kwargs):
        """Add a log entry to the span"""
        log_entry = {
            "timestamp": time.time(),
            "level": level,
            "message": message,
            **kwargs
        }
        self.logs.append(log_entry)
    
    def record_llm_usage(self, prompt_tokens: int, completion_tokens: int, model: str):
        """Record LLM usage metrics"""
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.model_name = model
        self.token_usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }
        
        # Estimate cost (rough estimates)
        if "gpt-4" in model:
            self.cost_estimate = (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000
        elif "gpt-3.5" in model:
            self.cost_estimate = (prompt_tokens * 0.0015 + completion_tokens * 0.002) / 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary for serialization"""
        return asdict(self)

class AgentTracer:
    """
    Distributed tracer for AI agents
    Tracks execution flows across multiple agents like Jaeger/Zipkin
    """
    
    def __init__(self):
        self._spans: Dict[str, AgentSpan] = {}
        self._active_spans: Dict[str, AgentSpan] = {}  # thread_local
        self._traces: Dict[str, List[AgentSpan]] = {}
        self._lock = threading.Lock()
        
        # Storage
        self.trace_storage_path = Path("traces")
        self.trace_storage_path.mkdir(exist_ok=True)
    
    @contextmanager
    def start_span(
        self, 
        agent_name: str, 
        operation: str, 
        context: Optional[TraceContext] = None
    ) -> ContextManager[AgentSpan]:
        """
        Start a new agent span - like OpenTelemetry's start_span
        
        Usage:
        with tracer.start_span("user_facing_agent", "process_query") as span:
            span.add_tag("query_type", "complex")
            # ... agent execution
            span.record_llm_usage(150, 300, "gpt-4")
        """
        if context is None:
            context = TraceContext.create_root()
        
        span = AgentSpan(
            span_id=context.span_id,
            trace_id=context.trace_id,
            parent_span_id=context.parent_span_id,
            agent_name=agent_name,
            operation_name=operation,
            start_time=time.time()
        )
        
        # Store span
        with self._lock:
            self._spans[span.span_id] = span
            thread_id = threading.get_ident()
            self._active_spans[str(thread_id)] = span
            
            # Group by trace
            if span.trace_id not in self._traces:
                self._traces[span.trace_id] = []
            self._traces[span.trace_id].append(span)
        
        try:
            yield span
        except Exception as e:
            span.finish(SpanStatus.ERROR, str(e))
            raise
        else:
            span.finish(SpanStatus.OK)
        finally:
            # Clean up active span
            with self._lock:
                thread_id = threading.get_ident()
                self._active_spans.pop(str(thread_id), None)
    
    def get_current_span(self) -> Optional[AgentSpan]:
        """Get the currently active span"""
        thread_id = threading.get_ident()
        return self._active_spans.get(str(thread_id))
    
    def get_trace(self, trace_id: str) -> List[AgentSpan]:
        """Get all spans for a trace"""
        return self._traces.get(trace_id, [])
    
    def export_trace(self, trace_id: str) -> Dict[str, Any]:
        """Export a complete trace for analysis"""
        spans = self.get_trace(trace_id)
        if not spans:
            return {}
        
        # Build trace hierarchy
        root_spans = [s for s in spans if s.parent_span_id is None]
        
        def build_span_tree(parent_span: AgentSpan) -> Dict[str, Any]:
            children = [s for s in spans if s.parent_span_id == parent_span.span_id]
            return {
                "span": parent_span.to_dict(),
                "children": [build_span_tree(child) for child in children]
            }
        
        trace_data = {
            "trace_id": trace_id,
            "total_duration_ms": max(s.duration_ms or 0 for s in spans),
            "total_cost": sum(s.cost_estimate or 0 for s in spans),
            "agent_count": len(set(s.agent_name for s in spans)),
            "error_count": len([s for s in spans if s.status == SpanStatus.ERROR]),
            "spans": [build_span_tree(root) for root in root_spans]
        }
        
        # Save to file
        trace_file = self.trace_storage_path / f"trace_{trace_id}.json"
        with open(trace_file, 'w') as f:
            json.dump(trace_data, f, indent=2)
        
        return trace_data
    
    def get_agent_metrics(self, agent_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics for a specific agent"""
        cutoff_time = time.time() - (hours * 3600)
        
        agent_spans = [
            s for spans_list in self._traces.values() 
            for s in spans_list 
            if s.agent_name == agent_name and s.start_time > cutoff_time
        ]
        
        if not agent_spans:
            return {}
        
        total_executions = len(agent_spans)
        successful_executions = len([s for s in agent_spans if s.status == SpanStatus.OK])
        failed_executions = len([s for s in agent_spans if s.status == SpanStatus.ERROR])
        
        durations = [s.duration_ms for s in agent_spans if s.duration_ms]
        costs = [s.cost_estimate for s in agent_spans if s.cost_estimate]
        
        return {
            "agent_name": agent_name,
            "time_window_hours": hours,
            "total_executions": total_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "error_rate": failed_executions / total_executions if total_executions > 0 else 0,
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "p95_duration_ms": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
            "total_cost": sum(costs),
            "avg_cost_per_execution": sum(costs) / len(costs) if costs else 0,
            "total_tokens": sum(s.token_usage.get("total_tokens", 0) for s in agent_spans),
            "most_common_errors": self._get_top_errors(agent_spans)
        }
    
    def _get_top_errors(self, spans: List[AgentSpan], limit: int = 5) -> List[Dict[str, Any]]:
        """Get most common error messages"""
        error_counts = {}
        for span in spans:
            if span.error_message:
                error_counts[span.error_message] = error_counts.get(span.error_message, 0) + 1
        
        return [
            {"error": error, "count": count} 
            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        ]

# Global tracer instance
tracer = AgentTracer()
