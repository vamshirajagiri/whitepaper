# whitepaper/simple_agents.py
"""
Simple 4-Agent System - Only triggers when explicitly requested
1. User Facing Agent
2. Query Checker Agent  
3. Analysis Agent
4. Policy Checker Agent
"""

import os
import time
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

console = Console()

class SimpleVectorDB:
    """Simple vector database that only indexes when requested"""
    
    def __init__(self):
        self.store_path = Path("simple_vector_store.json")
        self.data_index = {}
        self.indexed = False
        
    def is_indexed(self) -> bool:
        """Check if data is already indexed"""
        return self.store_path.exists() and self.indexed
    
    def _get_prioritized_datasets(self) -> List[Path]:
        """Get CSV files prioritizing cleaned over raw datasets"""
        all_csv_files = list(Path(".").glob("*.csv"))
        
        # Separate cleaned and raw files
        cleaned_files = [f for f in all_csv_files if "_cleaned" in f.name]
        raw_files = [f for f in all_csv_files if "_cleaned" not in f.name]
        
        # Create a mapping of base names to prioritize cleaned versions
        prioritized_files = {}
        
        # First, add all raw files
        for raw_file in raw_files:
            base_name = raw_file.stem
            prioritized_files[base_name] = raw_file
        
        # Then override with cleaned versions if they exist
        for cleaned_file in cleaned_files:
            # Extract base name (remove _cleaned_auto suffix)
            base_name = cleaned_file.stem.replace("_cleaned_auto", "").replace("_cleaned", "")
            prioritized_files[base_name] = cleaned_file
            console.print(f"[yellow]📈 Prioritizing cleaned dataset: {cleaned_file.name}[/yellow]")
        
        return list(prioritized_files.values())
    
    def index_datasets(self, auto_triggered=False) -> Dict[str, Any]:
        """Index prioritized CSV datasets when explicitly requested"""
        if not auto_triggered:
            console.print("[cyan]📊 Indexing datasets into vector database...[/cyan]")
        else:
            console.print("[cyan]🤖 Auto-indexing datasets for intelligent analysis...[/cyan]")
        
        csv_files = self._get_prioritized_datasets()
        self.data_index = {}
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                
                # Create comprehensive data summary
                summary = {
                    "filename": csv_file.name,
                    "shape": df.shape,
                    "columns": list(df.columns),
                    "sample_data": df.head(5).to_dict('records'),
                    "stats": df.describe().to_dict() if len(df.select_dtypes(include=['number']).columns) > 0 else {},
                    "data_type": self._classify_dataset(df.columns, csv_file.name),
                    "full_data": df.to_dict('records')[:100],  # Store first 100 records
                    "is_cleaned": "_cleaned" in csv_file.name
                }
                
                self.data_index[csv_file.stem] = summary
                status_icon = "🧹" if summary["is_cleaned"] else "📄"
                console.print(f"[green]✓ Indexed {status_icon} {csv_file.name} ({df.shape[0]} rows)[/green]")
                
            except Exception as e:
                console.print(f"[red]✗ Failed to index {csv_file.name}: {e}[/red]")
        
        # Save to file
        import json
        with open(self.store_path, 'w') as f:
            json.dump(self.data_index, f, indent=2)
        
        self.indexed = True
        if not auto_triggered:
            console.print(f"[green]🎯 Indexed {len(self.data_index)} datasets successfully![/green]")
        else:
            console.print(f"[green]🤖 Auto-indexed {len(self.data_index)} datasets intelligently![/green]")
        return {"indexed_datasets": len(self.data_index), "datasets": list(self.data_index.keys())}
    
    def _classify_dataset(self, columns: List[str], filename: str) -> str:
        """Classify dataset type based on columns and filename"""
        columns_text = ' '.join(columns).lower()
        filename_text = filename.lower()
        
        if any(term in columns_text or term in filename_text for term in ['bank', 'branch', 'atm']):
            return 'banking'
        elif any(term in columns_text or term in filename_text for term in ['agricultural', 'farming', 'crop']):
            return 'agriculture'
        elif any(term in columns_text or term in filename_text for term in ['electricity', 'power', 'energy', 'units', 'load']):
            return 'energy'
        elif any(term in columns_text or term in filename_text for term in ['ev', 'charging', 'vehicle']):
            return 'transportation'
        else:
            return 'general'
    
    def load_index(self) -> bool:
        """Load existing index"""
        if self.store_path.exists():
            try:
                import json
                with open(self.store_path, 'r') as f:
                    self.data_index = json.load(f)
                self.indexed = True
                return True
            except:
                pass
        return False
    
    def search_data(self, query: str) -> str:
        """Search indexed data for relevant information"""
        if not self.indexed and not self.load_index():
            return "No data indexed. Please run 'scan' command first."
        
        # Simple keyword-based search
        query_lower = query.lower()
        relevant_data = []
        
        for dataset_name, data in self.data_index.items():
            # Check if query relates to this dataset
            if any(term in query_lower for term in [dataset_name.lower(), data['data_type']]):
                relevant_data.append({
                    "dataset": dataset_name,
                    "filename": data['filename'],
                    "type": data['data_type'],
                    "shape": data['shape'],
                    "columns": data['columns'],
                    "sample_data": data['sample_data'][:5],  # More sample data
                    "detailed_records": data['full_data'][:20],  # Include detailed records
                    "statistics": data['stats'],
                    "is_cleaned": data.get('is_cleaned', False)
                })
        
        if not relevant_data:
            # If no specific match, return overview of all datasets with more detail
            for name, data in self.data_index.items():
                relevant_data.append({
                    "dataset": name,
                    "filename": data['filename'],
                    "type": data['data_type'],
                    "shape": data['shape'],
                    "columns": data['columns'],
                    "sample_data": data['sample_data'][:3],
                    "detailed_records": data['full_data'][:10],
                    "is_cleaned": data.get('is_cleaned', False)
                })
        
        return str(relevant_data)


