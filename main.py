import os
import time
import requests
from dotenv import load_dotenv
import tweepy
from telegram import Bot
from datetime import datetime, timezone

load_dotenv()
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWITTER_USERNAMES = os.getenv("TWITTER_USERNAMES", "realDonaldTrump").split(",")

client = tweepy.Client(bearer_token=BEARER_TOKEN)
bot = Bot(token=TELEGRAM_TOKEN)
sent_tweet_ids = {u: set() for u in TWITTER_USERNAMES}
last_checked = {u: 0 for u in TWITTER_USERNAMES}
RATE_LIMIT_INTERVAL = 16 * 60  # 16 minutes

def get_today_tweets_with_media(username):
    try:
        user = client.get_user(username=username)
        user_id = user.data.id
        tweets = client.get_users_tweets(
            id=user_id,
            max_results=5,
            tweet_fields=["created_at", "text", "attachments", "referenced_tweets"],
            expansions=["attachments.media_keys"],
            media_fields=["url", "type", "preview_image_url"]
        )
        result = []
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
                result.append((tweet.id, tweet.text, media))
        return result
    except tweepy.errors.TooManyRequests as e:
        print(f"Rate limit hit for @{username}, waiting 16 minutes...")
        time.sleep(RATE_LIMIT_INTERVAL)
        return []
    except Exception as e:
        print(f"Error getting tweets for {username}: {e}")
        return []

while True:
    now = time.time()
    for username in TWITTER_USERNAMES:
        if now - last_checked[username] < RATE_LIMIT_INTERVAL:
            continue
        print(f"\n[+] Checking @{username} at {time.strftime('%H:%M:%S')}")
        todays_tweets = get_today_tweets_with_media(username)
        # Filter new tweets (not already sent)
        new_tweets = [t for t in todays_tweets if t[0] not in sent_tweet_ids[username]]
        if new_tweets:
            # Send from oldest to newest
            for tweet_id, tweet_text, media in reversed(new_tweets):
                msg = f"🕊️ @{username}:\n\n{tweet_text}\n\nhttps://twitter.com/{username}/status/{tweet_id}"
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
                print(f"Forwarded @{username}'s tweet: {tweet_id}")
                sent_tweet_ids[username].add(tweet_id)
        else:
            print(f"No new tweets for today from @{username}.")
        last_checked[username] = now
        time.sleep(2)  # Polite gap between accounts

    # Sleeping logic: Only sleep for single account, otherwise loop and catch due ones
    if len(TWITTER_USERNAMES) == 1:
        username = TWITTER_USERNAMES[0]
        now = time.time()
        time_to_wait = RATE_LIMIT_INTERVAL - (now - last_checked[username])
        if time_to_wait > 0:
            print(f"Sleeping {int(time_to_wait)} seconds before next check.")
            time.sleep(time_to_wait)
    else:
        # For multiple accounts, check again after a short delay to see if another is due
        time.sleep(10)
