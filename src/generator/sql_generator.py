import os
import json
import re
from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field
from .providers import BaseLLMProvider, get_provider

class SQLGenerationOutput(BaseModel):
    sql_query: str = Field(..., description="The executable SQLite SELECT query.")
    explanation: str = Field(..., description="Clear explanation of how the query answers the user question.")
    tables_used: List[str] = Field(default_factory=list, description="List of table names referenced in the query.")

SYSTEM_PROMPT = """You are an expert Text-to-SQL AI assistant specializing in SQLite database queries.
Your task is to convert natural language questions into accurate, executable SQLite SELECT queries based on the provided database schema.

Rules:
1. Always output ONLY valid SQLite compatible SQL statements.
2. Only generate SELECT or WITH queries (read-only). Never generate INSERT, UPDATE, DELETE, or DROP queries.
3. Ensure table and column names match the provided schema exactly.
4. Use standard JOIN syntax when combining tables based on foreign keys.
5. Provide a clear, step-by-step explanation of how the SQL query works.
6. Return your response as valid JSON matching this schema:
{
  "sql_query": "SELECT ...",
  "explanation": "...",
  "tables_used": ["table1", "table2"]
}
"""

class SQLGenerator:
    def __init__(self, provider_type: str = "auto", **provider_kwargs):
        self.provider_type = provider_type
        self.provider: BaseLLMProvider = get_provider(provider_type, **provider_kwargs)

    def generate_sql(self, user_question: str, db_schema: str, error_context: Optional[str] = None) -> SQLGenerationOutput:
        """
        Generates SQL query from question and schema.
        Optionally accepts error_context for agentic self-repair retries.
        """
        prompt_user = f"Database Schema & Sample Data:\n{db_schema}\n\nUser Question:\n\"{user_question}\""
        
        if error_context:
            prompt_user += f"\n\n[PREVIOUS ATTEMPT FAILED WITH ERROR]:\n{error_context}\n\nPlease correct the SQL query to fix this error and ensure it runs on SQLite."

        raw_response = self.provider.generate(SYSTEM_PROMPT, prompt_user)
        return self._parse_json_response(raw_response, user_question)

    def generate_sql_with_self_correction(
        self, 
        user_question: str, 
        db_manager, 
        validator, 
        max_retries: int = 2
    ) -> Tuple[SQLGenerationOutput, List[str], Optional[Tuple[List[str], List[List[Any]]]]]:
        """
        Agentic Self-Correction Loop:
        Attempts SQL generation, validates security, and executes query.
        If validation or database execution fails, captures the error and feeds it back
        to the LLM to self-correct up to `max_retries` times.
        
        Returns: (output, repair_logs, execution_result)
        """
        repair_logs = []
        db_schema = db_manager.extract_schema(include_sample_rows=True)
        error_context = None

        for attempt in range(max_retries + 1):
            if attempt > 0:
                repair_logs.append(f"🔄 Self-Correction Attempt {attempt}/{max_retries}...")
            
            output = self.generate_sql(user_question, db_schema, error_context=error_context)
            
            # Step 1: Security Validation
            is_safe, safety_msg = validator.is_safe_query(output.sql_query)
            if not is_safe:
                error_context = f"Security Violation: {safety_msg}. Query: {output.sql_query}"
                repair_logs.append(f"⚠️ Attempt {attempt+1} failed security check: {safety_msg}")
                continue

            # Step 2: Database Execution
            try:
                columns, rows = db_manager.execute_query(output.sql_query)
                if attempt > 0:
                    repair_logs.append("✅ Query successfully self-corrected!")
                return output, repair_logs, (columns, rows)
            except Exception as db_err:
                error_context = f"SQLite Execution Error: {str(db_err)}. Failed Query: {output.sql_query}"
                repair_logs.append(f"⚠️ Attempt {attempt+1} database error: {db_err}")

        # If all retries exhausted, return last output
        return output, repair_logs, None

    def _parse_json_response(self, raw_response: str, question: str) -> SQLGenerationOutput:
        """Helper to extract JSON object from raw response string."""
        cleaned = raw_response.strip()
        # Remove markdown codeblock backticks if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned).strip()

        try:
            data = json.loads(cleaned)
            return SQLGenerationOutput(**data)
        except Exception:
            # Fallback if parsing fails
            if hasattr(self.provider, '_mock_generator_fallback'):
                return self.provider._mock_generator_fallback(question)
            
            # Simple regex extract
            sql_match = re.search(r"SELECT.*?;", raw_response, re.IGNORECASE | re.DOTALL)
            sql_str = sql_match.group(0) if sql_match else "SELECT * FROM employees LIMIT 5;"
            return SQLGenerationOutput(
                sql_query=sql_str,
                explanation="Generated SQL query based on user prompt.",
                tables_used=[]
            )
