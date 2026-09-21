# 🧠 SQLMind-AI: Enterprise Agentic Text-to-SQL Platform

**SQLMind-AI** is a full-stack, commercial agentic Text-to-SQL platform that converts natural language questions into accurate, executable database queries. 

It features a production **FastAPI Commercial REST API**, **JWT Authentication**, **Freemium Daily Quotas**, **Stripe Subscription Monetization**, **Multi-LLM Provider Support** (OpenAI, Google Gemini, Ollama, Mock), an **Agentic Self-Correction Loop**, **Automated Plotly Data Visualization**, and an **Interactive Streamlit Web Dashboard**.

---

## 🌟 Key Features

- ⚡ **FastAPI Commercial REST API (`api_server.py`)**:
  - JWT Bearer Authentication (`/api/v1/auth/register`, `/api/v1/auth/login`)
  - Freemium Quota Enforcement (`10 free queries/day`, Unlimited for Pro)
  - Interactive OpenAPI/Swagger Docs (`http://localhost:8000/docs`)
  - Stripe Subscription Billing Integration (`/api/v1/billing/create-checkout-session` for $19/mo Pro)
- 🌐 **Interactive Streamlit Dashboard (`app.py`)**: Sleek web UI with chat interface, interactive schema browser, SQL syntax highlighting, and 1-click **CSV Download**.
- 🔌 **Multi-LLM Provider Support**:
  - **Google Gemini API** (100% Free API Key)
  - **OpenAI API** (`gpt-4o-mini`, `gpt-4o`)
  - **Ollama** (100% Free local offline execution using `llama3` / `codellama`)
  - **Smart Mock Fallback** (Instant offline testing without API keys)
- 🔄 **Agentic Self-Correction Loop**: Catches SQL execution or validation errors, feeds error messages back to the LLM, and self-repairs queries automatically.
- 📈 **Automated Visual Analytics**: Detects numeric & time-series dataset patterns and renders interactive Plotly bar, line, or pie charts automatically.
- 🛡️ **Read-Only Safety Guardrails**: Enforces regex-based security rules blocking destructive operations (`DROP`, `DELETE`, `UPDATE`, `INSERT`, multi-query injections).
- 🗄️ **Multi-Database Support (SQLAlchemy)**: Works with SQLite, PostgreSQL, and MySQL databases.

---

## 📁 Project Structure

```text
SQLMind-AI/
├── api_server.py               # FastAPI Commercial REST API Server
├── app.py                      # Streamlit Web Dashboard Entry Point
├── main.py                     # Interactive CLI Application Entry Point
├── setup_sample_db.py          # Script to seed sample SQLite database (company.db)
├── requirements.txt            # Python dependencies
├── .env.example                # Environment configuration template
├── src/
│   ├── database/
│   │   ├── db_manager.py       # SQLite connection & CSV importer
│   │   └── sqlalchemy_manager.py # Unified SQLAlchemy multi-database manager (SQLite/Postgres/MySQL)
│   ├── generator/
│   │   ├── sql_generator.py    # Generator engine with Agentic Self-Correction
│   │   └── providers.py        # Multi-provider factory (OpenAI, Gemini, Ollama, Mock)
│   ├── validator/
│   │   └── sql_validator.py    # Read-only SQL safety validator
│   └── visualization/
│       └── chart_generator.py  # Automatic Plotly chart generator
└── tests/
    └── test_text_to_sql.py     # Unit test suite (API endpoints, Auth, SQL engine)
```

---

## 🚀 Quick Start

### 1. Clone & Setup Environment
```bash
git clone https://github.com/YOUR_USERNAME/SQLMind-AI.git
cd SQLMind-AI

python -m venv .venv

# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Seed Sample Database
```bash
python setup_sample_db.py
```

### 3. Configure API Keys (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
- For **Free Google Gemini**: Set `GEMINI_API_KEY=your_gemini_key`
- For **OpenAI**: Set `OPENAI_API_KEY=your_openai_key`
- For **Stripe Billing**: Set `STRIPE_SECRET_KEY=your_stripe_key`

---

## 💻 Running the Application & Services

### ⚡ Option A: Run FastAPI Commercial REST API Server
```bash
uvicorn api_server:app --reload --port 8000
```
Open interactive Swagger API Documentation at: `http://localhost:8000/docs`

### 🌐 Option B: Streamlit Web Dashboard
```bash
streamlit run app.py
```

### 🖥️ Option C: Interactive CLI
```bash
python main.py
```

### 🧪 Option D: Run Automated Unit Tests
```bash
python -m unittest discover -s tests
```

---

## 🛡️ Security & Safety
SQLMind-AI strictly enforces read-only query execution (`SELECT` / `WITH`). Destructive operations (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`) and multi-statement SQL injection attempts are blocked.

---

## 📜 License
MIT License
