import os
import sys
import argparse
from dotenv import load_dotenv

# Ensure stdout uses utf-8 encoding on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import DatabaseManager
from src.validator import SQLValidator
from src.generator import SQLGenerator

load_dotenv()

def run_text_to_sql_pipeline(user_question: str, db_manager: DatabaseManager, generator: SQLGenerator):
    print("\n" + "="*70)
    print(f"[?] User Question: {user_question}")
    print("="*70)

    # 1. Extract Schema
    schema_info = db_manager.extract_schema(include_sample_rows=True)

    # 2. Generate SQL from question & schema
    print("\n[*] Generating SQL query with LLM...")
    try:
        output = generator.generate_sql(user_question, schema_info)
    except Exception as err:
        print(f"[!] Generation Error: {err}")
        return

    print("\n[+] Generated SQL Query:")
    print("-" * 50)
    print(output.sql_query)
    print("-" * 50)
    print(f"Explanation: {output.explanation}")
    if output.tables_used:
        print(f"Tables Referenced: {', '.join(output.tables_used)}")

    # 3. Security Validation
    is_safe, safety_msg = SQLValidator.is_safe_query(output.sql_query)
    if not is_safe:
        print(f"\n[!] Query Security Check Failed: {safety_msg}")
        return

    print("\n[+] Security Check: Query passed read-only safety inspection.")

    # 4. Execute Query
    print("\n[*] Executing Query against SQLite Database...")
    try:
        columns, rows = db_manager.execute_query(output.sql_query)
        print("\nResults:")
        print(db_manager.format_results(columns, rows))
    except Exception as exec_err:
        print(f"[!] Execution Error: {exec_err}")
    print("="*70 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Text-to-SQL AI Assistant for SQLite Databases")
    parser.add_argument("--db", type=str, default=os.getenv("DATABASE_PATH", "company.db"), help="Path to SQLite database file")
    parser.add_argument("--question", type=str, help="Single natural language question to run")
    args = parser.parse_args()

    db_path = args.db
    if not os.path.exists(db_path):
        print(f"[!] Database '{db_path}' not found. Creating sample database 'company.db'...")
        from setup_sample_db import create_sample_database
        create_sample_database(db_path)

    db_manager = DatabaseManager(db_path)
    generator = SQLGenerator()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("[i] Note: OPENAI_API_KEY not set in .env. Running in Offline Mock Fallback mode.")
        print("    (Add your OpenAI API key to '.env' to enable live LLM generation)\n")

    if args.question:
        run_text_to_sql_pipeline(args.question, db_manager, generator)
    else:
        print("=== Text-to-SQL Assistant ===")
        print(f"Connected to Database: '{db_path}'")
        print("Type your question in natural language (or type 'exit' or 'q' to quit).\n")
        
        while True:
            try:
                question = input("SQL-AI> ").strip()
                if not question:
                    continue
                if question.lower() in ["exit", "quit", "q"]:
                    print("Goodbye!")
                    break
                run_text_to_sql_pipeline(question, db_manager, generator)
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break

if __name__ == "__main__":
    main()
