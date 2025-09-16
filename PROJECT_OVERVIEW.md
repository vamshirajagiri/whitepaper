# Whitepaper CLI - Simple 4-Agent Policy Analysis System

## 🚀 Project Overview

**Whitepaper** is an intelligent CLI-based policy analysis system that leverages AI agents to automatically analyze government datasets and generate actionable policy recommendations. The system uses a 4-agent architecture with automatic data preparation, intelligent dataset prioritization, and comprehensive policy analysis capabilities.

## 🏗️ Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Whitepaper CLI                           │
├─────────────────────────────────────────────────────────────┤
│  🤖 Simple 4-Agent System                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ User Facing   │→ │ Query Checker │→ │ Analysis      │   │
│  │ Agent         │  │ Agent         │  │ Agent         │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
│                                         ↓                   │
│  ┌───────────────┐  ┌─────────────────────────────────────┐ │
│  │ Policy        │← │ Intelligence Layer                  │ │
│  │ Checker Agent │  │ (Auto ETL + Indexing)              │ │
│  └───────────────┘  └─────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  📊 Simple Vector Database                                  │
│  - Prioritized Dataset Indexing                            │
│  - Smart Data Search & Retrieval                          │
├─────────────────────────────────────────────────────────────┤
│  🔧 ETL Pipeline                                           │
│  - Automatic Data Cleaning                                 │
│  - Format Standardization                                  │
└─────────────────────────────────────────────────────────────┘
```

### 4-Agent Workflow

1. **👤 User Facing Agent**: Receives user input and determines if it's a command or natural language query
2. **🔍 Query Checker Agent**: Validates queries for clarity, relevance, and policy analysis suitability
3. **📊 Analysis Agent**: Performs data-driven analysis using indexed datasets from the vector database
4. **✅ Policy Checker Agent**: Reviews analysis results and generates actionable policy recommendations

### 🧠 Intelligence Layer

The system includes an intelligent layer that automatically:
- **Detects** when data isn't indexed
- **Triggers ETL** for raw datasets when needed
- **Prioritizes cleaned datasets** over raw ones
- **Indexes datasets** seamlessly during query processing

## 🎯 Key Features

### ✅ Intelligent Auto-Processing
- **Smart Data Preparation**: Automatically prepares data when queries are received
- **Dataset Prioritization**: Prefers cleaned datasets (`*_cleaned_auto.csv`) over raw ones
- **No Manual Setup**: Users can directly ask questions without manual indexing

### ✅ Real Data-Driven Analysis
- **Actual Statistics**: Uses real numbers, district names, and metrics from datasets
- **Comprehensive Context**: Provides detailed records and sample data for analysis
- **Specific Insights**: Generates district-level, data-backed policy recommendations

### ✅ Seamless User Experience
- **Natural Language**: Ask questions in plain English
- **Command Support**: Traditional CLI commands for system management
- **Report Generation**: Automatic saving of analysis reports with timestamps

## 📁 Project Structure

```
whitepaper/
├── whitepaper/
│   ├── __init__.py                 # Package initialization
│   ├── cli.py                      # Main CLI entry point
│   ├── shell.py                    # Interactive shell interface
│   ├── simple_agents.py            # 4-Agent system implementation
│   ├── scanner.py                  # Dataset scanning utilities
│   ├── etl.py                      # ETL pipeline for data cleaning
│   └── utils.py                    # Utility functions (logo, etc.)
├── reports/                        # Generated policy reports
├── cleaned-dataset/                # ETL processed datasets
├── *.csv                          # Raw and cleaned datasets
└── simple_vector_store.json       # Vector database index
```

## 🚀 How to Run

### Prerequisites
```bash
# Install dependencies
pip install pandas rich langchain-openai pathlib

# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

### Installation & Usage

1. **Clone/Navigate to Project Directory**
```bash
cd /path/to/whitepaper
```

2. **Install Package** (if needed)
```bash
pip install -e .
```

3. **Run the CLI**
```bash
python -m whitepaper
```

### Usage Examples

