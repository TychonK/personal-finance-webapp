# Personal Finance Web Application

A Flask-based web application for managing personal finances, tracking expenses and income, and analyzing spending patterns.

## Features

- User authentication (register, login, logout)
- Add and manage transactions with categories
- Track income and expenses
- Upload and process bank statements (PDF)
- Visual analytics and summaries
- Responsive design

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/personal-finance-webapp.git
cd personal-finance-webapp
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables (optional):
```bash
# Create a .env file with the following variables
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///app.db  # or your database URL
```

5. Initialize the database:
```bash
python run.py
```

## Usage

1. Start the development server:
```bash
python run.py
```

2. Open a web browser and navigate to `http://localhost:5000`

3. Register a new account or login with existing credentials

4. Start managing your finances:
   - Add transactions manually
   - Upload bank statements (PDF)
   - View analytics and summaries
   - Track spending by category

## Project Structure

```
personal-finance-webapp/
├── app/
│   ├── __init__.py
│   ├── auth/
│   ├── main/
│   ├── transactions/
│   ├── static/
│   └── templates/
├── venv/
├── config.py
├── requirements.txt
└── run.py
```

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
