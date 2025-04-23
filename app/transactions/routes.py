import os
import re
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.transactions import bp
from app.models import Transaction
import pdfplumber
import pandas as pd
from datetime import datetime

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_transactions_from_text(text):
    transactions = []
    current_app.logger.debug(f"Processing text: {text[:200]}...")  # Log first 200 chars
    
    # Simplified amount pattern
    amount_pattern = r'\$?\s*(\d+\.\d{2})'
    
    # Split text into lines and process each line
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    for line in lines:
        try:
            # Look for amount
            amount_match = re.search(amount_pattern, line)
            if not amount_match:
                continue
                
            amount = float(amount_match.group(1))
            
            # Get description by removing the amount and cleaning up
            description = re.sub(amount_pattern, '', line).strip()
            if not description:
                continue
                
            # Determine transaction type
            transaction_type = 'expense'
            if any(word in description.lower() for word in ['salary', 'deposit', 'refund', 'credit']):
                transaction_type = 'income'
            
            # Determine category
            category = 'Other'
            category_keywords = {
                'Food': ['restaurant', 'cafe', 'food', 'groceries', 'dining'],
                'Transportation': ['uber', 'lyft', 'taxi', 'transport', 'gas', 'fuel'],
                'Housing': ['rent', 'mortgage', 'housing', 'apartment'],
                'Entertainment': ['movie', 'netflix', 'spotify', 'entertainment', 'game'],
                'Utilities': ['electric', 'water', 'internet', 'phone', 'utility'],
                'Salary': ['salary', 'paycheck', 'income']
            }
            
            for cat, keywords in category_keywords.items():
                if any(keyword in description.lower() for keyword in keywords):
                    category = cat
                    break
            
            transactions.append({
                'amount': amount,
                'description': description,
                'transaction_type': transaction_type,
                'category': category,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            current_app.logger.debug(f"Found transaction: {amount} - {description}")
            
        except Exception as e:
            current_app.logger.error(f"Error processing line '{line}': {str(e)}")
            continue
    
    return transactions

@bp.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    try:
        data = request.get_json()
        current_app.logger.debug(f'Received data: {data}')
        
        if not data:
            current_app.logger.error('No data provided')
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['amount', 'category', 'transaction_type']
        for field in required_fields:
            if field not in data:
                current_app.logger.error(f'Missing required field: {field}')
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Convert amount to float and validate
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({'error': 'Amount must be greater than 0'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid amount format'}), 400

        transaction = Transaction(
            amount=amount,
            category=data['category'],
            transaction_type=data['transaction_type'],
            description=data.get('description', ''),
            user_id=current_user.id
        )
        
        current_app.logger.debug(f'Creating transaction: {transaction.to_dict()}')
        
        db.session.add(transaction)
        db.session.commit()
        
        current_app.logger.debug('Transaction created successfully')
        return jsonify(transaction.to_dict())
    except Exception as e:
        current_app.logger.error(f'Error creating transaction: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/delete_transaction/<int:id>', methods=['DELETE'])
@login_required
def delete_transaction(id):
    try:
        transaction = Transaction.query.get_or_404(id)
        if transaction.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        db.session.delete(transaction)
        db.session.commit()
        return jsonify({'message': 'Transaction deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/upload_pdf', methods=['POST'])
@login_required
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            current_app.logger.info(f"Processing PDF file: {filename}")
            
            # Process PDF
            extracted_transactions = []
            with pdfplumber.open(filepath) as pdf:
                for i, page in enumerate(pdf.pages):
                    current_app.logger.info(f"Processing page {i+1}")
                    text = page.extract_text()
                    if text:
                        transactions = extract_transactions_from_text(text)
                        extracted_transactions.extend(transactions)
            
            current_app.logger.info(f"Extracted {len(extracted_transactions)} transactions")
            
            # Save extracted transactions to database
            saved_transactions = []
            for transaction_data in extracted_transactions:
                try:
                    transaction = Transaction(
                        amount=transaction_data['amount'],
                        category=transaction_data['category'],
                        transaction_type=transaction_data['transaction_type'],
                        description=transaction_data['description'],
                        date=datetime.strptime(transaction_data['date'], '%Y-%m-%d %H:%M:%S'),
                        user_id=current_user.id,
                        source='pdf'
                    )
                    db.session.add(transaction)
                    saved_transactions.append(transaction.to_dict())
                except Exception as e:
                    current_app.logger.error(f"Error saving transaction: {str(e)}")
                    continue
            
            db.session.commit()
            
            if os.path.exists(filepath):
                os.remove(filepath)
                
            return jsonify({
                'message': f'Successfully extracted {len(saved_transactions)} transactions',
                'transactions': saved_transactions
            })
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            current_app.logger.error(f'Error processing PDF: {str(e)}')
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Invalid file type'}), 400

@bp.route('/get_summary')
@login_required
def get_summary():
    try:
        transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
        transactions_list = [t.to_dict() for t in transactions]
        df = pd.DataFrame(transactions_list)
        
        if df.empty:
            return jsonify({
                'total_income': 0,
                'total_expenses': 0,
                'by_category': {},
                'monthly_summary': {},
                'transactions': transactions_list
            })
        
        summary = {
            'total_income': float(df[df['transaction_type'] == 'income']['amount'].sum()),
            'total_expenses': float(df[df['transaction_type'] == 'expense']['amount'].sum()),
            'by_category': df.groupby('category')['amount'].sum().to_dict(),
            'monthly_summary': df.groupby(pd.to_datetime(df['date']).dt.to_period('M').astype(str))['amount'].sum().to_dict(),
            'transactions': transactions_list
        }
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500 