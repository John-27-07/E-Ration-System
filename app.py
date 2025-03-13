from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime
import logging

app = Flask(__name__)
app.secret_key = '2005'

# Set up logging
logging.basicConfig(level=logging.INFO)

# Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="2005",  # Replace with your database password
        database="e_ration_system"
    )

# Update the stock automatically every minute
def update_stock():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Update the stock for items with less than 100 stock by adding 10
        cursor.execute("UPDATE ration_items SET stock = stock + 10 WHERE stock < 100")
        conn.commit()
        logging.info(f"Stock updated at {datetime.now()}")
    except mysql.connector.Error as e:
        logging.error(f"Error updating stock: {e}")
    finally:
        conn.close()

# Schedule the stock update every minute
def start_scheduler():
    scheduler = BackgroundScheduler(executors={'default': ThreadPoolExecutor(10)})
    scheduler.add_job(update_stock, 'interval', minutes=1)  # Changed to 1 minute
    scheduler.start()

    # Log the scheduled jobs to verify it's working
    logging.info(f"Scheduled jobs: {scheduler.get_jobs()}")

# Login Page (default route)
@app.route("/", methods=["GET"])
def login_page():
    if "user_id" in session:  # If already logged in, redirect to home
        return redirect(url_for("home"))
    return render_template("login_register.html")

# Home Page
@app.route("/home", methods=["GET"])
def home():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login_page"))

    user_name = session.get("user_name")
    user_id = session["user_id"]  # Get the logged-in user ID
    conn = get_db_connection()

    # Fetch the ration items from the database
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM ration_items")  # Fetch all items from ration_items table
    items = cursor.fetchall()

    # Check if the user has stock allocation for each item
    cursor.execute("""
        SELECT item_id, allocated_stock, available_stock
        FROM user_item_stock
        WHERE user_id = %s
    """, (user_id,))
    user_stock_data = cursor.fetchall()

    # Create a dictionary for faster lookup of stock information
    user_stock_map = {stock['item_id']: stock for stock in user_stock_data}

    # Default allocation for users who don't have stock
    default_allocation = {
        1: 10,  # Rice (10 kg)
        2: 5,   # Sugar (5 kg)
        3: 7,   # Wheat (7 kg)
        4: 3    # Salt (3 kg)
    }

    # Allocate stock if user doesn't have any allocated stock
    for item in items:
        if item['id'] not in user_stock_map:
            # Allocate stock to the user if not already allocated
            cursor.execute(
                "INSERT INTO user_item_stock (user_id, item_id, allocated_stock, available_stock) VALUES (%s, %s, %s, %s)",
                (user_id, item['id'], default_allocation.get(item['id'], 0), default_allocation.get(item['id'], 0))
            )
        else:
            # If stock already exists, ensure it's up-to-date (optional, depending on the scenario)
            cursor.execute(
                "UPDATE user_item_stock SET allocated_stock = %s, available_stock = %s WHERE user_id = %s AND item_id = %s",
                (user_stock_map[item['id']]['allocated_stock'], user_stock_map[item['id']]['available_stock'], user_id, item['id'])
            )

    conn.commit()
    conn.close()

    # Pass 'items' and 'user_stock_map' to the template
    return render_template("home.html", user_name=user_name, items=items, user_stock_map=user_stock_map)

# Login Functionality
@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        flash("Login successful!", "success")
        return redirect(url_for("home"))
    else:
        flash("Invalid email or password", "danger")
        return redirect(url_for("login_page"))


@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    password = generate_password_hash(request.form['password'])  # Hash the password
    total_members = int(request.form['total_members'])

    # Fetch family member details from form
    family_names = request.form.getlist('family_names[]')
    family_ages = request.form.getlist('family_ages[]')
    family_genders = request.form.getlist('family_genders[]')
    family_relations = request.form.getlist('family_relations[]')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Insert user data into users table
        cursor.execute(
            "INSERT INTO users (name, email, phone, password) VALUES (%s, %s, %s, %s)",
            (name, email, phone, password)
        )
        user_id = cursor.lastrowid  # Get the last inserted user_id

        # Insert family members into family_members table
        for i in range(total_members):
            cursor.execute(
                "INSERT INTO family_members (user_id, name, age, gender, relation) VALUES (%s, %s, %s, %s, %s)",
                (user_id, family_names[i], family_ages[i], family_genders[i], family_relations[i])
            )

        # Fetch all ration items for stock allocation
        cursor.execute("SELECT id FROM ration_items")
        items = cursor.fetchall()

        # Calculate total family members (including user)
        total_family_members = total_members + 1

        # Default stock allocation per member
        base_allocation = {
            1: 5,   # Rice (5 kg per person)
            2: 1,   # Wheat (1 kg per person)
            3: 1,   # Sugar (1 kg per person)
            4: 0.5, # Oil (0.5 L per person)
            5: 1,   # Dal (1 kg per person)
            6: 1,   # Salt (1 kg per person)
            7: 0.25,   # Kerosene (5 L per person)
            8: 0.5  # Coffee Powder (0.5 kg per person)
        }

        # Allocate stock for each item based on family size
        for item in items:
            item_id = item['id']
            allocated_stock = base_allocation.get(item_id, 0) * total_family_members
            cursor.execute(
                "INSERT INTO user_item_stock (user_id, item_id, allocated_stock, available_stock) VALUES (%s, %s, %s, %s)",
                (user_id, item_id, allocated_stock, allocated_stock)
            )

        conn.commit()

        # Set session after successful registration
        session["user_id"] = user_id
        session["user_name"] = name

        flash("Registration successful. Please login.", "success")

    except mysql.connector.IntegrityError as e:
        flash(f"Error: {str(e)}", "danger")
    except mysql.connector.Error as e:
        flash(f"Database error: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("home"))
# Profile Page (Edit Profile)
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login_page"))

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch user details
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("login_page"))

        # Fetch family members
        cursor.execute("SELECT * FROM family_members WHERE user_id = %s", (user_id,))
        family_members = cursor.fetchall()

        if request.method == "POST":
            name = request.form["name"]
            email = request.form["email"]
            phone = request.form["phone"]

            # Update user details
            cursor.execute(
                "UPDATE users SET name = %s, email = %s, phone = %s WHERE id = %s",
                (name, email, phone, user_id)
            )
            conn.commit()

            # Update session data
            session["user_name"] = name

            # Fetch form data for family members
            family_ids = request.form.getlist("family_ids[]")
            family_names = request.form.getlist("family_names[]")
            family_ages = request.form.getlist("family_ages[]")
            family_genders = request.form.getlist("family_genders[]")
            family_relations = request.form.getlist("family_relations[]")

            # Update existing family members
            for i in range(len(family_ids)):
                cursor.execute(
                    "UPDATE family_members SET name = %s, age = %s, gender = %s, relation = %s WHERE id = %s AND user_id = %s",
                    (family_names[i], family_ages[i], family_genders[i], family_relations[i], family_ids[i], user_id)
                )

            conn.commit()
            flash("Profile updated successfully.", "success")
            return redirect(url_for("profile"))

    except mysql.connector.Error as e:
        flash(f"Database error: {str(e)}", "danger")
    finally:
        conn.close()

    return render_template("profile.html", user=user, family_members=family_members)

