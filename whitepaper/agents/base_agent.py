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
        
        # Show agent communication
        action = "routing" if "forwarding" in content.lower() else "processing"
        console.print(f"[dim]▸ {self.agent_type.value}: {action}[/dim]")
        
        # Track costs
        if "model_costs" not in state:
            state["model_costs"] = {}
        state["model_costs"][self.cost_tier] = state["model_costs"].get(self.cost_tier, 0) + 1
        
        return state
    
    def execute_with_prompt(self, query: str, context: str = "") -> str:
        """Execute agent with system prompt and query"""
        try:
            # Escape any curly braces in context to prevent template variable conflicts
            safe_context = context.replace("{", "{{").replace("}", "}}")
            safe_query = query.replace("{", "{{").replace("}", "}}")
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("human", f"Context: {safe_context}\n\nQuery: {safe_query}")
            ])
            
            chain = prompt | self.model
            response = chain.invoke({})
            return response.content
            
        except Exception as e:
            error_msg = str(e)
            console.print(f"[red]❌ {self.agent_type.value} failed: {e}[/red]")
            
            # Check for API key issues and provide better error messages
            if "401" in error_msg and "api key" in error_msg.lower():
                return self._get_api_key_error_message()
            elif "api key" in error_msg.lower() or "openai_api_key" in error_msg.lower():
                return self._get_api_key_error_message()
            else:
                return self._get_generic_error_message(error_msg)
    
    def _get_api_key_error_message(self) -> str:
        """Get user-friendly message for API key issues"""
        return (
            f"🔑 {self.agent_type.value} requires a valid OpenAI API key to provide analysis. "
            "Please set your OPENAI_API_KEY environment variable and try again. "
            "You can get an API key from https://platform.openai.com/account/api-keys"
        )
    
    def _get_generic_error_message(self, error_msg: str) -> str:
        """Get user-friendly message for generic errors"""
        return (
            f"⚠️ {self.agent_type.value} encountered an issue and cannot provide analysis at this time. "
            f"This might be due to network connectivity, API limits, or system configuration. "
            f"Technical details: {error_msg[:100]}{'...' if len(error_msg) > 100 else ''}"
        )
    
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
