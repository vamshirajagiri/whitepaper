# whitepaper/agents/state.py
"""
State Management for 9-Agent Hub-and-Spoke System
"""
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, TypedDict, Annotated
from dataclasses import dataclass, field
from enum import Enum
import operator

class AgentType(Enum):
    """9-Agent System Types"""
    USER_FACING = "👤 User Interface"
    QUERY_CHECKER = "🔍 Query Checker"
    SUPERVISOR = "🎯 Supervisor"        # HUB
    DATASET_HANDLER = "📊 Dataset Handler"
    WEB_SEARCHER = "🌐 Web Searcher"
    ANALYSIS_STATS = "📈 Stats Analyst"
    ANALYSIS_VIZ = "📊 Visualization"
    ANALYSIS_INSIGHTS = "💡 Insights"
    CHECKER = "✅ Quality Checker"

@dataclass
class AgentMessage:
    """Inter-agent communication message"""
    from_agent: AgentType
    to_agent: AgentType
    content: str
    timestamp: float = field(default_factory=time.time)
    message_type: str = "communication"
    
    def __str__(self):
        return f"[{self.from_agent.value} → {self.to_agent.value}]: {self.content}"

class MultiAgentState(TypedDict):
    """Shared state across all 9 agents"""
    # Core query flow
    query: str
    current_agent: AgentType
    next_agent: Optional[AgentType]
    
    # Data management
    datasets: List[Path]
    cleaned_datasets: List[Path]
    vector_db: Optional[Any]
    
    # Analysis pipeline  
    is_analysis_query: bool
    web_context: Optional[Dict[str, Any]]
    stats_results: Optional[Dict[str, Any]]
    viz_data: Optional[Dict[str, Any]]
    insights: Optional[Dict[str, Any]]
    
    # Quality control
    checker_feedback: Optional[Dict[str, Any]]
    revision_count: int
    approved: bool
    
    # Final output
    final_report: Optional[str]
    
    # Communication system
    agent_messages: Annotated[List[AgentMessage], operator.add]
    execution_log: Annotated[List[str], operator.add]
    
    # Performance tracking
    start_time: float
    model_costs: Dict[str, int]  # Track API calls by model type