#### Commands
```bash
whitepaper> help          # Show all available commands
whitepaper> list          # Show available datasets  
whitepaper> scan          # Manually index datasets
whitepaper> status        # Show system status
whitepaper> exit          # Exit the system
```

#### Natural Language Queries
```bash
whitepaper> which areas need more bank branches?
whitepaper> analyze district-wise agricultural consumption patterns
whitepaper> what trends do you see in the electricity data?
whitepaper> provide policy recommendations for EV charging infrastructure
```

### Intelligent Workflow Example
```
User Query: "Which districts need more bank branches?"
    ↓
🤖 System detects no indexed data
    ↓  
🔧 Auto-triggers ETL (if needed) + Indexing
    ↓
📊 Prioritizes cleaned datasets (Bank Branches_cleaned_auto.csv)
    ↓
🔍 Analyzes actual data (Adilabad: 34 branches, Jangaon: 47 branches...)
    ↓
📝 Generates specific policy recommendations
    ↓
💾 Saves report to reports/policy_analysis_YYYYMMDD_HHMMSS.txt
```

## 🔧 Core Code Components

### 1. Simple4AgentSystem (`simple_agents.py`)

**Main orchestrator** that manages the 4-agent workflow:

```python
class Simple4AgentSystem:
    def __init__(self):
        self.vector_db = SimpleVectorDB()          # Data storage
        self.user_agent = UserFacingAgent()        # Input processing
        self.query_checker = QueryCheckerAgent()   # Query validation
        self.analysis_agent = AnalysisAgent()      # Data analysis  
        self.policy_checker = PolicyCheckerAgent() # Policy recommendations
    
    def handle_input(self, user_input: str) -> str:
        # Main entry point - routes commands vs queries
        
    def _check_and_prepare_data(self) -> bool:
        # Intelligence layer - auto ETL + indexing
```

**Key Methods:**
- `handle_input()`: Main entry point for all user interactions
- `_check_and_prepare_data()`: Intelligent auto-preparation logic
- `process_query()`: 4-agent pipeline execution

### 2. SimpleVectorDB (`simple_agents.py`)

**Intelligent dataset management**:

```python
class SimpleVectorDB:
    def _get_prioritized_datasets(self) -> List[Path]:
        # Prioritizes cleaned over raw datasets
        
    def index_datasets(self, auto_triggered=False) -> Dict[str, Any]:
        # Indexes prioritized datasets with smart selection
        
    def search_data(self, query: str) -> str:
        # Retrieves relevant data with detailed records
```

**Key Features:**
- Smart dataset prioritization (cleaned over raw)
- Comprehensive data indexing with statistics
- Intelligent search with detailed record access

### 3. Analysis Agents (`simple_agents.py`)

Each agent has a specific role:

```python
# Agent 1: User interaction
class UserFacingAgent:
    def process_input(self, user_input: str) -> Dict[str, Any]
    def format_final_response(self, analysis: str, policy: str) -> str

# Agent 2: Query validation  
class QueryCheckerAgent:
    def validate_query(self, query: str) -> Dict[str, Any]

# Agent 3: Data analysis
class AnalysisAgent:
    def analyze_query(self, query: str) -> str

# Agent 4: Policy recommendations
class PolicyCheckerAgent:
    def check_and_recommend(self, query: str, analysis: str) -> str
    def save_report(self, query: str, analysis: str, recommendations: str) -> str
```

### 4. Shell Interface (`shell.py`)

**CLI interface** that provides:
- Interactive command processing
- Rich console output with colors and formatting
- Integration with the 4-agent system
- Status monitoring and help system

## 📊 Data Flow

```
Raw CSV Data → ETL Processing → Cleaned Datasets → Vector Indexing → AI Analysis → Policy Reports
```

1. **Input**: Raw CSV datasets (banking, agriculture, energy, etc.)
2. **ETL**: Automatic cleaning and standardization
3. **Indexing**: Smart prioritization and vector storage
4. **Analysis**: AI-powered data analysis using GPT-4
5. **Output**: Actionable policy recommendations with specific metrics

## 🎯 Upgrade & Enhancement Guide

