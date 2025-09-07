
# Next-Generation CLI AI Agent Tool: Comprehensive Development Prompt

Hey, I need you to build (or expand) a next-generation CLI AI agent tool in Python called "whitepaper-cli" . This tool is targeted at policy makers but usable by anyone for analyzing datasets like CSV or XLS files and text,json files also. It focuses on scanning datasets, running ETL (Extract, Transform, Load) pipelines to clean them, and performing intelligent analysis via a team of AI agents. The goal is to create a seamless, conversational CLI experience where users can ask questions about data (e.g., "Why isn't the agriculture sector performing well in the last 4 months?") and get detailed, unbiased reports.

## Current Project State (What Already Exists—Integrate This)
The user has already built some core features, so incorporate and expand them without breaking existing functionality:
- **Scan Tool**: When the user runs a command like whitepaper it opens a session and there it asks to scan the datsets and run etl and provides a high-level overview. Example output (streamed in CLI):
  - "Scanning dataset1.csv: 500 rows, 10 columns. Missing values: 15% in 'revenue' column. Duplicates: 20 rows. Potential issues: High variance in 'date' column—may need formatting."
  - It uses Pandas to load and analyze.
- **ETL Pipeline**: User commands like "etl dataset1.csv" trigger cleaning: Remove duplicates, handle missing values (e.g., fill with median for numerics, mode for categoricals), normalize formats (e.g., dates to ISO). After processing, output a comprehensive summary of changes, e.g.:
  - "ETL complete on dataset1.csv: Removed 20 duplicates, filled 75 missing values with medians (e.g., 'revenue' median=5000). Warn: Dataset has low quality for policy analysis (e.g., too many outliers in 'yield'—consider external data)."
  - Even if the dataset is "waste" (poor quality), it still runs ETL but warns the user.
- **Existing AI Agents (3 Agents)**: 
  - User-Facing Agent: Handles conversation, e.g., user asks "What's happening in agriculture from 2024-01-01 to 2024-12-31?" and it triggers others.
  - Analysis Agent: Performs the core analysis (e.g., trends, stats).
  - Checker Agent: Reviews results; if unsatisfied (e.g., incomplete), reverts to analysis agent for fixes, then hands back.

Build on this by expanding to a full multi-agent architecture (now 9 agents total, including a new Query Checker Agent). Make agents intelligent: They plan tasks, understand context, and only activate when needed. Use LangGraph for orchestration to handle conditional flows, loops (for revisions), and shared state.

## Overall Project Goals and Enhancements
This is a multi-agent system where agents collaborate intelligently, "talk" to each other (visible as streaming text in CLI), and hand off tasks. Key enhancements:
- **Intelligent Query Handling**: Agents plan first. For simple queries (e.g., "What's today's date?"), the User-Facing Agent replies directly without involving others. For complex ones needing analysis/dataset eval (e.g., "Why agriculture sector underperforming last 4 months?"), forward to full team.
- **Add Query Checker Agent**: New agent to evaluate user queries and decide if analysis is needed.
- **Agent Communication**: All inter-agent responses stream in CLI as text, e.g., "[Agent 1 → Agent 9]: Query needs analysis—proceeding to plan." Use Rich library for formatting (colors, bold, italics) to make it readable.
- **UX Inspiration (Warp/Claude Code Level)**: Emulate Warp Terminal's modern CLI feel and Claude's code interpreter UX.
  - **Streaming Text**: Outputs appear progressively (e.g., via Rich Live display or print with sys.stdout.flush() for real-time).
  - **Icons/Emojis**: Use for status, e.g., ✅ for success, ⚠️ for warnings, 🔍 for searching.
  - **ASCII Charts**: Render analysis results with termplotlib or ascii_charts (e.g., bar charts for trends).
  - **Blocks/Groups**: Group outputs like Warp's "blocks" (use Rich panels/boxes for command + response groupings).
  - **Suggestions/Autocomplete**: Like Claude, suggest commands (e.g., "Try 'etl file.csv' next?") or AI-powered completions via prompt.
  - **Real-Time Feedback**: Spinners for loading (e.g., "Analyzing... ⏳"), live updates.
  - **Navigation**: Allow scrolling through chat history; use Textual for TUI if possible for more interactive feel (e.g., arrow keys to navigate blocks).
- **Exceptional Additions for Next-Gen Feel**:
  - **Voice Mode (Optional)**: If on iOS/Android, integrate simple text-to-speech for responses (use gTTS library).
  - **Real-Time Collaboration Hint**: Agents can "suggest" user inputs mid-flow (e.g., "Need clarification on location? Type 'India'").
  - **Export Reports**: Auto-save analysis as PDF/Markdown with charts.
  - **Guardrails Everywhere**: Prompts to avoid biases (e.g., no unsubstantiated negatives like "This policy is bad").
  - **Tools for Agents**: Each agent gets access to tools like web search (Tavily/Serper), code execution (for stats via Pandas/NumPy), vector DB queries.

## Detailed Agent Architecture (9 Agents Total)
Use LangGraph to model this as a graph: Nodes = Agents, Edges = Handoffs/Conditions, State = Shared dict (e.g., {'query': str, 'dataset': pd.DataFrame, 'logs': list, 'report': dict}). Agents are LLM-powered (e.g., OpenAI API). Each has a clear role, responsibilities, tools, and prompt template.

