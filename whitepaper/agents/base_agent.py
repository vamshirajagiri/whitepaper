# whitepaper/agents/base_agent.py
"""
Base Agent Class for 9-Agent Hub-and-Spoke System
"""
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from rich.console import Console
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

from .state import MultiAgentState, AgentMessage, AgentType
from .models import get_agent_model, get_model_cost_tier
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

class BaseAgent(ABC):
    """Base class for all agents in the 9-agent system"""
    
    def __init__(self, agent_type: AgentType, system_prompt: str):
        self.agent_type = agent_type
        self.system_prompt = system_prompt
        self.model = get_agent_model(agent_type)
        self.cost_tier = get_model_cost_tier(agent_type)
        
    def send_message(self, state: MultiAgentState, to_agent: AgentType, content: str) -> MultiAgentState:
        """Send a message to another agent and log it"""
        message = AgentMessage(
            from_agent=self.agent_type,
            to_agent=to_agent,
            content=content
        )
        
        # Add to state
        new_messages = state.get("agent_messages", []) + [message]
        state["agent_messages"] = new_messages
        
        # Cyberpunk-style agent communication
        action = "ROUTING" if "forwarding" in content.lower() else "PROCESSING"
        cyber_terminal.agent_activation(self.agent_type.value, action)
        
        # Track costs
        if "model_costs" not in state:
            state["model_costs"] = {}
        state["model_costs"][self.cost_tier] = state["model_costs"].get(self.cost_tier, 0) + 1
        
        return state
    
    def execute_with_prompt(self, query: str, context: str = "") -> str:
        """Execute agent with system prompt and query"""
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("human", f"Context: {context}\n\nQuery: {query}")
            ])
            
            chain = prompt | self.model
            response = chain.invoke({"query": query, "context": context})
            return response.content
            
        except Exception as e:
            console.print(f"[red]❌ {self.agent_type.value} failed: {e}[/red]")
            return f"Error in {self.agent_type.value}: {str(e)}"
    
    @abstractmethod
    def execute(self, state: MultiAgentState) -> MultiAgentState:
        """Execute the agent's main function"""
        pass
    
    def log_execution(self, state: MultiAgentState, action: str) -> MultiAgentState:
        """Log agent execution"""
        log_entry = f"{self.agent_type.value}: {action}"
        new_logs = state.get("execution_log", []) + [log_entry]
        state["execution_log"] = new_logs
        return state
