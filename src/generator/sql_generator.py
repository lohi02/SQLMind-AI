import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
import openai

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
"""

class SQLGenerator:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if self.api_key and self.api_key != "your_openai_api_key_here":
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def generate_sql(self, user_question: str, db_schema: str) -> SQLGenerationOutput:
        """
        Translates a natural language question into SQL using OpenAI Structured Outputs (or fallback heuristics if offline).
        """
        if not self.client:
            return self._mock_generator_fallback(user_question)

        prompt_user_content = f"""Database Schema & Sample Data:
{db_schema}

User Question:
"{user_question}"

Generate the SQL query to answer the user question."""

        try:
            # Utilizing OpenAI Structured Outputs with Pydantic model
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_user_content}
                ],
                response_format=SQLGenerationOutput,
                temperature=0.0
            )
            return response.choices[0].message.parsed
        except Exception as e:
            # Gracefully handle API errors or fallback
            raise RuntimeError(f"OpenAI API Error during SQL generation: {str(e)}")

    def _mock_generator_fallback(self, question: str) -> SQLGenerationOutput:
        """
        Provides expanded offline fallback responses when API Key is not configured.
        """
        q = question.lower()

        # 1. Count / How many employees
        if ("how many" in q or "count" in q or "total number" in q) and "employee" in q:
            return SQLGenerationOutput(
                sql_query="SELECT COUNT(*) AS total_employees FROM employees;",
                explanation="Counts the total number of employee records in the employees table.",
                tables_used=["employees"]
            )

        # 2. Count / Total departments
        elif ("how many" in q or "count" in q) and "department" in q:
            return SQLGenerationOutput(
                sql_query="SELECT COUNT(*) AS total_departments FROM departments;",
                explanation="Counts the total number of department records in the departments table.",
                tables_used=["departments"]
            )

        # 3. Highest paid / Top salary
        elif "highest" in q or "top salary" in q or "max salary" in q:
            return SQLGenerationOutput(
                sql_query="""SELECT e.employee_id, e.first_name, e.last_name, e.salary, d.department_name
FROM employees e
JOIN departments d ON e.department_id = d.department_id
ORDER BY e.salary DESC
LIMIT 5;""",
                explanation="Joins employees and departments to list the top 5 highest paid employees sorted by salary descending.",
                tables_used=["employees", "departments"]
            )

        # 4. Lowest paid / Min salary
        elif "lowest" in q or "min salary" in q or "least paid" in q:
            return SQLGenerationOutput(
                sql_query="""SELECT e.employee_id, e.first_name, e.last_name, e.salary, d.department_name
FROM employees e
JOIN departments d ON e.department_id = d.department_id
ORDER BY e.salary ASC
LIMIT 5;""",
                explanation="Lists the 5 employees with the lowest salary sorted ascending.",
                tables_used=["employees", "departments"]
            )

        # 5. Average salary
        elif "average" in q or "avg" in q or "mean salary" in q:
            return SQLGenerationOutput(
                sql_query="""SELECT d.department_name, ROUND(AVG(e.salary), 2) AS average_salary
FROM employees e
JOIN departments d ON e.department_id = d.department_id
GROUP BY d.department_name
ORDER BY average_salary DESC;""",
                explanation="Calculates the average employee salary grouped by department.",
                tables_used=["employees", "departments"]
            )

        # 6. Sales / Region / Revenue
        elif "sales" in q or "region" in q or "revenue" in q:
            return SQLGenerationOutput(
                sql_query="""SELECT region, SUM(amount) AS total_sales, COUNT(sale_id) AS total_orders
FROM sales
GROUP BY region
ORDER BY total_sales DESC;""",
                explanation="Groups sales by region and calculates total revenue and order count per region.",
                tables_used=["sales"]
            )

        # 7. Products
        elif "product" in q or "item" in q:
            return SQLGenerationOutput(
                sql_query="""SELECT product_name, COUNT(*) AS units_sold, SUM(amount) AS total_revenue
FROM sales
GROUP BY product_name
ORDER BY total_revenue DESC;""",
                explanation="Groups sales by product name and aggregates total units sold and revenue.",
                tables_used=["sales"]
            )

        # 8. Department list / locations
        elif "department" in q or "location" in q or "office" in q:
            return SQLGenerationOutput(
                sql_query="""SELECT department_name, location FROM departments;""",
                explanation="Retrieves all department names along with their office locations.",
                tables_used=["departments"]
            )

        # 9. Hire date / recent hires
        elif "hire" in q or "hired" in q or "date" in q or "recent" in q:
            return SQLGenerationOutput(
                sql_query="""SELECT first_name, last_name, hire_date, salary
FROM employees
ORDER BY hire_date DESC;""",
                explanation="Lists all employees ordered by their hire date with the most recently hired first.",
                tables_used=["employees"]
            )

        # 10. Default fallback
        else:
            return SQLGenerationOutput(
                sql_query="""SELECT e.first_name, e.last_name, e.email, d.department_name, e.salary
FROM employees e
LEFT JOIN departments d ON e.department_id = d.department_id
LIMIT 10;""",
                explanation="[Offline Fallback] Retrieves basic employee information including names, emails, departments, and salaries.",
                tables_used=["employees", "departments"]
            )
