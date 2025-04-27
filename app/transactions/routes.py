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

import re
from datetime import datetime

def extract_transactions_from_text(text):
    transactions = []
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    date_pattern = r'\d{2}\.\d{2}\.\d{4}'
    amount_pattern = r'([-+]?[0-9\s,.]+)\s*(PLN|EUR)'

    current_transaction = {}
    last_date = None

    for idx, line in enumerate(lines):
        # Debug print
        print(f"Line {idx}: {line}")

        # If line has a date
        date_match = re.search(date_pattern, line)
        if date_match:
            last_date = date_match.group()

        # If line has amount
        amount_match = re.search(amount_pattern, line)
        if amount_match and last_date:
            amount_raw = amount_match.group(1)
            currency = amount_match.group(2)
            try:
                amount_clean = float(amount_raw.replace(' ', '').replace(',', '.'))
            except ValueError:
                # Skip if cannot cleanly convert amount
                continue

            description = 'Unknown'
            # Search backwards for the merchant (quote line)
            for back_idx in range(idx-1, max(idx-5, -1), -1):
                if lines[back_idx].startswith('"') and lines[back_idx].endswith('"'):
                    description = lines[back_idx].strip('\"')
                    break

            transaction_type = 'income' if amount_clean > 0 else 'expense'

            # Optional category detection
            category = 'Other'
            nearby_text = ' '.join(lines[max(0, idx-3):idx+3]).lower()
            if 'restauracje' in nearby_text or 'kawiarnia' in nearby_text:
                category = 'Food & Drink'
            elif 'internet' in nearby_text or 'telefon' in nearby_text:
                category = 'Utilities'
            elif 'hobby' in nearby_text:
                category = 'Hobby'

            transactions.append({
                'date': datetime.strptime(last_date, '%d.%m.%Y').strftime('%Y-%m-%d %H:%M:%S'),
                'amount': abs(amount_clean),
                'currency': currency,
                'description': description,
                'transaction_type': transaction_type,
                'category': category,
            })

            # After using this date, clear it
            last_date = None

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

            # current_app.logger.info(f"Processing PDF file: {filename}")

            # Collect all text at once
            full_text = ""
            with pdfplumber.open(filepath) as pdf:
                for i, page in enumerate(pdf.pages):
                    # current_app.logger.info(f"Processing page {i+1}")
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"

            # Process full text ONCE
            print("----- FULL EXTRACTED TEXT START -----")
            print(full_text)
            print("----- FULL EXTRACTED TEXT END -----")

            extracted_transactions = extract_transactions_from_text(full_text)

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