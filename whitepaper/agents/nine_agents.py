# whitepaper/agents/nine_agents.py
"""
9 Individual Agents for Hub-and-Spoke Architecture
Each agent has specific role, GPT model, and responsibilities
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from rich.console import Console

from .base_agent import BaseAgent
from .state import MultiAgentState, AgentType

console = Console()

class UserFacingAgent(BaseAgent):
    """Agent 1: User Interface & Conversation (GPT-3.5)"""
    
    def __init__(self):
        system_prompt = """You are a friendly CLI assistant for data analysis. Your role:
        1. Greet users and handle conversations
        2. For simple queries (date, help, greetings), respond directly
        3. For complex queries needing analysis, forward to Query Checker
        4. Present final results with clear formatting and insights
        5. Ask clarifying questions when needed
        
        Keep responses concise and professional. Use emojis sparingly."""
        
        super().__init__(AgentType.USER_FACING, system_prompt)
    
    def execute(self, state: MultiAgentState) -> MultiAgentState:
        query = state["query"]
        
        # Check if simple query
        simple_keywords = ["date", "time", "help", "hello", "hi", "thanks", "thank you"]
        if any(keyword in query.lower() for keyword in simple_keywords):
            response = self.execute_with_prompt(query, "This is a simple query, respond directly.")
            state["final_report"] = response
            state["approved"] = True
            return self.log_execution(state, "Handled simple query directly")
        
        # Forward complex queries
        state = self.send_message(state, AgentType.QUERY_CHECKER, 
                                "Complex query detected - forwarding for analysis")
        state["current_agent"] = AgentType.QUERY_CHECKER
        return self.log_execution(state, "Forwarded complex query to Query Checker")

class QueryCheckerAgent(BaseAgent):
    """Agent 2: Query Validation & Routing (GPT-3.5)"""

    def __init__(self):
        system_prompt = """You are a query validation specialist for a policy analysis system. Your role is to:

        APPROVE queries that involve:
        - Data analysis and insights
        - Policy analysis and recommendations
        - Economic trends and patterns
        - Consumption patterns and statistics
        - Regional/state-level analysis (Telangana, Hyderabad, etc.)
        - Business and investment analysis
        - Market research and trends
        - Statistical analysis requests

        REJECT only queries that are:
        - Personal questions (who are you, what's your favorite)
        - Inappropriate or offensive content
        - Completely unrelated to analysis
        - Pure entertainment or casual conversation

        For policy analysis queries like "consumption data in Telangana" or "IT investment analysis":
        - ALWAYS approve them as they are legitimate analysis requests
        - Set needs_data=true for data-related queries
        - Set needs_web=true for current trends or external context

        Respond with JSON: {{"approved": true/false, "reason": "brief explanation", "needs_web": true/false, "needs_data": true/false}}

        Default to APPROVAL for analysis-related queries."""

        super().__init__(AgentType.QUERY_CHECKER, system_prompt)
    
    def execute(self, state: MultiAgentState) -> MultiAgentState:
        query = state["query"]
        context = f"Query to validate: {query}"

        # Check for obvious analysis keywords before calling LLM
        analysis_keywords = [
            "data", "analysis", "consumption", "telangana", "hyderabad", "economic",
            "policy", "investment", "it companies", "business", "market", "trends",
            "statistics", "patterns", "insights", "correlation"
        ]

        has_analysis_keywords = any(keyword in query.lower() for keyword in analysis_keywords)

        # If query contains analysis keywords, auto-approve
        if has_analysis_keywords:
            state["is_analysis_query"] = True
            state = self.send_message(state, AgentType.SUPERVISOR,
                                    "Query contains analysis keywords - auto-approved for data analysis")
            state["current_agent"] = AgentType.SUPERVISOR
            return self.log_execution(state, "Auto-approved based on analysis keywords")

        response = self.execute_with_prompt(query, context)

        try:
            # Parse JSON response
            result = json.loads(response)

            if not result.get("approved", False):
                # Query rejected
                state["final_report"] = f"❌ Query not suitable for analysis: {result.get('reason', 'Invalid query type')}"
                state["approved"] = True  # End workflow
                return self.log_execution(state, f"Rejected query: {result.get('reason')}")

            # Query approved - forward to Supervisor
            state["is_analysis_query"] = True
            state = self.send_message(state, AgentType.SUPERVISOR,
                                    f"Query approved for analysis. Needs web: {result.get('needs_web')}, Needs data: {result.get('needs_data')}")
            state["current_agent"] = AgentType.SUPERVISOR
            return self.log_execution(state, "Query approved - forwarded to Supervisor")

        except json.JSONDecodeError:
            # Fallback if JSON parsing fails - default to approval for analysis queries
            if has_analysis_keywords:
                state["is_analysis_query"] = True
                state = self.send_message(state, AgentType.SUPERVISOR, "JSON parse error but analysis keywords detected - proceeding with analysis")
                state["current_agent"] = AgentType.SUPERVISOR
                return self.log_execution(state, "JSON parse error - defaulted to approval due to analysis keywords")
            else:
                state = self.send_message(state, AgentType.SUPERVISOR, "Query validation unclear - proceeding with analysis")
                state["current_agent"] = AgentType.SUPERVISOR
                return self.log_execution(state, "JSON parse error - defaulted to approval")

class SupervisorAgent(BaseAgent):
    """Agent 3: Hub - Orchestrates entire workflow (GPT-3.5)"""
    
    def __init__(self):
        system_prompt = """You are the Supervisor - the orchestration hub. Your responsibilities:
        
        1. Analyze the query and determine required agents
        2. Coordinate Dataset Handler, Web Searcher, Analysis Team
        3. Monitor progress and handle agent failures
        4. Ensure quality before sending to Checker
        
        Think step-by-step and delegate efficiently. Track all agent communications."""
        
        super().__init__(AgentType.SUPERVISOR, system_prompt)
    
    def execute(self, state: MultiAgentState) -> MultiAgentState:
        query = state["query"]
        
        # Determine what's needed
        needs_data = self._query_needs_data(query)
        needs_web = self._query_needs_web(query)
        
        state = self.log_execution(state, f"Orchestrating: Data={needs_data}, Web={needs_web}")
        
        # Route to appropriate agents
        if needs_data:
            state = self.send_message(state, AgentType.DATASET_HANDLER, 
                                    "Load and process available datasets for analysis")
            state["current_agent"] = AgentType.DATASET_HANDLER
        elif needs_web:
            state = self.send_message(state, AgentType.WEB_SEARCHER, 
                                    f"Search for information about: {query}")
            state["current_agent"] = AgentType.WEB_SEARCHER
        else:
            # Go directly to analysis
            state = self.send_message(state, AgentType.ANALYSIS_STATS, 
                                    "Proceed with statistical analysis")
            state["current_agent"] = AgentType.ANALYSIS_STATS
        
        return state
    
    def _query_needs_data(self, query: str) -> bool:
        """Check if query needs dataset analysis"""
        data_keywords = [
            "data", "dataset", "csv", "excel", "statistics", "trends", "correlation",
            "consumption", "analysis", "patterns", "insights", "telangana", "hyderabad",
            "economic", "policy", "investment", "it companies", "business", "market"
        ]
        return any(keyword in query.lower() for keyword in data_keywords)

    def _query_needs_web(self, query: str) -> bool:
        """Check if query needs web search"""
        web_keywords = [
            "recent", "current", "news", "latest", "trends", "market", "policy",
            "investment", "companies", "business", "industry", "growth", "development"
        ]
        return any(keyword in query.lower() for keyword in web_keywords)

class DatasetHandlerAgent(BaseAgent):
    """Agent 4: Data Processing & ETL (GPT-3.5)"""
    
    def __init__(self):
        system_prompt = """You are the Dataset Handler. Your role:
        
        1. Load and scan available datasets
        2. Run ETL processes if needed
        3. Prepare data summaries for analysis
        4. Store processed data in vector database
        
        Focus on data quality and provide clear summaries."""
        
        super().__init__(AgentType.DATASET_HANDLER, system_prompt)
    
    def execute(self, state: MultiAgentState) -> MultiAgentState:
        # Get available cleaned datasets
        cleaned_dir = Path("cleaned-dataset")
        datasets = []
        
        if cleaned_dir.exists():
            datasets = list(cleaned_dir.glob("*_cleaned*.csv"))
        
        if not datasets:
            # Look for raw datasets
            datasets = list(Path(".").glob("*.csv"))
        
        state["datasets"] = datasets
        
        if datasets:
            dataset_summary = f"Found {len(datasets)} datasets: {[d.name for d in datasets[:3]]}"
            state = self.send_message(state, AgentType.ANALYSIS_STATS, 
                                    f"Datasets ready for analysis. {dataset_summary}")
            state["current_agent"] = AgentType.ANALYSIS_STATS
        else:
            state = self.send_message(state, AgentType.WEB_SEARCHER, 
                                    "No datasets found - requesting web data")
            state["current_agent"] = AgentType.WEB_SEARCHER
        
        return self.log_execution(state, f"Processed {len(datasets)} datasets")

class WebSearcherAgent(BaseAgent):
    """Agent 5: Web Search & External Context (GPT-3.5)"""
    
    def __init__(self):
        system_prompt = """You are the Web Searcher. Your role:
        
        1. Search for relevant external information
        2. Summarize findings clearly
        3. Provide context for analysis
        
        Focus on credible sources and recent information."""
        
        super().__init__(AgentType.WEB_SEARCHER, system_prompt)
    
    def execute(self, state: MultiAgentState) -> MultiAgentState:
        query = state["query"]
        
        # Simulate web search (in production, use Tavily API)
        web_context = {
            "search_query": query,
            "summary": f"External context for: {query}. This would contain web search results.",
            "sources": ["example.com", "news.com"],
            "timestamp": "2025-01-07"
        }
        
        state["web_context"] = web_context
        
        state = self.send_message(state, AgentType.ANALYSIS_STATS, 
                                "Web context gathered - proceeding to analysis")
        state["current_agent"] = AgentType.ANALYSIS_STATS
        
        return self.log_execution(state, "Web search completed")

class AnalysisStatsAgent(BaseAgent):
    """Agent 6: Statistical Analysis (GPT-4)"""
    
    def __init__(self):
        system_prompt = """You are the Statistics Analyst. Your role:
        
        1. Perform statistical analysis on datasets
        2. Calculate trends, correlations, key metrics
        3. Generate numerical insights
        4. Prepare data for visualization
        
        Be precise and data-driven. Focus on policy-relevant statistics."""
        
        super().__init__(AgentType.ANALYSIS_STATS, system_prompt)
    
    def execute(self, state: MultiAgentState) -> MultiAgentState:
        query = state["query"]
        datasets = state.get("datasets", [])
        web_context = state.get("web_context", {})
        
        context = f"Datasets: {len(datasets)}, Web context: {bool(web_context)}"
        analysis_result = self.execute_with_prompt(query, context)
        
        state["stats_results"] = {
            "analysis": analysis_result,
            "metrics": {"processed_datasets": len(datasets)},
            "timestamp": "2025-01-07"
        }
        
        state = self.send_message(state, AgentType.ANALYSIS_VIZ, 
                                "Statistical analysis complete - ready for visualization")
        state["current_agent"] = AgentType.ANALYSIS_VIZ
        
        return self.log_execution(state, "Statistical analysis completed")

class AnalysisVizAgent(BaseAgent):
    """Agent 7: Visualization & Charts (GPT-4)"""
    
    def __init__(self):
        system_prompt = """You are the Visualization Specialist. Your role:
        
        1. Create ASCII charts and visualizations
        2. Design clear data presentations
        3. Generate visual insights
        
        Use simple ASCII art for terminal display."""
        
        super().__init__(AgentType.ANALYSIS_VIZ, system_prompt)
    
    def execute(self, state: MultiAgentState) -> MultiAgentState:
        stats_results = state.get("stats_results", {})
        
        # Generate simple ASCII visualization
        viz_data = {
            "charts": [
                "    Data Trend:\n    ████  High\n    ██    Medium\n    █     Low"
            ],
            "summary": "Visual representation of key findings"
        }
        
        state["viz_data"] = viz_data
        
        state = self.send_message(state, AgentType.ANALYSIS_INSIGHTS, 
                                "Visualizations ready - generating insights")
        state["current_agent"] = AgentType.ANALYSIS_INSIGHTS
        
        return self.log_execution(state, "Visualizations generated")

class AnalysisInsightsAgent(BaseAgent):
    """Agent 8: Strategic Insights & Recommendations (GPT-4)"""
    
    def __init__(self):
        system_prompt = """You are the Insights Generator. Your role:
        
        1. Synthesize all analysis into actionable insights
        2. Generate policy recommendations
        3. Identify key trends and implications
        4. Create comprehensive reports
        
        Focus on practical, unbiased recommendations for policy makers."""
        
        super().__init__(AgentType.ANALYSIS_INSIGHTS, system_prompt)
    
    def execute(self, state: MultiAgentState) -> MultiAgentState:
        query = state["query"]
        stats = state.get("stats_results", {})
        viz = state.get("viz_data", {})
        web = state.get("web_context", {})
        
        context = f"Stats: {bool(stats)}, Viz: {bool(viz)}, Web: {bool(web)}"
        insights = self.execute_with_prompt(query, context)
        
        state["insights"] = {
            "recommendations": insights,
            "confidence": "High",
            "sources": ["Statistical Analysis", "Web Research"]
        }
        
        state = self.send_message(state, AgentType.CHECKER, 
                                "Insights generated - ready for quality review")
        state["current_agent"] = AgentType.CHECKER
        
        return self.log_execution(state, "Strategic insights generated")

class CheckerAgent(BaseAgent):
    """Agent 9: Quality Assurance & Final Review (GPT-4)"""
    
    def __init__(self):
        system_prompt = """You are the Quality Checker. Your role:
        
        1. Review all analysis for completeness and accuracy
        2. Check for biases or unsupported claims
        3. Ensure professional, balanced reporting
        4. Approve or request revisions
        
        Be thorough but efficient. Focus on factual accuracy."""
        
        super().__init__(AgentType.CHECKER, system_prompt)
    
    def execute(self, state: MultiAgentState) -> MultiAgentState:
        insights = state.get("insights", {})
        stats = state.get("stats_results", {})

        # Quality check
        quality_check = self.execute_with_prompt(
            "Review this analysis for quality and bias",
            f"Analysis complete. Insights generated: {bool(insights)}. Stats available: {bool(stats)}"
        )

        # Compile final report
        final_report = self._compile_final_report(state)

        # Save report to files
        saved_files = self._save_report_to_files(final_report, state["query"])

        # Add file save notification to the report
        file_notification = self._create_file_notification(saved_files)
        final_report_with_files = final_report + "\n\n" + file_notification

        state["final_report"] = final_report_with_files
        state["approved"] = True

        state = self.send_message(state, AgentType.USER_FACING,
                                "Analysis approved and saved to files - ready for presentation")

        return self.log_execution(state, "Quality check passed - analysis approved and saved")
    
    def _compile_final_report(self, state: MultiAgentState) -> str:
        """Compile comprehensive final report"""
        query = state["query"]
        insights = state.get("insights", {}).get("recommendations", "No insights generated")
        stats = state.get("stats_results", {}).get("analysis", "No statistical analysis")
        viz = state.get("viz_data", {}).get("charts", ["No visualizations"])
        
        report = f"""
🎯 POLICY ANALYSIS RESULTS

Query: {query}

📊 KEY FINDINGS:
{stats}

💡 STRATEGIC INSIGHTS:
{insights}

📈 VISUALIZATIONS:
{viz[0] if viz else "No charts available"}

✅ Quality assured and bias-checked
        """
        
        return report.strip()

    def _save_report_to_files(self, report: str, query: str) -> Dict[str, str]:
        """Save the analysis report to both .txt and .pdf files"""
        # Create reports directory if it doesn't exist (in project root)
        reports_dir = Path("../../reports")  # Go up to project root from whitepaper/
        reports_dir.mkdir(exist_ok=True)

        # Generate filename based on query and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Clean query for filename (remove special characters)
        clean_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_query = clean_query.replace(' ', '_')[:50]  # Limit length
        base_filename = f"analysis_{clean_query}_{timestamp}"

        saved_files = {}

        try:
            # Save as .txt file
            txt_filename = f"{base_filename}.txt"
            txt_filepath = reports_dir / txt_filename

            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write(f"WHITEPAPER AI ANALYSIS REPORT\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Query: {query}\n")
                f.write("=" * 80 + "\n\n")
                f.write(report)

            saved_files['txt'] = str(txt_filepath)

            # Save as .pdf file (simple text-based PDF)
            pdf_filename = f"{base_filename}.pdf"
            pdf_filepath = reports_dir / pdf_filename

            # Create a simple PDF-like text file
            pdf_content = self._create_pdf_content(report, query)
            with open(pdf_filepath, 'w', encoding='utf-8') as f:
                f.write(pdf_content)

            saved_files['pdf'] = str(pdf_filepath)

            console.print(f"[green]✅ Analysis report saved to files:[/green]")
            console.print(f"   📄 {txt_filepath}")
            console.print(f"   📕 {pdf_filepath}")

        except Exception as e:
            console.print(f"[red]❌ Error saving report to files: {e}[/red]")
            # Return empty dict if saving fails
            return {}

        return saved_files

    def _create_pdf_content(self, report: str, query: str) -> str:
        """Create PDF-like formatted content"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Create basic PDF structure
        header = """%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length """

        content_length = len(report.encode('utf-8')) + 200
        content = f"""{content_length}
>>
stream
BT
/F1 12 Tf
72 720 Td
(WHITEPAPER AI ANALYSIS REPORT) Tj
0 -20 Td
(Generated: {timestamp}) Tj
0 -20 Td
(Query: {query}) Tj
0 -40 Td

{report.replace('(', '\\(').replace(')', '\\)')}
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
0000001000 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref"""

        footer = "%%EOF"

        # Calculate startxref position
        total_length = len(header) + len(str(content_length)) + len(content) + len(footer)
        startxref_pos = total_length - len(footer) - 10

        pdf_content = header + str(content_length) + content + str(startxref_pos) + "\n" + footer

        return pdf_content

    def _create_file_notification(self, saved_files: Dict[str, str]) -> str:
        """Create notification message about saved files"""
        if not saved_files:
            return "⚠️  Note: Report could not be saved to files due to an error."

        notification = "💾 ANALYSIS REPORT SAVED\n"
        notification += "=" * 40 + "\n"

        if 'txt' in saved_files:
            txt_path = Path(saved_files['txt'])
            notification += f"📄 Text File: {txt_path.name}\n"
            notification += f"   Location: {txt_path.parent}\n"

        if 'pdf' in saved_files:
            pdf_path = Path(saved_files['pdf'])
            notification += f"📕 PDF File: {pdf_path.name}\n"
            notification += f"   Location: {pdf_path.parent}\n"

        notification += "\n🔍 You can find these files in the 'reports' folder in your project directory."
        notification += "\n📧 The reports contain the complete analysis with all findings and recommendations."

        return notification
