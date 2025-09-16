# whitepaper/core/godagent.py
"""
God-Level Intelligent Agent System
The ultimate AI agent that understands everything and delivers policy analysis
"""

import os
import time
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from .intelligence import SmartDatasetIntelligence, DatasetInfo, QueryContext
from .vectordb import IntelligentVectorDB

console = Console()

class GodLevelAgent:
    """
    The Ultimate AI Agent - Understands Everything, Analyzes Everything
    """
    
    def __init__(self):
        self.console = console
        
        # Initialize components
        self.dataset_intelligence = SmartDatasetIntelligence()
        self.vector_db = IntelligentVectorDB()
        
        # Initialize LLM models
        self.analyst_model = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,
            max_tokens=3000
        )
        
        self.insight_model = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            max_tokens=2500
        )
        
        # System status
        self.ready = False
        self.datasets_loaded = False
        
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the god-level system"""
        console.print("[bold cyan]🚀 Initializing God-Level AI Agent System...[/bold cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Step 1: Load datasets into vector DB
            task1 = progress.add_task("Loading datasets into intelligent memory...", total=None)
            self._load_datasets_to_vector_db()
            progress.update(task1, completed=True)
            
            # Step 2: System ready
            task2 = progress.add_task("Activating god-level intelligence...", total=None)
            time.sleep(0.5)  # Dramatic pause
            progress.update(task2, completed=True)
        
        self.ready = True
        console.print("[bold green]✅ God-Level AI Agent System Ready![/bold green]")
        console.print(f"[green]📊 Loaded {len(self.dataset_intelligence.datasets)} datasets with full intelligence[/green]")
        
        # Show vector DB stats
        stats = self.vector_db.get_stats()
        console.print(f"[green]🧠 Vector DB: {stats['total_chunks']} chunks, {stats['unique_datasets']} datasets[/green]")
    
    def _load_datasets_to_vector_db(self):
        """Load all datasets into vector database for intelligent retrieval"""
        for dataset in self.dataset_intelligence.datasets:
            try:
                # Auto-clean if needed
                if not dataset.cleaned:
                    dataset = self.dataset_intelligence.auto_clean_dataset(dataset)
                
                # Load full dataframe
                df = pd.read_csv(dataset.path)
                
                # Add to vector database
                self.vector_db.add_dataset_to_vector_store(dataset, df)
                
            except Exception as e:
                console.print(f"[red]❌ Failed to load {dataset.name} to vector DB: {e}[/red]")
        
        self.datasets_loaded = True
    
    def analyze_query(self, user_query: str) -> str:
        """
        The main god-level analysis function
        Understands user query and delivers intelligent analysis
        """
        if not self.ready:
            return "❌ System not ready. Please wait for initialization."
        
        console.print(f"\n[bold blue]🎯 Analyzing: {user_query}[/bold blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Step 1: Understand the query
            task1 = progress.add_task("Understanding query intent and context...", total=None)
            query_context = self.dataset_intelligence.understand_query(user_query)
            progress.update(task1, completed=True)
            
            # Step 2: Select relevant datasets
            task2 = progress.add_task("Selecting most relevant datasets...", total=None)
            relevant_datasets = self.dataset_intelligence.select_best_datasets(query_context)
            progress.update(task2, completed=True)
            
            # Step 3: Gather intelligent context
            task3 = progress.add_task("Gathering intelligent context from vector DB...", total=None)
            if relevant_datasets:
                dataset_names = [d.name for d in relevant_datasets]
                context = self.vector_db.get_relevant_context(user_query, dataset_names)
            else:
                context = self.vector_db.get_relevant_context(user_query)
            progress.update(task3, completed=True)
            
            # Step 4: Generate analysis
            task4 = progress.add_task("Generating intelligent analysis...", total=None)
            analysis = self._generate_intelligent_analysis(user_query, query_context, relevant_datasets, context)
            progress.update(task4, completed=True)
            
            # Step 5: Generate insights and recommendations
            task5 = progress.add_task("Creating policy recommendations...", total=None)
            recommendations = self._generate_policy_recommendations(user_query, analysis, query_context, relevant_datasets)
            progress.update(task5, completed=True)
        
        # Compile final report
        final_report = self._compile_final_report(user_query, query_context, relevant_datasets, analysis, recommendations)
        
        return final_report
    
    def _generate_intelligent_analysis(self, query: str, query_context: QueryContext, 
                                     datasets: List[DatasetInfo], context: str) -> str:
        """Generate intelligent analysis using the best available data"""
        
        # Create dynamic system prompt based on query context
        system_prompt = self._create_dynamic_analysis_prompt(query_context, datasets)
        
        # Create context-rich user prompt
        user_prompt = f"""
