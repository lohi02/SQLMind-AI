import unittest
import os
import sys

# Ensure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import DatabaseManager
from src.validator import SQLValidator
from src.generator import SQLGenerator
from setup_sample_db import create_sample_database

class TestTextToSQL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = "test_company.db"
        create_sample_database(cls.db_path)
        cls.db_manager = DatabaseManager(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def test_schema_extraction(self):
        schema = self.db_manager.extract_schema(include_sample_rows=True)
        self.assertIn("Table: employees", schema)
        self.assertIn("Table: departments", schema)
        self.assertIn("Table: sales", schema)
        self.assertIn("PRIMARY KEY", schema)

    def test_sql_validator_safe_queries(self):
        safe_queries = [
            "SELECT * FROM employees;",
            "SELECT e.first_name, d.department_name FROM employees e JOIN departments d ON e.department_id = d.department_id",
            "WITH regional_sales AS (SELECT region, SUM(amount) as total FROM sales GROUP BY region) SELECT * FROM regional_sales;"
        ]
        for query in safe_queries:
            is_safe, reason = SQLValidator.is_safe_query(query)
            self.assertTrue(is_safe, f"Query should be safe but failed: {reason}")

    def test_sql_validator_unsafe_queries(self):
        unsafe_queries = [
            "DROP TABLE employees;",
            "DELETE FROM sales WHERE sale_id = 1;",
            "UPDATE employees SET salary = 1000000;",
            "SELECT * FROM employees; DROP TABLE sales;",
            "INSERT INTO departments (department_name) VALUES ('Hacking');"
        ]
        for query in unsafe_queries:
            is_safe, reason = SQLValidator.is_safe_query(query)
            self.assertFalse(is_safe, f"Query should be unsafe but passed: {query}")

    def test_mock_sql_generator_and_execution(self):
        generator = SQLGenerator(api_key=None)
        output = generator.generate_sql("Who are the highest paid employees?", self.db_manager.extract_schema())
        self.assertIsNotNone(output.sql_query)
        self.assertTrue(output.sql_query.strip().startswith("SELECT"))
        
        # Execute generated query
        columns, rows = self.db_manager.execute_query(output.sql_query)
        self.assertTrue(len(columns) > 0)
        self.assertTrue(len(rows) > 0)

if __name__ == "__main__":
    unittest.main()
