# 🧠 SQLMind-AI: Natural Language to SQL Assistant

**SQLMind-AI** is a modular Python AI engine that converts natural language questions into executable SQLite queries. It features dynamic schema introspection, LLM structured output parsing via Pydantic, strict read-only safety guardrails, and tabular result formatting.

---

## 🌟 Key Features

- **Dynamic Schema Introspection**: Introspects table structures, column types, primary/foreign keys, and sample data automatically.
- **Structured LLM Generation**: Uses OpenAI API with Pydantic schemas to ensure reliable, valid SQL output.
- **Read-Only Security Guardrails**: Enforces regex-based security rules blocking destructive statements (`DROP`, `DELETE`, `UPDATE`, `INSERT`, multi-query injections).
- **Interactive CLI & Command Mode**: Choose between terminal interactive mode or instant single-query execution.
- **Smart Offline Fallback**: Includes intelligent keyword heuristics for testing out-of-the-box without an API key.
- **Automated Unit Test Suite**: Includes comprehensive tests for schema extraction, validation, and generation pipeline.

---

## 📁 Project Structure

```text
SQLMind-AI/
├── .env.example                # Configuration template
├── requirements.txt            # Python dependencies
├── setup_sample_db.py          # Script to seed sample SQLite database (company.db)
├── main.py                     # Main Application Entry Point
├── src/
│   ├── database/
│   │   └── db_manager.py       # SQLite connection & schema manager
│   ├── generator/
│   │   └── sql_generator.py    # OpenAI LLM integration with Pydantic output
│   └── validator/
│       └── sql_validator.py    # Read-only SQL safety validator
└── tests/
    └── test_text_to_sql.py     # Unit test suite
```

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/SQLMind-AI.git
cd SQLMind-AI
```

### 2. Set Up Virtual Environment & Dependencies
```bash
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Seed Sample Database
```bash
python setup_sample_db.py
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optional)* Add your `OPENAI_API_KEY` to `.env` for live LLM query generation.

---

## 💻 Usage

### Interactive Terminal Mode
```bash
python main.py
```

### Single Question Execution
```bash
python main.py --question "Who are the highest paid employees?"
```

### Run Unit Tests
```bash
python -m unittest discover -s tests
```

---

## 🛡️ Security
This project enforces read-only SQL queries (`SELECT` / `WITH`). It automatically blocks destructive statements (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`) and prevents multi-statement SQL injections.

---

## 📜 License
MIT License
