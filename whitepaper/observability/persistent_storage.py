# whitepaper/observability/persistent_storage.py
"""
Persistent Storage for Cross-Session Observability
Like what production AI systems use for long-term analytics
"""
import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid

class PersistentAgentStorage:
    """
    Enterprise-grade persistent storage for AI agent observability
    Stores data across sessions for long-term analytics
    """
    
    def __init__(self, storage_dir: str = "whitepaper_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # SQLite database for structured queries
        self.db_path = self.storage_dir / "agent_analytics.db"
        self.init_database()
        
        # JSON files for detailed trace data
        self.traces_dir = self.storage_dir / "traces"
        self.traces_dir.mkdir(exist_ok=True)
        
        # Logs directory for structured logs
        self.logs_dir = self.storage_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
    
    def init_database(self):
        """Initialize SQLite database with proper schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                total_queries INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                total_agents INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS traces (
                trace_id TEXT PRIMARY KEY,
                session_id TEXT,
                query TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                total_duration_ms REAL,
                total_cost REAL,
                agent_count INTEGER,
                error_count INTEGER,
                success BOOLEAN,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            );
            
            CREATE TABLE IF NOT EXISTS agent_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT,
                agent_name TEXT,
                model_name TEXT,
                start_time TIMESTAMP,
                duration_ms REAL,
                cost REAL,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                success BOOLEAN,
                error_message TEXT,
                FOREIGN KEY (trace_id) REFERENCES traces (trace_id)
            );
            
            CREATE TABLE IF NOT EXISTS daily_stats (
                date DATE PRIMARY KEY,
                total_queries INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                avg_query_time_ms REAL DEFAULT 0.0,
                success_rate REAL DEFAULT 0.0,
                top_agent TEXT,
                cost_gpt35 REAL DEFAULT 0.0,
                cost_gpt4 REAL DEFAULT 0.0
            );
            """)
    
    def create_session(self) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO sessions (session_id, start_time, total_queries, total_cost)
                VALUES (?, ?, 0, 0.0)
            """, (session_id, datetime.now()))
        
        return session_id
    
    def end_session(self, session_id: str):
        """End a session and update statistics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE sessions 
                SET end_time = ?,
                    total_queries = (
                        SELECT COUNT(*) FROM traces WHERE session_id = ?
                    ),
                    total_cost = (
                        SELECT COALESCE(SUM(total_cost), 0) FROM traces WHERE session_id = ?
                    )
                WHERE session_id = ?
            """, (datetime.now(), session_id, session_id, session_id))
    
    def store_trace(self, trace_data: Dict[str, Any], session_id: str):
        """Store a complete trace with all agent data"""
        trace_id = trace_data['trace_id']
        
        # Store main trace record
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO traces (
                    trace_id, session_id, query, start_time, end_time,
                    total_duration_ms, total_cost, agent_count, error_count, success
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trace_id, session_id, trace_data.get('query', ''),
                datetime.now(), datetime.now(),
                trace_data.get('total_duration_ms', 0),
                trace_data.get('total_cost', 0),
                trace_data.get('agent_count', 0),
                trace_data.get('error_count', 0),
                trace_data.get('error_count', 0) == 0
            ))
            
            # Store individual agent calls
            for span in trace_data.get('spans', []):
                if isinstance(span, dict) and 'span' in span:
                    span_data = span['span']
                    conn.execute("""
                        INSERT INTO agent_calls (
                            trace_id, agent_name, model_name, start_time,
                            duration_ms, cost, prompt_tokens, completion_tokens,
                            success, error_message
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        trace_id, span_data.get('agent_name', ''),
                        span_data.get('model_name', ''),
                        datetime.fromtimestamp(span_data.get('start_time', time.time())),
                        span_data.get('duration_ms', 0),
                        span_data.get('cost_estimate', 0),
                        span_data.get('prompt_tokens', 0),
                        span_data.get('completion_tokens', 0),
                        span_data.get('status') == 'ok',
                        span_data.get('error_message')
                    ))
        
        # Store detailed trace JSON
        trace_file = self.traces_dir / f"trace_{trace_id}.json"
        with open(trace_file, 'w') as f:
            json.dump(trace_data, f, indent=2)
    
    def get_cross_session_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get analytics across all sessions for the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Overall statistics
            stats = conn.execute("""
                SELECT 
                    COUNT(DISTINCT session_id) as total_sessions,
                    COUNT(*) as total_queries,
                    SUM(total_cost) as total_cost,
                    AVG(total_duration_ms) as avg_duration,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate,
                    SUM(error_count) as total_errors
                FROM traces 
                WHERE start_time > ?
            """, (cutoff_date,)).fetchone()
            
            # Agent performance
            agent_stats = conn.execute("""
                SELECT 
                    agent_name,
                    COUNT(*) as call_count,
                    AVG(duration_ms) as avg_duration,
                    SUM(cost) as total_cost,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
                FROM agent_calls
                WHERE start_time > ?
                GROUP BY agent_name
                ORDER BY call_count DESC
            """, (cutoff_date,)).fetchall()
            
            # Daily trends
            daily_trends = conn.execute("""
                SELECT 
                    DATE(start_time) as date,
                    COUNT(*) as queries,
                    SUM(total_cost) as cost,
                    AVG(total_duration_ms) as avg_duration
                FROM traces
                WHERE start_time > ?
                GROUP BY DATE(start_time)
                ORDER BY date
            """, (cutoff_date,)).fetchall()
            
            # Cost breakdown by model
            cost_breakdown = conn.execute("""
                SELECT 
                    model_name,
                    COUNT(*) as calls,
                    SUM(cost) as total_cost,
                    SUM(prompt_tokens + completion_tokens) as total_tokens
                FROM agent_calls
                WHERE start_time > ?
                GROUP BY model_name
            """, (cutoff_date,)).fetchall()
            
            return {
                'period_days': days,
                'overall_stats': dict(stats) if stats else {},
                'agent_performance': [dict(row) for row in agent_stats],
                'daily_trends': [dict(row) for row in daily_trends],
                'cost_breakdown': [dict(row) for row in cost_breakdown]
            }
    
    def get_session_list(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get list of recent sessions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            sessions = conn.execute("""
                SELECT session_id, start_time, end_time, total_queries, total_cost
                FROM sessions
                ORDER BY start_time DESC
                LIMIT ?
            """, (limit,)).fetchall()
            
            return [dict(row) for row in sessions]
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to prevent storage bloat"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with sqlite3.connect(self.db_path) as conn:
            # Delete old records
            deleted_traces = conn.execute("""
                DELETE FROM traces WHERE start_time < ?
            """, (cutoff_date,)).rowcount
            
            deleted_calls = conn.execute("""
                DELETE FROM agent_calls WHERE start_time < ?
            """, (cutoff_date,)).rowcount
            
            deleted_sessions = conn.execute("""
                DELETE FROM sessions WHERE start_time < ?
            """, (cutoff_date,)).rowcount
            
            return {
                'deleted_traces': deleted_traces,
                'deleted_calls': deleted_calls,
                'deleted_sessions': deleted_sessions
            }

# Global persistent storage instance
persistent_storage = PersistentAgentStorage()