@app.route('/buy_item/<int:item_id>', methods=['POST'])
def buy_item(item_id):
    if "user_id" not in session:
        flash("Please login to make a purchase.", "warning")
        return redirect(url_for("login_page"))

    # Get the item details from the database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM ration_items WHERE id = %s", (item_id,))
    item = cursor.fetchone()

    if item is None:
        flash("Item not found.", "danger")
        return redirect(url_for("home"))

    # Get the quantity from the form
    quantity = int(request.form["quantity"])

    if quantity > item["stock"]:
        flash(f"Insufficient stock! Only {item['stock']} items available.", "danger")
        return redirect(url_for("item_details", item_id=item_id))

    # Get the user’s allocated stock from the user_item_stock table
    cursor.execute("SELECT * FROM user_item_stock WHERE user_id = %s AND item_id = %s", (session["user_id"], item_id))
    user_stock = cursor.fetchone()

    if user_stock:
        # Deduct stock from user's allocated stock if available
        if user_stock["available_stock"] >= quantity:
            new_stock = item["stock"] - quantity
            cursor.execute("UPDATE ration_items SET stock = %s WHERE id = %s", (new_stock, item_id))

            cursor.execute(
                "UPDATE user_item_stock SET available_stock = available_stock - %s WHERE user_id = %s AND item_id = %s",
                (quantity, session["user_id"], item_id)
            )
            conn.commit()

            flash(f"Purchase successful! You bought {quantity} {item['name']}(s) for ₹{quantity * item['rate']}.", "success")
        else:
            flash(f"You do not have enough allocated stock for this purchase. You have {user_stock['available_stock']} available.", "danger")
    else:
        # If the user doesn't have stock allocated yet, automatically allocate some stock
        default_allocation = 5  # For example, allocate 5 units if not already allocated
        cursor.execute(
            "INSERT INTO user_item_stock (user_id, item_id, allocated_stock, available_stock) VALUES (%s, %s, %s, %s)",
            (session["user_id"], item_id, default_allocation, default_allocation)
        )

        # After automatic allocation, deduct the purchased quantity
        new_stock = item["stock"] - quantity
        cursor.execute("UPDATE ration_items SET stock = %s WHERE id = %s", (new_stock, item_id))

        cursor.execute(
            "UPDATE user_item_stock SET available_stock = available_stock - %s WHERE user_id = %s AND item_id = %s",
            (quantity, session["user_id"], item_id)
        )

        conn.commit()

        flash(f"Purchase successful! You bought {quantity} {item['name']}(s) for ₹{quantity * item['rate']}.", "success")

    conn.close()
    return redirect(url_for("home"))


# Logout
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login_page"))

@app.route('/item/<int:item_id>')
def item_details(item_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch the item details from the database based on item_id
    cursor.execute("SELECT * FROM ration_items WHERE id = %s", (item_id,))
    item = cursor.fetchone()

    # If item not found, return 404 error
    if item is None:
        conn.close()  # Close the connection before returning
        return "Item not found", 404

    # Fetch the user's stock for this item from the user_item_stock table
    if "user_id" in session:
        cursor.execute("SELECT * FROM user_item_stock WHERE user_id = %s AND item_id = %s", (session["user_id"], item_id))
        user_item_stock = cursor.fetchone()

        if user_item_stock is None:
            flash("You have no allocated stock for this item. Please check your stock allocation.", "warning")
            user_item_stock = None  # Explicitly set to None if no stock is found
        else:
            flash(f"You have {user_item_stock['available_stock']} units available.", "info")
    else:
        flash("Please login to view your stock.", "warning")
        user_item_stock = None  # Set to None if the user is not logged in

    conn.close()  # Close the connection after using it

    # Pass the item and user_item_stock to the template
    return render_template('item_details.html', item=item, user_item_stock=user_item_stock)

if __name__ == "__main__":
    start_scheduler()  # Start the scheduler to update stock every minute
    app.run(debug=True)  # Run the Flask application in debug mode
