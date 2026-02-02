from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import joblib
import pandas as pd
import sqlite3
from datetime import datetime
import os
from models import init_db, create_user, verify_user, save_prediction, get_user_predictions, delete_prediction

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['DATABASE'] = 'database.db'

# Initialize database
init_db()

def predict_delays(input_data):
    """Prediction function using your trained model"""
    try:
        # Load components (update paths as needed)
        le_carrier = joblib.load('carrier_encoder.pkl')
        le_airport = joblib.load('airport_encoder.pkl')
        scaler = joblib.load('scaler.pkl')
        model = joblib.load('random_forest_model.pkl')
        
        # Preprocess
        input_df = pd.DataFrame([input_data])
        input_df['carrier_encoded'] = le_carrier.transform(input_df['carrier'])
        input_df['airport_encoded'] = le_airport.transform(input_df['airport'])
        
        features = input_df[['year', 'month', 'arr_flights', 'arr_del15', 'carrier_ct', 
                           'weather_ct', 'nas_ct', 'security_ct', 'late_aircraft_ct', 
                           'arr_cancelled', 'arr_diverted', 'carrier_encoded', 'airport_encoded']]
        
        features_scaled = scaler.transform(features)
        
        # Predict
        predictions = model.predict(features_scaled)
        
        # Format results
        targets = ['arr_delay', 'carrier_delay', 'weather_delay', 
                  'nas_delay', 'security_delay', 'late_aircraft_delay']
        
        results = {target: float(predictions[0, i]) for i, target in enumerate(targets)}
        return results
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = verify_user(username, password)
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if create_user(username, email, password):
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username already exists!', 'error')
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    predictions = get_user_predictions(session['user_id'])
    return render_template('dashboard.html', predictions=predictions)

@app.route('/delete_prediction/<int:pred_id>')
def delete_prediction_route(pred_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if delete_prediction(pred_id, session['user_id']):
        flash('Prediction deleted successfully!', 'success')
    else:
        flash('Error deleting prediction!', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/input')
def input_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('input.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        input_data = {
            'year': int(request.form['year']),
            'month': int(request.form['month']),
            'carrier': request.form['carrier'],
            'airport': request.form['airport'],
            'arr_flights': int(request.form['arr_flights']),
            'arr_del15': int(request.form['arr_del15']),
            'carrier_ct': float(request.form['carrier_ct']),
            'weather_ct': float(request.form['weather_ct']),
            'nas_ct': float(request.form['nas_ct']),
            'security_ct': float(request.form['security_ct']),
            'late_aircraft_ct': float(request.form['late_aircraft_ct']),
            'arr_cancelled': int(request.form['arr_cancelled']),
            'arr_diverted': int(request.form['arr_diverted'])
        }
        
        # Get predictions
        results = predict_delays(input_data)
        
        if results:
            # Save prediction to database
            save_prediction(session['user_id'], input_data, results)
            
            # Convert to minutes for display
            display_results = {k: v/60 for k, v in results.items()}
            return render_template('result.html', results=display_results, input_data=input_data)
        else:
            flash('Prediction failed! Please try again.', 'error')
            return redirect(url_for('input_page'))
            
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('input_page'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)