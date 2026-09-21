import os
import re
from typing import Dict, List, Any, Tuple, Optional
from sqlalchemy import create_engine, inspect, text, MetaData, Table
from tabulate import tabulate

class SQLAlchemyManager:
    """
    Unified Database Manager supporting SQLite, PostgreSQL, MySQL, and generic SQLAlchemy URIs.
    """
    def __init__(self, connection_uri: Optional[str] = None):
        self.uri = connection_uri or os.getenv("DATABASE_URI", "sqlite:///company.db")
        # Ensure SQLite URI format
        if not ("://" in self.uri):
            self.uri = f"sqlite:///{self.uri}"
        self.engine = create_engine(self.uri)

    def extract_schema(self, include_sample_rows: bool = True) -> str:
        """
        Dynamically extracts database schema using SQLAlchemy inspector.
        """
        schema_info = []
        inspector = inspect(self.engine)
        table_names = inspector.get_table_names()

        for table in table_names:
            table_str = f"Table: {table}\nColumns:"
            columns = inspector.get_columns(table)
            pk_constraint = inspector.get_pk_constraint(table)
            pk_cols = pk_constraint.get("constrained_columns", []) if pk_constraint else []

            col_descriptions = []
            for col in columns:
                col_name = col['name']
                col_type = str(col['type'])
                is_pk = " (PRIMARY KEY)" if col_name in pk_cols else ""
                col_descriptions.append(f"  - {col_name} ({col_type}){is_pk}")

            table_str += "\n" + "\n".join(col_descriptions)

            # Foreign Keys
            fks = inspector.get_foreign_keys(table)
            if fks:
                fk_str = "\nForeign Keys:"
                for fk in fks:
                    referred_table = fk.get('referred_table')
                    constrained = fk.get('constrained_columns', [])
                    referred = fk.get('referred_columns', [])
                    if constrained and referred:
                        fk_str += f"\n  - {constrained[0]} -> {referred_table}({referred[0]})"
                table_str += fk_str

            # Sample Rows
            if include_sample_rows:
                try:
                    with self.engine.connect() as conn:
                        res = conn.execute(text(f"SELECT * FROM {table} LIMIT 3;"))
                        rows = [list(r) for r in res.fetchall()]
                        headers = list(res.keys())
                        if rows:
                            sample_fmt = tabulate(rows, headers=headers, tablefmt="simple")
                            table_str += f"\nSample Data:\n{sample_fmt}\n"
                except Exception:
                    pass

            schema_info.append(table_str)

        return "\n\n".join(schema_info)

    def execute_query(self, query: str) -> Tuple[List[str], List[List[Any]]]:
        """
        Executes a SQL query and returns columns and rows.
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            columns = list(result.keys()) if result.returns_rows else []
            rows = [list(row) for row in result.fetchall()] if result.returns_rows else []
            return columns, rows
