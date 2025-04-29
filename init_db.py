from app import create_app, db
from app.models import User, Transaction, Category

app = create_app()
with app.app_context():
    # Drop all tables
    db.drop_all()
    
    # Create all tables
    db.create_all()
    
    print("Database initialized successfully!") 