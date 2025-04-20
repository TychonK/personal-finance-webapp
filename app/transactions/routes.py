import os
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.transactions import bp
from app.models import Transaction
import pdfplumber
import pandas as pd

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            
            # Process PDF
            transactions = []
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    # Here you would implement your specific PDF parsing logic
                    # This is a placeholder for the actual parsing logic
                    pass
            
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'message': 'PDF processed successfully', 'transactions': transactions})
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
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