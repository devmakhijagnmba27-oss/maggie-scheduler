"""
Maggie Calendar Scheduler – Configuration
==========================================
Central configuration for bot token, styling, and default subject lists.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env ────────────────────────────────────────────
load_dotenv(Path(__file__).parent / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ── Email settings ───────────────────────────────────────
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "")

# ── Paths ────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "user_data"
DATA_DIR.mkdir(exist_ok=True)
SUBJECTS_FILE = DATA_DIR / "my_subjects.txt"

# ── Days ordering ────────────────────────────────────────
DAYS_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# ── Image card styling ───────────────────────────────────
CARD_STYLE = {
    # Dark modern palette
    "bg_color":         (18, 18, 28),        # Deep navy-black
    "header_bg":        (30, 30, 50),        # Slightly lighter header
    "card_bg":          (38, 38, 60),        # Card background
    "card_border":      (72, 61, 139),       # Muted purple border
    "accent_gradient":  [(108, 92, 231),     # Purple start
                         (72, 149, 239)],    # Blue end
    "text_primary":     (240, 240, 255),     # Near-white
    "text_secondary":   (170, 170, 200),     # Muted lavender
    "text_accent":      (108, 92, 231),      # Purple accent text
    "room_badge_bg":    (46, 134, 171),      # Teal badge
    "room_badge_text":  (255, 255, 255),
    "faculty_tag":      (255, 183, 77),      # Warm amber
    "time_badge_bg":    (108, 92, 231),      # Purple badge
    "time_badge_text":  (255, 255, 255),
    "day_colors": [                          # One per day
        (108, 92, 231),   # Monday – Purple
        (72, 149, 239),   # Tuesday – Blue
        (6, 214, 160),    # Wednesday – Emerald
        (255, 159, 67),   # Thursday – Orange
        (239, 71, 111),   # Friday – Rose
        (17, 138, 178),   # Saturday – Teal
    ],
    # Fonts (will fallback to default if not found)
    "font_title_size":  42,
    "font_day_size":    28,
    "font_subject_size": 22,
    "font_detail_size": 17,
    "card_radius":      16,
    "card_padding":     18,
    "card_gap":         14,
    "image_width":      1100,
}


def load_user_subjects() -> list[str]:
    """Load the user's enrolled subjects from disk."""
    if SUBJECTS_FILE.exists():
        lines = SUBJECTS_FILE.read_text(encoding="utf-8").strip().splitlines()
        return [s.strip().upper() for s in lines if s.strip()]
    return []


def save_user_subjects(subjects: list[str]) -> None:
    """Persist the user's enrolled subjects to disk."""
    SUBJECTS_FILE.write_text(
        "\n".join(s.strip().upper() for s in subjects),
        encoding="utf-8",
    )
