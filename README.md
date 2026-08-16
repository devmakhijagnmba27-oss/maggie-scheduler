# 📅 Maggie Calendar Scheduler – Telegram Bot

A smart Telegram bot that filters your weekly college timetable based on your enrolled subjects, and sends you a **beautifully designed schedule card** with classroom numbers and faculty names.

---

## ✨ Features

- 📤 **Send your timetable** (`.xlsx`, `.xls`, or `.pdf`) directly in Telegram chat
- 🎯 **Auto-filters** classes to show only your enrolled subjects
- 🏫 **Room numbers** and 👨‍🏫 **faculty names** included for every class
- 🖼️ **Gorgeous visual card** – dark-themed, color-coded by day
- 📱 **Clean text message** – organized day-by-day with emojis
- ⚡ **Subject management** – add/remove subjects via bot commands

---

## 🚀 Quick Setup

### 1. Create Your Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name (e.g., "Maggie Scheduler")
4. Choose a username (e.g., `maggie_scheduler_bot`)
5. **Copy the token** BotFather gives you

### 2. Configure the Bot

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and paste your token
# TELEGRAM_BOT_TOKEN=your_token_here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Bot

```bash
python bot.py
```

---

## 💬 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message & instructions |
| `/help` | Show help |
| `/mysubjects` | View your enrolled subjects |
| `/setsubjects B2B, DSMM, CB, PBM` | Set all subjects at once |
| `/addsubject B2B` | Add a subject |
| `/removesubject WM` | Remove a subject |
| `/clearsubjects` | Remove all subjects |

### Usage Flow

1. **Set your subjects**: `/setsubjects B2B, DSMM, CB, PBM, DDM, EI`
2. **Upload your timetable**: Send the `.xlsx` or `.pdf` file in chat
3. **Get your schedule**: Bot replies with a visual card + text summary! 🎉

---

## 📁 Project Structure

```
Maggie-Calendar-Scheduler/
├── bot.py              # Telegram bot entry point
├── config.py           # Configuration & styling
├── parser.py           # Timetable & elective PDF parser
├── filter_engine.py    # Subject matching & filtering
├── image_generator.py  # Visual schedule card renderer
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── .env                # Your actual config (create this)
└── user_data/          # Persisted subject list
    └── my_subjects.txt
```

---

## 🎨 Output Preview

The bot sends two types of responses:

1. **Visual Card** – A stunning dark-themed image with:
   - Color-coded day sections (purple, blue, green, orange, rose, teal)
   - Pill badges for time slots and room numbers
   - Faculty names in warm amber
   - Clean modern typography

2. **Text Message** – A clean, formatted message like:
   ```
   🟣 MONDAY
   ────────────────────────
     🕐 10:20-11:35
     📘 B2B (Business to Business Marketing)
     🏫 Room 302
     👨‍🏫 Dr. Pratigya Kwatra
   ```
