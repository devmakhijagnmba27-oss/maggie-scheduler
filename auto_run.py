"""
Maggie Calendar Scheduler – Auto Runner
========================================
Automatically finds the newest timetable file (.xlsx / .pdf) in the project,
filters it against saved subjects (mandatory + electives), generates the
aesthetic schedule card, and emails it.

Ideal for scheduled execution (GitHub Actions / Windows Task Scheduler / Cron).
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Windows encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    BASE_DIR,
    GMAIL_ADDRESS,
    GMAIL_APP_PASSWORD,
    RECIPIENT_EMAIL,
    load_user_subjects,
)
from parser import parse_timetable
from filter_engine import filter_schedule, format_text_schedule, group_by_day
from image_generator import generate_schedule_image
from email_sender import send_schedule_email


def find_latest_timetable() -> Path | None:
    """Find the most recently modified timetable file in the workspace."""
    patterns = ["*.xlsx", "*.xls", "*.pdf"]
    candidates: list[Path] = []
    
    for pattern in patterns:
        for f in BASE_DIR.glob(pattern):
            # Skip user elective PDFs or non-timetable files
            if "elective" in f.name.lower() or "submission" in f.name.lower():
                continue
            candidates.append(f)
            
    if not candidates:
        return None
        
    # Sort by modification time descending
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def run_automation() -> bool:
    print("=" * 50)
    print(f"🕒 Maggie Auto-Scheduler Execution – {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 1. Check subjects
    subjects = load_user_subjects()
    if not subjects:
        # Default full list (Mandatory + Marketing Electives)
        subjects = ["B2B", "DSMM", "CB", "PBM", "DDM", "EI", "DA", "AIM", "CFBSB", "CRP3", "CRP"]
        print(f"📋 Using default subjects: {', '.join(subjects)}")
    else:
        print(f"📋 Loaded {len(subjects)} subjects: {', '.join(subjects)}")

    # 2. Locate timetable
    timetable_path = find_latest_timetable()
    if not timetable_path:
        print("❌ No timetable file (.xlsx / .pdf) found in project directory!")
        return False
        
    print(f"📄 Found latest timetable: {timetable_path.name}")

    # 3. Parse
    print("⏳ Parsing timetable for Section D...")
    parsed = parse_timetable(str(timetable_path), section="Sec D")
    print(f"   Extracted {len(parsed['slots'])} active slots, {len(parsed.get('course_map', {}))} courses")

    # 4. Filter
    filtered = filter_schedule(parsed, subjects)
    if not filtered:
        print("📭 No matching classes found for your subjects.")
        return False

    grouped = group_by_day(filtered)
    print(f"   ✅ Filtered {len(filtered)} classes across {len(grouped)} days.")

    # 5. Generate Card Image
    print("🎨 Rendering visual schedule card...")
    img_buf = generate_schedule_image(filtered)
    local_png = BASE_DIR / "my_schedule.png"
    img_buf.seek(0)
    local_png.write_bytes(img_buf.read())
    print(f"   💾 Saved local copy to: {local_png}")

    # 6. Send Email
    if GMAIL_ADDRESS and RECIPIENT_EMAIL:
        now_str = datetime.now().strftime("%d-%b %I:%M %p")
        subject_line = f"📅 Weekly Timetable (Sec-D) | {len(filtered)} Classes – {now_str}"
        print(f"📧 Sending email to {RECIPIENT_EMAIL}...")
        img_buf.seek(0)
        success = send_schedule_email(filtered, img_buf, subject_line=subject_line)
        if success:
            print("   ✅ Email delivered successfully!")
            return True
        else:
            print("   ❌ Email failed to send.")
            return False
    else:
        print("⚠️ Email credentials not set in environment.")
        return False


if __name__ == "__main__":
    success = run_automation()
    sys.exit(0 if success else 1)
