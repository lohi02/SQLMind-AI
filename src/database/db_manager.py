import sqlite3
import os
from typing import Dict, List, Any, Tuple
from tabulate import tabulate

class DatabaseManager:
    def __init__(self, db_path: str):
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found at path: '{db_path}'")
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        """Returns a connection to the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def extract_schema(self, include_sample_rows: bool = True) -> str:
        """
        Dynamically inspects the database and generates a detailed string
        representation of tables, columns, data types, and sample data for LLM context.
        """
        schema_info = []
        conn = self.get_connection()
        cursor = conn.cursor()

        # Fetch all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            table_str = f"Table: {table}\nColumns:"
            cursor.execute(f"PRAGMA table_info('{table}');")
            columns = cursor.fetchall()
            
            col_descriptions = []
            for col in columns:
                # col schema: (cid, name, type, notnull, dflt_value, pk)
                col_name = col['name']
                col_type = col['type']
                is_pk = " (PRIMARY KEY)" if col['pk'] else ""
                col_descriptions.append(f"  - {col_name} ({col_type}){is_pk}")
            
            table_str += "\n" + "\n".join(col_descriptions)

            # Retrieve Foreign Keys
            cursor.execute(f"PRAGMA foreign_key_list('{table}');")
            fks = cursor.fetchall()
            if fks:
                fk_str = "\nForeign Keys:"
                for fk in fks:
                    fk_str += f"\n  - {fk['from']} -> {fk['table']}({fk['to']})"
                table_str += fk_str

            # Include sample rows for contextual understanding
            if include_sample_rows:
                cursor.execute(f"SELECT * FROM '{table}' LIMIT 3;")
                sample_rows = cursor.fetchall()
                if sample_rows:
                    headers = [description[0] for description in cursor.description]
                    rows_data = [list(row) for row in sample_rows]
                    sample_table_fmt = tabulate(rows_data, headers=headers, tablefmt="simple")
                    table_str += f"\nSample Data:\n{sample_table_fmt}\n"

            schema_info.append(table_str)

        conn.close()
        return "\n\n".join(schema_info)

    def execute_query(self, query: str) -> Tuple[List[str], List[List[Any]]]:
        """
        Executes a SQL query and returns column headers and rows.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(query)
        columns = [description[0] for description in cursor.description] if cursor.description else []
        rows = [list(row) for row in cursor.fetchall()]
        
        conn.close()
        return columns, rows

    def format_results(self, columns: List[str], rows: List[List[Any]]) -> str:
        """Formats query results into a visual text table."""
        if not rows:
            return "No records found."
        return tabulate(rows, headers=columns, tablefmt="grid")
