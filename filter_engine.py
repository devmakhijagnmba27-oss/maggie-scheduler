"""
Maggie Calendar Scheduler – Schedule Filtering Engine
=====================================================
Takes parsed timetable data + the student's enrolled subjects
and produces a filtered, enriched schedule.

Output: a list of FilteredSlot dicts, one per class the student must attend:
    {
        "day":     "Monday",
        "time":    "10:20-11:35",
        "subject": "B2B",
        "full_name": "Business to Business Marketing",
        "room":    "302",
        "faculty": "Dr. Pratigya Kwatra",
    }
"""

from __future__ import annotations

import re
from config import DAYS_ORDER


def filter_schedule(
    parsed: dict,
    my_subjects: list[str],
) -> list[dict]:
    """
    Filter the parsed timetable to only the student's enrolled subjects.

    Parameters
    ----------
    parsed : dict
        Output of parser.parse_timetable()  – contains "slots", "course_map", "room_map".
    my_subjects : list[str]
        Upper-cased subject codes the student is enrolled in (e.g. ["B2B", "DSMM", "CB"]).

    Returns
    -------
    list[dict]
        Filtered and enriched slot list, sorted by day & time.
    """
    slots = parsed["slots"]
    course_map = parsed.get("course_map", {})
    room_map = parsed.get("room_map", {})

    my_set = {s.strip().upper() for s in my_subjects}
    filtered: list[dict] = []

    for slot in slots:
        # Check if any entry in this cell matches the student's subjects
        matched_entries = [e for e in slot["entries"] if e in my_set]
        if not matched_entries:
            continue

        for subject_code in matched_entries:
            # Enrich with course map data
            course_info = course_map.get(subject_code, {})
            full_name = course_info.get("name", "")
            faculty = course_info.get("faculty", "")

            # Try slot-level faculty first, then course map
            if slot.get("faculty"):
                faculty = slot["faculty"]

            # Resolve room: slot-level > room_map > default
            room = slot.get("room", "")
            if not room:
                room = room_map.get(subject_code, "")
            if not room:
                room = room_map.get("_DEFAULT_ROOM", "")

            filtered.append({
                "day": slot["day"],
                "time": slot["time"],
                "subject": subject_code,
                "full_name": full_name,
                "room": room,
                "faculty": faculty,
            })

    # Sort by day order then by time
    filtered.sort(key=lambda s: (_day_sort_key(s["day"]), _time_sort_key(s["time"])))

    # Deduplicate (same day + time + subject)
    seen = set()
    deduped = []
    for item in filtered:
        key = (item["day"], item["time"], item["subject"])
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return deduped


def group_by_day(filtered: list[dict]) -> dict[str, list[dict]]:
    """Group filtered slots by day, preserving day order."""
    grouped: dict[str, list[dict]] = {}
    for day in DAYS_ORDER:
        day_slots = [s for s in filtered if s["day"] == day]
        if day_slots:
            grouped[day] = day_slots
    return grouped


def format_text_schedule(filtered: list[dict]) -> str:
    """
    Format the filtered schedule as a pretty Telegram-compatible text message.
    Uses Unicode symbols for a clean look.
    """
    grouped = group_by_day(filtered)
    if not grouped:
        return "📭 *No classes found for your subjects this week!*\nDouble-check your subject list with /mysubjects"

    lines = ["🗓️ *Your Filtered Schedule*\n"]

    day_emojis = {
        "Monday": "🟣", "Tuesday": "🔵", "Wednesday": "🟢",
        "Thursday": "🟠", "Friday": "🔴", "Saturday": "🟤",
    }

    for day, slots in grouped.items():
        emoji = day_emojis.get(day, "📌")
        lines.append(f"\n{emoji} *{day.upper()}*")
        lines.append("─" * 24)

        for s in slots:
            subj_display = f"*{s['subject']}*"
            if s["full_name"]:
                subj_display += f" ({s['full_name']})"

            lines.append(f"  🕐 `{s['time']}`")
            lines.append(f"  📘 {subj_display}")

            if s["room"]:
                lines.append(f"  🏫 Room {s['room']}")
            if s["faculty"]:
                lines.append(f"  👨‍🏫 {s['faculty']}")
            lines.append("")

    lines.append("─" * 24)
    lines.append("✨ _Filtered by Maggie Scheduler Bot_")
    return "\n".join(lines)


# ── Helpers ──────────────────────────────────────────────

def _day_sort_key(day: str) -> int:
    try:
        return DAYS_ORDER.index(day)
    except ValueError:
        return 99


def _time_sort_key(time_str: str) -> tuple[int, int]:
    """Sort by start hour and minute, converting 1-5 PM slots to 13-17 hours."""
    m = re.search(r'(\d{1,2})[:.](\d{2})', time_str)
    if m:
        h = int(m.group(1))
        minute = int(m.group(2))
        # If hour is between 1 and 7, it's afternoon/PM in college timetable
        if 1 <= h <= 7:
            h += 12
        return (h, minute)
    return (99, 99)
