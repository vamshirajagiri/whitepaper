# Whitepaper 🤖

**AI-Powered Data Analysis Terminal for Policy Makers & Analysts**

CLI tool that combines traditional command-line operations with advanced AI multi-agent analysis for government datasets. Experience the future of data analysis with intelligent automation and natural language interaction.

## ✨ Key Features

- 🚀 **Unified CLI Experience** - Commands + Natural Language in one interface
- 🤖 **Multi-Agent AI System** - specialized AI agents working collaboratively
- 📊 **Intelligent Data Processing** - Automated ETL pipeline with quality checks
- 🔍 **Policy-Focused Analysis** - Deep insights for government decision-making
- 📈 **ASCII Visualizations** - Beautiful charts and animations in terminal
- 💬 **Natural Language Interaction** - Ask questions in plain English
- ⚡ **Warp-Style Terminal** - Smart command vs AI query detection

## 🎯 Quick Start

```bash
# Install dependencies
pip install -e .

# Set up OpenAI API key
cp .env.example .env
# Edit .env with your OpenAI API key

# Start the intelligent terminal
whitepaper
```

## 🔄 Workflow

1. **Launch**: `whitepaper` command starts the intelligent terminal
2. **Setup**: Choose to scan datasets and run ETL preprocessing
3. **Interact**: Use commands OR natural language queries seamlessly
4. **Analyze**: AI agents automatically process and analyze your data
5. **Visualize**: Get beautiful ASCII charts and policy recommendations

## 💡 Usage Examples

### Commands (Traditional CLI)

```bash
whitepaper> scan agricultural_2019_6.csv
whitepaper> etl
whitepaper> list
whitepaper> status
```

### Natural Language Queries

```bash
whitepaper> Analyze agricultural trends and provide policy recommendations
whitepaper> What are the consumption patterns in the dataset?
whitepaper> Give me insights about economic indicators
whitepaper> Show me correlations in the data
```

## Here's the demo for this project

[![asciicast](https://asciinema.org/a/7RFxJEZ2cvMhQFbs1ZNBCqVdb.svg)](https://asciinema.org/a/7RFxJEZ2cvMhQFbs1ZNBCqVdb)

demo google drive link:
https://drive.google.com/file/d/1t2tq9OKqdwhGp-2Gpg9UmmRKLtX0JNAN/view?usp=sharings

## 🏗️ Enterprise Architecture

### Elite AI Policy Analyst System

- **🏛️ Enterprise Policy Analyst** - Deterministic, hallucination-free analysis
- **🔒 Consistency Engine** - Hash-based caching for identical results
- **🛡️ Quality Assurance** - Multi-layer validation and fact-checking
- **📊 Structured Analysis** - Evidence-based policy insights
- **🎯 Cross-Sector Intelligence** - Multi-dataset correlation analysis

### Technology Stack

- **AI/ML**: LangChain, LangGraph, OpenAI GPT-4
- **Vector DB**: FAISS + ChromaDB for persistent storage
- **Data Processing**: pandas, numpy, scikit-learn
- **Terminal UI**: Rich library with live updates
- **Charts**: plotext for ASCII visualizations
- **Quality Control**: TF-IDF similarity, confidence scoring

## 📋 Available Commands

| Command             | Description                                                 |
| ------------------- | ----------------------------------------------------------- |
| `scan <files>`      | Scan datasets for quality analysis (works with raw/cleaned) |
| `etl <files>`       | Run ETL cleaning pipeline (intelligently finds files)       |
| `list` / `datasets` | Show all available datasets (raw + cleaned)                 |
| `status`            | Display system status                                       |
| `help`              | Show help information                                       |
| `exit`              | Exit the terminal                                           |

## 🎨 Natural Language Examples

- "What are the key trends in agricultural production?"
- "Analyze consumption patterns for policy recommendations"
- "Show me correlations between economic indicators"
- "What insights can you provide about this dataset?"
- "Generate a summary report for policymakers"

## 🔧 Configuration

Create a `.env` file with your OpenAI API key:

```bash
OPENAI_API_KEY=your-api-key-here
```

## 📊 Sample Datasets

The tool comes with sample government datasets:

- `agricultural_2019_6.csv` - Agricultural production data
- `consumption_detail_06_2021_general_purpose.csv` - Consumption patterns

## 🎯 Use Cases

- **Policy Makers**: Quick insights from government datasets
- **Data Analysts**: Automated ETL and analysis workflows
- **Researchers**: Natural language data exploration
- **Government Officials**: Evidence-based policy recommendations

---

**Built for the RTGS-Style AI Analyst 48hr Buildathon**
