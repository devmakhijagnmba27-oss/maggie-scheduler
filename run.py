"""
Maggie Calendar Scheduler – Run Script
=======================================
Usage:
    python run.py <timetable_file>

Examples:
    python run.py timetable.xlsx
    python run.py timetable.pdf

This script:
  1. Parses the timetable file
  2. Filters it to your enrolled subjects
  3. Generates a beautiful schedule card image
  4. Emails it to you
  5. Also saves the image locally
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path

from config import load_user_subjects, save_user_subjects, RECIPIENT_EMAIL, GMAIL_ADDRESS
from parser import parse_timetable
from filter_engine import filter_schedule, format_text_schedule, group_by_day
from image_generator import generate_schedule_image
from email_sender import send_schedule_email


def main():
    print()
    print("╔══════════════════════════════════════════╗")
    print("║    📅  Maggie Calendar Scheduler         ║")
    print("╚══════════════════════════════════════════╝")
    print()

    # ── Check for timetable file argument ────────────────
    if len(sys.argv) < 2:
        print("Usage: python run.py <timetable_file>")
        print()
        print("Examples:")
        print("  python run.py timetable.xlsx")
        print("  python run.py timetable.pdf")
        print()

        # Check if any timetable files exist in current dir
        tt_files = list(Path(".").glob("*.xlsx")) + list(Path(".").glob("*.xls")) + list(Path(".").glob("*.pdf"))
        if tt_files:
            print("Found files in current directory:")
            for f in tt_files:
                print(f"  • {f.name}")
        return

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        return

    # ── Check subjects ───────────────────────────────────
    subjects = load_user_subjects()
    if not subjects:
        print("⚠️  No subjects configured yet!")
        print()
        print("Enter your subject codes (comma-separated):")
        print("Example: B2B, DSMM, CB, PBM, DDM, EI, CRP3")
        print()
        raw = input("Your subjects: ").strip()
        if not raw:
            print("No subjects entered. Exiting.")
            return
        subjects = [s.strip().upper() for s in raw.replace(",", " ").split() if s.strip()]
        save_user_subjects(subjects)
        print(f"✅ Saved {len(subjects)} subjects: {', '.join(subjects)}")
        print()

    print(f"📋 Your subjects: {', '.join(subjects)}")
    print(f"📄 Timetable file: {filepath.name}")
    print()

    # ── Parse ────────────────────────────────────────────
    print("⏳ Parsing timetable...")
    try:
        parsed = parse_timetable(str(filepath))
    except Exception as e:
        print(f"❌ Error parsing file: {e}")
        return

    total_slots = len(parsed["slots"])
    total_courses = len(parsed.get("course_map", {}))
    print(f"   Found {total_slots} time slots, {total_courses} course definitions")

    if not parsed["slots"]:
        print()
        print("⚠️  No timetable data could be extracted!")
        print("   Make sure the file contains a timetable grid with:")
        print("   • Day names (Monday, Tuesday, etc.)")
        print("   • Time slots (e.g. 10:20-11:35)")
        print("   • Subject codes in the cells")
        return

    # ── Filter ───────────────────────────────────────────
    print("🔍 Filtering your classes...")
    filtered = filter_schedule(parsed, subjects)

    if not filtered:
        all_entries = set()
        for slot in parsed["slots"]:
            all_entries.update(slot["entries"])
        print()
        print("📭 No matching classes found!")
        print(f"   Your subjects: {', '.join(subjects)}")
        print(f"   Found in timetable: {', '.join(sorted(all_entries)[:20])}")
        print()
        print("   Check if your subject codes match the timetable.")
        print("   Run again or edit user_data/my_subjects.txt")
        return

    grouped = group_by_day(filtered)
    print(f"   ✅ Found {len(filtered)} classes across {len(grouped)} days!")
    print()

    # ── Print text schedule ──────────────────────────────
    text_msg = format_text_schedule(filtered)
    print(text_msg)
    print()

    # ── Generate image ───────────────────────────────────
    print("🎨 Generating schedule card...")
    img_buf = generate_schedule_image(filtered)

    # Save locally
    output_path = Path("my_schedule.png")
    img_buf.seek(0)
    output_path.write_bytes(img_buf.read())
    print(f"   💾 Saved to: {output_path.absolute()}")

    # ── Send email ───────────────────────────────────────
    print()
    if GMAIL_ADDRESS and RECIPIENT_EMAIL:
        print(f"📧 Sending to {RECIPIENT_EMAIL}...")
        img_buf.seek(0)
        from datetime import datetime
        now_str = datetime.now().strftime("%d-%b %I:%M %p")
        subject_line = f"📅 Complete Weekly Timetable (Sec-D) | {len(filtered)} Classes – {now_str}"
        success = send_schedule_email(filtered, img_buf, subject_line=subject_line)
        if success:
            print(f"   ✅ Email sent successfully with subject: '{subject_line}'")
        else:
            print(f"   ❌ Email failed. Check your .env credentials.")
            print(f"   📎 Your schedule image is saved at: {output_path.absolute()}")
    else:
        print("📧 Email not configured (set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env)")
        print(f"   📎 Your schedule image is saved at: {output_path.absolute()}")

    print()
    print("✨ Done!")


if __name__ == "__main__":
    main()
