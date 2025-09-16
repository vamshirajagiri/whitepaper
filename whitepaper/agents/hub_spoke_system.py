# whitepaper/agents/hub_spoke_system.py
"""
Hub-and-Spoke System using LangGraph
Orchestrates 9-Agent workflow with conditional routing
"""
import os
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
# Simple progress display
def show_progress(message):
    console.print(f"[cyan]{message}[/cyan]")

console = Console()

class HubSpokeSystem:
    """
    9-Agent Hub-and-Spoke System
    Hub: Supervisor Agent orchestrates workflow
    Spokes: Specialized agents handle specific tasks
    """
    
    def __init__(self):
        # Early API key validation to provide better error messages
        api_key_valid, api_key_message = self._validate_api_key()
        if not api_key_valid:
            console.print(f"[yellow]⚠️ Warning: {api_key_message}[/yellow]")
            console.print("[dim]Hub-Spoke system will initialize but agents won't work without valid API key[/dim]")
            # Set a temporary API key to allow initialization
            os.environ["OPENAI_API_KEY"] = "temp-key-for-initialization"
            self._api_key_missing = True
        else:
            self._api_key_missing = False
        
        self.agents = self._initialize_agents()
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
        
    def _initialize_agents(self) -> Dict[AgentType, Any]:
        """Initialize all 9 agents"""
        show_progress("⚡ Initializing 9-Agent System...")
        
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
        
        show_progress(f"✅ {len(agents)} agents initialized successfully")
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
    
    def _validate_api_key(self) -> tuple[bool, str]:
        """Validate if OpenAI API key is available and properly formatted"""
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            return False, (
                "🔑 OpenAI API key not found. Please set your OPENAI_API_KEY environment variable.\n"
                "\nTo fix this issue:\n"
                "1. Get your API key from: https://platform.openai.com/account/api-keys\n"
                "2. Set it in your terminal: export OPENAI_API_KEY='your-key-here'\n"
                "3. Or create a .env file with: OPENAI_API_KEY=your-key-here\n"
                "\nWithout an API key, the AI agents cannot analyze your data."
            )
        
        if api_key.startswith("sk-") and len(api_key) > 20:
            return True, "API key format looks valid"
        elif len(api_key) < 20:
            return False, (
                "🔑 OpenAI API key appears to be incomplete or invalid.\n"
                "Please verify your API key is correctly set. It should start with 'sk-' and be much longer."
            )
        else:
            # May be valid, let the API call determine
            return True, "API key detected (format validation passed)"
    
    def analyze_query(self, query: str) -> str:
        """
        Main entry point for query analysis
        
        Args:
            query: User's natural language query
            
        Returns:
            Final analysis report
        """
        # Check if API key was missing during initialization or validate again
        if hasattr(self, '_api_key_missing') and self._api_key_missing:
            # Re-validate in case user has set the key since initialization
            api_key_valid, api_key_message = self._validate_api_key()
            if not api_key_valid:
                console.print(f"[red]❌ API Key Issue:[/red]")
                console.print(Panel(api_key_message, title="🔑 OpenAI API Key Required", border_style="red"))
                return api_key_message
            else:
                # API key is now valid, update the flag
                self._api_key_missing = False
        
        show_progress("🔍 Starting query analysis...")
        
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
            # Execute the workflow
            show_progress("🤖 9-Agent workflow executing...")
            
            # Run the workflow
            final_state = self.app.invoke(initial_state)
            
            show_progress("✅ Analysis complete!")
            
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
        total_cost = costs.get('standard', 0) * 0.002 + costs.get('premium', 0) * 0.03
        
        console.print(f"[green]✅ Analysis completed in {execution_time:.1f}s[/green]")
        console.print(f"[blue]💰 Estimated cost: ${total_cost:.4f} | Agents used: {agent_count}[/blue]")

    def get_agent_status(self) -> Dict[str, Any]:
        """Get system status for debugging"""
        return {
            "agents_initialized": len(self.agents),
            "workflow_compiled": self.app is not None,
            "available_agents": [agent_type.value for agent_type in self.agents.keys()]
        }
