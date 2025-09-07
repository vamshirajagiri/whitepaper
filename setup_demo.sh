#!/bin/bash
# 🚀 Whitepaper Multi-Agent Demo Setup Script
# Ensures all dependencies are installed and system is ready for demonstration

echo "🧠 Whitepaper Multi-Agent Policy Analysis System"
echo "🚀 Demo Setup Script"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the whitepaper project root directory"
    exit 1
fi

echo "📦 Installing dependencies..."
pip install -e .

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file and add your OpenAI API key"
    echo "   OPENAI_API_KEY=your-api-key-here"
fi

# Check for datasets
if [ ! -d "cleaned-dataset" ] || [ -z "$(ls -A cleaned-dataset)" ]; then
    echo "📊 No cleaned datasets found. Running ETL on sample data..."
    python -c "
import os
from pathlib import Path
from whitepaper.etl import etl_files

# Find CSV files
csv_files = list(Path('.').glob('*.csv'))
if csv_files:
    print(f'Found {len(csv_files)} CSV files for ETL processing...')
    etl_files(csv_files)
    print('✅ ETL processing complete')
else:
    print('⚠️  No CSV files found for ETL processing')
"
fi

echo ""
echo "🎯 Demo Setup Complete!"
echo ""
echo "Available demo commands:"
echo "  python demo.py              # Quick 3-query demo"
echo "  python demo_agent_system.py # Full interactive demo with agent communication"
echo "  python -m whitepaper        # Interactive terminal mode"
echo "  whitepaper demo            # Demo command in interactive mode"
echo ""
echo "Make sure your OPENAI_API_KEY is set in the .env file!"
echo ""
echo "🚀 Ready for presentation!"
