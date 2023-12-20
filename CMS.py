from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import MetaData, or_
from random import randint
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')
db = SQLAlchemy(app)

# Initialize CORS
CORS(app)

# Initialize the Limiter
limiter = Limiter(app)
limiter.init_app(app)
#limiter.key_loader(get_remote_address)
logging.basicConfig(level=logging.ERROR)

# Bin model
class Bin(db.Model):
    __tablename__ = 'bin'
    id = db.Column(db.Integer, primary_key=True)
    bin_number = db.Column(db.String(10), unique=True, nullable=False)
    country = db.Column(db.String(50), nullable=True)
    card_vendor = db.Column(db.String(50), nullable=True)
    bin_name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    credit_card_number = db.Column(db.String(16), nullable=False)
    cards = db.relationship('Card', backref='bin', lazy=True)

# Card model
class Card(db.Model):
    __tablename__ = 'card'
    id = db.Column(db.Integer, primary_key=True) 
    card_number = db.Column(db.String(16), unique=True, nullable=False)
    expiry_month = db.Column(db.Integer, nullable=False)
    expiry_year = db.Column(db.Integer, nullable=False)
    cvv = db.Column(db.String(3), nullable=False) 
    name = db.Column(db.String(100), nullable=False)
    national_id = db.Column(db.String(14), nullable=False)
    phone_number = db.Column(db.String(11), nullable=False)
    bin_id = db.Column(db.Integer, db.ForeignKey('bin.id'), nullable=False)
    status = Column(String(10), default="Live")
    balance = db.Column(db.Float, default=0.0)
    transactions = db.relationship('Transaction', backref='card', lazy=True)
    cvv_attempts = db.Column(db.Integer, default=0)
    country = db.Column(db.String(50))
    age = db.Column(db.Integer)

# Transaction model
class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(16), db.ForeignKey('card.card_number'), nullable=False)
    cardholder_name = db.Column(db.String(255), nullable=False)
    expiry_date = db.Column(db.String(5), nullable=False)
    cvv = db.Column(db.String(3), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(10), default="Live")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Add this line
    ip_address = db.Column(db.String(15), nullable=True)

    @staticmethod
    def is_suspicious(transaction, max_cvv_attempts=3):
        with app.app_context():
            # Check for too many unsuccessful CVV attempts
            unsuccessful_cvv_attempts = Transaction.query.filter(
                Transaction.card_number == transaction.card_number,
                Transaction.status == "Failed",
                Transaction.cvv.isnot(None)
            ).count()

            if unsuccessful_cvv_attempts >= max_cvv_attempts:
                # Change the status of the card to "Dead"
                card = Card.query.filter_by(card_number=transaction.card_number).first()
                if card:
                    card.status = "Dead"
                    db.session.commit()

                return True

            return False

    @staticmethod
    def process_payment(card_number, expiry_date, cvv, amount):
        # Check card information and status
        card = Card.query.filter_by(card_number=card_number).first()

        if not card or card.expiry_date != expiry_date or card.cvv != cvv or card.status != "Live":
            # Mark the transaction as failed
            return "Failed"

        # Check if the card has sufficient balance
        if card.balance < amount:
            # Mark the transaction as failed
            return "Failed"

        # Process the payment
        card.balance -= amount
        db.session.commit()

        return "Completed"

# User model
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False, server_default='', index=True)
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    def check_password(self, password):
    	return check_password_hash(self.password_hash, password)

    def increment_login_attempts(self):
        self.login_attempts += 1
        if self.login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()

    def reset_login_attempts(self):
        self.login_attempts = 0
        self.locked_until = None
        db.session.commit()

# Luhn algorithm for generating credit card numbers
def generate_credit_card(bin_number):
    bin_digits = [int(digit) for digit in bin_number]
    # Assume the last digit is the check digit and generate the remaining digits
    digits_to_generate = 16 - len(bin_digits) - 1
    generated_digits = [randint(0, 9) for _ in range(digits_to_generate)]
    # Calculate the check digit using the Luhn algorithm
    check_digit = (10 - (sum(bin_digits + generated_digits) % 10)) % 10
    # Construct the complete credit card number
    credit_card_number = ''.join(map(str, bin_digits + generated_digits + [check_digit]))
    return credit_card_number

