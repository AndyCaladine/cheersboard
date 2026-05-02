-- ============================================================
-- CheersBoard - Database Schema
-- ============================================================
-- Author: Andy Caladine
-- Schema Version: v1.0
-- Milestone: Schema Review & Foundation
--
-- Overview:
-- Core database schema for CheersBoard — a Flask-based pay-per-board
-- shared celebration platform. Users create boards for occasions like
-- birthdays and weddings, share a link, and others add messages.
--
-- Key Design Principles:
-- - Authentication and profile data kept lean and intentional
-- - Full GDPR and payment compliance baked into the schema
-- - Audit trail on all mutable records
-- - Theme and tier access controlled by data, not hardcoded logic
-- - Guest contributors do not require accounts
--
-- Core Structure:
-- - users            = authentication, profile, GDPR and audit fields
-- - boards           = board records owned by users
-- - messages         = guest and user contributions to boards
-- - payments         = Stripe payment records per board transaction
-- - themes           = visual themes with tier access control
-- - occasions        = occasion types (birthday, wedding, etc.)
-- - voucher_codes    = discount codes applicable at checkout
-- - password_resets  = time-limited reset tokens (same flow as TMS)
--
-- Notes for future me:
-- Keep this file clean and intentional.
-- If it starts to feel messy, the data model probably needs refactoring.
-- Billing address snapshot on payments is critical — do not remove.
-- Theme tier access is data-driven. Keep it that way.
-- ============================================================


-- ============================================================
-- Drop existing tables
-- ============================================================
-- Dropped in dependency order (children first) to avoid
-- foreign key constraint violations.
-- ============================================================

DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS boards;
DROP TABLE IF EXISTS voucher_codes;
DROP TABLE IF EXISTS password_resets;
DROP TABLE IF EXISTS themes;
DROP TABLE IF EXISTS occasions;
DROP TABLE IF EXISTS users;


-- ============================================================
-- Users
-- ============================================================
-- Core account table. Stores authentication, personal data,
-- legal consent, communication preferences, and audit fields.
--
-- Design notes:
-- - is_admin is a flag on this table rather than a separate role
--   system because CheersBoard has only two access levels.
-- - terms_version and gdpr_version allow consent re-prompting
--   when documents are updated.
-- - updated_by_user_id and updated_by_role track whether the user
--   or an admin made the last change. The role field is required
--   because the user ID alone does not tell you which capacity
--   the change was made in.
-- - billing_address fields are stored here for Stripe compliance.
--   A snapshot is also stored on each payment record in case the
--   user updates their address after a transaction.
-- - security_question and security_answer_hash support the
--   account recovery flow alongside password reset tokens.
-- - is_active allows soft-deletion without destroying records.
-- ============================================================

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identity
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    date_of_birth TEXT NOT NULL,
    mobile_number TEXT,

    -- Authentication
    password_hash TEXT NOT NULL,
    security_question TEXT NOT NULL,
    security_answer_hash TEXT NOT NULL,

    -- Billing address (for Stripe compliance and dispute resolution)
    address_line_1 TEXT,
    address_line_2 TEXT,
    city TEXT,
    county TEXT,
    postcode TEXT,
    country TEXT NOT NULL DEFAULT 'United Kingdom',

    -- Legal consent
    terms_accepted INT NOT NULL DEFAULT 0,
    terms_accepted_at TEXT,
    terms_version TEXT,
    gdpr_accepted INT NOT NULL DEFAULT 0,
    gdpr_accepted_at TEXT,
    gdpr_version TEXT,

    -- Communication preferences
    marketing_opt_in INT NOT NULL DEFAULT 0,
    notifications_opt_in INT NOT NULL DEFAULT 1,
    communication_preference TEXT NOT NULL DEFAULT 'email' CHECK (
        communication_preference IN ('email', 'sms', 'both', 'none')
    ),

    -- Admin access
    is_admin INT NOT NULL DEFAULT 0,
    admin_granted_at TEXT,
    admin_granted_by_user_id INT,

    -- Account state
    is_active INT NOT NULL DEFAULT 1,

    -- Audit
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by_user_id INT,
    updated_by_role TEXT CHECK (
        updated_by_role IN ('customer', 'admin')
    )
);


-- ============================================================
-- Password reset tokens
-- ============================================================
-- Standard one-time reset flow. Tokens expire after 1 hour.
-- used_at is set when the token is consumed to prevent reuse.
-- ============================================================

CREATE TABLE password_resets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    used_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);


-- ============================================================
-- Occasions
-- ============================================================
-- Seeded list of occasion types used when creating a board.
-- Managed via the admin panel. display_order controls the
-- order they appear in the board creation form.
-- ============================================================

CREATE TABLE occasions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    display_order INT NOT NULL DEFAULT 0,
    is_active INT NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- Themes
-- ============================================================
-- Each theme defines a visual style applied to a board.
-- Access is controlled by tier_required so that users on
-- lower tiers can preview a theme but cannot apply it without
-- upgrading their board to the required tier.
--
-- layout_type maps to the four board layout modes:
-- grid, scattered, masonry, polaroid.
--
-- css_class is the identifier used to apply the theme in
-- the frontend stylesheet. Adding a new theme means adding
-- a row here and a corresponding CSS class — no code changes.
--
-- display_order controls the order themes appear in the picker.
-- ============================================================

