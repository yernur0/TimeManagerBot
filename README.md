# Telegram Bot for Calendar Management

This repository contains a Telegram bot for calendar management, task planning, and productivity analysis. The bot allows users to add events and tasks, list them, remove them, and generate daily or weekly plans. 

## Features

- **Event Management**: Add, list, and remove events.
- **Task Management**: Add, list, and remove tasks.
- **Planning**: Generate daily and weekly plans.
- **User-friendly Input**: Date and time picker using inline keyboard for easy input.

## Requirements

- Python 3.6+
- `pyTelegramBotAPI`
- `sqlite3`

## Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/calendar-bot.git
    cd calendar-bot
    ```

2. Install dependencies:
    ```bash
    pip install pyTelegramBotAPI
    ```

3. Create a `config.py` file with your Telegram bot token:
    ```python
    token = 'YOUR_TELEGRAM_BOT_TOKEN'
    ```

4. Initialize the database:
    ```bash
    python bot.py
    ```

## Usage

1. Start the bot:
    ```bash
    python bot.py
    ```

2. Interact with the bot using the following commands:

    - `/start` - Start the bot and show the main menu.
    - `/help` - Show the help message with all available commands.
    - `/add_event` - Add an event.
    - `/list_events` - List all events.
    - `/remove_event <YYYY-MM-DD HH:MM>` - Remove an event.
    - `/add_task` - Add a task.
    - `/list_tasks` - List all tasks.
    - `/remove_task <ID>` - Remove a task by ID.
    - `/plan_day` - Generate a daily plan.
    - `/plan_week` - Generate a weekly plan.

## Code Overview

- `init_db()`: Initializes the SQLite database with tables for events and tasks.
- `start(message)`: Handles the `/start` command and shows the main menu.
- `help(message)`: Handles the `/help` command and shows the help message.
- `handle_callback_query(call)`: Handles inline keyboard callbacks for adding and listing events and tasks.
- `handle_message(message)`: Handles text messages for adding events and tasks.
- `show_date_picker(chat_id)`: Shows a date picker inline keyboard.
- `show_time_picker(chat_id, date_str)`: Shows a time picker inline keyboard.
- `process_event_description(message, date_str, time_str, event_desc)`: Processes the event description and saves the event to the database.
- `list_events(message)`: Lists all events.
- `process_remove_event(message)`: Processes the removal of an event.
- `process_add_task(message)`: Processes the addition of a task.
- `list_tasks(message)`: Lists all tasks.
- `process_remove_task(message)`: Processes the removal of a task.
- `plan_day(message)`: Generates a daily plan.
- `plan_week(message)`: Generates a weekly plan.
- `generate_plan(message, start_date, end_date)`: Generates a plan between the given start and end dates.
- `schedule_notification(chat_id, event_datetime, event_desc)`: Schedules a notification for an event or task.
- `send_notification(chat_id, event_desc)`: Sends a notification message.

