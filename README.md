# Twitter-to-Telegram Forwarder Bot

Automatically forward tweets (including images, videos, and links) from any number of Twitter accounts to your Telegram channel or group.

---

## Features

- Monitor multiple Twitter accounts
- Sends images, videos, and tweet text to Telegram
- Removes Twitter media links for a clean look
- Formats real web links as clickable Markdown
- Prevents duplicate forwards (per session)
- Safe for the free Twitter API

---

## Quick Start

1. **Clone this repository:**
git clone https://github.com/yourusername/twitter-to-telegram-bot.git
cd twitter-to-telegram-bot****

2. **Create a `.env` file** in the root folder with your API credentials:

BEARER_TOKEN=your_twitter_bearer_token
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
TWITTER_USERNAMES=realDonaldTrump,gboy31202,another_username

3. **Install dependencies:**
pip install -r requirements.txt

4. **Run the bot:**
python twitter_to_telegram_bot.py
