"""
Maggie Calendar Scheduler – Telegram Bot
=========================================
Interactive Telegram bot that:
  • Accepts timetable files (.xlsx, .xls, .pdf) and filters them
  • Manages the student's enrolled subject list
  • Returns a stunning visual schedule card + formatted text message

Commands:
  /start, /help           – Welcome & usage guide
  /mysubjects             – View current enrolled subjects
  /addsubject CODE [CODE] – Add one or more subjects
  /removesubject CODE     – Remove a subject
  /clearsubjects          – Clear all subjects
  /setsubjects CODE,CODE  – Set subjects (comma-separated)
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN, load_user_subjects, save_user_subjects
from parser import parse_timetable, parse_electives_pdf
from filter_engine import filter_schedule, format_text_schedule
from image_generator import generate_schedule_image

# ── Logging ──────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── Command Handlers ─────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Send welcome message."""
    subjects = load_user_subjects()
    subj_text = ", ".join(subjects) if subjects else "_None set yet_"

    await update.message.reply_text(
        "👋 *Welcome to Maggie Scheduler Bot!*\n\n"
        "I filter your weekly college timetable to show only *your* classes "
        "with room numbers and faculty names.\n\n"
        "*How to use:*\n"
        "1️⃣  Set your subjects:\n"
        "   `/setsubjects B2B, DSMM, CB, PBM, DDM, EI`\n\n"
        "2️⃣  Send me your timetable file (`.xlsx`, `.xls`, or `.pdf`)\n\n"
        "3️⃣  I'll reply with your filtered schedule! 🎉\n\n"
        f"📋 *Your current subjects:* {subj_text}\n\n"
        "*Commands:*\n"
        "/mysubjects – View subjects\n"
        "/addsubject – Add subjects\n"
        "/removesubject – Remove a subject\n"
        "/setsubjects – Set all subjects at once\n"
        "/clearsubjects – Clear subjects\n"
        "/help – Show this message",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Alias for /start."""
    await cmd_start(update, ctx)


async def cmd_my_subjects(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Show currently enrolled subjects."""
    subjects = load_user_subjects()
    if subjects:
        formatted = "\n".join(f"  • `{s}`" for s in subjects)
        await update.message.reply_text(
            f"📋 *Your enrolled subjects:*\n{formatted}\n\n"
            "Use /addsubject or /removesubject to modify.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "📭 You haven't set any subjects yet.\n"
            "Use `/setsubjects B2B, DSMM, CB` to set them.",
            parse_mode="Markdown",
        )


async def cmd_add_subject(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Add one or more subjects."""
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "Usage: `/addsubject B2B DSMM CB`",
            parse_mode="Markdown",
        )
        return

    subjects = load_user_subjects()
    added = []
    for code in args:
        code = code.strip().upper().replace(",", "")
        if code and code not in subjects:
            subjects.append(code)
            added.append(code)
    save_user_subjects(subjects)

    if added:
        await update.message.reply_text(
            f"✅ Added: {', '.join(f'`{s}`' for s in added)}\n"
            f"📋 Total subjects: {len(subjects)}",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("All subjects already in your list! ✨")


async def cmd_remove_subject(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Remove one or more subjects."""
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "Usage: `/removesubject B2B`",
            parse_mode="Markdown",
        )
        return

    subjects = load_user_subjects()
    removed = []
    for code in args:
        code = code.strip().upper().replace(",", "")
        if code in subjects:
            subjects.remove(code)
            removed.append(code)
    save_user_subjects(subjects)

    if removed:
        await update.message.reply_text(
            f"🗑️ Removed: {', '.join(f'`{s}`' for s in removed)}\n"
            f"📋 Remaining subjects: {len(subjects)}",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("Those subjects weren't in your list.")


async def cmd_set_subjects(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Set subjects (comma or space separated)."""
    if not ctx.args:
        await update.message.reply_text(
            "Usage: `/setsubjects B2B, DSMM, CB, PBM, DDM, EI`",
            parse_mode="Markdown",
        )
        return

    raw = " ".join(ctx.args)
    codes = [c.strip().upper() for c in raw.replace(",", " ").split() if c.strip()]
    codes = list(dict.fromkeys(codes))  # deduplicate preserving order
    save_user_subjects(codes)

    formatted = ", ".join(f"`{c}`" for c in codes)
    await update.message.reply_text(
        f"✅ Subjects set!\n📋 {formatted}\n\n"
        "Now send me your timetable file to get your filtered schedule! 📤",
        parse_mode="Markdown",
    )


async def cmd_clear_subjects(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Clear all subjects."""
    save_user_subjects([])
    await update.message.reply_text(
        "🗑️ All subjects cleared.\nUse /setsubjects to set new ones.",
        parse_mode="Markdown",
    )


# ── File Handler ─────────────────────────────────────────

async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Process an uploaded timetable or elective-choice file."""
    document = update.message.document
    if not document:
        return

    file_name = document.file_name or "file"
    ext = Path(file_name).suffix.lower()

    if ext not in (".xlsx", ".xls", ".pdf"):
        await update.message.reply_text(
            "⚠️ Unsupported file type. Please send a `.xlsx`, `.xls`, or `.pdf` file.",
            parse_mode="Markdown",
        )
        return

    subjects = load_user_subjects()
    if not subjects:
        await update.message.reply_text(
            "⚠️ *No subjects configured!*\n\n"
            "Set your subjects first:\n"
            "`/setsubjects B2B, DSMM, CB, PBM, DDM, EI`\n\n"
            "Or send me your elective-choice PDF by typing:\n"
            "`/help`",
            parse_mode="Markdown",
        )
        return

    # Download file
    processing_msg = await update.message.reply_text("⏳ Processing your timetable...")

    try:
        tg_file = await document.get_file()
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp_path = tmp.name
            await tg_file.download_to_drive(tmp_path)

        # Parse
        parsed = parse_timetable(tmp_path)

        if not parsed["slots"]:
            await processing_msg.edit_text(
                "⚠️ *Couldn't extract timetable data from this file.*\n\n"
                "Make sure the file contains a timetable grid with:\n"
                "• Day names (Monday, Tuesday, etc.)\n"
                "• Time slots (e.g. 10:20-11:35)\n"
                "• Subject codes in the cells",
                parse_mode="Markdown",
            )
            return

        # Filter
        filtered = filter_schedule(parsed, subjects)

        if not filtered:
            all_entries = set()
            for slot in parsed["slots"]:
                all_entries.update(slot["entries"])

            await processing_msg.edit_text(
                f"📭 *No matching classes found!*\n\n"
                f"Your subjects: {', '.join(f'`{s}`' for s in subjects)}\n\n"
                f"Subjects found in timetable:\n"
                f"{', '.join(f'`{e}`' for e in sorted(all_entries)[:30])}\n\n"
                "Check if your subject codes match. Use /setsubjects to update.",
                parse_mode="Markdown",
            )
            return

        # Generate outputs
        # 1. Text message
        text_msg = format_text_schedule(filtered)

        # 2. Image card
        img_buf = generate_schedule_image(filtered)

        # Send image
        await update.message.reply_photo(
            photo=img_buf,
            caption="📅 Your filtered weekly schedule!",
        )

        # Send text
        await update.message.reply_text(text_msg, parse_mode="Markdown")

        # Clean up processing message
        await processing_msg.delete()

        # Stats
        day_count = len(set(s["day"] for s in filtered))
        await update.message.reply_text(
            f"✅ Found *{len(filtered)} classes* across *{day_count} days* "
            f"from your {len(subjects)} enrolled subjects.",
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        await processing_msg.edit_text(
            f"❌ *Error processing file:*\n`{str(e)[:200]}`\n\n"
            "Please check the file format and try again.",
            parse_mode="Markdown",
        )
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ── Main ─────────────────────────────────────────────────

def main():
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("=" * 60)
        print("ERROR: Telegram Bot Token not configured!")
        print()
        print("Steps to fix:")
        print("1. Open Telegram and search for @BotFather")
        print("2. Send /newbot and follow the prompts")
        print("3. Copy the token BotFather gives you")
        print("4. Create a .env file in this directory:")
        print("   TELEGRAM_BOT_TOKEN=your_token_here")
        print("=" * 60)
        return

    print("🚀 Starting Maggie Scheduler Bot...")
    print("   Press Ctrl+C to stop.\n")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("mysubjects", cmd_my_subjects))
    app.add_handler(CommandHandler("addsubject", cmd_add_subject))
    app.add_handler(CommandHandler("removesubject", cmd_remove_subject))
    app.add_handler(CommandHandler("setsubjects", cmd_set_subjects))
    app.add_handler(CommandHandler("clearsubjects", cmd_clear_subjects))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Start polling
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
