import os
import json
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt_system: str, prompt_user: str) -> str:
        """
        Sends system and user prompt to LLM provider and returns raw response string.
        """
        pass

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        import openai
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            raise ValueError("OpenAI API Key is missing or invalid in environment.")
        self.client = openai.OpenAI(api_key=self.api_key)

    def generate(self, prompt_system: str, prompt_user: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user}
            ],
            temperature=0.0
        )
        return response.choices[0].message.content

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        target_model = model or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        if target_model in ["gemini-1.5-flash", "gemini-2.5-flash"]:
            target_model = "gemini-3.6-flash"
        self.model = target_model
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise ValueError("Google Gemini API Key is missing or invalid in environment.")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model_client = genai.GenerativeModel(self.model)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Gemini API client: {e}")

    def generate(self, prompt_system: str, prompt_user: str) -> str:
        full_prompt = f"{prompt_system}\n\nUser Request:\n{prompt_user}"
        response = self.model_client.generate_content(full_prompt)
        return response.text

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = os.getenv("OLLAMA_BASE_URL", base_url).rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", model)

    def generate(self, prompt_system: str, prompt_user: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": f"{prompt_system}\n\n{prompt_user}",
            "stream": False
        }
        try:
            res = requests.post(url, json=payload, timeout=60)
            res.raise_for_status()
            data = res.json()
            return data.get("response", "")
        except Exception as e:
            raise RuntimeError(f"Failed to communicate with local Ollama service at '{url}': {e}")

class MockProvider(BaseLLMProvider):
    """Offline heuristic provider when no external API key or server is configured."""
    def generate(self, prompt_system: str, prompt_user: str) -> str:
        q = prompt_user.lower()
        if ("how many" in q or "count" in q) and "employee" in q:
            return json.dumps({
                "sql_query": "SELECT COUNT(*) AS total_employees FROM employees;",
                "explanation": "Counts total number of employees in table.",
                "tables_used": ["employees"]
            })
        elif "sales" in q or "region" in q:
            return json.dumps({
                "sql_query": "SELECT region, SUM(amount) AS total_sales, COUNT(sale_id) AS total_orders FROM sales GROUP BY region ORDER BY total_sales DESC;",
                "explanation": "Summarizes total sales and orders per region.",
                "tables_used": ["sales"]
            })
        elif "highest" in q or "salary" in q:
            return json.dumps({
                "sql_query": "SELECT e.employee_id, e.first_name, e.last_name, e.salary, d.department_name FROM employees e JOIN departments d ON e.department_id = d.department_id ORDER BY e.salary DESC LIMIT 5;",
                "explanation": "Retrieves top 5 highest paid employees with department names.",
                "tables_used": ["employees", "departments"]
            })
        else:
            return json.dumps({
                "sql_query": "SELECT e.first_name, e.last_name, e.email, d.department_name FROM employees e LEFT JOIN departments d ON e.department_id = d.department_id LIMIT 10;",
                "explanation": "Retrieves general employee details and department names.",
                "tables_used": ["employees", "departments"]
            })

def get_provider(provider_type: str = "auto", **kwargs) -> BaseLLMProvider:
    """Provider Factory Function."""
    p_type = provider_type.lower().strip()
    
    if p_type == "openai":
        return OpenAIProvider(**kwargs)
    elif p_type == "gemini":
        return GeminiProvider(**kwargs)
    elif p_type == "ollama":
        return OllamaProvider(**kwargs)
    elif p_type == "mock":
        return MockProvider()
    elif p_type == "auto":
        # Auto-detect available keys
        if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your_openai_api_key_here":
            try: return OpenAIProvider(**kwargs)
            except Exception: pass
        if os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "your_gemini_api_key_here":
            try: return GeminiProvider(**kwargs)
            except Exception: pass
        return MockProvider()
    else:
        return MockProvider()
