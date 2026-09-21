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
from src.visualization import ChartGenerator

load_dotenv()

def run_text_to_sql_pipeline(user_question: str, db_manager: DatabaseManager, generator: SQLGenerator, validator: SQLValidator):
    print("\n" + "="*70)
    print(f"[?] User Question: {user_question}")
    print("="*70)

    print("\n[*] Generating SQL query with Agentic Self-Correction...")
    
    output, repair_logs, exec_result = generator.generate_sql_with_self_correction(
        user_question=user_question,
        db_manager=db_manager,
        validator=validator,
        max_retries=2
    )

    if repair_logs:
        print("\n[🔄 Self-Correction Log]:")
        for log in repair_logs:
            print(f"   {log}")

    print("\n[+] Generated SQL Query:")
    print("-" * 50)
    print(output.sql_query)
    print("-" * 50)
    print(f"Explanation: {output.explanation}")
    if output.tables_used:
        print(f"Tables Referenced: {', '.join(output.tables_used)}")

    # Execution & Formatting
    if exec_result:
        columns, rows = exec_result
        print("\nResults:")
        print(db_manager.format_results(columns, rows))
    else:
        print("\n[!] Query execution or validation failed after retries.")
    print("="*70 + "\n")

def main():
    parser = argparse.ArgumentParser(description="SQLMind-AI: Natural Language to SQL Assistant")
    parser.add_argument("--db", type=str, default=os.getenv("DATABASE_PATH", "company.db"), help="Path to SQLite database file")
    parser.add_argument("--question", type=str, help="Single natural language question to run")
    parser.add_argument("--provider", type=str, default="auto", choices=["auto", "mock", "openai", "gemini", "ollama"], help="LLM Provider")
    args = parser.parse_args()

    db_path = args.db
    if not os.path.exists(db_path):
        print(f"[!] Database '{db_path}' not found. Creating sample database 'company.db'...")
        from setup_sample_db import create_sample_database
        create_sample_database(db_path)

    db_manager = DatabaseManager(db_path)
    validator = SQLValidator()
    generator = SQLGenerator(provider_type=args.provider)

    if args.question:
        run_text_to_sql_pipeline(args.question, db_manager, generator, validator)
    else:
        print("=== 🧠 SQLMind-AI Assistant ===")
        print(f"Connected to Database: '{db_path}'")
        print(f"Active Provider Mode: {generator.provider_type}")
        print("Type your question in natural language (or type 'exit' or 'q' to quit).\n")
        
        while True:
            try:
                question = input("SQLMind> ").strip()
                if not question:
                    continue
                if question.lower() in ["exit", "quit", "q"]:
                    print("Goodbye!")
                    break
                run_text_to_sql_pipeline(question, db_manager, generator, validator)
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break

if __name__ == "__main__":
    main()