### To Add New Dataset Types:

1. **Update Dataset Classification** (`simple_agents.py`):
```python
def _classify_dataset(self, columns: List[str], filename: str) -> str:
    # Add new classification logic
    if any(term in columns_text for term in ['healthcare', 'hospital']):
        return 'healthcare'
```

2. **Enhance Search Logic**:
```python
def search_data(self, query: str) -> str:
    # Add domain-specific search patterns
```

### To Add New Agents:

1. **Create Agent Class**:
```python
class NewSpecializedAgent:
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4", temperature=0.3)
    
    def process_specialized_task(self, data: str) -> str:
        # Specialized processing logic
```

2. **Integrate into System**:
```python
class Simple4AgentSystem:
    def __init__(self):
        # Add new agent
        self.specialized_agent = NewSpecializedAgent()
```

### To Enhance Analysis Quality:

1. **Improve Prompts** (`simple_agents.py`):
   - Update `system_prompt` in `AnalysisAgent`
   - Enhance context provided to models
   - Add domain-specific instructions

2. **Add More Data Context**:
```python
def search_data(self, query: str) -> str:
    # Include more detailed records
    # Add cross-dataset relationships
    # Provide historical trends
```

### To Scale Performance:

1. **Vector Database Enhancement**:
   - Replace SimpleVectorDB with ChromaDB or Pinecone
   - Add semantic embeddings for better search
   - Implement caching mechanisms

2. **Parallel Processing**:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add async processing for multiple agents
```

### To Add New Output Formats:

1. **Report Generation** (`simple_agents.py`):
```python
def save_report(self, query: str, analysis: str, recommendations: str, format='txt') -> str:
    if format == 'pdf':
        # Generate PDF report
    elif format == 'json':
        # Generate JSON output
```

## 🎤 Demo Script for Judges

### 1. Introduction (30 seconds)
> "Whitepaper is an intelligent policy analysis CLI that automatically analyzes government datasets using a 4-agent AI system. It can process raw data, generate insights, and provide actionable policy recommendations without manual data preparation."

### 2. Live Demo (2 minutes)

**Show Intelligence Layer:**
```bash
# Start with clean state
rm simple_vector_store.json

# Ask a direct question - watch auto-preparation
python -m whitepaper
> which districts need more bank branches?
```

**Highlight Key Points:**
- ✅ Auto-detects no indexed data
- ✅ Prioritizes cleaned datasets over raw
- ✅ Provides specific district names and numbers
- ✅ Generates actionable policy recommendations
- ✅ Saves detailed report automatically

### 3. Architecture Explanation (1 minute)
> "The system uses 4 specialized AI agents: User Facing for input processing, Query Checker for validation, Analysis Agent for data-driven insights, and Policy Checker for recommendations. An Intelligence Layer automatically handles data preparation, prioritizing cleaned datasets over raw ones."

### 4. Technical Highlights (30 seconds)
> "Built with Python, LangChain, and GPT-4. Features include intelligent auto-ETL, vector database indexing, natural language processing, and comprehensive report generation. The system scales easily with new datasets and can be extended with additional specialized agents."

### 5. Impact & Use Cases (30 seconds)
> "Perfect for government agencies, policy researchers, and decision-makers who need rapid, data-driven insights from complex datasets. Reduces analysis time from hours to minutes while ensuring accuracy with real data points."

## 🛡️ Error Handling & Robustness

- **Graceful Degradation**: System continues with available data if some datasets fail
- **Auto-Recovery**: Retries ETL and indexing with fallback mechanisms  
- **User Feedback**: Clear error messages and guidance for resolution
- **API Resilience**: Handles OpenAI API failures with informative messages

## 🔒 Security & Privacy

- **Local Processing**: All data analysis happens locally
- **API Key Management**: Secure handling of OpenAI credentials
- **Data Isolation**: No sensitive data sent to external services beyond LLM queries
- **Report Security**: Generated reports stored locally with controlled access

---

**Built for intelligent, automated policy analysis with real-world impact.** 🚀

*For questions or support, contact the development team.*