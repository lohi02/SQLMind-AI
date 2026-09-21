# 🤖 Text-to-SQL Assistant with SQLite & OpenAI

A modular Python-based **Text-to-SQL AI Assistant** that converts natural language questions into executable SQLite queries, automatically inspects database schema, validates queries for read-only safety, and displays formatted tabular results.

---

## 🌟 Key Features

- **Schema Introspection**: Dynamically extracts table structures, column names, data types, primary/foreign keys, and sample data for context-aware SQL generation.
- **LLM SQL Generator**: Uses OpenAI's API with Pydantic structured outputs to generate precise, valid SQLite queries.
- **Read-Only Safety Guard**: Validates queries using strict regex security rules to block non-SELECT statements (`DROP`, `DELETE`, `UPDATE`, `INSERT`, etc.).
- **Interactive CLI & Command Mode**: Run interactively or execute single query flags.
- **Offline Mock Fallback**: Runs keyword-based heuristics when no API key is provided, making it testable out-of-the-box.
- **Automated Unit Test Suite**: Comprehensive tests covering schema extraction, query validation, and generation pipeline.

---

## 📁 Project Structure

```text
text_to_sql_project/
├── .env.example                # Environment variables template
├── requirements.txt            # Project dependencies
├── setup_sample_db.py          # Script to create and seed sample SQLite database
├── main.py                     # CLI Application Entry Point
├── src/
│   ├── database/
│   │   └── db_manager.py       # SQLite connection & schema extraction manager
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
git clone https://github.com/YOUR_USERNAME/text_to_sql_project.git
cd text_to_sql_project
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

### 3. Create Sample Database
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

### Run Single Question
```bash
python main.py --question "Who are the highest paid employees?"
```

### Run Unit Tests
```bash
python -m unittest discover -s tests
```

---

## 🛡️ Security
This project enforces read-only SQL queries (`SELECT` / `WITH`). It automatically blocks destructive statements like `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, and multiple query execution via semicolons.

---

## 📜 License
MIT License