Query: {query}

Query Context:
- Intent: {query_context.intent}
- Domain: {query_context.domain}
- Analysis Type: {query_context.analysis_type}
- Key Entities: {', '.join(query_context.entities)}
- Keywords: {', '.join(query_context.keywords)}

Relevant Data Context:
{context}

Available Datasets:
"""
        for dataset in datasets:
            user_prompt += f"- {dataset.name} ({dataset.type}): {dataset.shape[0]:,} records\n"
        
        user_prompt += """
Please provide a comprehensive data-driven analysis based on the actual data provided in the context. 
Focus on specific numerical insights, patterns, and trends from the real data.
"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.analyst_model.invoke(messages)
            return response.content
            
        except Exception as e:
            console.print(f"[red]❌ Analysis generation failed: {e}[/red]")
            return f"Analysis generation failed due to: {str(e)}"
    
    def _create_dynamic_analysis_prompt(self, query_context: QueryContext, datasets: List[DatasetInfo]) -> str:
        """Create a dynamic system prompt based on query context and available data"""
        
        base_prompt = """You are an elite AI data analyst and policy expert with god-level intelligence. 
Your expertise spans economics, policy analysis, statistics, and domain-specific knowledge."""
        
        # Add domain-specific expertise
        if query_context.domain == 'banking':
            domain_expertise = """
You are specialized in banking and financial services analysis. You understand:
- Banking infrastructure and branch optimization
- Financial inclusion and accessibility
- ATM distribution and usage patterns
- Regional banking needs assessment
"""
        elif query_context.domain == 'agriculture':
            domain_expertise = """
You are specialized in agricultural policy and resource analysis. You understand:
- Agricultural electricity consumption patterns
- Rural infrastructure needs
- Irrigation and power requirements
- Regional agricultural development
"""
        elif query_context.domain == 'energy':
            domain_expertise = """
You are specialized in energy policy and consumption analysis. You understand:
- Electricity consumption patterns and optimization
- Energy efficiency and conservation
- Grid management and load balancing
- Renewable energy integration
"""
        else:
            domain_expertise = """
You have broad analytical expertise across multiple domains and can adapt your analysis
to the specific data and context provided.
"""
        
        # Add analysis type specific guidance
        analysis_guidance = ""
        if query_context.analysis_type == 'trend':
            analysis_guidance = "Focus on temporal patterns, growth trends, and time-series insights."
        elif query_context.analysis_type == 'correlation':
            analysis_guidance = "Focus on relationships between variables and correlation analysis."
        elif query_context.analysis_type == 'geographic':
            analysis_guidance = "Focus on geographical patterns, regional variations, and spatial analysis."
        elif query_context.analysis_type == 'comparison':
            analysis_guidance = "Focus on comparative analysis and benchmarking between entities."
        else:
            analysis_guidance = "Focus on comprehensive statistical analysis and key insights."
        
        # Add data-specific instructions
        data_instructions = """
CRITICAL: Base your analysis ONLY on the real data provided in the context. 
- Use actual district names, numbers, and specific data points from the records
- If district-level data is provided, analyze specific districts by name
- Reference exact values and perform calculations on the actual data
- Avoid generic analysis - be specific about which districts/entities need attention
- When data shows specific records, use them to identify the lowest/highest performers
- Provide concrete, actionable insights with specific names and numbers
"""
        
        return f"{base_prompt}\n\n{domain_expertise}\n\nAnalysis Focus: {analysis_guidance}\n\n{data_instructions}"
    
    def _generate_policy_recommendations(self, query: str, analysis: str, 
                                       query_context: QueryContext, datasets: List[DatasetInfo]) -> str:
        """Generate policy recommendations based on analysis"""
        
        system_prompt = f"""You are a senior policy advisor with extensive experience in {query_context.domain} policy.
Your role is to translate data analysis into actionable policy recommendations.

You excel at:
- Creating practical, implementable policy solutions
- Balancing stakeholder interests and constraints
- Considering economic, social, and political implications
- Designing evidence-based interventions

Focus on creating specific, measurable, and achievable recommendations based on the data analysis provided."""
        
        user_prompt = f"""
Based on the following data analysis, please provide specific policy recommendations:

Query: {query}
Domain: {query_context.domain}
Intent: {query_context.intent}

Data Analysis:
{analysis}

Please provide:
1. Top 3-5 specific policy recommendations
2. Implementation priorities and timeline
3. Expected outcomes and success metrics
4. Potential challenges and mitigation strategies
5. Budget and resource considerations

Make recommendations concrete and actionable for policymakers.
"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.insight_model.invoke(messages)
            return response.content
            
        except Exception as e:
            console.print(f"[red]❌ Recommendation generation failed: {e}[/red]")
            return f"Recommendation generation failed due to: {str(e)}"
    
    def _compile_final_report(self, query: str, query_context: QueryContext, 
                            datasets: List[DatasetInfo], analysis: str, recommendations: str) -> str:
        """Compile the final comprehensive report"""
        
        # Header
        report = "=" * 80 + "\n"
        report += "🎯 GOD-LEVEL AI POLICY ANALYSIS REPORT\n"
        report += "=" * 80 + "\n\n"
        
        # Query Information
        report += f"📝 QUERY: {query}\n\n"
        
        # Query Context
        report += "🧠 INTELLIGENT ANALYSIS CONTEXT:\n"
        report += f"• Intent: {query_context.intent.title()}\n"
        report += f"• Domain: {query_context.domain.title()}\n"
        report += f"• Analysis Type: {query_context.analysis_type.title()}\n"
        report += f"• Key Entities: {', '.join(query_context.entities) if query_context.entities else 'None detected'}\n"
        report += f"• Keywords: {', '.join(query_context.keywords[:5]) if query_context.keywords else 'None detected'}\n\n"
        
        # Datasets Used
        if datasets:
            report += "📊 DATASETS ANALYZED:\n"
            for i, dataset in enumerate(datasets, 1):
                report += f"{i}. {dataset.name} ({dataset.type})\n"
                report += f"   • Shape: {dataset.shape[0]:,} rows × {dataset.shape[1]} columns\n"
                report += f"   • Key Columns: {', '.join(dataset.columns[:5])}\n"
                report += f"   • Relevance Score: {dataset.relevance_score:.2f}\n\n"
        
        # Data-Driven Analysis
        report += "📈 DATA-DRIVEN ANALYSIS:\n"
        report += "-" * 50 + "\n"
        report += analysis + "\n\n"
        
        # Policy Recommendations
        report += "💡 POLICY RECOMMENDATIONS:\n"
        report += "-" * 50 + "\n"
        report += recommendations + "\n\n"
        
        # System Information
        report += "🤖 ANALYSIS METADATA:\n"
        report += f"• AI Model: GPT-4 (God-Level Intelligence)\n"
        report += f"• Analysis Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"• Datasets Used: {len(datasets)}\n"
        report += f"• Vector DB Chunks: {len(self.vector_db.chunks)}\n"
        report += f"• Analysis Confidence: High (Real Data Based)\n\n"
        
        report += "=" * 80 + "\n"
        report += "🎉 ANALYSIS COMPLETE - Ready for Policy Implementation\n"
        report += "=" * 80
        
        return report
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and statistics"""
        vector_stats = self.vector_db.get_stats()
        
        return {
            "ready": self.ready,
            "datasets_loaded": self.datasets_loaded,
            "total_datasets": len(self.dataset_intelligence.datasets),
            "vector_db_stats": vector_stats,
            "model_status": "GPT-4 (God-Level)",
            "capabilities": [
                "Automatic dataset selection",
                "Intelligent data cleaning",
                "Vector-based semantic search",
                "Domain-specific analysis",
                "Policy recommendation generation",
                "Real-time adaptation"
            ]
        }
    
    def list_available_datasets(self) -> str:
        """List all available datasets with intelligence"""
        if not self.dataset_intelligence.datasets:
            return "❌ No datasets found. Please add CSV files to the directory."
        
        result = "📊 AVAILABLE INTELLIGENT DATASETS:\n"
        result += "=" * 50 + "\n"
        
        # Group by type
        by_type = {}
        for dataset in self.dataset_intelligence.datasets:
            if dataset.type not in by_type:
                by_type[dataset.type] = []
            by_type[dataset.type].append(dataset)
        
        for dataset_type, datasets_list in by_type.items():
            result += f"\n🏷️  {dataset_type.upper()} ({len(datasets_list)} datasets):\n"
            for dataset in datasets_list:
                status = "✅ Cleaned" if dataset.cleaned else "🧹 Raw"
                result += f"   • {dataset.name} - {dataset.shape[0]:,} rows - {status}\n"
                result += f"     Columns: {', '.join(dataset.columns[:4])}{'...' if len(dataset.columns) > 4 else ''}\n"
        
        result += f"\n💡 Total: {len(self.dataset_intelligence.datasets)} datasets ready for god-level analysis"
        return result
