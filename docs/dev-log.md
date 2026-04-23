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