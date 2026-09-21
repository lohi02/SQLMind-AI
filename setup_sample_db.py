import sqlite3
import os

DB_PATH = "company.db"

def create_sample_database(db_path: str = DB_PATH):
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Departments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        department_id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_name TEXT NOT NULL,
        location TEXT NOT NULL
    );
    """)
    
    departments = [
        ("Engineering", "Building A - San Francisco"),
        ("Sales", "Building B - New York"),
        ("Marketing", "Building B - New York"),
        ("Human Resources", "Building A - San Francisco"),
        ("Finance", "Building C - Chicago")
    ]
    cursor.executemany("INSERT INTO departments (department_name, location) VALUES (?, ?);", departments)
    
    # 2. Employees Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        salary REAL NOT NULL,
        hire_date DATE NOT NULL,
        department_id INTEGER,
        FOREIGN KEY (department_id) REFERENCES departments(department_id)
    );
    """)
    
    employees = [
        ("Alice", "Smith", "alice@company.com", 120000.0, "2021-03-15", 1),
        ("Bob", "Johnson", "bob@company.com", 95000.0, "2020-06-01", 2),
        ("Charlie", "Brown", "charlie@company.com", 85000.0, "2022-01-10", 3),
        ("Diana", "Prince", "diana@company.com", 140000.0, "2019-11-20", 1),
        ("Evan", "Wright", "evan@company.com", 78000.0, "2023-04-05", 4),
        ("Fiona", "Gallagher", "fiona@company.com", 110000.0, "2021-08-12", 5),
        ("George", "Clark", "george@company.com", 102000.0, "2020-09-18", 2),
        ("Hannah", "Abbott", "hannah@company.com", 88000.0, "2022-05-30", 3)
    ]
    cursor.executemany("""
    INSERT INTO employees (first_name, last_name, email, salary, hire_date, department_id)
    VALUES (?, ?, ?, ?, ?, ?);
    """, employees)
    
    # 3. Sales Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        product_name TEXT NOT NULL,
        amount REAL NOT NULL,
        sale_date DATE NOT NULL,
        region TEXT NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    );
    """)
    
    sales = [
        (2, "Enterprise Software License", 25000.0, "2024-01-15", "North"),
        (2, "Cloud Migration Package", 45000.0, "2024-02-10", "North"),
        (7, "Consulting Package A", 15000.0, "2024-01-20", "East"),
        (7, "Enterprise Software License", 25000.0, "2024-03-05", "South"),
        (2, "Support Contract Annual", 12000.0, "2024-03-12", "North"),
        (7, "Cloud Migration Package", 50000.0, "2024-04-01", "West")
    ]
    cursor.executemany("""
    INSERT INTO sales (employee_id, product_name, amount, sale_date, region)
    VALUES (?, ?, ?, ?, ?);
    """, sales)
    
    conn.commit()
    conn.close()
    print(f"Sample SQLite database successfully created at '{db_path}'.")

if __name__ == "__main__":
    create_sample_database()
