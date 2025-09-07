"""
9-Agent Hub-and-Spoke Architecture
Main entry point for the multi-agent analysis system
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, TypedDict, Annotated, Sequence, Literal
import time
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, AIMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import operator
import functools

# Vector DB imports
try:
    import faiss
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings
    VECTOR_DB_AVAILABLE = True
except ImportError:
    VECTOR_DB_AVAILABLE = False

# Import existing ETL and scanner
try:
    from .etl import etl_files
    from .scanner import scan_files
except ImportError:
    # Fallback for direct imports
    from etl import etl_files
    from scanner import scan_files

# Import 9-agent system
try:
    from .agents import HubSpokeSystem, MultiAgentState, AgentType
except ImportError:
    # Fallback for direct imports
    from agents import HubSpokeSystem, MultiAgentState, AgentType

# Load environment variables
load_dotenv()

console = Console()

# ===== 9-AGENT SYSTEM STATE =====

class NineAgentState(TypedDict):
    """State shared across all 9 agents in the system"""
    # Core query and flow
    query: str
    current_agent: str
    next_agent: Optional[str]

    # Data management
    datasets: List[Path]
    cleaned_datasets: List[Path]
    vector_db: Optional[Any]  # FAISS vectorstore

    # Analysis pipeline
    is_analysis_query: bool
    web_context: Optional[Dict]
    stats_analysis: Optional[Dict]
    visualization_data: Optional[Dict]
    insights_analysis: Optional[Dict]

    # Quality and feedback
    checker_feedback: Optional[Dict]
    revision_count: int
    approved_for_response: bool

    # Final output
    final_report: Optional[str]

    # Communication logs
    agent_messages: Annotated[List[Dict], operator.add]
    handover_logs: Annotated[List[str], operator.add]

# ===== 9-AGENT TOOLS =====

@tool
def scan_dataset(dataset_path: str) -> str:
    """Scan a dataset for an overview without cleaning"""
    try:
        console.print(f"[blue]🔍 Scanning dataset: {dataset_path}[/blue]")
        df = pd.read_csv(dataset_path)
        
        # Basic scan analysis
        rows, cols = df.shape
        missing_percent = (df.isnull().sum() / len(df) * 100).round(1).to_dict()
        duplicates = df.duplicated().sum()
        high_missing_cols = [col for col, pct in missing_percent.items() if pct > 15]
        
        analysis = {
            "dataset": Path(dataset_path).name,
            "rows": rows,
            "columns": cols,
            "column_names": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_percent": missing_percent,
            "high_missing_columns": high_missing_cols,
            "duplicates": int(duplicates),
            "sample": df.head(2).to_dict(orient='records')
        }
        
        return json.dumps(analysis, indent=2)
    except Exception as e:
        return f"Error scanning dataset: {e}"

@tool
def clean_dataset(dataset_path: str) -> str:
    """Run ETL pipeline on a dataset to clean it"""
    try:
        console.print(f"[blue]⚙️ Cleaning dataset: {dataset_path}[/blue]")
        input_path = Path(dataset_path)
        
        # Run ETL using existing functionality
        cleaned_paths = etl_files([input_path])
        
        if cleaned_paths and len(cleaned_paths) > 0:
            return json.dumps({
                "original": str(input_path),
                "cleaned": str(cleaned_paths[0]),
                "success": True
            })
        else:
            return json.dumps({"success": False, "error": "ETL process didn't return cleaned files"})
    except Exception as e:
        return f"Error cleaning dataset: {e}"

@tool
def analyze_dataset(dataset_path: str, query: str) -> str:
    """Analyze a specific dataset for the given query"""
    try:
        df = pd.read_csv(dataset_path)

        # Basic analysis
        analysis = {
            "dataset": Path(dataset_path).name,
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": df.dtypes.to_dict(),
            "summary_stats": df.describe().to_dict() if len(df.select_dtypes(include=[np.number]).columns) > 0 else {},
            "missing_values": df.isnull().sum().to_dict(),
            "sample_data": df.head(3).to_dict(orient='records')
        }

        return json.dumps(analysis, indent=2)
    except Exception as e:
        return f"Error analyzing dataset: {e}"

@tool
def web_search(query: str) -> str:
    """Search the web for additional context and information"""
    try:
        # Use Tavily for web search if API key is available
        tavily_api_key = os.getenv('TAVILY_API_KEY')
        if tavily_api_key:
            search = TavilySearchAPIWrapper(tavily_api_key=tavily_api_key)
            results = search.results(query, max_results=5)
            return json.dumps(results, indent=2)
        else:
            return "Web search not available - set TAVILY_API_KEY for web search capabilities"
    except Exception as e:
        return f"Web search error: {e}"

@tool
def create_vector_db(dataset_paths: List[str]) -> str:
    """Create or update vector database from datasets for semantic search"""
    if not VECTOR_DB_AVAILABLE:
        return "Vector DB not available - install FAISS: pip install faiss-cpu langchain-community"
    
    try:
        console.print(f"[blue]🔢 Creating vector database from {len(dataset_paths)} datasets[/blue]")
        
        # Process each dataset into text chunks
        texts = []
        metadatas = []
        
        for path in dataset_paths:
            df = pd.read_csv(path)
            dataset_name = Path(path).name
            
            # Convert each row to a text chunk with metadata
            for i, row in df.iterrows():
                row_text = f"Dataset: {dataset_name}\n" + "\n".join([f"{col}: {val}" for col, val in row.items()])
                texts.append(row_text)
                metadatas.append({"source": dataset_name, "row": i})
        
        # Create vector store
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_texts(texts=texts, embedding=embeddings, metadatas=metadatas)
        
        return json.dumps({
            "success": True,
            "vector_count": len(texts),
            "datasets_indexed": [Path(p).name for p in dataset_paths]
        })
    except Exception as e:
        return f"Error creating vector database: {e}"

@tool
def query_vector_db(query: str, top_k: int = 10) -> str:
    """Search vector database for relevant data points"""
    if not VECTOR_DB_AVAILABLE:
        return "Vector DB not available - install FAISS: pip install faiss-cpu langchain-community"
    
    try:
        # This would normally use the actual vectorstore from state
        # In a real implementation we'd pass the vectorstore from the state
        return json.dumps({
            "success": False,
            "error": "Vectorstore must be initialized and passed in state"
        })
    except Exception as e:
        return f"Error querying vector database: {e}"

@tool
def generate_visualization(data: Dict[str, Any], chart_type: str) -> str:
    """Generate visualization data for the Analysis Viz Agent"""
    try:
        # This is a placeholder for actual chart generation
        # In production, this would create matplotlib/ASCII charts
        # and return the data needed for visualization
        
        return json.dumps({
            "success": True,
            "chart_type": chart_type,
            "data": data,
            "ascii_chart": """    Agriculture Yield Trend:
    █████  (Jan: 100)
    ████   (Feb: 85)
    ███    (Mar: 70)
    """
        })
    except Exception as e:
        return f"Error generating visualization: {e}"

# ===== 9-AGENT SYSTEM INTEGRATION =====

class WhitepaperMultiAgent:
    """Main interface for the 9-Agent Hub-and-Spoke System"""

    def __init__(self):
        self.system = HubSpokeSystem()

    def analyze_policy_query(self, user_query: str) -> Optional[str]:
        """Main entry point for policy analysis queries"""
        try:
            return self.system.analyze_query(user_query)
        except Exception as e:
            console.print(f"[red]❌ 9-Agent System Error: {e}[/red]")
            return f"Analysis failed: {str(e)}"

    def process_query(self, user_query: str) -> str:
        """Legacy compatibility method"""
        return self.analyze_policy_query(user_query)

# ===== LEGACY COMPATIBILITY =====

class WhitepaperIntelligentAgent:
    """Legacy compatibility class - redirects to 9-agent system"""

    def __init__(self):
        self.agent = WhitepaperMultiAgent()

    def process_query(self, user_query: str) -> str:
        """Legacy method - redirects to 9-agent system"""
        return self.agent.process_query(user_query)
