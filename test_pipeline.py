"""
Test Pipeline – Generates a preview schedule image with sample data
to verify the image generator and filter engine work correctly.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, ".")

from filter_engine import filter_schedule, format_text_schedule, group_by_day
from image_generator import generate_schedule_image


def main():
    # ── Simulated parsed timetable data ──────────────────
    # This mimics what parser.parse_timetable() would return
    parsed = {
        "slots": [
            # Monday
            {"day": "Monday", "time": "10:20-11:35", "entries": ["B2B", "WM", "PRM"], "room": "302", "faculty": "Dr. Pratigya Kwatra", "raw_cell": "B2B/WM/PRM"},
            {"day": "Monday", "time": "11:40-12:55", "entries": ["CB", "SOME", "DDM"], "room": "302", "faculty": "Dr. Mohd. Danish Kirmani", "raw_cell": "CB/SOME/DDM"},
            {"day": "Monday", "time": "15:00-16:15", "entries": ["PBM", "EI", "WM"], "room": "302", "faculty": "Dr. Ankita Sharma", "raw_cell": "PBM/EI/WM"},

            # Tuesday
            {"day": "Tuesday", "time": "09:00-10:15", "entries": ["DDM", "PRM", "B2B"], "room": "303", "faculty": "Dr. Pratigya Kwatra", "raw_cell": "DDM/PRM/B2B"},
            {"day": "Tuesday", "time": "10:20-11:35", "entries": ["SOME", "WM", "CB"], "room": "302", "faculty": "Dr. Pooja Sharma", "raw_cell": "SOME/WM/CB"},
            {"day": "Tuesday", "time": "14:00-15:15", "entries": ["EI", "PBM", "DSMM"], "room": "Seminar Hall", "faculty": "Dr. Abhishek Kumar", "raw_cell": "EI/PBM/DSMM"},

            # Wednesday
            {"day": "Wednesday", "time": "09:00-10:15", "entries": ["CRP3"], "room": "302", "faculty": "Prof. Mehta", "raw_cell": "CRP3"},
            {"day": "Wednesday", "time": "11:40-12:55", "entries": ["DSMM", "WM", "PRM"], "room": "303", "faculty": "Dr. Pooja Sharma", "raw_cell": "DSMM/WM/PRM"},

            # Thursday
            {"day": "Thursday", "time": "10:20-11:35", "entries": ["CB", "SOME", "DDM"], "room": "302", "faculty": "Dr. Mohd. Danish Kirmani", "raw_cell": "CB/SOME/DDM"},
            {"day": "Thursday", "time": "11:40-12:55", "entries": ["DSMM", "EI", "B2B"], "room": "303", "faculty": "Dr. Pooja Sharma", "raw_cell": "DSMM/EI/B2B"},
            {"day": "Thursday", "time": "15:00-16:15", "entries": ["PBM", "PRM", "WM"], "room": "302", "faculty": "Dr. Ankita Sharma", "raw_cell": "PBM/PRM/WM"},

            # Friday
            {"day": "Friday", "time": "09:00-10:15", "entries": ["DDM", "SOME", "CB"], "room": "Seminar Hall", "faculty": "Dr. Abhishek Kumar", "raw_cell": "DDM/SOME/CB"},
            {"day": "Friday", "time": "10:20-11:35", "entries": ["B2B", "DSMM", "PRM"], "room": "302", "faculty": "Dr. Pratigya Kwatra", "raw_cell": "B2B/DSMM/PRM"},
        ],
        "course_map": {
            "B2B":  {"name": "Business to Business Marketing", "faculty": "Dr. Pratigya Kwatra", "credits": "3"},
            "DSMM": {"name": "Digital & Social Media Marketing", "faculty": "Dr. Pooja Sharma", "credits": "3"},
            "CB":   {"name": "Consumer Behaviour", "faculty": "Dr. Mohd. Danish Kirmani", "credits": "3"},
            "PBM":  {"name": "Product & Brand Management", "faculty": "Dr. Ankita Sharma", "credits": "3"},
            "DDM":  {"name": "Data Driven Marketing", "faculty": "Dr. Pratigya Kwatra", "credits": "3"},
            "EI":   {"name": "Entrepreneurship & Innovation", "faculty": "Dr. Abhishek Kumar", "credits": "3"},
            "WM":   {"name": "Wealth Management", "faculty": "", "credits": "3"},
            "PRM":  {"name": "Performance Management", "faculty": "", "credits": "3"},
            "SOME": {"name": "Social Media Engagement", "faculty": "", "credits": "3"},
            "CRP3": {"name": "Comprehensive Research Project III", "faculty": "Prof. Mehta", "credits": "2"},
        },
        "room_map": {
            "B2B": "302", "CB": "302", "WM": "302", "PBM": "302",
            "DSMM": "303", "DDM": "303",
        },
    }

    # Student's enrolled subjects
    my_subjects = ["B2B", "DSMM", "CB", "PBM", "DDM", "EI", "CRP3"]

    # ── Filter ──────────────────────────────────────────
    filtered = filter_schedule(parsed, my_subjects)

    print(f"Total classes found: {len(filtered)}")
    print(f"Days with classes: {len(group_by_day(filtered))}")
    print()

    # ── Print text schedule ─────────────────────────────
    text_msg = format_text_schedule(filtered)
    print(text_msg)
    print()

    # ── Generate image ──────────────────────────────────
    img_buf = generate_schedule_image(filtered)
    output_path = "schedule_preview.png"
    with open(output_path, "wb") as f:
        f.write(img_buf.read())
    print(f"Schedule image saved to: {output_path}")


if __name__ == "__main__":
    main()
