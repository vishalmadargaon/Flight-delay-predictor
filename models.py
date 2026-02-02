import sqlite3
import json
from datetime import datetime
import ast

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Predictions table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            input_data TEXT NOT NULL,
            results TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_user(username, email, password):
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
            (username, email, password)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def verify_user(username, password):
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ? AND password = ?',
        (username, password)
    ).fetchone()
    conn.close()
    return user

def save_prediction(user_id, input_data, results):
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO predictions (user_id, input_data, results) VALUES (?, ?, ?)',
        (user_id, json.dumps(input_data), json.dumps(results))
    )
    conn.commit()
    conn.close()

def get_user_predictions(user_id):
    conn = get_db_connection()
    predictions = conn.execute(
        'SELECT * FROM predictions WHERE user_id = ? ORDER BY created_at DESC',
        (user_id,)
    ).fetchall()
    
    # Convert JSON strings to dictionaries
    formatted_predictions = []
    for pred in predictions:
        try:
            input_data = json.loads(pred['input_data'])
            results = json.loads(pred['results'])
            
            # Convert results from seconds to minutes
            results_minutes = {k: v/60 for k, v in results.items()}
            
            formatted_predictions.append({
                'id': pred['id'],
                'user_id': pred['user_id'],
                'input_data': input_data,
                'results': results_minutes,
                'created_at': pred['created_at']
            })
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Error parsing prediction data: {e}")
            continue
    
    conn.close()
    return formatted_predictions

def delete_prediction(pred_id, user_id):
    conn = get_db_connection()
    cursor = conn.execute(
        'DELETE FROM predictions WHERE id = ? AND user_id = ?',
        (pred_id, user_id)
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted