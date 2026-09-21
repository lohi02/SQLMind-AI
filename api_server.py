import os
import sys
import time
import datetime
import hashlib
import hmac
import sqlite3
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import jwt
from fastapi import FastAPI, HTTPException, Depends, Security, UploadFile, File, Form, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import DatabaseManager
from src.validator import SQLValidator
from src.generator import SQLGenerator
from src.visualization import ChartGenerator
from setup_sample_db import create_sample_database

# Configuration & Secrets
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sqlmind_super_secret_commercial_jwt_key_2026")
ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
FREE_DAILY_QUOTA = 10

# Password Hashing Helper (SHA-256 with Salt)
def hash_password(password: str) -> str:
    salt = "sqlmind_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    return hmac.compare_digest(hash_password(password), hashed_password)

# Initialize Database & Tools
DB_PATH = os.getenv("DATABASE_PATH", "company.db")
if not os.path.exists(DB_PATH):
    create_sample_database(DB_PATH)

db_manager = DatabaseManager(DB_PATH)
validator = SQLValidator()
security_bearer = HTTPBearer()

# --- SQLite Persistent User Database ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_user_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS saas_users (
        email TEXT PRIMARY KEY,
        hashed_password TEXT NOT NULL,
        tier TEXT NOT NULL DEFAULT 'FREE',
        queries_today INTEGER NOT NULL DEFAULT 0,
        last_query_date TEXT NOT NULL
    );
    """)
    # Seed default demo account if missing
    c.execute("SELECT email FROM saas_users WHERE email = 'demo@sqlmind.ai';")
    if not c.fetchone():
        c.execute("""
        INSERT INTO saas_users (email, hashed_password, tier, queries_today, last_query_date)
        VALUES (?, ?, ?, ?, ?);
        """, ("demo@sqlmind.ai", hash_password("demo1234"), "FREE", 0, str(datetime.date.today())))
    conn.commit()
    conn.close()

init_user_db()

def get_user_record(email: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT email, hashed_password, tier, queries_today, last_query_date FROM saas_users WHERE email = ?;", (email,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def create_user_record(email: str, hashed_pwd: str):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO saas_users (email, hashed_password, tier, queries_today, last_query_date)
    VALUES (?, ?, 'FREE', 0, ?);
    """, (email, hashed_pwd, str(datetime.date.today())))
    conn.commit()
    conn.close()

