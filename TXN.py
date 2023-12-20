from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import os
import re
import json
import logging
from logging.handlers import RotatingFileHandler

class CustomError(Exception):
    pass

app = Flask(__name__)
CORS(app)

# Configuration
API_URL = os.getenv('API_URL', 'http://localhost:5000/api/create_transaction')
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 5))

# Configure logging
handler = RotatingFileHandler('transaction_server.log', maxBytes=10000, backupCount=3)
logging_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(logging_format)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Security headers
@app.after_request
def apply_security_headers(response):
    #response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers.pop('Server', None)  # Remove the Server header
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/issue_transaction', methods=['POST'])
def issue_transaction():
    try:
        card_number = request.form.get('card_number')
        cardholder_name = request.form.get('cardholder_name')
        expiry_date = request.form.get('expiry_date')
        cvv = request.form.get('cvv')
        amount = request.form.get('amount')

        validate_card_info(card_number, expiry_date, cvv)

        data = {
            "card_number": card_number,
            "cardholder_name": cardholder_name,
            "expiry_date": expiry_date,
            "cvv": cvv,
            "amount": amount
        }

        response = requests.post(API_URL, json=data, headers={'Content-Type': 'application/json'}, timeout=REQUEST_TIMEOUT)

        if response.status_code == 201:
            app.logger.info('Transaction issued successfully')
            return jsonify({'message': 'Transaction issued successfully'})
        else:
            error_detail = response.text if response.text else "No detailed error message provided."
            error_message = f'Failed to issue transaction: Status code {response.status_code}, Detail: {error_detail}' #Detail: {error_detail}
            app.logger.error(error_message)
            return jsonify({'error': error_message}), response.status_code

    except CustomError as e:
        app.logger.error(f'Input validation error: {str(e)},')
        return jsonify({'error': str(e)}), 400
    except requests.RequestException as e:
        error_message = f'Network error: {str(e)}'
        app.logger.error(error_message)
        return jsonify({'error': error_message}), 500
    except Exception as e:
        error_message = f'Unexpected error: {str(e)}'
        app.logger.error(error_message)
        return jsonify({'error': error_message}), 500

# Function to validate card number, expiry date, and CVV
def validate_card_info(card_number, expiry_date, cvv):
    if not re.match(r'^\d{16}$', card_number):
        raise CustomError('Invalid card number format')
    if not re.match(r'^\d{2}/\d{2}$', expiry_date):
        raise CustomError('Invalid expiry date format')
    if not re.match(r'^\d{3}$', cvv):
        raise CustomError('Invalid CVV format')

# Custom error handlers
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(CustomError)
def handle_custom_error(e):
    return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=os.getenv('FLASK_DEBUG', 'False') == 'False', port=5002)
