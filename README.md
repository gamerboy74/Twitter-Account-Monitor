# 🐦 Twitter to Telegram Forwarder Bot

A powerful async-based bot that automatically monitors tweets from selected Twitter accounts and forwards them to a Telegram channel — **with image support, markdown formatting, and media filtering.**

---

## ✨ Features

- 📡 **Auto Fetch Tweets**: Monitors specified usernames every ~16 minutes
- 🧠 **Smart Filtering**: Skips replies and retweets, only fetches original posts
- 🖼️ **Media Support**: Supports tweets with photos, videos, and GIFs
- 🧹 **Cleaned Tweet Text**: Removes t.co clutter and media links, formats real URLs
- 🛡️ **Rate Limit Aware**: Avoids hitting Twitter API rate limits
- 📆 **Today-Only Filter**: Ignores tweets not created today
- ⚙️ **Async + Fast**: Built with `httpx`, `tweepy`, `python-telegram-bot`, and asyncio

---

## 🚀 Quick Start

### 📦 Requirements

- Python 3.8+
- Telegram Bot Token
- Twitter Developer Account (Bearer Token)

### 🛠️ Installation

```bash
git clone https://github.com/your-username/twitter-to-telegram-forwarder.git
cd twitter-to-telegram-forwarder

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🔧 Environment Variables

Create a `.env` file in the root directory:

```env
BEARER_TOKEN=your_twitter_bearer_token
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=@your_channel_or_group_id
TWITTER_USERNAMES=elonmusk,coinbase,binance  # comma-separated Twitter usernames
```

---

## ▶️ Run the Bot

```bash
python main.py
```

Bot will continuously check tweets and forward new ones to your Telegram channel or group.

---

## 📁 Project Structure

```
twitter-to-telegram-forwarder/
├── main.py              # Main bot script
├── requirements.txt     # Python dependencies
├── .env                 # Environment config (not committed)
```

---

## 💡 How It Works

1. Fetches user ID from username using Twitter API
2. Filters tweets by today's date
3. Excludes retweets and replies
4. Forwards original tweets (with photo/media support) to Telegram
5. Keeps track of sent tweet IDs to prevent duplicates

---

## 🧪 Testing

1. Run the script and ensure your `.env` is correctly set
2. Post a new tweet from a watched user
3. Check if it appears in your Telegram group/channel

---

## 🛡️ Security & Stability

- Uses `.env` for secrets
- Implements retry + timeout for Twitter media fetches
- Rate-limit safe (waits 16 min between user checks)
- Clean Markdown formatting with escaped links

---

## 📄 License

Licensed under the MIT License.

---

## 🙏 Acknowledgements

- [Tweepy](https://github.com/tweepy/tweepy)
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [httpx](https://www.python-httpx.org/)
