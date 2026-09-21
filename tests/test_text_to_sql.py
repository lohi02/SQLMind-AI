import unittest
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import DatabaseManager
from src.database.sqlalchemy_manager import SQLAlchemyManager
from src.validator import SQLValidator
from src.generator import SQLGenerator
from src.visualization import ChartGenerator
from setup_sample_db import create_sample_database
from api_server import app

class TestSQLMindAISaaS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = "test_company.db"
        create_sample_database(cls.db_path)
        cls.db_manager = DatabaseManager(cls.db_path)
        cls.validator = SQLValidator()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        try:
            if os.path.exists(cls.db_path):
                os.remove(cls.db_path)
        except Exception:
            pass

    def test_schema_extraction(self):
        schema = self.db_manager.extract_schema(include_sample_rows=True)
        self.assertIn("Table: employees", schema)
        self.assertIn("Table: departments", schema)

    def test_sqlalchemy_manager(self):
        sqla_mgr = SQLAlchemyManager(f"sqlite:///{self.db_path}")
        schema = sqla_mgr.extract_schema()
        self.assertIn("Table: employees", schema)
        cols, rows = sqla_mgr.execute_query("SELECT COUNT(*) FROM employees;")
        self.assertTrue(len(rows) > 0)

    def test_sql_validator(self):
        self.assertTrue(self.validator.is_safe_query("SELECT * FROM employees;")[0])
        self.assertFalse(self.validator.is_safe_query("DROP TABLE employees;")[0])

    def test_fastapi_auth_and_usage_endpoints(self):
        # 1. Login with demo account
        response = self.client.post("/api/v1/auth/login", json={"email": "demo@sqlmind.ai", "password": "demo1234"})
        self.assertEqual(response.status_code, 200)
        token_data = response.json()
        self.assertIn("access_token", token_data)

        # 2. Access /user/usage with Bearer token
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        usage_res = self.client.get("/api/v1/user/usage", headers=headers)
        self.assertEqual(usage_res.status_code, 200)
        self.assertEqual(usage_res.json()["email"], "demo@sqlmind.ai")

    def test_fastapi_query_generate_endpoint(self):
        # Login
        response = self.client.post("/api/v1/auth/login", json={"email": "demo@sqlmind.ai", "password": "demo1234"})
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Query
        query_payload = {"question": "Who are the highest paid employees?", "provider": "mock"}
        res = self.client.post("/api/v1/query/generate", json=query_payload, headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("sql_query", data)
        self.assertTrue(len(data["rows"]) > 0)

if __name__ == "__main__":
    unittest.main()
