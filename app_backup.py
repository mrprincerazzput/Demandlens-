
import sqlite3
import csv
import io

from flask import (
    Flask, render_template, request,
    redirect, url_for, make_response, flash, abort
)

app = Flask(__name__)
app.secret_key = "demandlens-development-key"


# DATABASE CONNECTION
def get_db_connection():
    conn = sqlite3.connect("demandlens.db")
    conn.row_factory = sqlite3.Row
    return conn


# HOME DASHBOARD
@app.route("/")
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
def products_page():
    conn = get_db_connection()

    products = conn.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template("products.html", products=products)


# ADD PRODUCT
@app.route("/products/add", methods=["POST"])
def add_product():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()

    try:
        price = float(request.form.get("price", ""))
        units_sold = int(request.form.get("units_sold", ""))
    except (ValueError, TypeError):
        flash("Please enter valid price and units sold.", "error")
        return redirect(url_for("products_page"))

    if (
        not name or not category
        or price < 0 or units_sold < 0
    ):
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


# EDIT PRODUCT PAGE
@app.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
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

        if (
            not name or not category
            or price < 0 or units_sold < 0
        ):
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
