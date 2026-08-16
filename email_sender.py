"""
Maggie Calendar Scheduler – Email Sender
=========================================
Sends the filtered schedule (image + formatted HTML) via Gmail SMTP.
"""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from io import BytesIO
from datetime import datetime

from config import (
    GMAIL_ADDRESS,
    GMAIL_APP_PASSWORD,
    RECIPIENT_EMAIL,
)
from filter_engine import group_by_day


def send_schedule_email(
    filtered: list[dict],
    image_buf: BytesIO,
    subject_line: str | None = None,
) -> bool:
    """
    Send the filtered schedule as a beautifully formatted HTML email
    with the schedule card image embedded.

    Returns True on success, False on failure.
    """
    if not subject_line:
        today = datetime.now().strftime("%d %b %Y")
        subject_line = f"📅 Your Filtered Schedule – Week of {today}"

    grouped = group_by_day(filtered)

    # ── Build HTML body ──────────────────────────────────
    html = _build_html(grouped, filtered)

    # ── Compose email ────────────────────────────────────
    msg = MIMEMultipart("related")
    msg["Subject"] = subject_line
    msg["From"] = f"Maggie Scheduler <{GMAIL_ADDRESS}>"
    msg["To"] = RECIPIENT_EMAIL

    # HTML part
    html_part = MIMEMultipart("alternative")
    # Plain text fallback
    plain_text = _build_plain_text(grouped)
    html_part.attach(MIMEText(plain_text, "plain", "utf-8"))
    html_part.attach(MIMEText(html, "html", "utf-8"))
    msg.attach(html_part)

    # Embed schedule card image
    image_buf.seek(0)
    img_attachment = MIMEImage(image_buf.read(), _subtype="png")
    img_attachment.add_header("Content-ID", "<schedule_card>")
    img_attachment.add_header("Content-Disposition", "inline", filename="schedule.png")
    msg.attach(img_attachment)

    # Also attach as downloadable file
    image_buf.seek(0)
    img_download = MIMEImage(image_buf.read(), _subtype="png")
    img_download.add_header("Content-Disposition", "attachment", filename="my_schedule.png")
    msg.attach(img_download)

    # ── Send via Gmail SMTP ──────────────────────────────
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


# ── HTML Builder ─────────────────────────────────────────

def _build_html(grouped: dict, filtered: list) -> str:
    """Build a stunning HTML email body."""
    day_colors = {
        "Monday": "#6C5CE7", "Tuesday": "#4895EF", "Wednesday": "#06D6A0",
        "Thursday": "#FF9F43", "Friday": "#EF476F", "Saturday": "#118AB2",
    }
    day_emojis = {
        "Monday": "🟣", "Tuesday": "🔵", "Wednesday": "🟢",
        "Thursday": "🟠", "Friday": "🔴", "Saturday": "🟤",
    }

    total_classes = len(filtered)
    total_days = len(grouped)

    # Build day sections
    day_sections = ""
    for day, slots in grouped.items():
        color = day_colors.get(day, "#6C5CE7")
        emoji = day_emojis.get(day, "📌")

        cards_html = ""
        for s in slots:
            room_badge = ""
            if s["room"]:
                room_badge = f'''
                <span style="background: #2E86AB; color: white; padding: 3px 10px;
                      border-radius: 12px; font-size: 12px; margin-left: 8px;">
                    🏫 Room {s["room"]}
                </span>'''

            faculty_line = ""
            if s["faculty"]:
                faculty_line = f'''
                <div style="color: #FFB74D; font-size: 13px; margin-top: 6px;">
                    👨‍🏫 {s["faculty"]}
                </div>'''

            full_name = ""
            if s["full_name"]:
                full_name = f'''
                <div style="color: #AAAACC; font-size: 13px; margin-top: 2px;">
                    {s["full_name"]}
                </div>'''

            cards_html += f'''
            <div style="background: #26263C; border-radius: 12px; padding: 14px 18px;
                        margin-bottom: 10px; border-left: 4px solid {color};">
                <div style="font-size: 16px; font-weight: bold; color: #F0F0FF;">
                    {s["subject"]}
                </div>
                {full_name}
                <div style="margin-top: 8px;">
                    <span style="background: {color}; color: white; padding: 3px 10px;
                          border-radius: 12px; font-size: 12px;">
                        🕐 {s["time"]}
                    </span>
                    {room_badge}
                </div>
                {faculty_line}
            </div>'''

        day_sections += f'''
        <div style="margin-bottom: 24px;">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <div style="width: 5px; height: 28px; background: {color};
                     border-radius: 3px; margin-right: 12px;"></div>
                <span style="font-size: 20px; font-weight: bold; color: {color};">
                    {emoji} {day.upper()}
                </span>
            </div>
            {cards_html}
        </div>'''

    html = f'''
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin: 0; padding: 0; background: #0E0E1A; font-family: 'Segoe UI', Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; background: #12121C; border-radius: 16px;
                    overflow: hidden;">

            <!-- Header -->
            <div style="background: linear-gradient(135deg, #6C5CE7, #4895EF); padding: 24px;
                        text-align: center;">
                <div style="font-size: 28px; font-weight: bold; color: white;">
                    📅 Your Weekly Schedule
                </div>
                <div style="font-size: 14px; color: rgba(255,255,255,0.85); margin-top: 6px;">
                    {total_classes} classes across {total_days} days
                </div>
            </div>

            <!-- Schedule Card Image -->
            <div style="padding: 20px; text-align: center;">
                <img src="cid:schedule_card" alt="Schedule Card"
                     style="max-width: 100%; border-radius: 12px; border: 1px solid #333;">
            </div>

            <!-- Detailed Breakdown -->
            <div style="padding: 20px 24px;">
                <div style="font-size: 18px; font-weight: bold; color: #F0F0FF;
                     margin-bottom: 16px; padding-bottom: 8px;
                     border-bottom: 1px solid #333;">
                    📋 Detailed Breakdown
                </div>
                {day_sections}
            </div>

            <!-- Footer -->
            <div style="padding: 16px; text-align: center; background: #1E1E32;
                        border-top: 1px solid #333;">
                <div style="font-size: 12px; color: #888;">
                    ✨ Generated by Maggie Scheduler Bot
                </div>
            </div>
        </div>
    </body>
    </html>'''

    return html


def _build_plain_text(grouped: dict) -> str:
    """Build plain-text fallback."""
    lines = ["YOUR FILTERED SCHEDULE", "=" * 40, ""]

    day_emojis = {
        "Monday": ">>", "Tuesday": ">>", "Wednesday": ">>",
        "Thursday": ">>", "Friday": ">>", "Saturday": ">>",
    }

    for day, slots in grouped.items():
        lines.append(f"\n{day.upper()}")
        lines.append("-" * 24)
        for s in slots:
            lines.append(f"  {s['time']}  |  {s['subject']}")
            if s["full_name"]:
                lines.append(f"             {s['full_name']}")
            if s["room"]:
                lines.append(f"             Room: {s['room']}")
            if s["faculty"]:
                lines.append(f"             Faculty: {s['faculty']}")
            lines.append("")

    lines.append("Generated by Maggie Scheduler Bot")
    return "\n".join(lines)