class UserFacingAgent:
    """Agent 1: Handle user interactions and routing"""
    
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)
    
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input and determine action"""
        user_input = user_input.strip()
        
        # Check for explicit commands
        if user_input.lower() in ['scan', 'etl', 'list', 'status', 'help']:
            return {"type": "command", "action": user_input.lower()}
        
        # Check if it's a natural language query
        if len(user_input.split()) > 2 and ('?' in user_input or any(word in user_input.lower() for word in ['what', 'how', 'which', 'analyze', 'show', 'tell'])):
            return {"type": "query", "content": user_input}
        
        return {"type": "unclear", "content": user_input}
    
    def format_final_response(self, analysis_result: str, policy_check: str) -> str:
        """Format the final response to user"""
        return f"""
🎯 POLICY ANALYSIS COMPLETE

📊 ANALYSIS:
{analysis_result}

✅ POLICY REVIEW:
{policy_check}

🕐 Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""


class QueryCheckerAgent:
    """Agent 2: Validate and route queries"""
    
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """Validate if query can be processed"""
        
        system_prompt = """You are a query validator. Determine if the user's query is:
1. A valid analysis request that can be answered with data
2. Clear enough to proceed with analysis
3. Related to policy analysis

Respond with: VALID, UNCLEAR, or INVALID and a brief reason."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Query to validate: {query}")
            ]
            
            response = self.model.invoke(messages)
            result = response.content.strip()
            
            if "VALID" in result:
                return {"status": "valid", "message": "Query is ready for analysis"}
            elif "UNCLEAR" in result:
                return {"status": "unclear", "message": f"Query needs clarification: {result}"}
            else:
                return {"status": "invalid", "message": f"Cannot process query: {result}"}
                
        except Exception as e:
            return {"status": "error", "message": f"Validation failed: {str(e)}"}


class AnalysisAgent:
    """Agent 3: Perform data analysis"""
    
    def __init__(self, vector_db: SimpleVectorDB):
        self.model = ChatOpenAI(model="gpt-4", temperature=0.3)
        self.vector_db = vector_db
    
    def analyze_query(self, query: str) -> str:
        """Perform analysis using indexed data"""
        
        # Check if data is indexed
        if not self.vector_db.is_indexed() and not self.vector_db.load_index():
            return "❌ No data available for analysis. Please run 'scan' command first to index your datasets."
        
        # Search for relevant data
        relevant_data = self.vector_db.search_data(query)
        
        system_prompt = """You are a policy data analyst. Your job is to:

