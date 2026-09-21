import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import DatabaseManager
from src.validator import SQLValidator
from src.generator import SQLGenerator
from src.visualization import ChartGenerator
from setup_sample_db import create_sample_database

class TestSQLMindAI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = "test_company.db"
        create_sample_database(cls.db_path)
        cls.db_manager = DatabaseManager(cls.db_path)
        cls.validator = SQLValidator()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def test_schema_extraction(self):
        schema = self.db_manager.extract_schema(include_sample_rows=True)
        self.assertIn("Table: employees", schema)
        self.assertIn("Table: departments", schema)
        self.assertIn("Table: sales", schema)

    def test_sql_validator(self):
        self.assertTrue(self.validator.is_safe_query("SELECT * FROM employees;")[0])
        self.assertFalse(self.validator.is_safe_query("DROP TABLE employees;")[0])

    def test_mock_generator_with_self_correction(self):
        generator = SQLGenerator(provider_type="mock")
        output, logs, exec_res = generator.generate_sql_with_self_correction(
            user_question="Who are the highest paid employees?",
            db_manager=self.db_manager,
            validator=self.validator,
            max_retries=1
        )
        self.assertIsNotNone(output.sql_query)
        self.assertIsNotNone(exec_res)
        columns, rows = exec_res
        self.assertTrue(len(rows) > 0)

    def test_chart_generator(self):
        columns = ["region", "total_sales"]
        rows = [["North", 50000.0], ["South", 25000.0]]
        fig = ChartGenerator.create_chart(columns, rows)
        self.assertIsNotNone(fig)

if __name__ == "__main__":
    unittest.main()
