# whitepaper/agents/models.py
"""
Cost-Optimized Model Selection for 9-Agent System
GPT-3.5 for conversation/routing, GPT-4 for deep analysis
"""
from langchain_openai import ChatOpenAI
from .state import AgentType

# Cost-optimized model mapping
AGENT_MODELS = {
    # Conversation & Routing (GPT-3.5 - Cost Efficient)
    AgentType.USER_FACING: "gpt-3.5-turbo",
    AgentType.QUERY_CHECKER: "gpt-3.5-turbo", 
    AgentType.SUPERVISOR: "gpt-3.5-turbo",
    
    # Utility Tasks (GPT-3.5 - Good for structured tasks)
    AgentType.DATASET_HANDLER: "gpt-3.5-turbo",
    AgentType.WEB_SEARCHER: "gpt-3.5-turbo",
    
    # Deep Analysis (GPT-4 - Premium for complex reasoning)
    AgentType.ANALYSIS_STATS: "gpt-4",
    AgentType.ANALYSIS_VIZ: "gpt-4", 
    AgentType.ANALYSIS_INSIGHTS: "gpt-4",
    AgentType.CHECKER: "gpt-4"
}

def get_agent_model(agent_type: AgentType, temperature: float = 0.3) -> ChatOpenAI:
    """
    Get cost-optimized LLM for specific agent type
    
    Args:
        agent_type: The type of agent requesting the model
        temperature: Creativity level (0.0 = deterministic, 1.0 = creative)
        
    Returns:
        Configured ChatOpenAI instance
    """
    model_name = AGENT_MODELS[agent_type]
    
    # Adjust temperature based on agent role
    if agent_type in [AgentType.ANALYSIS_INSIGHTS, AgentType.ANALYSIS_VIZ]:
        temperature = 0.7  # More creativity for insights and visualization
    elif agent_type in [AgentType.QUERY_CHECKER, AgentType.DATASET_HANDLER]:
        temperature = 0.1  # Very deterministic for routing and data handling
    
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        max_tokens=2048 if "gpt-4" in model_name else 1024,
        streaming=True  # Enable streaming for real-time UX
    )

def get_model_cost_tier(agent_type: AgentType) -> str:
    """Get cost tier for tracking"""
    model = AGENT_MODELS[agent_type]
    return "premium" if "gpt-4" in model else "standard"
