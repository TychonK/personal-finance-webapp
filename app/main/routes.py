from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from app.main import bp
from app.models import Transaction, Category
from app import db

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')

@bp.route('/transactions/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    data = request.get_json()
    if not data or 'amount' not in data or 'category_id' not in data or 'transaction_type' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    category = Category.query.filter_by(id=data['category_id'], user_id=current_user.id).first()
    if not category:
        return jsonify({'error': 'Invalid category'}), 400
    
    transaction = Transaction(
        amount=data['amount'],
        category=category.name,  # Keep for backward compatibility
        category_id=category.id,
        transaction_type=data['transaction_type'],
        description=data.get('description', ''),
        user_id=current_user.id
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify(transaction.to_dict())

@bp.route('/transactions/get_summary')
@login_required
def get_summary():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    
    # Debug logging
    print(f"Found {len(transactions)} transactions")
    for t in transactions:
        print(f"Transaction: amount={t.amount}, type={t.transaction_type}, category={t.category}")
    
    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.transaction_type == 'income')
    total_expenses = sum(abs(t.amount) for t in transactions if t.transaction_type == 'expense')
    
    print(f"Total income: {total_income}")
    print(f"Total expenses: {total_expenses}")
    print(f"Balance: {total_income - total_expenses}")
    
    # Calculate category breakdown (only for expenses)
    by_category = {}
    for t in transactions:
        if t.transaction_type == 'expense':
            category_name = t.category_ref.name if t.category_ref else t.category
            by_category[category_name] = by_category.get(category_name, 0) + abs(t.amount)
    
    # Calculate monthly summary
    monthly_summary = {}
    for t in transactions:
        month = t.date.strftime('%Y-%m')
        if t.transaction_type == 'income':
            monthly_summary[month] = monthly_summary.get(month, 0) + t.amount
        else:
            monthly_summary[month] = monthly_summary.get(month, 0) - abs(t.amount)
    
    response_data = {
        'transactions': [t.to_dict() for t in transactions],
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': total_income - total_expenses,
        'by_category': by_category,
        'monthly_summary': monthly_summary
    }
    
    print("Response data:", response_data)
    return jsonify(response_data)

@bp.route('/transactions/delete_transaction/<int:transaction_id>', methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first()
    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404
    
    db.session.delete(transaction)
    db.session.commit()
    
    return jsonify({'message': 'Transaction deleted successfully'})

@bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': cat.id,
        'name': cat.name,
        'is_default': cat.is_default
    } for cat in categories])

@bp.route('/categories', methods=['POST'])
@login_required
def add_category():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Category name is required'}), 400
    
    category = Category(name=data['name'], user_id=current_user.id)
    db.session.add(category)
    db.session.commit()
    
    return jsonify({
        'id': category.id,
        'name': category.name,
        'is_default': category.is_default
    }), 201

@bp.route('/categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first()
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    if category.is_default:
        return jsonify({'error': 'Cannot delete default category'}), 400
    
    # Update transactions that use this category to use a default category
    default_category = Category.query.filter_by(
        user_id=current_user.id,
        is_default=True
    ).first()
    
    if default_category:
        Transaction.query.filter_by(category_id=category_id).update({
            'category_id': default_category.id,
            'category': default_category.name
        })
    
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({'message': 'Category deleted successfully'}), 200 