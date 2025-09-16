# whitepaper/core/vectordb.py
"""
Vector Database Integration for Semantic Analysis and RAG
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
from rich.console import Console

# Try to import vector DB libraries (install if needed)
try:
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
    VECTOR_DB_AVAILABLE = True
except ImportError:
    VECTOR_DB_AVAILABLE = False

console = Console()

@dataclass
class DataChunk:
    """A chunk of data for vector storage"""
    content: str
    metadata: Dict[str, Any]
    chunk_id: str
    dataset_name: str
    chunk_type: str  # 'summary', 'statistics', 'sample', 'insights'

class IntelligentVectorDB:
    """
    Intelligent Vector Database for semantic search and RAG
    """
    
    def __init__(self, persist_directory: str = "./vector_store"):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        
        self.embeddings = None
        self.vector_store = None
        self.chunks: List[DataChunk] = []
        
        global VECTOR_DB_AVAILABLE
        if VECTOR_DB_AVAILABLE:
            try:
                self.embeddings = OpenAIEmbeddings()
                self._load_or_create_vector_store()
            except Exception as e:
                console.print(f"[yellow]⚠️ Vector DB initialization failed: {e}[/yellow]")
                console.print("[yellow]Will use fallback semantic search[/yellow]")
                VECTOR_DB_AVAILABLE = False
        
        if not VECTOR_DB_AVAILABLE:
            console.print("[yellow]📋 Using fallback semantic search (install langchain packages for full vector DB)[/yellow]")
    
    def _load_or_create_vector_store(self):
        """Load existing vector store or create new one"""
        vector_store_path = self.persist_directory / "faiss_index"
        
        if vector_store_path.exists():
            try:
                self.vector_store = FAISS.load_local(
                    str(vector_store_path), 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                console.print("[green]✅ Loaded existing vector store[/green]")
                self._load_chunks_metadata()
            except Exception as e:
                console.print(f"[yellow]⚠️ Failed to load vector store: {e}[/yellow]")
                self.vector_store = None
        else:
            console.print("[cyan]🔄 Creating new vector store...[/cyan]")
    
    def _load_chunks_metadata(self):
        """Load chunks metadata from disk"""
        metadata_file = self.persist_directory / "chunks_metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    chunks_data = json.load(f)
                    self.chunks = [DataChunk(**chunk) for chunk in chunks_data]
                console.print(f"[green]✅ Loaded {len(self.chunks)} data chunks[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️ Failed to load chunks metadata: {e}[/yellow]")
    
    def _save_chunks_metadata(self):
        """Save chunks metadata to disk"""
        metadata_file = self.persist_directory / "chunks_metadata.json"
        try:
            chunks_data = [asdict(chunk) for chunk in self.chunks]
            with open(metadata_file, 'w') as f:
                json.dump(chunks_data, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Failed to save chunks metadata: {e}[/red]")
    
    def add_dataset_to_vector_store(self, dataset_info, df: pd.DataFrame):
        """Add dataset to vector store for semantic search"""
        global VECTOR_DB_AVAILABLE
        console.print(f"[cyan]🔄 Adding {dataset_info.name} to vector database...[/cyan]")
        
        documents = []
        chunks = []
        
        # 1. Dataset Summary Chunk
        summary_content = f"""
Dataset: {dataset_info.name}
Type: {dataset_info.type}
Shape: {dataset_info.shape[0]:,} rows × {dataset_info.shape[1]} columns
Columns: {', '.join(dataset_info.columns)}