# Function to check if the user is logged in
def is_logged_in():
    return 'user_id' in session


@app.route('/')
def login():
    if is_logged_in():
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']
    
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', error='Invalid credentials')

@app.route('/logout', methods=['POST'])
def logout():
    # Check if the user is logged in
    if 'user_id' in session:
        # Remove the user's session data
        session.pop('user_id', None)
        # You can remove other session data as needed
        return 'Logged out successfully'
    else:
        return 'User is not logged in'

@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/bin_adding', methods=['GET', 'POST'])
def bin_adding():
    if not is_logged_in():
        return redirect(url_for('login'))

    if request.method == 'POST':
        bin_number = request.form['bin']
        country = request.form['country']
        card_vendor = request.form['card_vendor']
        bin_name = request.form['bin_name']

        # Check if the bin_number already exists
        existing_bin = Bin.query.filter_by(bin_number=bin_number).first()
        if existing_bin:
            return render_template('bin_adding.html', error='This bin already exists. Please enter a different bin.')

        # Get the current user (assuming only one user for simplicity)
        current_user = User.query.first()

        # Create a new Bin instance
        new_bin = Bin(bin_number=bin_number, country=country, card_vendor=card_vendor, bin_name=bin_name, user_id=current_user.id)
        new_bin.credit_card_number = generate_credit_card(new_bin.bin_number)

        # Add the new bin to the database
        db.session.add(new_bin)
        db.session.commit()

        # Create a new Card instance
        new_card = Card(card_number=new_bin.credit_card_number, expiry_month=randint(1, 12), expiry_year=randint(2023, 2031), cvv=f'{randint(0, 9):03}', bin_id=new_bin.id)

        # Add the new card to the database
        db.session.add(new_card)
        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('bin_adding.html')

@app.route('/track_transactions')
def track_transactions():
    if not is_logged_in():
        return redirect(url_for('login'))

    # Fetch bins and their associated cards and transactions
    bins = Bin.query.all()

    return render_template('track_transactions.html', bins=bins)

@app.route('/card_generation', methods=['GET', 'POST'])
def card_generation():
    if not is_logged_in():
        return redirect(url_for('login'))

    message = None

    if request.method == 'POST':
        bin_id = int(request.form['bin'])
        name = request.form['name']
        national_id = request.form['national_id']
        phone_number = request.form['phone_number']

        # Get the selected bin
        selected_bin = Bin.query.get(bin_id)

        # Generate a new card using the Luhn algorithm
        new_card_number = generate_credit_card(selected_bin.bin_number)

        # Generate random expiry date (month and year)
        expiry_month = randint(1, 12)  # Random month between 1 and 12
        expiry_year = randint(2023, 2030)  # Random year between 2023 and 2030

        # Generate random CVV (assuming a 3-digit CVV)
        cvv = str(randint(100, 999))

        # Create a new Card instance with random expiry date and CVV
        new_card = Card(
            card_number=new_card_number,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            cvv=cvv,
            name=name,
            national_id=national_id,
            phone_number=phone_number,
            bin_id=selected_bin.id,
            country=selected_bin.country  # Set the card's country based on the associated bin
        )

        # Add the new card to the database
        db.session.add(new_card)
        db.session.commit()

        # Set the success message
        message = "Card generated successfully!"

    # Fetch bins for the dropdown menu
    bins = Bin.query.all()

    return render_template('card_generation.html', bins=bins, message=message)

# Balance Adding route
@app.route('/balance_adding', methods=['GET', 'POST'])
def balance_adding():
    if not is_logged_in():
        return redirect(url_for('login'))

    if request.method == 'POST':
        national_id = request.form['national_id']
        card_number = request.form['card_number']
        amount = float(request.form['amount'])

        # Find the card based on national_id and card_number
        card = Card.query.filter_by(national_id=national_id, card_number=card_number).first()

        if card:
            # Update the card's balance
            card.balance += amount

            # Create a new transaction
            new_transaction = Transaction(
                card_number=card.card_number,
                cardholder_name=card.name,
                expiry_date=f"{card.expiry_month}/{card.expiry_year}",
                cvv=card.cvv,
                amount=amount,
                status="Completed"
            )

            # Add the transaction to the database
            db.session.add(new_transaction)
            db.session.commit()

            return redirect(url_for('dashboard'))
        else:
            return render_template('balance_adding.html', error='Card not found. Please check the entered information.')

    return render_template('balance_adding.html')
    
