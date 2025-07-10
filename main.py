import os
from dotenv import load_dotenv
load_dotenv()

import time
import tweepy
from telegram import Bot
import requests
from datetime import datetime, timezone

BEARER_TOKEN = os.getenv("BEARER_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME", "realDonaldTrump")

client = tweepy.Client(bearer_token=BEARER_TOKEN)
bot = Bot(token=TELEGRAM_TOKEN)

def get_latest_tweet_with_media(username):
    user = client.get_user(username=username)
    user_id = user.data.id

    tweets = client.get_users_tweets(
        id=user_id,
        max_results=5,
        tweet_fields=["created_at", "text", "attachments", "referenced_tweets"],
        expansions=["attachments.media_keys"],
        media_fields=["url", "type", "preview_image_url"]
    )
    if tweets.data:
        now_utc = datetime.now(timezone.utc).date()
        for tweet in tweets.data:
            tweet_created_at = tweet.created_at.astimezone(timezone.utc).date()
            if tweet_created_at != now_utc:
                continue
            is_reply = False
            is_retweet = False
            if hasattr(tweet, "referenced_tweets") and tweet.referenced_tweets:
                for ref in tweet.referenced_tweets:
                    if ref.type == "retweeted":
                        is_retweet = True
                    if ref.type == "replied_to":
                        is_reply = True
            if is_retweet or is_reply:
                continue
            media = []
            if hasattr(tweets, "includes") and tweets.includes and "media" in tweets.includes:
                for m in tweets.includes["media"]:
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
            print("No new tweet for today (not retweet/reply).")
    except tweepy.errors.TooManyRequests:
        print("Twitter rate limit hit! Waiting 10 minutes...")
        time.sleep(600)
    except Exception as e:
        print("Error:", e)
    time.sleep(60)
