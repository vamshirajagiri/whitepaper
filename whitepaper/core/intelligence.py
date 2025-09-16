# whitepaper/core/intelligence.py
"""
Smart Dataset Intelligence System
Automatically selects, processes, and analyzes datasets based on user queries
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import re
from rich.console import Console

console = Console()

@dataclass
class DatasetInfo:
    """Information about a dataset"""
    path: Path
    name: str
    type: str  # 'banking', 'agriculture', 'energy', 'general'
    columns: List[str]
    shape: Tuple[int, int]
    sample_data: List[Dict]
    stats: Dict
    cleaned: bool = False
    relevance_score: float = 0.0

@dataclass
class QueryContext:
    """Context extracted from user query"""
    intent: str  # 'analysis', 'prediction', 'comparison', 'recommendation'
    domain: str  # 'banking', 'agriculture', 'energy', 'policy', 'general'
    entities: List[str]
    keywords: List[str]
    analysis_type: str  # 'statistical', 'trend', 'correlation', 'geographic'

class SmartDatasetIntelligence:
    """
    God-level dataset intelligence that understands everything
    """
    
    def __init__(self, data_directory: str = "."):
        self.data_directory = Path(data_directory)
        self.datasets: List[DatasetInfo] = []
        self.vector_store = None
        
        # Domain classification patterns
        self.domain_patterns = {
            'banking': ['bank', 'branch', 'atm', 'credit', 'loan', 'finance', 'account', 'deposit'],
            'agriculture': ['agricultural', 'farming', 'crop', 'irrigation', 'rural', 'harvest', 'pesticide'],
            'energy': ['electricity', 'power', 'consumption', 'load', 'units', 'kwh', 'energy', 'grid'],
            'transportation': ['ev', 'charging', 'vehicle', 'station', 'transport', 'mobility'],
            'policy': ['policy', 'government', 'regulation', 'law', 'compliance', 'governance']
        }
        
        # Intent patterns
        self.intent_patterns = {
            'analysis': ['analyze', 'analysis', 'insights', 'understand', 'examine', 'study'],
            'prediction': ['predict', 'forecast', 'future', 'projection', 'trend', 'growth'],
            'comparison': ['compare', 'versus', 'vs', 'difference', 'contrast', 'benchmark'],
            'recommendation': ['recommend', 'suggest', 'should', 'best', 'optimal', 'improve']
        }
        
        self.scan_datasets()
    
    def scan_datasets(self):
        """Intelligently scan and catalog all available datasets"""
        console.print("[cyan]🧠 Scanning datasets with AI intelligence...[/cyan]")
        
        # Look for CSV files in current directory and subdirectories
        csv_files = []
        csv_files.extend(self.data_directory.glob("*.csv"))
        csv_files.extend(self.data_directory.glob("**/*.csv"))
        
        for csv_file in csv_files:
            try:
                dataset_info = self._analyze_dataset(csv_file)
                if dataset_info:
                    self.datasets.append(dataset_info)
                    console.print(f"[green]✓ Analyzed: {dataset_info.name} ({dataset_info.type})[/green]")
            except Exception as e:
                console.print(f"[red]✗ Failed to analyze {csv_file.name}: {e}[/red]")
        
        console.print(f"[green]🎯 Found {len(self.datasets)} intelligent datasets[/green]")
    
    def _analyze_dataset(self, file_path: Path) -> Optional[DatasetInfo]:
        """Deeply analyze a dataset to understand its structure and content"""
        try:
            df = pd.read_csv(file_path)
            
            # Basic info
            name = file_path.stem
            shape = df.shape
            columns = list(df.columns)
            
            # Sample data (first 3 rows)
            sample_data = df.head(3).to_dict('records')
            
            # Statistical summary
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            stats = {}
            if len(numeric_cols) > 0:
                stats = df[numeric_cols].describe().to_dict()
            
            # Classify dataset type based on columns and content
            dataset_type = self._classify_dataset_type(columns, sample_data)
            
            # Check if it's already cleaned
            cleaned = '_cleaned' in name or 'clean' in name.lower()
            
            return DatasetInfo(
                path=file_path,
                name=name,
                type=dataset_type,
                columns=columns,
                shape=shape,
                sample_data=sample_data,
                stats=stats,
                cleaned=cleaned
            )
        
        except Exception as e:
            console.print(f"[red]Error analyzing {file_path.name}: {e}[/red]")
            return None
    
    def _classify_dataset_type(self, columns: List[str], sample_data: List[Dict]) -> str:
        """Intelligently classify dataset type based on columns and content"""
        columns_text = ' '.join(columns).lower()
        sample_text = ' '.join(str(v) for row in sample_data for v in row.values()).lower()
        
        scores = {}
        for domain, keywords in self.domain_patterns.items():
            score = sum(1 for keyword in keywords if keyword in columns_text or keyword in sample_text)
            if score > 0:
                scores[domain] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'general'
    
    def understand_query(self, query: str) -> QueryContext:
        """Use AI to understand user query intent and requirements"""
        query_lower = query.lower()
        
        # Detect intent
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            if score > 0:
                intent_scores[intent] = score
        
        intent = max(intent_scores, key=intent_scores.get) if intent_scores else 'analysis'
        
        # Detect domain
        domain_scores = {}
        for domain, patterns in self.domain_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            if score > 0:
                domain_scores[domain] = score
        
        domain = max(domain_scores, key=domain_scores.get) if domain_scores else 'general'
        
        # Extract entities and keywords
        entities = self._extract_entities(query)
        keywords = self._extract_keywords(query)
        
        # Determine analysis type
        analysis_type = self._determine_analysis_type(query)
        
        return QueryContext(
            intent=intent,
            domain=domain,
            entities=entities,
            keywords=keywords,
            analysis_type=analysis_type
        )
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract named entities from query"""
        # Simple entity extraction - can be enhanced with NLP libraries
        entities = []
        
        # Look for location names
        locations = ['hyderabad', 'telangana', 'india', 'bangalore', 'mumbai', 'delhi']
        for loc in locations:
            if loc in query.lower():
                entities.append(loc.title())
        
        # Look for specific terms
        terms = re.findall(r'\b[A-Z][a-z]+\b', query)
        entities.extend(terms[:5])  # Limit to 5 entities
        
        return list(set(entities))
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query"""
        # Remove stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall'}
        
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords[:10]  # Limit to 10 keywords
    
    def _determine_analysis_type(self, query: str) -> str:
        """Determine the type of analysis needed"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['trend', 'time', 'over time', 'growth', 'decline']):
            return 'trend'
        elif any(word in query_lower for word in ['correlation', 'relationship', 'connected', 'related']):
            return 'correlation'
        elif any(word in query_lower for word in ['geographic', 'location', 'area', 'region', 'district']):
            return 'geographic'
        elif any(word in query_lower for word in ['compare', 'difference', 'vs', 'versus']):
            return 'comparison'
        else:
            return 'statistical'
    
    def select_best_datasets(self, query_context: QueryContext, max_datasets: int = 3) -> List[DatasetInfo]:
        """Intelligently select the most relevant datasets for the query"""
        
        # Score each dataset based on relevance
        for dataset in self.datasets:
            score = self._calculate_relevance_score(dataset, query_context)
            dataset.relevance_score = score
        
        # Sort by relevance and return top datasets
        relevant_datasets = sorted(
            [d for d in self.datasets if d.relevance_score > 0], 
            key=lambda x: x.relevance_score, 
            reverse=True
        )[:max_datasets]
        
        if relevant_datasets:
            console.print(f"[green]🎯 Selected {len(relevant_datasets)} most relevant datasets:[/green]")
            for dataset in relevant_datasets:
                console.print(f"[green]  • {dataset.name} ({dataset.type}) - Score: {dataset.relevance_score:.2f}[/green]")
        
        return relevant_datasets
    
    def _calculate_relevance_score(self, dataset: DatasetInfo, query_context: QueryContext) -> float:
        """Calculate how relevant a dataset is to the query"""
        score = 0.0
        
        # Domain match (highest weight)
        if dataset.type == query_context.domain:
            score += 10.0
        elif query_context.domain == 'general':
            score += 2.0
        
        # Column name matches
        dataset_text = ' '.join(dataset.columns).lower()
        for keyword in query_context.keywords:
            if keyword in dataset_text:
                score += 2.0
        
        # Entity matches
        for entity in query_context.entities:
            if entity.lower() in dataset_text:
                score += 3.0
        
        # Intent-specific scoring
        if query_context.intent == 'analysis' and len(dataset.stats) > 0:
            score += 1.0
        
        # Prefer cleaned datasets
        if dataset.cleaned:
            score += 1.0
        
        # Size bonus (not too small, not too large)
        if 100 <= dataset.shape[0] <= 50000:
            score += 1.0
        
        return score
    
    def auto_clean_dataset(self, dataset: DatasetInfo) -> DatasetInfo:
        """Automatically clean and prepare dataset for analysis"""
        if dataset.cleaned:
            return dataset
        
        console.print(f"[yellow]🧹 Auto-cleaning dataset: {dataset.name}[/yellow]")
        
        try:
            df = pd.read_csv(dataset.path)
            
            # Basic cleaning operations
            # 1. Handle missing values
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
            
            categorical_cols = df.select_dtypes(include=['object']).columns
            for col in categorical_cols:
                df[col] = df[col].fillna(df[col].mode().iloc[0] if not df[col].mode().empty else 'Unknown')
            
            # 2. Remove duplicates
            df = df.drop_duplicates()
            
            # 3. Clean column names
            df.columns = [col.strip().replace(' ', '_').upper() for col in df.columns]
            
            # 4. Handle outliers in numeric columns (simple IQR method)
            for col in numeric_cols:
                if col in df.columns:
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    df[col] = df[col].clip(lower_bound, upper_bound)
            
            # Save cleaned dataset
            cleaned_path = dataset.path.parent / f"{dataset.path.stem}_cleaned_auto.csv"
            df.to_csv(cleaned_path, index=False)
            
            # Update dataset info
            dataset.path = cleaned_path
            dataset.name = f"{dataset.name}_cleaned_auto"
            dataset.cleaned = True
            dataset.shape = df.shape
            dataset.columns = list(df.columns)
            dataset.sample_data = df.head(3).to_dict('records')
            
            # Update stats
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                dataset.stats = df[numeric_cols].describe().to_dict()
            
            console.print(f"[green]✅ Cleaned dataset saved: {cleaned_path.name}[/green]")
            return dataset
            
        except Exception as e:
            console.print(f"[red]❌ Failed to clean dataset: {e}[/red]")
            return dataset
    
    def get_dataset_summary(self, dataset: DatasetInfo) -> str:
        """Generate a comprehensive summary of the dataset"""
        summary = f"""
Dataset: {dataset.name}
Type: {dataset.type}
Shape: {dataset.shape[0]:,} rows × {dataset.shape[1]} columns
Cleaned: {'Yes' if dataset.cleaned else 'No'}

Columns: {', '.join(dataset.columns)}

Sample Data:
"""
        for i, row in enumerate(dataset.sample_data[:2], 1):
            summary += f"Row {i}: {row}\n"
        
        if dataset.stats:
            summary += "\nStatistical Summary:\n"
            for col, stats in dataset.stats.items():
                if isinstance(stats, dict):
                    mean = stats.get('mean', 0)
                    std = stats.get('std', 0)
                    summary += f"  {col}: Mean={mean:.2f}, Std={std:.2f}\n"
        
        return summary