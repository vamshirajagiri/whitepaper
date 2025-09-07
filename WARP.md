# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is **Whitepaper** - an AI-powered data analysis CLI tool for policy makers and analysts featuring a **cost-optimized 9-Agent Hub-and-Spoke architecture**. It combines traditional command-line operations with advanced multi-agent AI analysis, real-time agent communication, and intelligent query routing.

## Installation & Setup

```bash
# Install the package in development mode
pip install -e .

# Set up environment (copy .env.example to .env if available)
export OPENAI_API_KEY="your-openai-api-key"

# Optional: Set up web search capability  
export TAVILY_API_KEY="your-tavily-api-key"

# Start the application
whitepaper
```

## Core Commands

### Package Management
```bash
# Install all dependencies
pip install -e .

# Install specific dependencies for development
pip install rich langchain-openai pandas numpy python-dotenv faiss-cpu
```

### Application Usage
```bash
# Launch the main CLI interface
whitepaper

# Run the demo multi-agent system
python launch_demo.py
# or alternatively:
python demo_agent_system.py
```

### Within the CLI Interface
```bash
# Dataset operations
scan <files>              # Scan datasets for quality analysis
etl <files>              # Run ETL cleaning pipeline  
etl --overwrite <files>  # Run ETL with overwrite mode

# Information commands
list                     # Show all available datasets
datasets                 # Alias for list
status                   # Show system status (including hub-spoke mode)
help                     # Show help information

# 9-Agent Hub-Spoke features
toggle                   # Switch between 9-Agent Hub-Spoke & Legacy systems
performance              # Show system performance metrics
agents                   # Show detailed agent status

# Special features
demo                     # Launch multi-agent demo from within CLI
exit                     # Exit the terminal
```

## Architecture Overview

### 9-Agent Hub-and-Spoke Architecture
The core innovation is a cost-optimized hub-and-spoke architecture with 9 specialized AI agents:

**Hub (Supervisor Agent)**: Central orchestrator using GPT-3.5 for efficient routing

**Spokes (8 Specialized Agents)**:
- **User-Facing Agent** (GPT-3.5): Conversation and initial query handling
- **Query Checker Agent** (GPT-3.5): Smart query validation and routing
- **Dataset Handler Agent** (GPT-3.5): Data processing and ETL management
- **Web Searcher Agent** (GPT-3.5): External context gathering
- **Analysis Stats Agent** (GPT-4): Statistical analysis and metrics
- **Analysis Viz Agent** (GPT-4): Visualization and chart generation
- **Analysis Insights Agent** (GPT-4): Strategic recommendations
- **Checker Agent** (GPT-4): Quality assurance and bias detection

**Cost Optimization**: GPT-3.5 for routing/conversation, GPT-4 for deep analysis

### Key Components

**CLI Shell** (`whitepaper/shell.py` + `whitepaper/hub_spoke_shell.py`):
- Interactive terminal interface with Rich library
- Smart command vs natural language detection
- Hub-spoke system integration with feature flags
- Real-time agent communication streaming

**Hub-Spoke System** (`whitepaper/agents/`):
- 9-Agent architecture with LangGraph orchestration
- Cost-optimized model selection (GPT-3.5/GPT-4)
- State management across all agents
- Conditional routing and workflow management

**ETL Pipeline** (`whitepaper/etl.py`):
- Hash-based caching to prevent duplicate processing
- Intelligent missing value handling
- Quality assessment and reporting

**Data Scanner** (`whitepaper/scanner.py`):
- Dataset quality analysis
- Missing value detection
- Column profiling

### Data Flow
1. User input → Query classification (command vs natural language)
2. Commands → Direct execution (scan, ETL, list, etc.)
3. Natural language → User-Facing Agent → Query Checker → Supervisor (Hub)
4. Hub routes to spokes: Dataset Handler, Web Searcher, Analysis Team
5. Analysis pipeline: Stats → Visualization → Insights → Quality Check
6. ETL → Raw datasets → Cleaned datasets (in `cleaned-dataset/`)
7. Final report → User with cost summary and agent communications

## Development Patterns

### Entry Point Structure
- Main entry: `whitepaper/__main__.py` → `cli.py` → `shell.py`
- Package configuration in `pyproject.toml` with console script: `whitepaper = "whitepaper.__main__:main"`

### Dataset Management
- Raw datasets stored in project root (`.csv`, `.xls`, `.xlsx`)
- Cleaned datasets stored in `cleaned-dataset/` directory
- Hash-based ETL caching prevents reprocessing unchanged files
- ETL supports both incremental and overwrite modes

### Agent Communication
- Agents use structured state (`MultiAgentState` TypedDict)
- Real-time inter-agent messages streamed to user console
- LangGraph handles workflow orchestration with conditional routing
- Cost tracking for GPT-3.5 vs GPT-4 usage
- Rich library provides colored, streaming output with performance metrics

### Error Handling
- Graceful degradation when AI agents fail
- Fallback to basic commands when OpenAI API unavailable
- User-friendly error messages with helpful suggestions

## Environment Requirements

### Required
- Python 3.8+
- OpenAI API key (for AI agents)

### Optional
- Tavily API key (for web search capabilities)
- FAISS (for vector database functionality)

### Key Dependencies
- `langchain` & `langchain-openai` - AI agent orchestration
- `langgraph` - Agent workflow management  
- `rich` - Terminal UI and formatting
- `pandas` & `numpy` - Data processing
- `faiss-cpu` - Vector database (optional)
- `plotext` - ASCII visualizations

## Testing & Demo

### Demo System
The project includes a comprehensive demo system (`demo_agent_system.py`) that showcases:
- Agent-to-agent communication visualization
- Query validation and rejection
- Multi-dataset analysis capabilities
- Professional policy analysis reports

### Sample Data
Includes government datasets for testing:
- `agricultural_2019_6.csv` - Agricultural production data
- `consumption_detail_06_2021_general_purpose.csv` - Consumption patterns

## Natural Language Capabilities

The system can handle complex queries like:
- "Why is the agriculture sector underperforming in the last 6 months?"
- "What are the economic trends across different sectors?"
- "Analyze consumption patterns for policy recommendations"

The Query Checker Agent intelligently routes analytical queries to the full agent pipeline while rejecting irrelevant queries professionally.
