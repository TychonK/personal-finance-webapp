from app import create_app, db
from app.models import User, Transaction
import logging

app = create_app()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Transaction': Transaction}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 