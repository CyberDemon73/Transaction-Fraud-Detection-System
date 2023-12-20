# Card Management and Transaction Processing System

The Card Management and Transaction Processing System integrates card management (CMS) with advanced transaction processing (TXN), focusing on real-time fraud detection. It employs sophisticated algorithms to flag unusual transaction patterns, enhancing security in financial operations. The system combines user-friendly interfaces with robust back-end technologies, including Python, Flask, and SQLite, to efficiently manage and monitor card-related services and transactions. Its standout feature is the proactive detection and mitigation of fraudulent activities, showcasing practical applications of fraud detection in digital finance.

## Table of Contents
- [Architecture](#architecture)
- [Features](#features)
  - [Card Management System (CMS)](#card-management-system-cms)
  - [Transaction Processing System (TXN)](#transaction-processing-system-txn)
- [Technologies Used](#technologies-used)
- [Setup](#setup)
- [Usage](#usage)
- [Error Handling](#error-handling)
- [Logging](#logging)
- [Security](#security)
- [Monitoring](#monitoring)
- [Key Functions](#key-functions)
  - [Card Generation](#card-generation)
  - [Risk Calculations](#risk-calculations)
  - [Fraud Detection Cases](#fraud-detection-cases)
- [Contributing](#contributing)
- [License](#license)

## Architecture
The Card Management and Transaction Processing System is designed as a client-server architecture with two main components:

### Card Management System (CMS):
- Responsible for managing cards, including card issuance, balance adding, and bin management.
- Handles user authentication and authorization.
- Provides a user-friendly web interface for administrators.

### Transaction Processing System (TXN):
- Manages real-time transaction tracking and risk assessment.
- Calculates transaction risk scores based on various factors.
- Includes fraud detection mechanisms and logs suspicious transactions.

Both components share a common database to store card and transaction data, allowing seamless integration and communication between the CMS and TXN.

## Features

### Card Management System (CMS)
- **Bin Adding**:
  - Add and manage BIN (Bank Identification Number) details.
  - Perform operations related to BIN management.
- **Card Issuing**:
  - Issue new cards to customers.
  - Configure card details such as card number, cardholder name, expiry date, and CVV.
- **Balance Adding**:
  - Add funds to existing cards.
  - Manage card balances efficiently.

### Transaction Processing System (TXN)
- **Transaction Tracking**:
  - Track card transactions in real-time.
  - Calculate transaction risk scores based on various factors.
  - Log transaction details for auditing and monitoring.

## Technologies Used
- Frontend: HTML, CSS, JavaScript
- Backend: Python with Flask framework
- Database: SQLite for data storage
- Authentication: Flask-Login for user authentication
- Logging: Python logging library

## Setup
Follow these steps to set up the Card Management and Transaction Processing System on your local machine:

```bash
# Clone the repository
git clone https://github.com/CyberDemon73/Transaction-Fraud-Detection-System.git

# Navigate to the project directory
cd cms-txn-project

# Create a virtual environment (recommended)
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS and Linux:
source venv/bin/activate

# Install project dependencies
pip install -r requirements.txt

# Initialize the database
flask db init
flask db migrate
flask db upgrade

# Start the application
flask run

#OR
python3 CMS.py

# In another window in the same directory
python3 TXN.py

```
#### Open your web browser and go to http://localhost:5000 to access the CMS (Card Management System).
#### Open your web browser and go to http://localhost:5002 to access the TXN (Transaction Server).

## Usage
### Card Management System (CMS):
- Click on "Bin Adding" to manage BIN details.
- Navigate to "Card Issuing" to issue new cards to customers.
- Go to "Balance Adding" to add funds to existing cards.

### Transaction Processing System (TXN):
- Visit "Transaction Tracking" to track card transactions and view transaction risk scores.

## Error Handling
Both the CMS and TXN components include robust error handling to ensure smooth operation and a user-friendly experience. Errors are logged for debugging purposes, and users receive appropriate error messages when issues occur.

## Logging
The application implements logging to capture various events, errors, and user interactions. Logs are stored for auditing, monitoring, and debugging. Log files can be configured to rotate periodically to prevent excessive disk usage.

## Security
The CMS and TXN components take security seriously. User authentication is handled with Flask-Login, ensuring that only authorized users can access sensitive functionalities. Additionally, input validation and sanitation are enforced to prevent common security vulnerabilities, such as SQL injection and cross-site scripting (XSS) attacks.

## Monitoring
The application includes monitoring features to track user interactions, system performance, and potential issues. Monitoring tools can be integrated to provide real-time insights into the application's health.

## Key Functions
### Card Generation
The "Card Issuing" feature in the CMS allows administrators to generate new cards for customers. It includes functionality to configure card details like card number, cardholder name, expiry date, and CVV.

### Risk Calculations
The "Transaction Tracking" feature in the TXN component calculates transaction risk scores based on various factors, such as CVV attempts, transaction amount, cardholder age, and the country of the transaction. These risk scores help identify potentially fraudulent transactions.

### Fraud Detection Cases
The TXN component includes fraud detection mechanisms that trigger when certain conditions are met, such as multiple incorrect CVV attempts on an active card, large transaction amounts with a high number of transactions in a short time, or transactions flagged as suspicious by a fraud detection system. These cases are logged and monitored for further investigation.

## Contributing
Contributions are welcome! If you would like to contribute to the project, please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add feature-name'`
4. Push to your fork: `git push origin feature-name`
5. Submit a pull request.

## License
This project is licensed under the MIT License.

