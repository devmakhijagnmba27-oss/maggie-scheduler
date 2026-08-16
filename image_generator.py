"""
Maggie Calendar Scheduler – Visual Timetable Card Generator
===========================================================
Renders a high-quality, modern dark-themed timetable image using Pillow.
The card is day-segmented with color-coded badges, rounded cards, and
a clean typographic layout suitable for sharing on Telegram.
"""

from __future__ import annotations

import math
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from config import CARD_STYLE, DAYS_ORDER
from filter_engine import group_by_day


# ── Font Loading ─────────────────────────────────────────

def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a font; fall back to the Pillow default if custom fonts unavailable."""
    # Try common system font paths (Windows)
    candidates = []
    if bold:
        candidates = [
            "C:/Windows/Fonts/segoeuib.ttf",    # Segoe UI Bold
            "C:/Windows/Fonts/arialbd.ttf",      # Arial Bold
            "C:/Windows/Fonts/calibrib.ttf",
        ]
    else:
        candidates = [
            "C:/Windows/Fonts/segoeui.ttf",      # Segoe UI
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
        ]

    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)

    # Fallback
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


# ── Drawing Helpers ──────────────────────────────────────

def _rounded_rect(draw: ImageDraw.Draw, xy: tuple, radius: int,
                  fill=None, outline=None, width: int = 0):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _pill_badge(draw: ImageDraw.Draw, xy: tuple, text: str,
                bg_color: tuple, text_color: tuple, font: ImageFont.FreeTypeFont,
                padding_x: int = 14, padding_y: int = 5):
    """Draw a small pill-shaped badge with text."""
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x, y = xy
    pill_w = tw + padding_x * 2
    pill_h = th + padding_y * 2
    _rounded_rect(draw, (x, y, x + pill_w, y + pill_h), radius=pill_h // 2, fill=bg_color)
    draw.text((x + padding_x, y + padding_y - 1), text, fill=text_color, font=font)
    return pill_w, pill_h


def _text_width(font: ImageFont.FreeTypeFont, text: str) -> int:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def _text_height(font: ImageFont.FreeTypeFont, text: str) -> int:
    bbox = font.getbbox(text)
    return bbox[3] - bbox[1]


# ── Main Generator ───────────────────────────────────────

def generate_schedule_image(filtered: list[dict]) -> BytesIO:
    """
    Generate a beautiful schedule card image from filtered schedule data.

    Parameters
    ----------
    filtered : list[dict]
        Output of filter_engine.filter_schedule().

    Returns
    -------
    BytesIO
        PNG image in a BytesIO buffer (seeked to 0).
    """
    S = CARD_STYLE
    grouped = group_by_day(filtered)

    # Fonts
    font_title = _load_font(S["font_title_size"], bold=True)
    font_day = _load_font(S["font_day_size"], bold=True)
    font_subject = _load_font(S["font_subject_size"], bold=True)
    font_detail = _load_font(S["font_detail_size"])
    font_badge = _load_font(S["font_detail_size"] - 2, bold=True)

    W = S["image_width"]
    pad = S["card_padding"]
    gap = S["card_gap"]
    card_r = S["card_radius"]

    # ── Phase 1: Measure height ──────────────────────────
    y_cursor = 0

    # Title area
    title_h = 90
    y_cursor += title_h + 20

    if not grouped:
        y_cursor += 120
    else:
        for day_idx, (day, slots) in enumerate(grouped.items()):
            # Day header
            y_cursor += 50 + gap

            for slot in slots:
                # Each class card
                card_content_h = 0
                card_content_h += _text_height(font_subject, slot["subject"]) + 6
                if slot["full_name"]:
                    card_content_h += _text_height(font_detail, slot["full_name"]) + 4
                # Badges row (time + room)
                card_content_h += 34
                if slot["faculty"]:
                    card_content_h += _text_height(font_detail, slot["faculty"]) + 4
                y_cursor += card_content_h + pad * 2 + gap

            y_cursor += 10  # section gap

    # Footer
    y_cursor += 50

    H = y_cursor + 20
    img = Image.new("RGB", (W, H), S["bg_color"])
    draw = ImageDraw.Draw(img)

    # ── Phase 2: Draw ────────────────────────────────────
    y = 0

    # ── Title Bar ──
    _rounded_rect(draw, (0, 0, W, title_h), radius=0, fill=S["header_bg"])

    # Gradient accent line at top
    for i in range(4):
        ratio = i / 3
        c = _lerp_color(S["accent_gradient"][0], S["accent_gradient"][1], ratio)
        draw.line([(0, i), (W, i)], fill=c, width=1)

    # Title text
    title_text = "📅  My Schedule"
    title_tw = _text_width(font_title, title_text)
    draw.text(((W - title_tw) // 2, (title_h - S["font_title_size"]) // 2),
              title_text, fill=S["text_primary"], font=font_title)

    y = title_h + 20

    if not grouped:
        # Empty state
        msg = "No classes found for your subjects!"
        msg_w = _text_width(font_day, msg)
        draw.text(((W - msg_w) // 2, y + 30), msg, fill=S["text_secondary"], font=font_day)
    else:
        content_left = 32
        content_right = W - 32

        for day_idx, (day, slots) in enumerate(grouped.items()):
            day_color = S["day_colors"][day_idx % len(S["day_colors"])]

            # ── Day Header ──
            # Day indicator bar
            draw.rounded_rectangle(
                (content_left, y, content_left + 6, y + 36),
                radius=3, fill=day_color,
            )
            draw.text((content_left + 18, y + 2), day.upper(),
                       fill=day_color, font=font_day)

            # Subtle line under day header
            y += 44
            draw.line([(content_left, y), (content_right, y)],
                      fill=(*day_color, 60) if len(day_color) == 3 else day_color, width=1)
            y += gap

            for slot in slots:
                # ── Class Card ──
                card_x0 = content_left + 12
                card_x1 = content_right

                # Measure card height
                card_content_h = 0
                card_content_h += _text_height(font_subject, slot["subject"]) + 6
                if slot["full_name"]:
                    card_content_h += _text_height(font_detail, slot["full_name"]) + 4
                card_content_h += 34  # badge row
                if slot["faculty"]:
                    card_content_h += _text_height(font_detail, slot["faculty"]) + 4

                card_h = card_content_h + pad * 2
                card_y0 = y
                card_y1 = y + card_h

                # Card background
                _rounded_rect(draw, (card_x0, card_y0, card_x1, card_y1),
                              radius=card_r, fill=S["card_bg"],
                              outline=S["card_border"], width=1)

                # Left accent strip on card
                draw.rounded_rectangle(
                    (card_x0, card_y0 + 8, card_x0 + 4, card_y1 - 8),
                    radius=2, fill=day_color,
                )

                cx = card_x0 + pad + 8  # content x start
                cy = card_y0 + pad

                # Subject code
                draw.text((cx, cy), slot["subject"],
                          fill=S["text_primary"], font=font_subject)
                cy += _text_height(font_subject, slot["subject"]) + 6

                # Full name
                if slot["full_name"]:
                    draw.text((cx, cy), slot["full_name"],
                              fill=S["text_secondary"], font=font_detail)
                    cy += _text_height(font_detail, slot["full_name"]) + 8

                # Badges row: time + room
                bx = cx
                if slot["time"]:
                    pw, ph = _pill_badge(draw, (bx, cy), f"🕐 {slot['time']}",
                                         S["time_badge_bg"], S["time_badge_text"], font_badge)
                    bx += pw + 10

                if slot["room"]:
                    _pill_badge(draw, (bx, cy), f"🏫 Room {slot['room']}",
                                S["room_badge_bg"], S["room_badge_text"], font_badge)

                cy += 34

                # Faculty
                if slot["faculty"]:
                    draw.text((cx, cy), f"👨‍🏫 {slot['faculty']}",
                              fill=S["faculty_tag"], font=font_detail)
                    cy += _text_height(font_detail, slot["faculty"]) + 4

                y = card_y1 + gap

            y += 10  # extra gap between days

    # ── Footer ──
    y += 10
    footer_text = "✨ Generated by Maggie Scheduler Bot"
    fw = _text_width(font_detail, footer_text)
    draw.text(((W - fw) // 2, y), footer_text, fill=S["text_secondary"], font=font_detail)

    # ── Save to buffer ──
    buf = BytesIO()
    img.save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf


def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    """Linearly interpolate between two RGB colors."""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))