This dataset contains {dataset_info.type} data with {dataset_info.shape[0]:,} records.
Key columns include: {', '.join(dataset_info.columns[:5])}
"""
        
        summary_chunk = DataChunk(
            content=summary_content.strip(),
            metadata={
                "dataset_name": dataset_info.name,
                "dataset_type": dataset_info.type,
                "shape": dataset_info.shape,
                "columns": dataset_info.columns
            },
            chunk_id=self._generate_chunk_id("summary", dataset_info.name),
            dataset_name=dataset_info.name,
            chunk_type="summary"
        )
        chunks.append(summary_chunk)
        
        if VECTOR_DB_AVAILABLE:
            documents.append(Document(
                page_content=summary_content,
                metadata=summary_chunk.metadata
            ))
        
        # 2. Statistical Summary Chunk
        if dataset_info.stats:
            stats_content = f"Statistical Analysis for {dataset_info.name}:\n"
            for col, stats in dataset_info.stats.items():
                if isinstance(stats, dict):
                    mean = stats.get('mean', 0)
                    std = stats.get('std', 0)
                    min_val = stats.get('min', 0)
                    max_val = stats.get('max', 0)
                    stats_content += f"{col}: Mean={mean:.2f}, Std={std:.2f}, Range=[{min_val:.2f} to {max_val:.2f}]\n"
            
            stats_chunk = DataChunk(
                content=stats_content.strip(),
                metadata={
                    "dataset_name": dataset_info.name,
                    "statistics": dataset_info.stats
                },
                chunk_id=self._generate_chunk_id("statistics", dataset_info.name),
                dataset_name=dataset_info.name,
                chunk_type="statistics"
            )
            chunks.append(stats_chunk)
            
            if VECTOR_DB_AVAILABLE:
                documents.append(Document(
                    page_content=stats_content,
                    metadata=stats_chunk.metadata
                ))
        
        # 3. Sample Data Chunks
        sample_content = f"Sample data from {dataset_info.name}:\n"
        for i, row in enumerate(dataset_info.sample_data[:3], 1):
            sample_content += f"Record {i}: {row}\n"
        
        sample_chunk = DataChunk(
            content=sample_content.strip(),
            metadata={
                "dataset_name": dataset_info.name,
                "sample_data": dataset_info.sample_data[:3]
            },
            chunk_id=self._generate_chunk_id("sample", dataset_info.name),
            dataset_name=dataset_info.name,
            chunk_type="sample"
        )
        chunks.append(sample_chunk)
        
        if VECTOR_DB_AVAILABLE:
            documents.append(Document(
                page_content=sample_content,
                metadata=sample_chunk.metadata
            ))
        
        # 4. Detailed Records Chunk (for better analysis)
        if len(df) <= 100:  # For smaller datasets, include more records
            detailed_content = f"Complete records from {dataset_info.name}:\n"
            for idx, row in df.iterrows():
                row_dict = row.to_dict()
                detailed_content += f"{row_dict}\n"
                if idx >= 19:  # Limit to first 20 records to avoid token limits
                    break
        else:
            # For larger datasets, include strategic sample
            detailed_content = f"Representative records from {dataset_info.name}:\n"
            # Include first 10 records
            for idx, row in df.head(10).iterrows():
                row_dict = row.to_dict()
                detailed_content += f"{row_dict}\n"
        
        if detailed_content:
            detailed_chunk = DataChunk(
                content=detailed_content.strip(),
                metadata={
                    "dataset_name": dataset_info.name,
                    "chunk_type": "detailed_records",
                    "record_count": min(len(df), 20)
                },
                chunk_id=self._generate_chunk_id("detailed", dataset_info.name),
                dataset_name=dataset_info.name,
                chunk_type="detailed"
            )
            chunks.append(detailed_chunk)
            
            if VECTOR_DB_AVAILABLE:
                documents.append(Document(
                    page_content=detailed_content,
                    metadata=detailed_chunk.metadata
                ))
        
        # 5. Domain-specific Insights Chunk
        insights_content = self._generate_domain_insights(dataset_info, df)
        if insights_content:
            insights_chunk = DataChunk(
                content=insights_content,
                metadata={
                    "dataset_name": dataset_info.name,
                    "dataset_type": dataset_info.type,
                    "insights_type": "domain_specific"
                },
                chunk_id=self._generate_chunk_id("insights", dataset_info.name),
                dataset_name=dataset_info.name,
                chunk_type="insights"
            )
            chunks.append(insights_chunk)
            
            if VECTOR_DB_AVAILABLE:
                documents.append(Document(
                    page_content=insights_content,
                    metadata=insights_chunk.metadata
                ))
        
        # Add to vector store
        if VECTOR_DB_AVAILABLE and documents:
            try:
                if self.vector_store is None:
                    self.vector_store = FAISS.from_documents(documents, self.embeddings)
                else:
                    self.vector_store.add_documents(documents)
                
                # Save to disk
                vector_store_path = self.persist_directory / "faiss_index"
                self.vector_store.save_local(str(vector_store_path))
                
            except Exception as e:
                console.print(f"[red]❌ Failed to add to vector store: {e}[/red]")
        
        # Add chunks to memory
        self.chunks.extend(chunks)
        self._save_chunks_metadata()
        
        console.print(f"[green]✅ Added {len(chunks)} chunks to vector database[/green]")
    
    def _generate_chunk_id(self, chunk_type: str, dataset_name: str) -> str:
        """Generate unique chunk ID"""
        content = f"{chunk_type}_{dataset_name}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def _generate_domain_insights(self, dataset_info, df: pd.DataFrame) -> str:
        """Generate domain-specific insights based on dataset type"""
        insights = f"Domain insights for {dataset_info.name} ({dataset_info.type}):\n"
        
        try:
            if dataset_info.type == 'banking':
                # Banking-specific insights with detailed district analysis
                if 'DISTRICTS' in df.columns or 'Districts' in df.columns:
                    district_col = 'DISTRICTS' if 'DISTRICTS' in df.columns else 'Districts'
                    
                    # Calculate total banking presence per district
                    bank_cols = [col for col in df.columns if 'Bank' in col and col != district_col]
                    if bank_cols:
                        # Create total banking score
                        df['Total_Banks'] = df[bank_cols].sum(axis=1)
                        
                        insights += f"BANKING COVERAGE ANALYSIS ({df[district_col].nunique()} districts):\n"
                        
                        # Find districts with lowest coverage
                        bottom_5 = df.nsmallest(5, 'Total_Banks')
                        insights += f"\nDISTRICTS WITH LOWEST BANKING COVERAGE:\n"
                        for idx, row in bottom_5.iterrows():
                            insights += f"- {row[district_col]}: {row['Total_Banks']} total banks\n"
                        
                        # Find districts with highest coverage  
                        top_5 = df.nlargest(5, 'Total_Banks')
                        insights += f"\nDISTRICTS WITH HIGHEST BANKING COVERAGE:\n"
                        for idx, row in top_5.iterrows():
                            insights += f"- {row[district_col]}: {row['Total_Banks']} total banks\n"
                        
                        # Overall statistics
                        insights += f"\nOVERALL STATISTICS:\n"
                        insights += f"- Average banks per district: {df['Total_Banks'].mean():.1f}\n"
                        insights += f"- Median banks per district: {df['Total_Banks'].median():.1f}\n"
                        insights += f"- Banking coverage inequality (std dev): {df['Total_Banks'].std():.1f}\n"
            
            elif dataset_info.type == 'agriculture':
                # Agriculture-specific insights
                if 'LOAD' in df.columns and 'UNITS' in df.columns:
                    avg_load = df['LOAD'].mean()
                    avg_units = df['UNITS'].mean()
                    insights += f"Average electrical load: {avg_load:.2f}, Average units consumed: {avg_units:.2f}.\n"
                    
                    if 'AREANAME' in df.columns:
                        area_stats = df.groupby('AREANAME')[['LOAD', 'UNITS']].mean()
                        top_area = area_stats['UNITS'].idxmax()
                        insights += f"Highest consumption area: {top_area}.\n"
            
            elif dataset_info.type == 'energy':
                # Energy-specific insights
                consumption_cols = [col for col in df.columns if 'consumption' in col.lower() or 'units' in col.lower()]
                for col in consumption_cols:
                    if df[col].dtype in ['int64', 'float64']:
                        total_consumption = df[col].sum()
                        insights += f"Total {col}: {total_consumption:,.0f}.\n"
        
        except Exception as e:
            insights += f"Unable to generate specific insights: {str(e)}\n"
        
        return insights.strip() if len(insights.strip()) > 50 else ""
    
    def semantic_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search on stored data"""
        global VECTOR_DB_AVAILABLE
        if VECTOR_DB_AVAILABLE and self.vector_store:
            try:
                # Use vector similarity search
                docs = self.vector_store.similarity_search(query, k=k)
                
                results = []
                for doc in docs:
                    results.append({
                        'content': doc.page_content,
                        'metadata': doc.metadata,
                        'score': 1.0  # FAISS doesn't return scores by default
                    })
                
                console.print(f"[green]🔍 Found {len(results)} relevant chunks via vector search[/green]")
                return results
                
            except Exception as e:
                console.print(f"[yellow]⚠️ Vector search failed, using fallback: {e}[/yellow]")
        
        # Fallback: keyword-based search
        return self._fallback_search(query, k)
    
    def _fallback_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Fallback search using keyword matching"""
        query_words = set(query.lower().split())
        results = []
        
        for chunk in self.chunks:
            # Calculate simple relevance score
            content_words = set(chunk.content.lower().split())
            common_words = query_words.intersection(content_words)
            
            if common_words:
                score = len(common_words) / len(query_words)
                results.append({
                    'content': chunk.content,
                    'metadata': chunk.metadata,
                    'score': score,
                    'chunk_id': chunk.chunk_id,
                    'chunk_type': chunk.chunk_type
                })
        
        # Sort by relevance score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        console.print(f"[green]🔍 Found {min(len(results), k)} relevant chunks via keyword search[/green]")
        return results[:k]
    
    def get_relevant_context(self, query: str, dataset_names: List[str] = None) -> str:
        """Get relevant context for RAG-based analysis"""
        # Search for relevant chunks
        search_results = self.semantic_search(query, k=10)
        
        # Filter by dataset names if specified
        if dataset_names:
            search_results = [
                result for result in search_results 
                if result.get('metadata', {}).get('dataset_name') in dataset_names
            ]
        
        # Build context
        context_parts = []
        for result in search_results[:5]:  # Top 5 most relevant
            content = result['content']
            # Don't add chunk type prefixes that might confuse the LLM
            context_parts.append(content)
        
        return "\n\n".join(context_parts)
    
    def get_dataset_context(self, dataset_name: str) -> str:
        """Get comprehensive context for a specific dataset"""
        relevant_chunks = [chunk for chunk in self.chunks if chunk.dataset_name == dataset_name]
        
        context_parts = []
        # Order by chunk type priority - prioritize detailed records and insights
        type_priority = {'insights': 1, 'detailed': 2, 'summary': 3, 'statistics': 4, 'sample': 5}
        
        sorted_chunks = sorted(relevant_chunks, key=lambda x: type_priority.get(x.chunk_type, 6))
        
        for chunk in sorted_chunks:
            # Don't add chunk type prefixes that might confuse the LLM
            context_parts.append(chunk.content)
        
        return "\n\n".join(context_parts)
    
    def get_stats(self) -> Dict[str, int]:
        """Get vector database statistics"""
        return {
            'total_chunks': len(self.chunks),
            'unique_datasets': len(set(chunk.dataset_name for chunk in self.chunks)),
            'chunk_types': len(set(chunk.chunk_type for chunk in self.chunks)),
            'vector_db_enabled': VECTOR_DB_AVAILABLE and self.vector_store is not None
        }