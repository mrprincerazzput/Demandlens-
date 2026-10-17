
import sqlite3
import csv
import io
import os
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, make_response, flash, abort, session
)
from werkzeug.security import (
    generate_password_hash, check_password_hash
)

app = Flask(__name__)

# Local development key. Change this before deployment.
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "demandlens-local-development-key-change-before-deployment"
)


# DATABASE CONNECTION
def get_db_connection():
    conn = sqlite3.connect("demandlens.db")
    conn.row_factory = sqlite3.Row
    return conn


# CREATE USER TABLE WITHOUT DELETING EXISTING DATA
def create_user_table():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS "user" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)

    conn.commit()
    conn.close()


create_user_table()


# REQUIRE LOGIN FOR PROTECTED PAGES
def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))

        return route_function(*args, **kwargs)

    return wrapper


# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        try:
            conn.execute(
                """
                INSERT INTO "user" (name, email, password, role)
                VALUES (?, ?, ?, ?)
                """,
                (name, email, hashed_password, "user")
            )
            conn.commit()

        except sqlite3.IntegrityError:
            flash("This email is already registered.", "error")
            conn.close()
            return render_template("register.html")

        conn.close()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()

        user = conn.execute(
            'SELECT * FROM "user" WHERE email = ?',
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_role"] = user["role"]

            return redirect(url_for("home"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


# LOGOUT
@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have logged out successfully.", "success")
    return redirect(url_for("login"))


# HOME DASHBOARD
@app.route("/")
@login_required
def home():
    conn = get_db_connection()

    products = conn.execute(
        "SELECT * FROM products ORDER BY units_sold DESC"
    ).fetchall()

    total_products = len(products)

    total_units = sum(
        p["units_sold"] or 0 for p in products
    )

    total_revenue = sum(
        (p["price"] or 0) * (p["units_sold"] or 0)
        for p in products
    )

    high_demand = sum(
        1 for p in products
        if (p["units_sold"] or 0) >= 250
    )

    conn.close()

    return render_template(
        "index.html",
        products=products,
        total_products=total_products,
        total_units=total_units,
        total_revenue=total_revenue,
        high_demand=high_demand
    )


# PRODUCT MANAGEMENT PAGE
@app.route("/products")
@login_required
def products_page():
    conn = get_db_connection()

    products = conn.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template("products.html", products=products)


# ADD PRODUCT
@app.route("/products/add", methods=["POST"])
@login_required
def add_product():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()

    try:
        price = float(request.form.get("price", ""))
        units_sold = int(request.form.get("units_sold", ""))
    except (ValueError, TypeError):
        flash("Please enter valid price and units sold.", "error")
        return redirect(url_for("products_page"))

    if not name or not category or price < 0 or units_sold < 0:
        flash("Enter valid product details.", "error")
        return redirect(url_for("products_page"))

    conn = get_db_connection()

    conn.execute(
        """
        INSERT INTO products (name, category, price, units_sold)
        VALUES (?, ?, ?, ?)
        """,
        (name, category, price, units_sold)
    )

    conn.commit()
    conn.close()

    flash("Product added successfully!", "success")
    return redirect(url_for("products_page"))


# EDIT PRODUCT
@app.route(
    "/products/edit/<int:product_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_product(product_id):
    conn = get_db_connection()

    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if product is None:
        conn.close()
        abort(404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()

        try:
            price = float(request.form.get("price", ""))
            units_sold = int(request.form.get("units_sold", ""))
        except (ValueError, TypeError):
            conn.close()
            flash("Please enter valid price and units sold.", "error")
            return redirect(
                url_for("edit_product", product_id=product_id)
            )

        if not name or not category or price < 0 or units_sold < 0:
            conn.close()
            flash("Enter valid product details.", "error")
            return redirect(
                url_for("edit_product", product_id=product_id)
            )

        conn.execute(
            """
            UPDATE products
            SET name = ?, category = ?, price = ?, units_sold = ?
            WHERE id = ?
            """,
            (name, category, price, units_sold, product_id)
        )

        conn.commit()
        conn.close()

        flash("Product updated successfully!", "success")
        return redirect(url_for("products_page"))

    conn.close()

    return render_template(
        "edit_product.html",
        product=product
    )


# DELETE PRODUCT
@app.route("/products/delete/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    conn = get_db_connection()

    conn.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )

    conn.commit()
    conn.close()

    flash("Product deleted successfully.", "success")
    return redirect(url_for("products_page"))


# EXPORT CSV REPORT
@app.route("/export")
@login_required
def export_csv():
    conn = get_db_connection()

    products = conn.execute(
        "SELECT * FROM products"
    ).fetchall()

    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Product Name",
        "Category",
        "Price",
        "Units Sold",
        "Estimated Revenue"
    ])

    for product in products:
        price = product["price"] or 0
        units = product["units_sold"] or 0

        writer.writerow([
            product["name"],
            product["category"],
            price,
            units,
            price * units
        ])

    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Disposition"] = (
        "attachment; filename=demandlens_sales_report.csv"
    )
    response.headers["Content-Type"] = "text/csv; charset=utf-8"

    return response


# BACKEND HEALTH CHECK
@app.route("/health")
def health():
    return {
        "status": "success",
        "message": "DemandLens backend is running!"
    }


if __name__ == "__main__":
    app.run(debug=True)
