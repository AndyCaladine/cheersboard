#CheersBoard - Dev Log

---

# 24-04-2026 - Entry 001 - Project start up 

### What we built
- Full project folder structure
- Python virtual environment
- Installed all core dependencies
- Flask app factory pattern with Blueprints
- SQLite database initialised
- Git repo live on GitHub

### Why these decisions 
- **App factory** — keeps the app testable and scalable
- **Blueprints** — modular routing, each concern in its own file
- **SQLite** — zero config for development, easy to swap later
- **Stripe from day one** — pay-per-board is core to the product
- **python-dotenv** — secrets stay out of version control

### Next Time
- Database models: User, Board, Message, Payment
- Flask-Login user loader
- Register and login routes

# 24-04-2026 - Entry 002 - Authentication

### What we built
- Raw SQL schema with four tables: users, boards, messages, payments
- Switched from SQLAlchemy ORM to raw sqlite3
- Simple User class with UserMixin for Flask-Login compatibility
- Register, login and logout routes using raw SQL queries
- Password hashing with Werkzeug
- Base HTML template with nav and flash messages
- Register, login and dashboard templates

### Why these decisions
- **Raw SQL over ORM** — full visibility and control over every query
- **row_factory = sqlite3.Row** — results behave like dictionaries, much more readable
- **UserMixin** — gives Flask-Login what it needs without a full ORM model
- **PRAGMA foreign_keys = ON** — SQLite has foreign keys off by default, we always turn them on
- **Werkzeug password hashing** — industry standard, never store plain text passwords

### Next episode
- Create board flow
- Stripe payment integration
- Shareable board links
- Message submission