############ Custom Crafted AI Risk Calclation ###########
# Enhanced AI algorithm for risk calculation
logging.basicConfig(filename='transaction.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def calculate_transaction_risk(card, amount, cvv_attempts, transactions_in_last_second, country, card_holder_age):
    # Initialize risk score
    risk_score = 0

    # Check if CVV attempts exceed the limit and card status is "Active"
    if cvv_attempts >= 3 and card.status == "Active":
        risk_score += 12  # Very high risk for multiple incorrect CVV attempts on an active card

    # Check if the card status is "Dead" or CVV attempts exceed 1 (linked condition)
    if card.status == "Dead" or cvv_attempts > 1:
        risk_score += 5  # Moderate risk for a dead card or multiple incorrect CVV attempts

    # Check if the transaction amount is unusually large and there are more than 3 transactions in 1 second (linked condition)
    if amount > 1000 and transactions_in_last_second > 3:
        risk_score += 15  # Very high risk for a large transaction amount and exceeding maximum transactions in 1 second

    # Introduce additional conditions
    # Check if the transaction is from a high-risk country and CVV attempts exceed 2 (linked condition)
    high_risk_countries = ["Israel", "Russia"]
    if card.country in high_risk_countries and cvv_attempts > 2:
        risk_score += 12  # High risk for transactions from high-risk countries and multiple incorrect CVV attempts

    # Check if the cardholder is below 18 years old or the card is dead and the transaction amount is large (linked condition)
    if (card_holder_age < 18 or card.status == "Dead") and amount > 500:
        risk_score += 10  # High risk for transactions by underage cardholders or with a dead card and a large amount

    # Check if the transaction is flagged as suspicious by a fraud detection system
    if card.fraud_flag:
        risk_score += 20  # Very high risk for transactions flagged as suspicious by the fraud detection system

    # Log the risk score
    logging.info(f"Transaction Risk Score: {risk_score}")

    # Add more complex and overlapping conditions as needed based on specific business rules and requirements

    return risk_score
    
############   API   ##########
# API Endpoint - Create Transaction
# Inside your API endpoint where you create a new transaction
@app.route('/api/create_transaction', methods=['POST'])
def create_transaction():
    try:
        data = request.get_json()

        # Input validation
        required_fields = ['card_number', 'cardholder_name', 'expiry_date', 'cvv', 'amount']
        for field in required_fields:
            if field not in data:
                error_message = f'Missing required field: {field}'
                logging.error(error_message)
                return jsonify({'error': error_message}), 400

        card_number = data['card_number']
        cardholder_name = data['cardholder_name']
        expiry_date = data['expiry_date']
        cvv = data['cvv']
        amount = float(data['amount'])  # Convert amount to float
	
	# Retrieve 'country' and 'card_holder_age' from the database based on 'card_number'
        card = Card.query.filter_by(card_number=card_number).first()

        if card is not None:
            country = card.country
            card_holder_age = card.age
        else:
            # Handle the case when card_number is not found in the database
            error_message = f'Card not found for card_number: {card_number}'
            logging.error(error_message)
            return jsonify({'error': error_message}), 404
            
        if card is not None:
    	    card.fraud_flag = True  # Set the fraud_flag to True when needed
        
        
        card = Card.query.filter_by(card_number=card_number).first()
        if not card:
            error_message = 'Invalid Card Number'
            logging.error(error_message)
            return jsonify({'error': error_message}), 400
        
        if card.cvv != cvv:
            error_message = 'CVV Wrong Attempts +1'
            logging.error(error_message)
            # Increment CVV attempts
            card.cvv_attempts += 1
            # Check if CVV attempts exceed the limit
            if card.cvv_attempts > 3:
                card.status = "Dead"
                db.session.commit()
                error_message = 'Card blocked due to multiple invalid CVV attempts'
                # Save the updated card information
            db.session.commit()
            return jsonify({'error': error_message}), 400
        
        # Validate that the card_number is a valid card in the system
        card = Card.query.filter_by(card_number=card_number).first()
        if not card or card.cvv != cvv:
            error_message = 'Invalid card or CVV'
            logging.error(error_message)
            return jsonify({'error': error_message}), 400

        # Check if card status is "Dead"
        if card.status == "Dead":
            error_message = 'Card status is "Dead". Transaction failed.'
            logging.error(error_message)
            return jsonify({'error': error_message}), 400

        # Check if card is expired
        current_date = datetime.utcnow()
        if card.expiry_year < current_date.year or (card.expiry_year == current_date.year and card.expiry_month < current_date.month):
            error_message = 'Card is expired. Transaction failed.'
            logging.error(error_message)
            return jsonify({'error': error_message}), 400

        # Check if requested amount exceeds available balance
        if amount > float(card.balance):  # Convert card.balance to float
            error_message = 'Insufficient funds. Transaction failed.'
            logging.error(error_message)
            return jsonify({'error': error_message}), 400

        # Obtain client's IP address
        ip_address = request.remote_addr

        # Check if there are more than 3 transactions in 1 second
        transactions_in_last_second = Transaction.query.filter(
            Transaction.card_number == card_number,
            Transaction.timestamp >= (datetime.utcnow() - timedelta(seconds=1))
        ).count()

        if transactions_in_last_second > 3:
            # Change the status of the card to "Dead"
            card.status = "Dead"
            db.session.commit()
            return jsonify({'error': 'Exceeded maximum transactions in 1 second. Card status changed to "Dead".'}), 400
            
        country = card.country

        risk_score = calculate_transaction_risk(card, amount, card.cvv_attempts, transactions_in_last_second, country, card_holder_age)

        if risk_score >= 10:
             #Change the status of the card to "Dead"
            card.status = "Dead"
            db.session.commit()
            return jsonify({'error': 'High risk transaction. Card status changed to "Dead".'}), 400

        transaction = Transaction(
            card_number=card_number,
            cardholder_name=cardholder_name,
            expiry_date=expiry_date,
            cvv=cvv,
            amount=amount,
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )

        db.session.add(transaction)
        db.session.commit()

        # Check for suspicious activity
        if Transaction.is_suspicious(transaction):
            # Change the status of the card to "Dead"
            card.status = "Dead"
            db.session.commit()
            return jsonify({'error': 'Suspicious activity detected. Card status changed to "Dead".'}), 400

        # Additional conditions from my POV:
        # 1. Check if CVV entered wrong 4 times
        if card.cvv_attempts >= 3:
            # Change the status of the card to "Dead"
            card.status = "Dead"
            db.session.commit()
            return jsonify({'error': 'Exceeded maximum CVV attempts. Card status changed to "Dead".'}), 400

        # 2. Add more conditions based on your specific fraud detection criteria

        return jsonify({'message': 'Transaction created successfully'}), 201

    except Exception as e:
        # Capture the traceback information
        error_traceback = traceback.format_exc()

        # Log the exception with traceback for debugging
        error_message = f"Error creating transaction: {str(e)}\n{error_traceback}"
        logging.error(error_message)

        return jsonify({'error': 'Internal server error'}), 500

# API Endpoint - Transaction History
@app.route('/api/transaction_history', methods=['GET'])
def transaction_history():
    try:
        # Pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # Retrieve transaction history (paginate the results)
        transactions = Transaction.query.paginate(page=page, per_page=per_page, error_out=False)

        transaction_history = [{'card_number': t.card_number, 'amount': t.amount} for t in transactions.items]

        return jsonify({'transaction_history': transaction_history, 'total_pages': transactions.pages, 'current_page': transactions.page}), 200

    except Exception as e:
        # Log the exception for debugging
        app.logger.error(f"Error retrieving transaction history: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=os.getenv('FLASK_DEBUG', False))
