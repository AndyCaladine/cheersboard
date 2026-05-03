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

## Session — 2026-05-03

### What was built

**Schema v1.0 — full review and rebuild**
Scrapped the original four-table schema and rebuilt it properly from scratch. Now has eight tables: `users`, `boards`, `messages`, `payments`, `themes`, `occasions`, `voucher_codes`, and `password_resets`. The expanded `users` table covers full GDPR and payment compliance — billing address, consent fields with versioning, security question/answer, audit trail, and `theme_preference` for dark/light mode. Added `theme_preference TEXT NOT NULL DEFAULT 'dark'` after initial build via a schema rebuild rather than ALTER TABLE.

**Foundation files**
Rewrote `app.py`, `config.py`, `utils/db.py`, `utils/security.py`, and `utils/helpers.py` to match the style and patterns from the training management system. Dropped `flask_login` and the `create_app()` factory pattern entirely in favour of session-based auth and a flat `app = Flask(__name__)` structure.

**Multi-step registration flow**
Built a five-step registration flow with session-based state between steps:
- Step 1: About You (name, email, DOB via three dropdowns, mobile)
- Step 2: Address (full billing address for Stripe compliance)
- Step 3: Password and security question
- Step 4: Preferences and legal agreements
- Step 5: Review with edit links back to any step and voucher code placeholder

Each step validates server-side and returns an `errors` dict keyed by field name so error messages render directly beneath the relevant input rather than in a flash banner. Flash messages reserved for session-level issues only (expired session, email already taken at final submit).

Password rules: min 8 chars, one upper, one lower, one number, one special character. Security answer cannot match the password. DOB assembles from three dropdowns into `YYYY-MM-DD` for storage.

**Login page**
Clean login page matching the registration style — same dark navy background, show/hide password toggle, forgot password link (stub for now).

**Dashboard**
Full dashboard with:
- Welcome message using the user's first name
- Dark/light mode toggle — preference stored on the `users` table so it follows the user across devices and survives cache clears
- My Boards section with empty state and board cards for existing boards
- Full pricing and feature comparison table covering all four tiers (Free, Lite, Premium, Event)
- Expandable inline preview panels for themes and layouts — clicking Preview opens a panel showing placeholder thumbnails of what's included at each tier
- Touch-friendly throughout — min 44–52px tap targets, `@media (hover: hover)` guards on hover effects, `-webkit-tap-highlight-color: transparent` on buttons

**CSS architecture**
Established the pattern going forward:
- `static/css/main.css` — global styles only, nothing feature-specific
- `static/css/pages/register.css` — registration flow
- `static/css/pages/login.css` — login page
- `static/css/pages/dashboard.css` — dashboard with dual theme variable sets

### Key decisions made

**Analytics and monitoring** — cookie-based features and in-database analytics are out of scope by design. Will use Plausible or Fathom for traffic/geography and Sentry for error/performance monitoring. No cookie consent banner needed. Setup deferred until closer to production.

**Dark/light mode storage** — stored on the `users` table as `theme_preference` rather than browser localStorage or a cookie. Means the preference follows the user across devices and is not lost when cache or cookies are cleared. Toggle uses a slider for touch screen compatibility.

**Theme tier access** — data-driven via `tier_required` on the `themes` table. No hardcoded tier logic in routes. Adding a new theme in future means adding a row and a CSS class — no code changes.

**Inline form errors** — validation returns an `errors` dict keyed by field name. Each template renders errors directly beneath the relevant input. Flash messages only used for session-level issues.

**Light mode accent colour** — `btn--primary` overridden to teal in light mode as yellow on cream background has insufficient contrast. Dark mode keeps yellow. Controlled via `.theme--light .btn--primary` override in `dashboard.css`.

### Still to do
- Forgot password flow
- Create board flow (occasions, theme picker, Stripe payment)
- Board view page (public shareable link)
- Message submission by guests
- Admin panel
- Voucher code system (backend)
- PDF export and QR code generation
- Slideshow and embed/OBS mode (event tier)