1. **User-Facing Agent (Orchestrator)**:
   - **Role**: Personal assistant; handles all user interaction in conversational CLI loop.
   - **Responsibilities**: Greet user, accept commands/queries (e.g., "scan folder/", "etl file.csv", or natural questions). Plan high-level (e.g., "This query is simple—reply directly" or "Needs analysis—forward to Query Checker"). Receive final reports and present with streaming, icons, charts. Ask clarifications (e.g., "Which region for agriculture?").
   - **Tools**: None directly; routes to others.
   - **Example Flow**: User: "What's today's date?" → Plans: "Simple query." → Replies: "September 7, 2025. ✅" (No other agents).
   - **Prompt Example**: "You are a helpful CLI assistant for data analysis. Plan the query: If simple fact, reply directly. Else, forward to Query Checker. Stream responses."

2. **Query Checker Agent** (New):
   - **Role**: Gatekeeper for queries.
   - **Responsibilities**: Evaluate if query needs analysis/dataset eval/web search. If no (e.g., greeting), hand back to User-Facing with simple response. If yes, forward to Supervisor for planning.
   - **Tools**: None.
   - **Example**: Query: "Why agriculture underperforming last 4 months?" → Checks: "Needs analysis, dataset eval, possibly web search." → Streams: "[Query Checker → Supervisor]: Forwarding for full team orchestration. 🔍"
   - **Prompt Example**: "Assess query: Simple (e.g., date)? Suggest direct reply. Complex (analysis needed)? Forward with plan."

3. **Dataset Handler Agent** (Integrates Existing Scan/ETL):
   - **Role**: Manages data ingestion and prep.
   - **Responsibilities**: Run scan on folders/files for overview. Run ETL (clean duplicates, missing values with median/mode, format). Store cleaned data in vector DB (FAISS/Chroma for semantic queries). Warn if poor quality (e.g., "Low data for policy—suggest web augment. ⚠️").
   - **Tools**: Pandas for ETL, FAISS for vector store.
   - **Example**: Triggered by Supervisor: Loads "agri.csv", cleans, streams: "[Dataset Handler → Supervisor]: Cleaned 100 rows, filled 10 missing. Stored in DB. ✅"

4. **Supervisor/Maintainer Agent**:
   - **Role**: Team manager; ensures smooth operation.
   - **Responsibilities**: Receive plans from Query Checker, assign tasks (e.g., to Dataset if needed, Web Searcher for external data). Monitor reports: Agents must report before/after tasks. If issues, loop back (e.g., "Redo analysis—missing stats").
   - **Tools**: None; uses graph conditions.
   - **Example**: "[Supervisor → Web Searcher]: Query needs external data on agriculture—search 'agriculture trends last 4 months India'."

5. **Web Searcher Agent**:
   - **Role**: Gathers external context.
   - **Responsibilities**: Search web if data missing (e.g., for "why underperforming"). Summarize results, integrate with dataset. Ask clarifications via User-Facing.
   - **Tools**: Web search API (e.g., Tavily).
   - **Example**: Searches, streams: "[Web Searcher → Analysis Team]: Found data: Drought impacted yields by 20%. Handing summary. 🌐"

6-8. **Analysis Agents (Team of 3, Expands Existing Analysis Agent)**:
   - **Role**: Collaborative analysts.
   - **Responsibilities**: Divide work: #6 (Stats: Means, trends with NumPy); #7 (Viz: ASCII charts with termplotlib); #8 (Insights: Generate explanations). Chat among themselves (e.g., "[Analysis 6 → 7]: Stats ready—yield down 15%. Need chart?"). Merge dataset + web data into report.
   - **Tools**: NumPy, Pandas, Matplotlib (for ASCII export).
   - **Example**: Output chart: 
     ```
     Agriculture Yield Trend:
     █████  (Jan: 100)
     ████   (Feb: 85)
     ███    (Mar: 70)
     ```

9. **Checker Agent (Expands Existing Checker)**:
   - **Role**: Quality assurance.
   - **Responsibilities**: Review report for completeness, accuracy, biases (e.g., fix "Policy bad" to neutral). Loop back if needed, then hand to User-Facing.
   - **Tools**: None.
   - **Example**: "[Checker → User-Facing]: Report approved—no biases. ✅"

## Tech Stack and Implementation Details
- **CLI Framework**: Use Click for commands, Rich/Textual for TUI (streaming, panels, live updates). Emulate Warp: GPU-like smoothness via efficient rendering; blocks for grouped outputs.
- **Orchestration**: LangGraph StateGraph for flows/loops.
- **LLM**: OpenAI API; prompts with roles/tools.
- **Data Handling**: Pandas for ETL/scan, FAISS for DB.
- **Streaming Comms**: Print agent messages with flush(); use Rich Live for dynamic updates.
<!-- - **Run Instructions**: "pip install langchain langgraph rich textual pandas faiss-cpu openai tavily-python". Run: "python main.py" → Enters interactive loop. -->
<!-- - **Modularity**: Files: main.py (CLI entry), agents.py (agent defs), utils.py (tools/ETL/scan), graph.py (LangGraph setup). -->
- **Error Handling**: Graceful fails with warnings; retries for API.

Generate the full code, with examples in comments. Make it exceptional: Add auto-suggestions like Claude (e.g., predict next query). Ensure it's achievable on standard hardware.

---