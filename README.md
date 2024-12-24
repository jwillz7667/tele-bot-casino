# Telegram Casino Bot

A Telegram bot for managing virtual casino games and user wallets.

## Features

- User registration and management
- Virtual wallet system with deposits and withdrawals
- Balance tracking and transaction history
- Secure transaction handling with SQLAlchemy ORM
- Error handling and logging
- Type hints and modern Python practices

## Requirements

- Python 3.9 or higher
- SQLite3
- Dependencies listed in `requirements.txt`

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/TelegramCasinoBot.git
cd TelegramCasinoBot
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

4. Create a `.env` file with your Telegram bot token:
```bash
TELEGRAM_TOKEN=your_bot_token_here
DATABASE_URL=sqlite:///casino.db
```

5. Initialize the database:
```bash
python src/init_db.py
```

6. Start the bot:
```bash
python src/bot.py
```

## Usage

The bot supports the following commands:

- `/start` - Start the bot and register
- `/help` - Show help message
- `/deposit <amount>` - Deposit funds
- `/withdraw <amount>` - Withdraw funds
- `/balance` - Check your balance

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

The project uses:
- Black for code formatting
- isort for import sorting
- mypy for type checking
- pylint for linting

Run formatters:
```bash
black src/ tests/
isort src/ tests/
```

Run type checking:
```bash
mypy src/
```

Run linting:
```bash
pylint src/
```

## Project Structure

```
TelegramCasinoBot/
├── src/
│   ├── handlers/         # Command handlers
│   ├── wallet/          # Wallet management
│   ├── bot.py           # Main bot file
│   ├── init_db.py       # Database initialization
│   └── user_service.py  # User management
├── tests/               # Test files
├── .env                 # Environment variables
├── requirements.txt     # Dependencies
└── README.md           # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 