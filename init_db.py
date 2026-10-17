
import sqlite3

# Connect to database (creates file automatically)
conn = sqlite3.connect("demandlens.db")

cursor = conn.cursor()

# Create products table
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    price REAL,
    units_sold INTEGER
)
""")

# Add sample products only if table is empty
cursor.execute("SELECT COUNT(*) FROM products")
count = cursor.fetchone()[0]

if count == 0:
    products = [
        ("Wireless Mouse", "Electronics", 599, 350),
        ("USB-C Cable", "Accessories", 299, 250),
        ("Notebook Pack", "Stationery", 199, 150),
        ("Keyboard", "Electronics", 899, 200),
        ("Headphones", "Electronics", 1299, 300)
    ]

    cursor.executemany("""
        INSERT INTO products (name, category, price, units_sold)
        VALUES (?, ?, ?, ?)
    """, products)

conn.commit()
conn.close()

print("Database created successfully!")
print("Sample products added successfully!")
