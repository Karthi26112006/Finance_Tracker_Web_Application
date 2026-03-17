from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import mysql.connector
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
# Secure random key for session management
app.secret_key = os.urandom(24)

# Database configuration helper
def get_db_connection():
    db = mysql.connector.connect(
        host="localhost",
        username="root",
        password="K@rthip0" # Original password from source
    )
    cursor = db.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS project2")
    cursor.execute("USE project2")
    
    # Ensure users table exists for authentication
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL
        )
    """)
    db.commit()
    return db, cursor

# Authentication Decorator Equivalent Check
def check_auth():
    return 'user_id' in session

@app.route('/')
def index():
    if not check_auth():
        return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not password:
            flash('Username and Password are required!', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))

        try:
            db, cursor = get_db_connection()
            # Check if user exists
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                flash('Username already exists. Choose a different one.', 'error')
                return redirect(url_for('register'))

            hashed_password = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
            db.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
        finally:
            if 'db' in locals() and db.is_connected():
                cursor.close()
                db.close()
                
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            db, cursor = get_db_connection()
            cursor.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'error')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
        finally:
            if 'db' in locals() and db.is_connected():
                cursor.close()
                db.close()
                
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/load', methods=['POST'])
def load_table():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    month_year = data.get('month_year') # Expected format: MM_YYYY
    
    if not month_year or len(month_year) != 7 or '_' not in month_year:
        return jsonify({'error': 'Invalid format. Use MM_YYYY'}), 400
        
    user_id = session['user_id']
    # Create isolated table per user per month
    table_name = f"Finance_Tracker_{user_id}_{month_year}"
    
    try:
        db, cursor = get_db_connection()
        sql = f"""CREATE TABLE IF NOT EXISTS `{table_name}` (
        id INT PRIMARY KEY AUTO_INCREMENT,
        date DATE NOT NULL,
        category VARCHAR(20) NOT NULL,
        description VARCHAR(255) NOT NULL,
        amount INT NOT NULL)"""
        
        cursor.execute(sql)
        db.commit()
        
        return jsonify({
            'message': f'Table {month_year} ready',
            'table_name': table_name
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()

# Helper function to validate table ownership
def validate_table_access(table_name):
    if not check_auth():
        return False
    user_id = session['user_id']
    expected_prefix = f"Finance_Tracker_{user_id}_"
    return table_name.startswith(expected_prefix)

@app.route('/api/transactions/<table_name>', methods=['GET'])
def get_transactions(table_name):
    if not validate_table_access(table_name):
        return jsonify({'error': 'Unauthorized access to this table'}), 403

    try:
        db, cursor = get_db_connection()
        cursor.execute(f"SELECT * FROM `{table_name}` ORDER BY date DESC, id DESC")
        records = cursor.fetchall()
        
        transactions = []
        for row in records:
            transactions.append({
                'id': row[0],
                'date': str(row[1]),
                'category': row[2],
                'description': row[3],
                'amount': row[4]
            })
            
        return jsonify({'transactions': transactions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()

@app.route('/api/transactions/summary/<table_name>', methods=['GET'])
def get_summary(table_name):
    if not validate_table_access(table_name):
        return jsonify({'error': 'Unauthorized access to this table'}), 403

    try:
        db, cursor = get_db_connection()
        
        # Income
        cursor.execute(f"SELECT SUM(amount) FROM `{table_name}` WHERE amount > 0")
        res = cursor.fetchone()
        income = int(res[0]) if res[0] else 0
        
        # Expense
        cursor.execute(f"SELECT SUM(amount) FROM `{table_name}` WHERE amount < 0")
        res = cursor.fetchone()
        expense = int(res[0]) if res[0] else 0
        
        balance = income + expense
        
        return jsonify({
            'income': income,
            'expense': abs(expense),
            'balance': balance
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()

@app.route('/api/transactions/<table_name>', methods=['POST'])
def add_transaction(table_name):
    if not validate_table_access(table_name):
        return jsonify({'error': 'Unauthorized access to this table'}), 403

    data = request.json
    try:
        db, cursor = get_db_connection()
        sql = f"INSERT INTO `{table_name}` (date, category, description, amount) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (data['date'], data['category'], data['description'], int(data['amount'])))
        db.commit()
        return jsonify({'message': 'Transaction added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()

@app.route('/api/transactions/<table_name>/<int:id>', methods=['PUT'])
def update_transaction(table_name, id):
    if not validate_table_access(table_name):
        return jsonify({'error': 'Unauthorized access to this table'}), 403

    data = request.json
    try:
        db, cursor = get_db_connection()
        sql = f"UPDATE `{table_name}` SET date=%s, category=%s, description=%s, amount=%s WHERE id=%s"
        cursor.execute(sql, (data['date'], data['category'], data['description'], int(data['amount']), id))
        db.commit()
        return jsonify({'message': 'Transaction updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()

@app.route('/api/transactions/<table_name>/<int:id>', methods=['DELETE'])
def delete_transaction(table_name, id):
    if not validate_table_access(table_name):
        return jsonify({'error': 'Unauthorized access to this table'}), 403

    try:
        db, cursor = get_db_connection()
        sql = f"DELETE FROM `{table_name}` WHERE id=%s"
        cursor.execute(sql, (id,))
        db.commit()
        return jsonify({'message': 'Transaction deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
