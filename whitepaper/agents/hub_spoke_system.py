# whitepaper/agents/hub_spoke_system.py
"""
Hub-and-Spoke System using LangGraph
Orchestrates 9-Agent workflow with conditional routing
"""
import time
from pathlib import Path
from typing import Dict, Any, Literal
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from .state import MultiAgentState, AgentType
from .nine_agents import (
    UserFacingAgent, QueryCheckerAgent, SupervisorAgent,
    DatasetHandlerAgent, WebSearcherAgent, AnalysisStatsAgent,
    AnalysisVizAgent, AnalysisInsightsAgent, CheckerAgent
)
try:
    from whitepaper.ui.cyberpunk_terminal import cyber_terminal
except ImportError:
    # Fallback if import fails
    class MockCyberTerminal:
        def agent_activation(self, *args): pass
        def neural_loading(self, *args): pass
        def data_stream_effect(self, *args): pass
        def system_status(self, *args): pass
        def neural_progress(self, *args): pass
    cyber_terminal = MockCyberTerminal()

console = Console()

class HubSpokeSystem:
    """
    9-Agent Hub-and-Spoke System
    Hub: Supervisor Agent orchestrates workflow
    Spokes: Specialized agents handle specific tasks
    """
    
    def __init__(self):
        self.agents = self._initialize_agents()
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
        
    def _initialize_agents(self) -> Dict[AgentType, Any]:
        """Initialize all 9 agents"""
        cyber_terminal.neural_loading("⚡ Neural Network Initializing", 1.5)
        
        agents = {
            AgentType.USER_FACING: UserFacingAgent(),
            AgentType.QUERY_CHECKER: QueryCheckerAgent(),
            AgentType.SUPERVISOR: SupervisorAgent(),
            AgentType.DATASET_HANDLER: DatasetHandlerAgent(),
            AgentType.WEB_SEARCHER: WebSearcherAgent(),
            AgentType.ANALYSIS_STATS: AnalysisStatsAgent(),
            AgentType.ANALYSIS_VIZ: AnalysisVizAgent(),
            AgentType.ANALYSIS_INSIGHTS: AnalysisInsightsAgent(),
            AgentType.CHECKER: CheckerAgent()
        }
        
        cyber_terminal.agent_activation("Neural Network", "ONLINE")
        cyber_terminal.data_stream_effect("AGENTS", len(agents))
        return agents
        
    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow with conditional routing"""
        workflow = StateGraph(MultiAgentState)
        
        # Add all agent nodes
        for agent_type, agent in self.agents.items():
            workflow.add_node(agent_type.name.lower(), agent.execute)
        
        # Define the hub-spoke flow
        workflow.set_entry_point("user_facing")
        
        # User Facing -> Query Checker (for complex queries)
        workflow.add_conditional_edges(
            "user_facing",
            self._should_continue_from_user_facing,
            {
                "checker": "query_checker",
                "end": END
            }
        )
        
        # Query Checker -> Supervisor (for approved queries)
        workflow.add_conditional_edges(
            "query_checker", 
            self._should_continue_from_query_checker,
            {
                "supervisor": "supervisor",
                "end": END
            }
        )
        
        # Supervisor -> Hub routing (to spokes)
        workflow.add_conditional_edges(
            "supervisor",
            self._route_from_supervisor,
            {
                "dataset_handler": "dataset_handler",
                "web_searcher": "web_searcher", 
                "analysis_stats": "analysis_stats"
            }
        )
        
        # Dataset Handler -> Analysis Stats
        workflow.add_edge("dataset_handler", "analysis_stats")
        
        # Web Searcher -> Analysis Stats  
        workflow.add_edge("web_searcher", "analysis_stats")
        
        # Analysis pipeline: Stats -> Viz -> Insights -> Checker
        workflow.add_edge("analysis_stats", "analysis_viz")
        workflow.add_edge("analysis_viz", "analysis_insights") 
        workflow.add_edge("analysis_insights", "checker")
        
        # Checker -> End (analysis complete)
        workflow.add_edge("checker", END)
        
        return workflow
    
    def _should_continue_from_user_facing(self, state: MultiAgentState) -> str:
        """Decide whether to continue from User Facing agent"""
        return "end" if state.get("approved", False) else "checker"
    
    def _should_continue_from_query_checker(self, state: MultiAgentState) -> str:
        """Decide whether to continue from Query Checker"""
        return "end" if state.get("approved", False) else "supervisor"
    
    def _route_from_supervisor(self, state: MultiAgentState) -> str:
        """Hub routing logic from Supervisor"""
        current_agent = state.get("current_agent")
        
        if current_agent == AgentType.DATASET_HANDLER:
            return "dataset_handler"
        elif current_agent == AgentType.WEB_SEARCHER:
            return "web_searcher"
        else:
            return "analysis_stats"  # Default to analysis
    
    def analyze_query(self, query: str) -> str:
        """
        Main entry point for query analysis
        
        Args:
            query: User's natural language query
            
        Returns:
            Final analysis report
        """
        cyber_terminal.neural_loading("🔍 Query Analysis Initiated", 1.0)
        
        # Initialize state
        initial_state: MultiAgentState = {
            "query": query,
            "current_agent": AgentType.USER_FACING,
            "next_agent": None,
            "datasets": [],
            "cleaned_datasets": [],
            "vector_db": None,
            "is_analysis_query": False,
            "web_context": None,
            "stats_results": None,
            "viz_data": None,
            "insights": None,
            "checker_feedback": None,
            "revision_count": 0,
            "approved": False,
            "final_report": None,
            "agent_messages": [],
            "execution_log": [],
            "start_time": time.time(),
            "model_costs": {"standard": 0, "premium": 0}
        }
        
        try:
            # Execute the workflow with cyberpunk styling
            cyber_terminal.neural_progress("🤖 Deep Learning Protocols Active", 50)
            
            # Run the workflow
            final_state = self.app.invoke(initial_state)
            
            cyber_terminal.agent_activation("Analysis Matrix", "COMPLETE")
            
            # Display cost summary
            self._display_cost_summary(final_state)
            
            # Return final report
            return final_state.get("final_report", "Analysis failed to complete")
            
        except Exception as e:
            console.print(f"[red]❌ Workflow failed: {e}[/red]")
            return f"Analysis failed: {str(e)}"
    
    def _display_cost_summary(self, state: MultiAgentState):
        """Display cost optimization summary"""
        costs = state.get("model_costs", {})
        execution_time = time.time() - state.get("start_time", time.time())
        agent_count = len(state.get("agent_messages", []))
        
        # Cyberpunk-style system status
        cyber_terminal.system_status(
            agents_active=agent_count,
            cost=costs.get('standard', 0) * 0.002 + costs.get('premium', 0) * 0.03,
            duration=execution_time
        )

    def get_agent_status(self) -> Dict[str, Any]:
        """Get system status for debugging"""
        return {
            "agents_initialized": len(self.agents),
            "workflow_compiled": self.app is not None,
            "available_agents": [agent_type.value for agent_type in self.agents.keys()]
        }
