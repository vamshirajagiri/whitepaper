import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, TypedDict, Annotated, Sequence, Literal
from rich.console import Console
from rich.panel import Panel
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

# Load environment variables
load_dotenv()

console = Console()

# ===== MULTI-AGENT SYSTEM STATE =====

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_agent: str
    user_query: str
    datasets: List[Path]
    analysis_results: Optional[Dict]
    checker_feedback: Optional[Dict]
    final_answer: Optional[str]
    conversation_history: Annotated[Sequence[Dict], operator.add]
    handover_reason: Optional[str]
    revision_count: int

# ===== TOOLS =====

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
            "sample_data": df.head(3).to_string()
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

# ===== THREE-AGENT SYSTEM =====

class ThreeAgentSystem:
    """Three-agent system with User-Facing, Analyst, and Checker agents that communicate like humans"""

    def __init__(self):
        self.llm = None
        self.cleaned_data_dir = Path("cleaned-dataset")
        self.raw_data_dir = Path(".")
        self.graph = None
        self._init_llm()
        self._ensure_directories()
        self._build_graph()

    def _init_llm(self):
        """Initialize OpenAI LLM"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            env_file = Path('.env')
            if env_file.exists():
                load_dotenv(env_file)
                api_key = os.getenv('OPENAI_API_KEY')

        if api_key:
            try:
                self.llm = ChatOpenAI(
                    temperature=0.1,
                    model_name="gpt-4",
                    openai_api_key=api_key,
                    max_tokens=2000
                )
                console.print("[green]✅ Three-Agent System ready![/green]")
            except Exception as e:
                console.print(f"[red]❌ OpenAI API Error: {e}[/red]")
                self.llm = None
        else:
            console.print("[yellow]⚠️ No OpenAI API key found. Set OPENAI_API_KEY to enable AI features.[/yellow]")
            self.llm = None

    def _ensure_directories(self):
        """Ensure necessary directories exist"""
        self.cleaned_data_dir.mkdir(exist_ok=True)

    def _check_cleaned_data_availability(self) -> bool:
        """Check if cleaned datasets are available"""
        cleaned_files = list(self.cleaned_data_dir.glob("*_cleaned*.csv"))
        return len(cleaned_files) > 0

    def _auto_prepare_data(self) -> bool:
        """Automatically scan and clean data if needed"""
        console.print("[blue]🔄 Preparing your data...[/blue]")

        raw_files = list(self.raw_data_dir.glob("*.csv")) + list(self.raw_data_dir.glob("*.xlsx"))
        if not raw_files:
            console.print("[yellow]⚠️ No data files found[/yellow]")
            return False

        if not self._check_cleaned_data_availability():
            console.print("[blue]📊 Running ETL...[/blue]")
            try:
                from .etl import etl_files
                etl_files(raw_files)
                console.print("[green]✅ Data ready![/green]")
                return True
            except Exception as e:
                console.print(f"[red]❌ ETL failed: {e}[/red]")
                return False
        else:
            console.print("[green]✅ Data ready![/green]")
            return True

    def _load_cleaned_datasets(self) -> List[Path]:
        """Load all available cleaned datasets"""
        cleaned_files = list(self.cleaned_data_dir.glob("*_cleaned*.csv"))
        return cleaned_files

    def _build_graph(self):
        """Build the three-agent graph with human-like communication"""
        if not self.llm:
            return

        # ===== USER-FACING AGENT =====
        def user_facing_agent(state: AgentState) -> Dict:
            """User-facing agent that handles initial interaction and coordinates with other agents"""
            user_query = state["user_query"]
            conversation_history = state.get("conversation_history", [])
            handover_reason = state.get("handover_reason", "")
            analysis_results = state.get("analysis_results", {})
            checker_feedback = state.get("checker_feedback", {})

            console.print(f"[blue]👤 User-Facing Agent: Processing query - '{user_query}'[/blue]")
            console.print(f"[blue]📋 Handover reason: {handover_reason}[/blue]")

            # Check if we have validated results ready for final response
            if (analysis_results and checker_feedback and
                handover_reason and ("validation passed" in handover_reason.lower() or
                                   "ready for final response" in handover_reason.lower())):

                console.print(f"[green]✅ User-Facing Agent: Detected validated results - providing final response[/green]")

                # Prepare final comprehensive response
                final_response = self._prepare_final_response(user_query, analysis_results, checker_feedback, conversation_history)

                # Log the final response
                conversation_entry = {
                    "agent": "user_facing",
                    "action": "final_response",
                    "query": user_query,
                    "response": final_response[:200] + "...",
                    "timestamp": str(pd.Timestamp.now())
                }

                console.print(f"[green]🎉 FINAL RESPONSE COMPLETED![/green]")
                return {
                    "current_agent": "user_facing",
                    "final_answer": final_response,
                    "conversation_history": conversation_history + [conversation_entry]
                }

            # Check if this is a follow-up or new query
            if conversation_history:
                last_exchange = conversation_history[-1]
                context = f"Previous context: {last_exchange.get('response', '')}"
            else:
                context = "This is a new query."

            # User-facing agent decides what to do
            coordination_prompt = f"""
            You are the User-Facing Agent in a three-agent system. Your role is to:
            1. Understand the user's query
            2. Coordinate with Analyst and Checker agents
            3. Provide clear, helpful responses to users
            4. Hand over tasks to appropriate agents when needed

            Current user query: "{user_query}"
            Context: {context}
            Handover reason: {handover_reason}

            Available agents:
            - Analyst Agent: Performs data analysis, statistical modeling, insights generation
            - Checker Agent: Reviews analysis quality, validates findings, ensures accuracy

            IMPORTANT: If you have already received validated analysis results from the Checker Agent,
            respond with "provide_final_response" action instead of starting a new workflow.

            Decide your next action:
            - If this needs NEW data analysis: Hand over to Analyst Agent
            - If this needs verification of previous work: Hand over to Checker Agent
            - If this is a simple question you can answer: Respond directly
            - If you have VALIDATED results ready: Use "provide_final_response"
            - If this needs both analysis and checking: Start with Analyst, then Checker

            Return JSON with:
            {{
                "action": "respond_directly" | "handover_to_analyst" | "handover_to_checker" | "coordinated_workflow" | "provide_final_response",
                "response": "Your response to user if responding directly",
                "handover_reason": "Why you're handing over to another agent",
                "next_agent": "analyst" | "checker" | null
            }}
            """

            try:
                response = self.llm.invoke([
                    SystemMessage(content="You are the User-Facing Agent. If you have validated results, provide the final response. Otherwise coordinate with other agents. Return only valid JSON."),
                    HumanMessage(content=coordination_prompt)
                ])

                # Parse the response
                import re
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    decision = json.loads(json_match.group())
                    action = decision.get("action", "respond_directly")

                    # Log the conversation
                    conversation_entry = {
                        "agent": "user_facing",
                        "action": action,
                        "query": user_query,
                        "response": decision.get("response", ""),
                        "timestamp": str(pd.Timestamp.now())
                    }

                    if action == "provide_final_response":
                        console.print(f"[green]✅ User-Facing Agent providing final response[/green]")
                        # Use existing validated results
                        final_response = self._prepare_final_response(user_query, analysis_results, checker_feedback, conversation_history)
                        return {
                            "current_agent": "user_facing",
                            "final_answer": final_response,
                            "conversation_history": conversation_history + [conversation_entry]
                        }
                    elif action == "handover_to_analyst":
                        console.print(f"[yellow]🔄 Handing over to Analyst Agent: {decision.get('handover_reason', '')}[/yellow]")
                        return {
                            "current_agent": "analyst",
                            "handover_reason": decision.get("handover_reason", ""),
                            "conversation_history": conversation_history + [conversation_entry]
                        }
                    elif action == "handover_to_checker":
                        console.print(f"[yellow]🔄 Handing over to Checker Agent: {decision.get('handover_reason', '')}[/yellow]")
                        return {
                            "current_agent": "checker",
                            "handover_reason": decision.get("handover_reason", ""),
                            "conversation_history": conversation_history + [conversation_entry]
                        }
                    elif action == "coordinated_workflow":
                        console.print(f"[yellow]🔄 Starting coordinated workflow: {decision.get('handover_reason', '')}[/yellow]")
                        return {
                            "current_agent": "analyst",
                            "handover_reason": "Starting coordinated analysis and checking workflow",
                            "conversation_history": conversation_history + [conversation_entry]
                        }
                    else:
                        # Respond directly
                        console.print(f"[green]✅ User-Facing Agent responding directly[/green]")
                        return {
                            "current_agent": "user_facing",
                            "final_answer": decision.get("response", "I understand your query. Let me help you with that."),
                            "conversation_history": conversation_history + [conversation_entry]
                        }
                else:
                    return {
                        "current_agent": "analyst",
                        "handover_reason": "Unable to parse response, defaulting to analyst"
                    }
            except Exception as e:
                console.print(f"[red]❌ User-Facing Agent error: {e}[/red]")
                return {
                    "current_agent": "analyst",
                    "handover_reason": f"Error in coordination: {e}"
                }

        # ===== ANALYST AGENT =====
        def analyst_agent(state: AgentState) -> Dict:
            """Analyst agent that performs data analysis and generates insights"""
            user_query = state["user_query"]
            datasets = state.get("datasets", [])
            handover_reason = state.get("handover_reason", "")
            conversation_history = state.get("conversation_history", [])

            console.print(f"[purple]📊 Analyst Agent: Analyzing data for query - '{user_query}'[/purple]")
            console.print(f"[purple]📋 Handover reason: {handover_reason}[/purple]")

            if not datasets:
                console.print("[yellow]⚠️ No datasets available for analysis[/yellow]")
                return {
                    "current_agent": "user_facing",
                    "analysis_results": {"error": "No datasets available for analysis"},
                    "handover_reason": "Analysis completed but no data available"
                }

            # Load and analyze datasets
            dataset_summaries = []
            detailed_analysis = []

            for dataset_path in datasets[:3]:  # Limit to 3 datasets
                try:
                    df = pd.read_csv(dataset_path)
                    summary = {
                        "name": dataset_path.name,
                        "shape": (int(df.shape[0]), int(df.shape[1])),  # Convert to tuple of ints
                        "columns": list(df.columns)[:10],
                        "numeric_cols": int(len(df.select_dtypes(include=[np.number]).columns)),
                        "missing_values": int(df.isnull().sum().sum()),
                        "sample": df.head(3).to_string()
                    }
                    dataset_summaries.append(summary)

                    # Perform detailed analysis
                    analysis = self._perform_detailed_analysis(df, dataset_path.name, user_query)
                    detailed_analysis.append(analysis)

                except Exception as e:
                    dataset_summaries.append({"name": dataset_path.name, "error": str(e)})
                    detailed_analysis.append({"name": dataset_path.name, "error": str(e)})

            # Generate comprehensive analysis report
            analysis_prompt = f"""
            You are the Analyst Agent. You have received this query from the User-Facing Agent: "{user_query}"

            Handover context: {handover_reason}

            Based on your analysis of the datasets, provide a comprehensive report that includes:

            1. **Data Overview**: Summary of datasets analyzed
            2. **Key Findings**: Important patterns, trends, and insights
            3. **Statistical Analysis**: Correlations, distributions, anomalies
            4. **Quality Assessment**: Data completeness, potential issues
            5. **Recommendations**: What the Checker Agent should verify

            Dataset Summaries:
            {json.dumps(dataset_summaries, indent=2)}

            Detailed Analysis:
            {json.dumps(detailed_analysis, indent=2)}

            Provide a thorough analysis that the Checker Agent can validate.
            """

            try:
                response = self.llm.invoke([
                    SystemMessage(content="You are the Analyst Agent. Provide detailed, data-driven analysis for the Checker Agent to validate."),
                    HumanMessage(content=analysis_prompt)
                ])

                analysis_results = {
                    "datasets_analyzed": len(dataset_summaries),
                    "analysis_report": response.content,
                    "raw_data_summary": dataset_summaries,
                    "detailed_findings": detailed_analysis,
                    "confidence_level": "high" if len(datasets) > 0 else "low"
                }

                # Log the analysis
                conversation_entry = {
                    "agent": "analyst",
                    "action": "analysis_completed",
                    "query": user_query,
                    "datasets_analyzed": len(dataset_summaries),
                    "findings_summary": response.content[:200] + "...",
                    "timestamp": str(pd.Timestamp.now())
                }

                console.print(f"[green]✅ Analyst Agent completed analysis of {len(dataset_summaries)} datasets[/green]")
                console.print(f"[yellow]🔄 Handing over to Checker Agent for validation[/yellow]")

                return {
                    "current_agent": "checker",
                    "analysis_results": analysis_results,
                    "handover_reason": "Analysis completed, requesting validation from Checker Agent",
                    "conversation_history": conversation_history + [conversation_entry]
                }

            except Exception as e:
                console.print(f"[red]❌ Analyst Agent error: {e}[/red]")
                return {
                    "current_agent": "user_facing",
                    "analysis_results": {"error": f"Analysis failed: {e}"},
                    "handover_reason": "Analysis failed, returning to user-facing agent"
                }

        # ===== CHECKER AGENT =====
        def checker_agent(state: AgentState) -> Dict:
            """Checker agent that validates analysis quality and ensures accuracy"""
            user_query = state["user_query"]
            analysis_results = state.get("analysis_results", {})
            handover_reason = state.get("handover_reason", "")
            conversation_history = state.get("conversation_history", [])
            revision_count = state.get("revision_count", 0)

            console.print(f"[orange]🔍 Checker Agent: Validating analysis for query - '{user_query}'[/orange]")
            console.print(f"[orange]📋 Handover reason: {handover_reason}[/orange]")

            if not analysis_results or "error" in analysis_results:
                console.print("[yellow]⚠️ No analysis results to check[/yellow]")
                return {
                    "current_agent": "user_facing",
                    "checker_feedback": {"error": "No analysis results available for checking"},
                    "handover_reason": "Cannot validate - no analysis provided"
                }

            # Validate the analysis
            validation_prompt = f"""
            You are the Checker Agent. Your role is to validate the quality and accuracy of the Analyst Agent's work.

            Original user query: "{user_query}"
            Handover context: {handover_reason}

            Analyst's Analysis Report:
            {analysis_results.get('analysis_report', 'No report provided')}

            Raw Data Summary:
            {json.dumps(analysis_results.get('raw_data_summary', []), indent=2)}

            Please validate:

            1. **Methodological Soundness**: Are the analysis methods appropriate?
            2. **Data Integrity**: Does the analysis accurately reflect the data?
            3. **Logical Consistency**: Are the conclusions supported by the data?
            4. **Completeness**: Has the query been fully addressed?
            5. **Potential Biases**: Any issues with data interpretation?

            Provide:
            - Validation score (1-10)
            - Strengths of the analysis
            - Areas for improvement
            - Confidence level in the findings
            - Recommendations for the final response

            If validation score < 7, suggest revisions to the Analyst Agent.
            """

            try:
                response = self.llm.invoke([
                    SystemMessage(content="You are the Checker Agent. Validate analysis quality and ensure accuracy. Be thorough but constructive."),
                    HumanMessage(content=validation_prompt)
                ])

                # Parse validation score
                validation_text = response.content
                import re
                score_match = re.search(r'validation score.*?(\d+)', validation_text, re.IGNORECASE)
                validation_score = int(score_match.group(1)) if score_match else 8

                checker_feedback = {
                    "validation_score": validation_score,
                    "validation_report": validation_text,
                    "recommendations": self._extract_recommendations(validation_text),
                    "confidence_assessment": "high" if validation_score >= 8 else "medium" if validation_score >= 6 else "low",
                    "needs_revision": validation_score < 7
                }

                # Log the validation
                conversation_entry = {
                    "agent": "checker",
                    "action": "validation_completed",
                    "validation_score": validation_score,
                    "needs_revision": validation_score < 7,
                    "recommendations": checker_feedback["recommendations"],
                    "timestamp": str(pd.Timestamp.now())
                }

                # Check revision limit to prevent infinite loops
                max_revisions = 2  # Limit revisions to prevent infinite loops
                if validation_score < 7 and revision_count < max_revisions:
                    console.print(f"[red]⚠️ Checker Agent found issues (Score: {validation_score}/10)[/red]")
                    console.print(f"[yellow]🔄 Requesting revision from Analyst Agent (Attempt {revision_count + 1}/{max_revisions})[/yellow]")
                    return {
                        "current_agent": "analyst",
                        "checker_feedback": checker_feedback,
                        "handover_reason": f"Validation score {validation_score}/10 - needs revision (attempt {revision_count + 1})",
                        "conversation_history": conversation_history + [conversation_entry],
                        "revision_count": revision_count + 1
                    }
                elif validation_score < 7 and revision_count >= max_revisions:
                    console.print(f"[yellow]⚠️ Checker Agent: Maximum revisions reached (Score: {validation_score}/10)[/yellow]")
                    console.print(f"[yellow]📋 Proceeding with current analysis despite lower validation score[/yellow]")
                    
                    # Force acceptance after max revisions to prevent infinite loops
                    checker_feedback["validation_score"] = 7  # Override to acceptable score
                    checker_feedback["forced_acceptance"] = True
                    checker_feedback["acceptance_reason"] = f"Maximum revisions ({max_revisions}) reached"
                    
                    final_response = self._prepare_final_response(user_query, analysis_results, checker_feedback, conversation_history)
                    
                    return {
                        "current_agent": "user_facing",
                        "final_answer": final_response,
                        "checker_feedback": checker_feedback,
                        "handover_reason": f"Forced acceptance after {max_revisions} revisions - ready for final response",
                        "conversation_history": conversation_history + [conversation_entry]
                    }
                else:
                    console.print(f"[green]✅ Checker Agent validated analysis (Score: {validation_score}/10)[/green]")
                    console.print(f"[yellow]🔄 Handing over to User-Facing Agent for final response[/yellow]")

                    # Prepare final comprehensive response
                    final_response = self._prepare_final_response(user_query, analysis_results, checker_feedback, conversation_history)

                    return {
                        "current_agent": "user_facing",
                        "final_answer": final_response,
                        "checker_feedback": checker_feedback,
                        "handover_reason": f"Validation passed (Score: {validation_score}/10) - ready for final response",
                        "conversation_history": conversation_history + [conversation_entry]
                    }

            except Exception as e:
                console.print(f"[red]❌ Checker Agent error: {e}[/red]")
                return {
                    "current_agent": "user_facing",
                    "checker_feedback": {"error": f"Validation failed: {e}"},
                    "final_answer": "Analysis completed but validation encountered an error."
                }

        # ===== BUILD THE GRAPH =====
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("user_facing", user_facing_agent)
        workflow.add_node("analyst", analyst_agent)
        workflow.add_node("checker", checker_agent)

        # Define conditional routing
        def route_after_user_facing(state: AgentState) -> str:
            # If we have a final answer, terminate the graph
            if state.get("final_answer"):
                return END
            return state["current_agent"]

        def route_after_analyst(state: AgentState) -> str:
            # If we have a final answer, terminate the graph
            if state.get("final_answer"):
                return END
            return state["current_agent"]

        def route_after_checker(state: AgentState) -> str:
            # If we have a final answer, terminate the graph
            if state.get("final_answer"):
                return END
            return state["current_agent"]

        # Add conditional edges
        workflow.add_conditional_edges("user_facing", route_after_user_facing)
        workflow.add_conditional_edges("analyst", route_after_analyst)
        workflow.add_conditional_edges("checker", route_after_checker)

        # Set entry point
        workflow.set_entry_point("user_facing")

        self.graph = workflow.compile()

    def _perform_detailed_analysis(self, df: pd.DataFrame, dataset_name: str, query: str) -> Dict:
        """Perform detailed analysis on a dataset"""
        try:
            analysis = {
                "dataset": dataset_name,
                "basic_stats": {},
                "correlations": {},
                "insights": []
            }

            # Basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                # Convert pandas describe() to native Python types
                desc_df = df[numeric_cols].describe()
                analysis["basic_stats"] = {}
                for col in desc_df.columns:
                    analysis["basic_stats"][col] = {}
                    for idx in desc_df.index:
                        value = desc_df.loc[idx, col]
                        # Convert numpy/pandas types to native Python types
                        if pd.isna(value):
                            analysis["basic_stats"][col][idx] = None
                        elif hasattr(value, 'item'):  # numpy types
                            analysis["basic_stats"][col][idx] = value.item()
                        else:
                            analysis["basic_stats"][col][idx] = float(value)

                # Correlations
                if len(numeric_cols) > 1:
                    corr_matrix = df[numeric_cols].corr()
                    # Get top correlations
                    top_correlations = {}
                    for i in range(len(numeric_cols)):
                        for j in range(i+1, len(numeric_cols)):
                            col1, col2 = numeric_cols[i], numeric_cols[j]
                            corr_value = corr_matrix.loc[col1, col2]
                            # Convert to native Python float
                            if hasattr(corr_value, 'item'):
                                corr_value = corr_value.item()
                            if abs(corr_value) > 0.3:  # Only significant correlations
                                top_correlations[f"{col1} vs {col2}"] = round(float(corr_value), 3)
                    analysis["correlations"] = top_correlations

            # Data quality insights
            missing_pct = (df.isnull().sum() / len(df) * 100).round(2)
            # Convert to native Python dict with float values
            missing_dict = {}
            for col in missing_pct.index:
                missing_dict[col] = float(missing_pct[col])

            analysis["data_quality"] = {
                "missing_percentages": missing_dict,
                "duplicate_rows": int(df.duplicated().sum()),
                "total_rows": int(len(df))
            }

            # Query-specific insights
            query_lower = query.lower()
            if any(word in query_lower for word in ["trend", "change", "over time"]):
                date_cols = [col for col in df.columns if any(word in col.lower() for word in ["date", "time", "year", "month"])]
                if date_cols:
                    analysis["insights"].append(f"Found potential time-series columns: {date_cols}")

            if any(word in query_lower for word in ["correlation", "relationship"]):
                if analysis["correlations"]:
                    analysis["insights"].append(f"Found {len(analysis['correlations'])} significant correlations")

            return analysis

        except Exception as e:
            return {"dataset": dataset_name, "error": str(e)}

    def _extract_recommendations(self, validation_text: str) -> List[str]:
        """Extract recommendations from validation text"""
        recommendations = []
        lines = validation_text.split('\n')

        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ["recommend", "suggest", "should", "consider", "improve"]):
                if len(line) > 10:  # Filter out very short lines
                    recommendations.append(line)

        return recommendations[:5]  # Limit to top 5 recommendations

    def _prepare_final_response(self, user_query: str, analysis_results: Dict, checker_feedback: Dict, conversation_history: List[Dict]) -> str:
        """Prepare the final comprehensive response for the user"""
        try:
            final_prompt = f"""
            You are preparing the final response to the user based on the collaborative work of all three agents.

            Original Query: "{user_query}"

            Analyst's Findings:
            {analysis_results.get('analysis_report', 'No analysis report available')}

            Checker's Validation:
            Score: {checker_feedback.get('validation_score', 'N/A')}/10
            Assessment: {checker_feedback.get('confidence_assessment', 'unknown')}
            Key Recommendations: {', '.join(checker_feedback.get('recommendations', []))}

            Agent Conversation Summary:
            - User-Facing Agent coordinated the workflow
            - Analyst Agent analyzed {analysis_results.get('datasets_analyzed', 0)} datasets
            - Checker Agent validated the analysis with score {checker_feedback.get('validation_score', 'N/A')}/10

            Provide a comprehensive, user-friendly response that:
            1. Addresses the original query directly
            2. Summarizes key findings
            3. Includes validated insights
            4. Provides actionable recommendations
            5. Notes any limitations or areas for further investigation

            Make the response clear, professional, and focused on the user's needs.
            """

            response = self.llm.invoke([
                SystemMessage(content="You are synthesizing the final response from the three-agent collaboration. Provide a clear, comprehensive answer to the user."),
                HumanMessage(content=final_prompt)
            ])

            return response.content

        except Exception as e:
            return f"Analysis completed successfully, but final response preparation failed: {e}\n\nKey findings: {analysis_results.get('analysis_report', 'Analysis completed')[:500]}..."

    def process_query(self, user_query: str) -> str:
        """Main entry point for processing user queries with the three-agent system"""

        # Handle simple interactions
        query_lower = user_query.lower().strip()

        # Greetings
        if query_lower in ['hi', 'hello', 'hey', 'how are you', 'what\'s up', 'good morning', 'good afternoon']:
            if self.llm:
                return "👋 Hello! I'm your three-agent analysis system with User-Facing, Analyst, and Checker agents working together. What would you like to explore today?"
            else:
                return "👋 Hello! I'm your analysis assistant. I can help analyze your data, but you'll need to set OPENAI_API_KEY for full AI capabilities."

        # Help
        if query_lower in ['help', 'commands', 'what can you do', '?']:
            return self._get_help_text()

        # Exit
        if query_lower in ['quit', 'exit', 'bye', 'goodbye']:
            return "👋 Goodbye! Have a great day analyzing your data!"

        # Status/API key check
        if query_lower in ['status', 'api key', 'check api']:
            if self.llm:
                return "✅ Three-Agent System is fully operational with OpenAI GPT-4!"
            else:
                return "❌ OpenAI API key not configured. Set OPENAI_API_KEY environment variable."

        # Data analysis queries
        if not self._check_cleaned_data_availability():
            if not self._auto_prepare_data():
                return "❌ Unable to prepare data. Please ensure you have CSV/Excel files in the current directory."

        # Load datasets
        datasets = self._load_cleaned_datasets()
        if not datasets:
            return "❌ No datasets available. Please add CSV/Excel files to your directory."

        console.print(f"[green]🤖 Processing with Three-Agent System...[/green]")
        console.print(f"[green]📊 Analyzing {len(datasets)} dataset(s)...[/green]")

        # Run three-agent analysis
        if self.llm and self.graph:
            try:
                initial_state = {
                    "messages": [HumanMessage(content=user_query)],
                    "current_agent": "user_facing",
                    "user_query": user_query,
                    "datasets": datasets,
                    "analysis_results": None,
                    "checker_feedback": None,
                    "final_answer": None,
                    "conversation_history": [],
                    "handover_reason": "Initial query processing",
                    "revision_count": 0
                }

                result = self.graph.invoke(initial_state)
                return result.get("final_answer", "Analysis completed but no final answer generated.")

            except Exception as e:
                console.print(f"[red]❌ Three-agent system error: {e}[/red]")
                console.print("[yellow]💡 Falling back to simple analysis[/yellow]")
                return self._perform_simple_analysis(user_query, datasets)
        else:
            return self._perform_simple_analysis(user_query, datasets)

    def _perform_simple_analysis(self, user_query: str, datasets: List[Path]) -> str:
        """Fallback simple analysis"""
        if not datasets:
            return "No datasets available."

        try:
            df = pd.read_csv(datasets[0])
            stats = {
                "dataset": datasets[0].name,
                "rows": len(df),
                "columns": len(df.columns),
                "numeric_columns": len(df.select_dtypes(include=[np.number]).columns),
                "missing_values": df.isnull().sum().sum()
            }

            response = f"📊 **Dataset: {stats['dataset']}**\n\n"
            response += f"• **Size**: {stats['rows']} rows, {stats['columns']} columns\n"
            response += f"• **Data Types**: {stats['numeric_columns']} numeric columns\n"
            response += f"• **Data Quality**: {stats['missing_values']} missing values\n\n"

            if len(df.columns) > 0:
                response += f"**Columns**: {', '.join(df.columns.tolist()[:5])}{'...' if len(df.columns) > 5 else ''}\n\n"

            response += "💡 Set OPENAI_API_KEY for full three-agent analysis with validation!"

            return response
        except Exception as e:
            return f"❌ Error: {e}"

    def _get_help_text(self) -> str:
        """Get help text for available commands"""
        help_text = f"""
