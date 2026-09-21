import os
import sys
import time
import pandas as pd
import streamlit as st

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import DatabaseManager
from src.validator import SQLValidator
from src.generator import SQLGenerator
from src.visualization import ChartGenerator
from setup_sample_db import create_sample_database

# Page Config
st.set_page_config(
    page_title="SQLMind-AI | Natural Language to SQL Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #9CA3AF;
        margin-bottom: 1.5rem;
    }
    .badge-safe {
        background-color: #059669;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .badge-provider {
        background-color: #3B82F6;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Sample DB if missing
DB_PATH = os.getenv("DATABASE_PATH", "company.db")
if not os.path.exists(DB_PATH):
    create_sample_database(DB_PATH)

db_manager = DatabaseManager(DB_PATH)
validator = SQLValidator()

# --- Sidebar Configuration ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/brain--v1.png", width=64)
    st.markdown("### 🧠 SQLMind-AI Settings")
    
    provider_choice = st.selectbox(
        "Select LLM Provider",
        ["Mock (Offline Fallback)", "Google Gemini (Free API)", "OpenAI", "Ollama (Local)"],
        index=0
    )
    
    provider_type_map = {
        "Mock (Offline Fallback)": "mock",
        "Google Gemini (Free API)": "gemini",
        "OpenAI": "openai",
        "Ollama (Local)": "ollama"
    }
    selected_provider_type = provider_type_map[provider_choice]
    
    # Provider-specific API Key inputs
    if selected_provider_type == "openai":
        api_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        if api_key: os.environ["OPENAI_API_KEY"] = api_key
    elif selected_provider_type == "gemini":
        api_key = st.text_input("Google Gemini API Key (Free)", type="password", value=os.getenv("GEMINI_API_KEY", ""))
        if api_key: os.environ["GEMINI_API_KEY"] = api_key
    elif selected_provider_type == "ollama":
        ollama_url = st.text_input("Ollama Base URL", value="http://localhost:11434")
        os.environ["OLLAMA_BASE_URL"] = ollama_url

    st.markdown("---")
    st.markdown("### 🗄️ Database Schema Browser")
    
    try:
        schema_text = db_manager.extract_schema(include_sample_rows=True)
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [r[0] for r in cursor.fetchall()]
        conn.close()

        for t in tables:
            with st.expander(f"📋 Table: {t}"):
                c_conn = db_manager.get_connection()
                c_cursor = c_conn.cursor()
                c_cursor.execute(f"PRAGMA table_info('{t}');")
                cols = c_cursor.fetchall()
                for col in cols:
                    st.text(f"• {col['name']} ({col['type']}){' [PK]' if col['pk'] else ''}")
                c_conn.close()
    except Exception as e:
        st.error(f"Error loading schema: {e}")

# --- Main Layout ---
st.markdown('<div class="main-header">SQLMind-AI Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Natural Language to SQL Assistant with Agentic Self-Correction & Auto Analytics</div>', unsafe_allow_html=True)

# Quick Suggestion Buttons
st.markdown("**Try Example Questions:**")
col1, col2, col3, col4 = st.columns(4)

selected_question = None
if col1.button("🏆 Top Paid Employees"):
    selected_question = "Who are the top 5 highest paid employees and their departments?"
if col2.button("📈 Sales by Region"):
    selected_question = "What is the total sales amount and order count per region?"
if col3.button("💼 Dept Average Salary"):
    selected_question = "What is the average salary per department?"
if col4.button("📊 Products Sold"):
    selected_question = "Show total sales revenue grouped by product name"

# Chat/Query Input
user_query = st.text_input(
    "Ask a question in natural language about your data:",
    value=selected_question if selected_question else "",
    placeholder="e.g. List all employees hired after 2021 with their salary"
)

if user_query:
    st.markdown("---")
    start_time = time.time()
    
    with st.spinner("🧠 Generating SQL query & analyzing database..."):
        try:
            generator = SQLGenerator(provider_type=selected_provider_type)
            output, repair_logs, exec_result = generator.generate_sql_with_self_correction(
                user_question=user_query,
                db_manager=db_manager,
                validator=validator,
                max_retries=2
            )
            exec_time_ms = round((time.time() - start_time) * 1000, 2)
            
            # Display Status Badges
            b_col1, b_col2, b_col3 = st.columns([1, 1, 2])
            with b_col1:
                st.markdown(f'<span class="badge-provider">Provider: {provider_choice}</span>', unsafe_allow_html=True)
            with b_col2:
                st.markdown('<span class="badge-safe">✅ Read-Only Verified</span>', unsafe_allow_html=True)
            with b_col3:
                st.caption(f"⚡ Execution Time: {exec_time_ms} ms")

            # Display Repair Logs if Self-Correction occurred
            if repair_logs:
                with st.expander("🔄 Agentic Self-Correction Trace Log", expanded=True):
                    for log_msg in repair_logs:
                        st.info(log_msg)

            # --- Results Tabs ---
            tab_data, tab_chart, tab_sql = st.tabs(["📊 Query Results", "📈 Visual Analytics", "💡 Generated SQL & Logic"])
            
            with tab_data:
                if exec_result:
                    columns, rows = exec_result
                    if rows:
                        df = pd.DataFrame(rows, columns=columns)
                        st.dataframe(df, use_container_width=True)
                        
                        # Download CSV
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Results as CSV",
                            data=csv,
                            file_name="query_results.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("No records found matching your query.")
                else:
                    st.error("Failed to execute query against database.")

            with tab_chart:
                if exec_result and exec_result[1]:
                    columns, rows = exec_result
                    fig = ChartGenerator.create_chart(columns, rows)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Visual chart auto-detection: Dataset is best viewed as tabular text.")

            with tab_sql:
                st.subheader("Generated SQL Query")
                st.code(output.sql_query, language="sql")
                st.subheader("Explanation")
                st.write(output.explanation)
                if output.tables_used:
                    st.caption(f"Tables Referenced: {', '.join(output.tables_used)}")

        except Exception as err:
            st.error(f"Error during query execution: {err}")
