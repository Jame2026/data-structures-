from flask import Flask , render_template,request, redirect, url_for
from flask_mysqldb import MySQL
import os
from werkzeug.utils import secure_filename
from flask import Response



# create app 
app = Flask(__name__)
# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'group_three'
app.config['MYSQL_PORT'] = 3307

mysql = MySQL(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about-us")
def about():
    return render_template("about-us.html")



app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')

@app.route("/products/add-product", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        name = request.form["product_name"]
        brand = request.form["brand"]
        product_price = request.form["product_price"]
        quantity = request.form["product_quantity"]
        # add news feature
        laptop_cpu = request.form["cpu"]
        laptop_ram = request.form["ram"]
        storage = request.form["storage"]
        screen = request.form["screen"]
        battery= request.form["battery"]
        description = request.form["description"]

        image_file = request.files["image"]
        if image_file:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
        else:
            filename = None

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO laptop 
            (product_name, brand, product_price, product_quantity, cpu, ram, storage, screen, battery, description, image)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, brand, product_price, quantity, laptop_cpu, laptop_ram, storage, screen, battery, description, filename))
        mysql.connection.commit()
        cur.close()
        return redirect("/products/list-products")
    return render_template("add-product.html")

@app.route('/products/edit-product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if request.method == "GET":
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM laptop WHERE product_id = %s", (product_id,))
        data = cur.fetchone()
        cur.close()
        return render_template("edit-product.html", laptop=data)
    return redirect(url_for("list_products"))

@app.route('/products/update-product', methods=['POST'])
def update_product():
    if request.method == 'POST':
        product_id = request.form['product_id']
        name = request.form['product_name']
        brand = request.form['brand']
        price = request.form['product_price']
        quantity = request.form['product_quantity']
        laptop_cpu = request.form["cpu"]
        laptop_ram = request.form["ram"]
        storage = request.form["storage"]
        screen = request.form["screen"]
        battery = request.form["battery"]
        description = request.form["description"]

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE laptop 
            SET product_name = %s,
                brand = %s,
                product_price = %s,
                product_quantity = %s,
                cpu = %s,
                ram = %s,
                storage = %s,
                screen = %s,
                battery = %s,
                description = %s
            WHERE product_id = %s
        """, (name, brand, price, quantity, laptop_cpu, laptop_ram, storage, screen, battery, description,  product_id))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('list_products'))


@app.route('/products/delete-product/<int:product_id>', methods=['GET'])
def delete_product(product_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM laptop WHERE product_id = %s", (product_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for("list_products"))

@app.route('/laptop/<int:product_id>', methods=['GET'])
def view_product(product_id):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT product_id, product_name, brand, product_price, product_quantity, cpu, ram, storage, screen, battery, description, image FROM laptop WHERE product_id=%s",
        (product_id,)
    )
    laptop = cur.fetchone()
    cur.close()

    if laptop:
        return render_template("info.html", laptop=laptop)
    else:
        return "Product not found", 404
    

# Search and oprion model

@app.route("/products/list-products", methods=["GET"])
def list_products():
    search_query   = request.args.get("q")
    selected_brand = request.args.get("brand")
    sort_order     = request.args.get("sort", "id_desc")  

    # NEW: price range
    max_price = request.args.get("max_price", type=float)

    cur = mysql.connection.cursor()

    sql = "SELECT * FROM laptop WHERE 1=1"
    params = []

    # search filter
    if search_query:
        sql += " AND product_name LIKE %s"
        params.append("%" + search_query + "%")

    # brand filter
    if selected_brand and selected_brand != "All":
        sql += " AND brand = %s"
        params.append(selected_brand)

    # NEW: price filter
    if max_price is not None:
        sql += " AND product_price <= %s"
        params.append(max_price)

    # sort order
    if sort_order == "name_asc":
        sql += " ORDER BY product_name ASC"
    elif sort_order == "name_desc":
        sql += " ORDER BY product_name DESC"
    else:
        sql += " ORDER BY product_id DESC"  # default (latest first)

    cur.execute(sql, tuple(params))
    data = cur.fetchall()

    # get brand list
    cur.execute("SELECT DISTINCT brand FROM laptop")
    brands = [row[0] for row in cur.fetchall()]
    cur.close()

    return render_template(
        "list-students.html",
        laptop=data,
        brand=brands,
        sort_order=sort_order,
        max_price=max_price or "",
        search_query=search_query or "",
        selected_brand=selected_brand or "All"
    )



@app.route("/products/download")
def download_products():
    cur = mysql.connection.cursor()
    
    # Only get the columns you want
    cur.execute("SELECT product_id, product_name, brand, product_price, product_quantity FROM laptop")
    data = cur.fetchall()
    cur.close()

    # Create CSV in memory
    def generate():
        # Header row
        yield "Nb.Product,Name,Brand,Price,Quantity\n"
        for row in data:
            yield f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}\n"

    # Send as downloadable file
    return Response(generate(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=products.csv"})


if __name__ == "__main__":
    app.run(debug=True)