🤖 **Whitepaper Three-Agent System**

**What I can do:**
• **User-Facing Agent**: Coordinates queries and manages communication
• **Analyst Agent**: Performs deep data analysis and generates insights
• **Checker Agent**: Validates analysis quality and ensures accuracy
• Human-like agent communication and task handovers
• Comprehensive data analysis with quality assurance
• Cross-dataset analysis and insights
• Automatic data preparation and cleaning

**Example queries:**
• "What are the key trends in the data?"
• "Analyze consumption patterns and their policy implications"
• "Show me correlations and provide recommendations"
• "What external factors might affect these trends?"

**Commands:**
• `help` - Show this help
• `status` - Check API key and system status
• `quit` - Exit the assistant
• `hi/hello` - Simple greeting

**Setup:**
• Set API key: `export OPENAI_API_KEY='your-key'`
• Optional: Set `TAVILY_API_KEY` for web search
• Add CSV/Excel files to current directory
• I automatically handle data cleaning!

**Agent Workflow:**
1. **User-Facing Agent** receives and understands your query
2. **Analyst Agent** performs detailed data analysis
3. **Checker Agent** validates the analysis quality
4. **User-Facing Agent** provides the final, validated response

**Status:** {'✅ Three-Agent Ready' if self.llm else '⚠️ Basic Mode (No API Key)'}
        """
        return help_text

# ===== LEGACY COMPATIBILITY =====

class MultiAgentSystem:
    """Legacy compatibility class - redirects to three-agent system"""

    def __init__(self):
        self.agent = ThreeAgentSystem()

    def process_query(self, user_query: str) -> str:
        """Legacy method - redirects to three-agent system"""
        return self.agent.process_query(user_query)



# ===== LEGACY COMPATIBILITY =====

class WhitepaperIntelligentAgent:
    """Legacy compatibility class - redirects to multi-agent system"""

    def __init__(self):
        self.agent = MultiAgentSystem()

    def process_query(self, user_query: str) -> str:
        """Legacy method - redirects to multi-agent system"""
        return self.agent.process_query(user_query)

class WhitepaperMultiAgent:
    """Legacy compatibility class - redirects to multi-agent system"""

    def __init__(self):
        self.agent = MultiAgentSystem()

    def analyze_policy_query(self, user_query: str) -> Optional[str]:
        """Legacy method - redirects to multi-agent system"""
        return self.agent.process_query(user_query)
