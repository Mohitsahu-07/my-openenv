import sqlite3
import os

def generate_db(task_id="easy", db_path="legacy.db"):
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    if task_id == "easy":
        # Table with messy emails and phone numbers
        c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, phone TEXT)")
        c.execute("INSERT INTO users (name, email, phone) VALUES ('Alice', 'ALICE@EXAMPLE.COM', '555-1234')")
        c.execute("INSERT INTO users (name, email, phone) VALUES ('Bob', 'bob@Example.com', '555-5678')")
        c.execute("INSERT INTO users (name, email, phone) VALUES ('Charlie', 'CHARLIE@example.COM', '555-9999')")
    
    elif task_id == "medium":
        # Table with nested JSON blob
        c.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, item TEXT, metadata TEXT)")
        c.execute("INSERT INTO orders (item, metadata) VALUES ('Laptop', '{\"payment_method\": \"credit\", \"shipping\": \"fast\"}')")
        c.execute("INSERT INTO orders (item, metadata) VALUES ('Mouse', '{\"payment_method\": \"paypal\", \"shipping\": \"slow\"}')")
    
    elif task_id == "hard":
        # Denormalized table
        c.execute("CREATE TABLE purchases (purchase_id INTEGER PRIMARY KEY, customer_name TEXT, customer_email TEXT, item TEXT, price REAL)")
        c.execute("INSERT INTO purchases (customer_name, customer_email, item, price) VALUES ('Alice', 'alice@example.com', 'Laptop', 1000.0)")
        c.execute("INSERT INTO purchases (customer_name, customer_email, item, price) VALUES ('Alice', 'alice@example.com', 'Mouse', 50.0)")
        c.execute("INSERT INTO purchases (customer_name, customer_email, item, price) VALUES ('Bob', 'bob@example.com', 'Keyboard', 75.0)")
        
    conn.commit()
    conn.close()
    return db_path

if __name__ == "__main__":
    generate_db("easy")
