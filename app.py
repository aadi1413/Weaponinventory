import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- DATABASE CONFIGURATION ---
# IMPORTANT: Replace these with your actual database credentials.
DB_CONFIG = {
    'user': 'root', # Use your MySQL root user or a dedicated user
    'password': 'your_secure_password', # <-- CHANGE THIS
    'host': '127.0.0.1',
    'database': 'weapon_inventory'
}

app = Flask(__name__)
# Enable CORS to allow the frontend HTML (running locally or on a different port)
# to communicate with this Flask backend.
CORS(app)

def get_db_connection():
    '''Establishes and returns a connection to the MySQL database.'''
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

# ----------------------------------------------------------------------
# ENDPOINT 1: USER LOGIN (POST)
# ----------------------------------------------------------------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database error"}), 500

    cursor = conn.cursor(dictionary=True)

    # In a real app, you would hash the POSTed password and compare it to the stored hash.
    query = "SELECT user_id, username, role FROM users WHERE username = %s AND password_hash = %s"
    # NOTE: We use the DUMMY_HASH_2 for the 'armory' user from our seed data
    cursor.execute(query, (username, 'DUMMY_HASH_2'))
    user = cursor.fetchone()

    conn.close()

    if user:
        # Return user_id to the frontend, which will be useful for logging issuances later
        return jsonify({
            "success": True,
            "message": f"Login successful for {user['username']}",
            "role": user['role'],
            "user_id": user['user_id']
        }), 200
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401


# ----------------------------------------------------------------------
# ENDPOINT 2: INVENTORY SUMMARY (GET)
# ----------------------------------------------------------------------
@app.route('/inventory_summary', methods=['GET'])
def inventory_summary():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database error"}), 500

    cursor = conn.cursor(dictionary=True)
    # Execute the analytics query from the workbench script
    query = '''
SELECT
COUNT(weapon_id) AS TotalWeapons,
SUM(CASE WHEN current_status = 'Issued' THEN 1 ELSE 0 END) AS IssuedWeapons,
SUM(CASE WHEN current_status = 'Available' THEN 1 ELSE 0 END) AS AvailableWeapons,
SUM(CASE WHEN current_status = 'Under Maintenance' THEN 1 ELSE 0 END) AS UnderMaintenanceWeapons
FROM weapons;'''
    try:
        cursor.execute(query)
        summary = cursor.fetchone()
        return jsonify(summary), 200
    except Exception as e:
        print(f"Error executing summary query: {e}")
        return jsonify({"message": "Could not retrieve inventory summary"}), 500
    finally:
        conn.close()


# ----------------------------------------------------------------------
# ENDPOINT 3: GET ALL WEAPONS (GET)
# This fetches the full, detailed list of every weapon.
# ----------------------------------------------------------------------
@app.route('/weapons', methods=['GET'])
def get_all_weapons():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database error"}), 500

    cursor = conn.cursor(dictionary=True)
    query = "SELECT weapon_id, serial_number, type, model, current_status FROM weapons ORDER BY serial_number;"

    try:
        cursor.execute(query)
        weapons_list = cursor.fetchall()
        return jsonify(weapons_list), 200
    except Exception as e:
        print(f"Error executing weapons query: {e}")
        return jsonify({"message": "Could not retrieve inventory summary"}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    # Run the server on the default port
    print("Flask App running on http://127.0.0.1:5000")
    app.run(debug=True)
