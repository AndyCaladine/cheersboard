"""
CheersBoard — seed_themes.py
============================
Seeds the themes and occasions tables with the full v1.0 data set.
Run this once after init_db.py to populate reference data.

Usage:
    python seed_themes.py

Safe to re-run — checks for existing records before inserting.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ============================================================
# Occasions
# ============================================================
# Matches schema: (name, slug, display_order, is_active)
# No emoji column in the occasions table — emoji lives in the
# name string for display purposes in templates.
# ============================================================

OCCASIONS = [
    ('Birthday',     'birthday',     1,  1),
    ('Wedding',      'wedding',      2,  1),
    ('New Arrival',  'new-arrival',  3,  1),
    ('Graduation',   'graduation',   4,  1),
    ('Retirement',   'retirement',   5,  1),
    ('New Home',     'new-home',     6,  1),
    ('Engagement',   'engagement',   7,  1),
    ('Promotion',    'promotion',    8,  1),
    ('Anniversary',  'anniversary',  9,  1),
    ('Farewell',     'farewell',     10, 1),
    ('Get Well',     'get-well',     11, 1),
    ('Holiday',      'holiday',      12, 1),
    ('Just Because', 'just-because', 13, 1),
]


# ============================================================
# Themes
# ============================================================
# Matches schema columns:
# (name, slug, layout_type, tier_required, css_class,
#  preview_image, is_active, display_order)
#
# css_class is the identifier used in the frontend stylesheet.
# slug is used in URLs and template logic.
# preview_image is NULL for now — added when screenshots exist.
#
# tier_required: free | lite | premium | event
# layout_type:   grid | scattered | masonry | polaroid
# ============================================================

THEMES = [
    # ── Free ─────────────────────────────────────────────────
    (
        'Classic',
        'classic',
        'grid',
        'free',
        'theme-classic',
        None, 1, 1
    ),

    # ── Lite ─────────────────────────────────────────────────
    (
        'Pastel Celebration',
        'pastel-celebration',
        'grid',
        'lite',
        'theme-pastel-celebration',
        None, 1, 2
    ),
    (
        'Pinboard',
        'pinboard',
        'scattered',
        'lite',
        'theme-pinboard',
        None, 1, 3
    ),

    # ── Premium ───────────────────────────────────────────────
    (
        'Scrapbook',
        'scrapbook',
        'scattered',
        'premium',
        'theme-scrapbook',
        None, 1, 4
    ),
    (
        'Polaroid Wall',
        'polaroid-wall',
        'polaroid',
        'premium',
        'theme-polaroid-wall',
        None, 1, 5
    ),
    (
        'Beach',
        'beach',
        'masonry',
        'premium',
        'theme-beach',
        None, 1, 6
    ),
    (
        'Enchanted Forest',
        'enchanted-forest',
        'scattered',
        'premium',
        'theme-enchanted-forest',
        None, 1, 7
    ),
    (
        'Bloom',
        'bloom',
        'grid',
        'premium',
        'theme-bloom',
        None, 1, 8
    ),
    (
        'Crime Board',
        'crime-board',
        'scattered',
        'premium',
        'theme-crime-board',
        None, 1, 9
    ),
    (
        'Noir',
        'noir',
        'grid',
        'premium',
        'theme-noir',
        None, 1, 10
    ),

    # ── Event ─────────────────────────────────────────────────
    (
        'Midnight Gala',
        'midnight-gala',
        'masonry',
        'event',
        'theme-midnight-gala',
        None, 1, 11
    ),
    (
        'Golden Hour',
        'golden-hour',
        'polaroid',
        'event',
        'theme-golden-hour',
        None, 1, 12
    ),
    (
        'Confetti Burst',
        'confetti-burst',
        'grid',
        'event',
        'theme-confetti-burst',
        None, 1, 13
    ),
]


def seed_occasions(conn):
    print("Seeding occasions...")
    inserted = 0
    skipped  = 0

    for (name, slug, display_order, is_active) in OCCASIONS:
        cursor = conn.execute(
            "SELECT id FROM occasions WHERE slug = ?",
            (slug,)
        )
        if cursor.fetchone():
            skipped += 1
            continue

        conn.execute(
            """
            INSERT INTO occasions (name, slug, display_order, is_active)
            VALUES (?, ?, ?, ?)
            """,
            (name, slug, display_order, is_active)
        )
        inserted += 1

    conn.commit()
    print(f"  Occasions — inserted: {inserted}, skipped: {skipped}")


def seed_themes(conn):
    print("Seeding themes...")
    inserted = 0
    skipped  = 0

    for (name, slug, layout_type, tier_required, css_class,
         preview_image, is_active, display_order) in THEMES:

        cursor = conn.execute(
            "SELECT id FROM themes WHERE slug = ?",
            (slug,)
        )
        if cursor.fetchone():
            skipped += 1
            continue

        conn.execute(
            """
            INSERT INTO themes (
                name, slug, layout_type, tier_required,
                css_class, preview_image, is_active, display_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, slug, layout_type, tier_required,
             css_class, preview_image, is_active, display_order)
        )
        inserted += 1

    conn.commit()
    print(f"  Themes — inserted: {inserted}, skipped: {skipped}")


def main():
    print(f"Connecting to: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print("ERROR: database.db not found. Run init_db.py first.")
        return

    conn = get_db()

    try:
        seed_occasions(conn)
        seed_themes(conn)
        print("\nDone. Database seeded successfully.")
    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()