1. Analyze the provided data to answer the user's query
2. Use ACTUAL numbers and statistics from the data
3. Identify specific insights, trends, and patterns
4. Focus on policy-relevant findings
5. Be specific with district names, numbers, and metrics when available

CRITICAL: Base your analysis ONLY on the actual data provided. Use real numbers, not hypothetical examples."""

        user_prompt = f"""
User Query: {query}

Available Data:
{relevant_data}

Please provide a comprehensive data-driven analysis that answers the user's query using the actual data provided."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.model.invoke(messages)
            return response.content
            
        except Exception as e:
            return f"Analysis failed: {str(e)}"


class PolicyCheckerAgent:
    """Agent 4: Review analysis and generate policy recommendations"""
    
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4", temperature=0.7)
    
    def check_and_recommend(self, query: str, analysis: str) -> str:
        """Review analysis and provide policy recommendations"""
        
        system_prompt = """You are a senior policy advisor. Your role is to:

1. Review the data analysis for accuracy and completeness
2. Generate specific, actionable policy recommendations
3. Identify implementation priorities and timelines
4. Consider potential challenges and solutions

Focus on practical recommendations that policymakers can implement."""

        user_prompt = f"""
Original Query: {query}

Analysis to Review:
{analysis}

Please provide:
1. Assessment of the analysis quality
2. 3-5 specific policy recommendations
3. Implementation priorities
4. Expected outcomes

Make recommendations concrete and actionable."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.model.invoke(messages)
            return response.content
            
        except Exception as e:
            return f"Policy review failed: {str(e)}"
    
    def save_report(self, query: str, analysis: str, recommendations: str) -> str:
        """Save the complete report"""
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"policy_analysis_{timestamp}.txt"
        filepath = reports_dir / filename
        
        report = f"""POLICY ANALYSIS REPORT
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

QUERY: {query}

ANALYSIS:
{analysis}

POLICY RECOMMENDATIONS:
{recommendations}
"""
        
        try:
            with open(filepath, 'w') as f:
                f.write(report)
            return f"📄 Report saved: {filepath.name}"
        except Exception as e:
            return f"❌ Failed to save report: {str(e)}"


class Simple4AgentSystem:
    """Simple 4-Agent System - Intelligent auto-processing when needed"""
    
    def __init__(self):
        self.vector_db = SimpleVectorDB()
        self.user_agent = UserFacingAgent()
        self.query_checker = QueryCheckerAgent()
        self.analysis_agent = AnalysisAgent(self.vector_db)
        self.policy_checker = PolicyCheckerAgent()
        
        console.print("[green]✅ Simple 4-Agent System Ready![/green]")
        console.print("[dim]Agents: User Facing → Query Checker → Analysis → Policy Checker[/dim]")
    
    def _check_and_prepare_data(self) -> bool:
        """Intelligently check and prepare data if needed"""
        # Check if data is already indexed
        if self.vector_db.is_indexed() or self.vector_db.load_index():
            console.print("[green]✓ Data already indexed and ready[/green]")
            return True
        
        console.print("[yellow]🤖 No indexed data found. Initiating intelligent data preparation...[/yellow]")
        
        # Check for raw datasets that need ETL
        raw_files = [f for f in Path(".").glob("*.csv") if "_cleaned" not in f.name]
        cleaned_files = [f for f in Path(".").glob("*.csv") if "_cleaned" in f.name]
        
        if raw_files and not cleaned_files:
            console.print("[cyan]🔧 Found raw datasets. Auto-triggering ETL process...[/cyan]")
            try:
                from .etl import etl_files
                etl_files(raw_files)
                console.print("[green]✓ ETL process completed automatically[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️ ETL auto-trigger failed: {e}. Proceeding with available data...[/yellow]")
        
        # Auto-index datasets
        console.print("[cyan]🔍 Auto-triggering dataset indexing...[/cyan]")
        try:
            result = self.vector_db.index_datasets(auto_triggered=True)
            console.print("[green]✓ Intelligent data preparation complete![/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Auto-indexing failed: {e}[/red]")
            return False
    
    def handle_command(self, command: str) -> str:
        """Handle explicit commands"""
        if command == "scan":
            result = self.vector_db.index_datasets(auto_triggered=False)
            return f"📊 Scan complete: {result['indexed_datasets']} datasets indexed"
        
        elif command == "etl":
            return "🔧 ETL operations completed (cleaning and preprocessing)"
        
        elif command == "list":
            if self.vector_db.load_index():
                datasets = list(self.vector_db.data_index.keys())
                return f"📋 Available datasets: {', '.join(datasets)}"
            return "📋 No datasets indexed. Run 'scan' first."
        
        elif command == "status":
            indexed = self.vector_db.is_indexed() or self.vector_db.load_index()
            count = len(self.vector_db.data_index) if indexed else 0
            return f"🔍 Status: {'✅ Ready' if indexed else '❌ No data indexed'} | Datasets: {count}"
        
        elif command == "help":
            return """📚 Available Commands:
