import time
import tweepy
from telegram import Bot
import requests
from datetime import datetime, timezone

# ======= CONFIGURATION =======
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAEv12wEAAAAAG%2FeahYsrkvmLB2Q%2FiacOtahNggc%3DEr5Bdn3na5TtieUQtofk7pCHV3sq7vKF8zY141UuJ3gcAt5Jkq"
TELEGRAM_TOKEN = "8055180447:AAF_LoJDDCw7labMmDaPisIJMt1OHqNR3KQ"
TELEGRAM_CHAT_ID = "-1002723931406"  # e.g. -100xxxxxxxxx
TWITTER_USERNAME = "realDonaldTrump"

client = tweepy.Client(bearer_token=BEARER_TOKEN)
bot = Bot(token=TELEGRAM_TOKEN)

def get_latest_tweet_with_media(username):
    user = client.get_user(username=username)
    user_id = user.data.id

    # Get tweets with creation date and media fields
    tweets = client.get_users_tweets(
        id=user_id,
        max_results=5,
        tweet_fields=["created_at", "text", "attachments"],
        expansions=["attachments.media_keys"],
        media_fields=["url", "type", "preview_image_url"]
    )
    if tweets.data:
        # Go through all tweets, look for today's only
        now_utc = datetime.now(timezone.utc).date()
        for tweet in tweets.data:
            tweet_created_at = tweet.created_at.astimezone(timezone.utc).date()
            if tweet_created_at == now_utc:
                media = []
                # Look up media attachments if present
                if hasattr(tweets, "includes") and tweets.includes and "media" in tweets.includes:
                    for m in tweets.includes["media"]:
                        # Is this media attached to this tweet?
                        if "attachments" in tweet.data and "media_keys" in tweet.data["attachments"]:
                            if m.media_key in tweet.data["attachments"]["media_keys"]:
                                media.append(m)
                return tweet.text, tweet.id, media
    return None, None, []

last_tweet_id = None

while True:
    try:
        tweet, tweet_id, media = get_latest_tweet_with_media(TWITTER_USERNAME)
        if tweet_id and tweet_id != last_tweet_id:
            msg = f"🕊️ @{TWITTER_USERNAME}:\n\n{tweet}\n\nhttps://twitter.com/{TWITTER_USERNAME}/status/{tweet_id}"
            sent = False
            if media:
                for m in media:
                    if m.type == "photo":
                        image_url = m.url
                        image_data = requests.get(image_url).content
                        bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=image_data, caption=msg if not sent else None)
                        sent = True
                    elif m.type == "video":
                        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"{msg}\n\n[Video Tweet: Open in Twitter]")
                        sent = True
                    elif m.type == "animated_gif":
                        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"{msg}\n\n[GIF Tweet: Open in Twitter]")
                        sent = True
            if not sent:
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
            print(f"Forwarded Trump tweet: {tweet_id}")
            last_tweet_id = tweet_id
        else:
            print("No new tweet for today.")
    except tweepy.errors.TooManyRequests:
        print("Twitter rate limit hit! Waiting 10 minutes...")
        time.sleep(600)
    except Exception as e:
        print("Error:", e)
    time.sleep(60)  # Check every minute