def update_user_quota(email: str, queries_today: int, last_query_date: str):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
    UPDATE saas_users SET queries_today = ?, last_query_date = ? WHERE email = ?;
    """, (queries_today, last_query_date, email))
    conn.commit()
    conn.close()

# --- FastAPI App Definition ---
app = FastAPI(
    title="SQLMind-AI Commercial SaaS API",
    description="Enterprise REST API for Text-to-SQL generation, Multi-LLM provider orchestration, Self-Correction, and Stripe billing integration.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware (Allows Web & Mobile Apps to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Data Models ---
class UserRegisterRequest(BaseModel):
    email: str = Field(..., example="user@example.com")
    password: str = Field(..., example="StrongPassword123!")

class UserLoginRequest(BaseModel):
    email: str = Field(..., example="user@example.com")
    password: str = Field(..., example="StrongPassword123!")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tier: str

class QueryRequest(BaseModel):
    question: str = Field(..., example="Who are the top 5 highest paid employees?")
    provider: str = Field(default="auto", example="gemini", description="Provider choice: auto, gemini, openai, ollama, mock")

class QueryResponse(BaseModel):
    sql_query: str
    explanation: str
    tables_used: List[str]
    execution_time_ms: float
    columns: List[str]
    rows: List[List[Any]]
    self_correction_logs: List[str]
    has_chart: bool

# --- Helper Security Functions ---
def create_jwt_token(email: str) -> str:
    expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {"sub": email, "exp": expiration}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> Dict[str, Any]:
    token = credentials.credentials.strip('"').strip("'").strip()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user = get_user_record(email) if email else None
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token user")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired JWT token")

def check_and_increment_quota(user: Dict[str, Any]):
    today_str = str(datetime.date.today())
    queries_today = user["queries_today"]
    
    if user["last_query_date"] != today_str:
        queries_today = 0
    
    if user["tier"] == "FREE" and queries_today >= FREE_DAILY_QUOTA:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily free quota limit reached ({FREE_DAILY_QUOTA} queries/day). Upgrade to PRO for unlimited queries!"
        )
    
    queries_today += 1
    update_user_quota(user["email"], queries_today, today_str)

# --- API Endpoints ---

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "service": "SQLMind-AI Commercial SaaS Engine",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.post("/api/v1/auth/register", response_model=TokenResponse, tags=["Authentication"])
def register(req: UserRegisterRequest):
    if get_user_record(req.email):
        raise HTTPException(status_code=400, detail="User email already registered")
    
    hashed_pwd = hash_password(req.password)
    create_user_record(req.email, hashed_pwd)
    token = create_jwt_token(req.email)
    return TokenResponse(access_token=token, tier="FREE")

@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["Authentication"])
def login(req: UserLoginRequest):
    user = get_user_record(req.email)
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_jwt_token(req.email)
    return TokenResponse(access_token=token, tier=user["tier"])

@app.get("/api/v1/user/usage", tags=["User Quota"])
def get_usage(current_user: Dict[str, Any] = Depends(get_current_user)):
    today_str = str(datetime.date.today())
    queries_today = current_user["queries_today"] if current_user["last_query_date"] == today_str else 0
    remaining = "unlimited" if current_user["tier"] == "PRO" else max(0, FREE_DAILY_QUOTA - queries_today)
    
    return {
        "email": current_user["email"],
        "tier": current_user["tier"],
        "queries_today": queries_today,
        "daily_limit": "unlimited" if current_user["tier"] == "PRO" else FREE_DAILY_QUOTA,
        "remaining_queries": remaining
    }

@app.post("/api/v1/query/generate", response_model=QueryResponse, tags=["Text-to-SQL Engine"])
def generate_sql_query(
    req: QueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # Enforce Rate Limit & Quota
    check_and_increment_quota(current_user)
    
    start_time = time.time()
    generator = SQLGenerator(provider_type=req.provider)
    
    output, repair_logs, exec_result = generator.generate_sql_with_self_correction(
        user_question=req.question,
        db_manager=db_manager,
        validator=validator,
        max_retries=2
    )
    exec_time_ms = round((time.time() - start_time) * 1000, 2)
    
    columns = exec_result[0] if exec_result else []
    rows = exec_result[1] if exec_result else []
    has_chart = ChartGenerator.create_chart(columns, rows) is not None

    return QueryResponse(
        sql_query=output.sql_query,
        explanation=output.explanation,
        tables_used=output.tables_used,
        execution_time_ms=exec_time_ms,
        columns=columns,
        rows=rows,
        self_correction_logs=repair_logs,
        has_chart=has_chart
    )

@app.post("/api/v1/dataset/upload-csv", tags=["Dataset Management"])
def upload_csv_dataset(
    table_name: str = Form(...),
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        msg = db_manager.import_csv(table_name, file.file)
        return {"status": "success", "message": msg}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV file: {str(e)}")

@app.post("/api/v1/billing/create-checkout-session", tags=["Monetization"])
def create_checkout_session(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Simulates / integrates Stripe Checkout Session for upgrading to Pro Subscription ($19/month).
    """
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if stripe_key and stripe_key != "your_stripe_secret_key_here":
        import stripe
        stripe.api_key = stripe_key
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'SQLMind-AI PRO Monthly Subscription',
                            'description': 'Unlimited AI SQL queries, custom database connections & priority support.',
                        },
                        'unit_amount': 1900,  # $19.00 USD
                        'recurring': {'interval': 'month'},
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url='https://sqlmind.ai/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='https://sqlmind.ai/cancel',
                customer_email=current_user["email"]
            )
            return {"checkout_url": session.url}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Stripe Session Creation Error: {str(e)}")
    
    # Mock Response when Stripe key is not set
    return {
        "checkout_url": f"https://checkout.stripe.com/pay/mock_session_{current_user['email'].replace('@', '_')}",
        "message": "Stripe sandbox checkout URL created. (Set STRIPE_SECRET_KEY in .env for live payments)"
    }
