import os
from pathlib import Path
from typing import List
from rich.console import Console
from rich.panel import Panel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

console = Console()

class WhitepaperMultiAgent:
    """Simple Multi-Agent System for Policy Analysis"""

    def __init__(self):
        self.cleaned_data_dir = Path("cleaned-dataset")
        self.llm = None
        self._init_llm()

    def _init_llm(self):
        """Initialize OpenAI LLM"""
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.llm = ChatOpenAI(
                temperature=0.1,
                model_name="gpt-4",
                openai_api_key=api_key,
                max_tokens=2000
            )
        else:
            console.print("[red]❌ OPENAI_API_KEY not found in environment variables[/red]")
            console.print("[yellow]Please set: export OPENAI_API_KEY='your-key'[/yellow]")

    def _select_datasets_for_analysis(self, user_query: str):
        """Select datasets for analysis"""
        cleaned_dir = Path("cleaned-dataset")
        if not cleaned_dir.exists():
            console.print("[red]❌ No cleaned datasets found. Run ETL first![/red]")
            return []

        cleaned_files = list(cleaned_dir.glob("*_cleaned.csv"))
        if not cleaned_files:
            console.print("[red]❌ No cleaned datasets available for analysis[/red]")
            return []

        # Simple selection - use all available datasets
        console.print(f"[green]📊 Analyzing {len(cleaned_files)} datasets[/green]")
        return cleaned_files

    def analyze_policy_query(self, user_query: str):
        """Main entry point for policy analysis"""
        console.print("[bold cyan]🤖 Whitepaper Multi-Agent Analysis[/bold cyan]")
        console.print("[blue]🔬 Performing policy analysis...[/blue]")

        # Select datasets
        selected_datasets = self._select_datasets_for_analysis(user_query)
        if not selected_datasets:
            return None

        # Load dataset contents
        dataset_contents = []
        for path in selected_datasets:
            try:
                import pandas as pd
                df = pd.read_csv(path)
                content = f"Dataset: {path.name}\n{df.head(10).to_string()}\n"
                dataset_contents.append(content)
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load {path.name}: {e}[/yellow]")

        combined_data = "\n".join(dataset_contents)

        # Simple multi-agent analysis
        analysis_prompt = f"""
        You are a policy analyst. Analyze the following datasets and provide insights for policy makers.

        USER QUERY: {user_query}

        DATASETS:
        {combined_data}

        Provide:
        1. Key findings from the data
        2. Policy implications
        3. Recommendations for government action

        Be specific and evidence-based.
        """

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are an expert policy analyst providing evidence-based analysis."),
                HumanMessage(content=analysis_prompt)
            ])

            # Display results
            console.print(Panel(
                response.content,
                title="🎯 Policy Analysis Results",
                border_style="green"
            ))

            return response.content

        except Exception as e:
            console.print(f"[red]❌ Analysis failed: {e}[/red]")
            return None