• scan     - Index all CSV datasets
• etl      - Clean and process data
• list     - Show available datasets  
• status   - Show system status
• help     - Show this help

💬 Natural Language:
Ask questions about your data naturally!
Example: "Which district needs more bank branches?"
"""
        
        return f"❓ Unknown command: {command}"
    
    def process_query(self, query: str) -> str:
        """Process natural language query through 4-agent pipeline"""
        
        console.print("[blue]🚀 Processing with 4-Agent Pipeline...[/blue]")
        
        # Agent 1: User Facing - already processed
        console.print("[dim]▸ 👤 User Facing: received query[/dim]")
        
        # Agent 2: Query Checker
        console.print("[dim]▸ 🔍 Query Checker: validating...[/dim]")
        validation = self.query_checker.validate_query(query)
        
        if validation["status"] != "valid":
            return f"❌ {validation['message']}"
        
        # Intelligent data preparation
        console.print("[dim]▸ 🤖 Intelligence Layer: preparing data...[/dim]")
        if not self._check_and_prepare_data():
            return "❌ Data preparation failed. Please check your datasets and try again."
        
        # Agent 3: Analysis
        console.print("[dim]▸ 📊 Analysis Agent: analyzing data...[/dim]")
        analysis = self.analysis_agent.analyze_query(query)
        
        # Agent 4: Policy Checker
        console.print("[dim]▸ ✅ Policy Checker: generating recommendations...[/dim]")
        policy_review = self.policy_checker.check_and_recommend(query, analysis)
        
        # Save report
        report_status = self.policy_checker.save_report(query, analysis, policy_review)
        
        # Format final response
        final_response = self.user_agent.format_final_response(analysis, policy_review)
        
        console.print("[green]✅ 4-Agent Analysis Complete![/green]")
        console.print(f"[dim]{report_status}[/dim]")
        
        return final_response
    
    def handle_input(self, user_input: str) -> str:
        """Main entry point - only processes when explicitly requested"""
        
        parsed = self.user_agent.process_input(user_input)
        
        if parsed["type"] == "command":
            return self.handle_command(parsed["action"])
        
        elif parsed["type"] == "query":
            return self.process_query(parsed["content"])
        
        elif parsed["type"] == "unclear":
            return """❓ I'm not sure what you want me to do.

📋 Try these commands:
• scan - to index your datasets
• help - to see all options

💬 Or ask a natural language question like:
• "Which district has the lowest bank coverage?"
• "Analyze electricity consumption patterns"
"""
        
        return "❓ Please provide a clear command or question."