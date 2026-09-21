# 🧠 SQLMind-AI: Enterprise Agentic Text-to-SQL Platform

**SQLMind-AI** is a full-stack, agentic Text-to-SQL platform that converts natural language questions into accurate, executable database queries. It features **Multi-LLM Provider Support** (OpenAI, Google Gemini, Ollama, Mock), an **Agentic Self-Correction Loop**, **Automated Plotly Data Visualization**, and an **Interactive Streamlit Web Dashboard**.

---

## 🌟 Key Features

- 🌐 **Interactive Streamlit Dashboard (`app.py`)**: Sleek web UI with chat interface, interactive schema browser, SQL syntax highlighting, and 1-click **CSV Download**.
- 🔌 **Multi-LLM Provider Support**:
  - **Google Gemini API** (100% Free API Key)
  - **OpenAI API** (`gpt-4o-mini`, `gpt-4o`)
  - **Ollama** (100% Free local offline execution using `llama3` / `codellama`)
  - **Smart Mock Fallback** (Instant offline testing without API keys)
- 🔄 **Agentic Self-Correction Loop**: Catches SQL execution or validation errors, feeds error messages back to the LLM, and self-repair queries automatically.
- 📈 **Automated Visual Analytics**: Detects numeric & time-series dataset patterns and renders interactive Plotly bar, line, or pie charts automatically.
- 🛡️ **Read-Only Safety Guardrails**: Enforces regex-based security rules blocking destructive operations (`DROP`, `DELETE`, `UPDATE`, `INSERT`, multi-query injections).
- 🗄️ **Dynamic Schema Introspection**: Introspects table structures, column types, primary/foreign keys, and sample data automatically.

---

## 📁 Project Structure

```text
SQLMind-AI/
├── app.py                      # Streamlit Web Dashboard Entry Point
├── main.py                     # Interactive CLI Application Entry Point
├── setup_sample_db.py          # Script to seed sample SQLite database (company.db)
├── requirements.txt            # Python dependencies
├── .env.example                # Environment configuration template
├── src/
│   ├── database/
│   │   └── db_manager.py       # SQLite connection & dynamic schema introspection
│   ├── generator/
│   │   ├── sql_generator.py    # Generator engine with Agentic Self-Correction
│   │   └── providers.py        # Multi-provider factory (OpenAI, Gemini, Ollama, Mock)
│   ├── validator/
│   │   └── sql_validator.py    # Read-only SQL safety validator
│   └── visualization/
│       └── chart_generator.py  # Automatic Plotly chart generator
└── tests/
    └── test_text_to_sql.py     # Unit test suite
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
- For **Ollama**: Run Ollama locally (`http://localhost:11434`)

---

## 💻 Running the Application

### 🌐 Option A: Streamlit Web Dashboard (Recommended)
```bash
streamlit run app.py
```

### 🖥️ Option B: Command Line Interface (CLI)
```bash
# Interactive CLI mode
python main.py

# Single query mode
python main.py --question "What is the total sales amount per region?" --provider auto
```

### 🧪 Option C: Run Unit Tests
```bash
python -m unittest discover -s tests
```

---

## 🛡️ Security & Safety
SQLMind-AI strictly enforces read-only query execution (`SELECT` / `WITH`). Destructive operations (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`) and multi-statement SQL injection attempts are blocked.

---

## 📜 License
MIT License