CREATE TABLE themes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    layout_type TEXT NOT NULL CHECK (
        layout_type IN ('grid', 'scattered', 'masonry', 'polaroid')
    ),
    tier_required TEXT NOT NULL CHECK (
        tier_required IN ('free', 'lite', 'premium', 'event')
    ),
    css_class TEXT NOT NULL UNIQUE,
    preview_image TEXT,
    is_active INT NOT NULL DEFAULT 1,
    display_order INT NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- Voucher codes
-- ============================================================
-- Discount codes that can be applied at checkout.
-- discount_type is either 'percent' or 'fixed' (pence).
-- applicable_tier restricts a code to a specific board tier,
-- or NULL means the code applies to any paid tier.
-- max_uses of NULL means unlimited uses.
-- ============================================================

CREATE TABLE voucher_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    discount_type TEXT NOT NULL CHECK (
        discount_type IN ('percent', 'fixed')
    ),
    discount_value INT NOT NULL,
    applicable_tier TEXT CHECK (
        applicable_tier IN ('lite', 'premium', 'event')
    ),
    max_uses INT,
    uses_count INT NOT NULL DEFAULT 0,
    is_active INT NOT NULL DEFAULT 1,
    expires_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- Boards
-- ============================================================
-- A board belongs to one user (the creator and payer).
-- slug is the unique URL identifier used in share links.
-- tier determines which features and themes are available.
-- theme_id is set by the user from themes available at their tier.
-- occasion_id links to the seeded occasions list.
--
-- Moderation and slideshow settings are stored here so they
-- can be configured per board rather than per account.
--
-- embed_token is a separate random token used for iframe and
-- OBS browser source access without requiring authentication.
--
-- Audit fields track whether the last change was made by the
-- board owner or by an admin on their behalf.
-- ============================================================

CREATE TABLE boards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INT NOT NULL,
    title TEXT NOT NULL,
    recipient_name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    occasion_id INT,
    theme_id INT,
    tier TEXT NOT NULL DEFAULT 'free' CHECK (
        tier IN ('free', 'lite', 'premium', 'event')
    ),
    is_paid INT NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active' CHECK (
        status IN ('active', 'archived', 'deleted')
    ),
    is_public INT NOT NULL DEFAULT 1,
    moderation_enabled INT NOT NULL DEFAULT 0,

    -- Slideshow (event tier only)
    slideshow_enabled INT NOT NULL DEFAULT 0,
    slideshow_speed INT NOT NULL DEFAULT 10,
    slideshow_transition TEXT NOT NULL DEFAULT 'fade' CHECK (
        slideshow_transition IN ('fade', 'slide', 'cut')
    ),

    -- Embed / OBS access token (event tier only)
    embed_token TEXT UNIQUE,

    -- Audit
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by_user_id INT,
    updated_by_role TEXT CHECK (
        updated_by_role IN ('customer', 'admin')
    ),

    FOREIGN KEY (owner_user_id) REFERENCES users(id),
    FOREIGN KEY (occasion_id) REFERENCES occasions(id),
    FOREIGN KEY (theme_id) REFERENCES themes(id)
);


-- ============================================================
-- Messages
-- ============================================================
-- Contributions left on a board by guests or registered users.
-- Contributors do not need an account — sender_name is free
-- text and sender_email is optional (used for moderation
-- notifications only, not stored for marketing purposes).
--
-- is_approved controls whether the message is visible on the
-- board when moderation is enabled. When moderation is off,
-- messages are approved by default on insert.
--
-- is_hidden allows an admin or board owner to hide a message
-- after the fact without deleting the record.
-- ============================================================

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    board_id INT NOT NULL,
    sender_name TEXT NOT NULL,
    sender_email TEXT,
    content TEXT NOT NULL,
    is_approved INT NOT NULL DEFAULT 1,
    is_hidden INT NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (board_id) REFERENCES boards(id)
);


-- ============================================================
-- Payments
-- ============================================================
-- One row per Stripe transaction. Records the board and user
-- at the time of payment, the tier purchased, and the amount.
--
-- billing_address_snapshot stores the user's billing address
-- as it was at the time of payment. This is critical for Stripe
-- dispute resolution — if the user later updates their address,
-- the address used at time of purchase must still be retrievable.
--
-- voucher_code_id records which voucher (if any) was applied.
-- amount_pence is the final charged amount after any discount.
-- original_amount_pence is the full price before any discount.
--
-- stripe_checkout_session_id is the Stripe session reference
-- used to verify payment success server-side via the Stripe API.
-- ============================================================

CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INT NOT NULL,
    board_id INT NOT NULL,
    tier_purchased TEXT NOT NULL CHECK (
        tier_purchased IN ('lite', 'premium', 'event')
    ),
    stripe_checkout_session_id TEXT NOT NULL UNIQUE,
    stripe_payment_intent_id TEXT UNIQUE,
    amount_pence INT NOT NULL,
    original_amount_pence INT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'gbp',
    voucher_code_id INT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'succeeded', 'failed', 'refunded')
    ),
    billing_address_snapshot TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (board_id) REFERENCES boards(id),
    FOREIGN KEY (voucher_code_id) REFERENCES voucher_codes(id)
);