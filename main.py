import os
import time
import httpx
import asyncio
import re
from dotenv import load_dotenv
import tweepy
from telegram import Bot
from datetime import datetime, timezone

# === Load Config ===
load_dotenv()
BEARER_TOKEN      = os.getenv("BEARER_TOKEN")
TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID")
TWITTER_USERNAMES = os.getenv("TWITTER_USERNAMES").split(",")

client = tweepy.Client(bearer_token=BEARER_TOKEN)
bot = Bot(token=TELEGRAM_TOKEN)
sent_tweet_ids = {u: set() for u in TWITTER_USERNAMES}
last_checked   = {u: 0 for u in TWITTER_USERNAMES}
RATE_LIMIT_INTERVAL = 16 * 60  # 16 minutes

# === Utility: Download Images Asynchronously ===
async def download_image_async(url):
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content

# === Clean and Format Tweet Text ===
def clean_and_format_tweet_text(tweet, media):
    """Removes t.co media links & /photo/1; formats real links as [View Link](url) Markdown."""
    text = tweet.text
    if hasattr(tweet, "entities") and tweet.entities and "urls" in tweet.entities:
        for url_obj in tweet.entities["urls"]:
            url = url_obj["url"]
            expanded_url = url_obj.get("expanded_url", url)
            # Remove media links (t.co pointing to twitter.com/media, /photo/1, or pbs.twimg)
            is_media_link = False
            if (expanded_url.startswith("https://twitter.com") or
                expanded_url.startswith("https://pbs.twimg.com") or
                "/photo/" in expanded_url or
                "/video/" in expanded_url):
                is_media_link = True
            if is_media_link:
                text = text.replace(url, "")
            else:
                label = "View Link"
                markdown_link = f"[{label}]({expanded_url})"
                text = text.replace(url, markdown_link)
    # Clean up extra spaces and newlines
    text = re.sub(r'\s+\n', '\n', text).strip()
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# === Fetch Today's Tweets with Media ===
def get_today_tweets_with_media(username):
    try:
        user = client.get_user(username=username)
        user_id = user.data.id
        tweets = client.get_users_tweets(
            id=user_id,
            max_results=5,
            tweet_fields=["created_at", "text", "attachments", "referenced_tweets", "entities"],
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
                result.append((tweet, tweet.id, media))
        return result
    except tweepy.errors.TooManyRequests:
        print(f"Rate limit hit for @{username}, waiting 16 minutes...")
        time.sleep(RATE_LIMIT_INTERVAL)
        return []
    except Exception as e:
        print(f"Error getting tweets for {username}: {e}")
        return []

# === Main Async Loop ===
async def main():
    while True:
        now = time.time()
        for username in TWITTER_USERNAMES:
            if now - last_checked[username] < RATE_LIMIT_INTERVAL:
                continue
            print(f"\n[+] Checking @{username} at {time.strftime('%H:%M:%S')}")
            todays_tweets = get_today_tweets_with_media(username)
            # Only send new tweets (not already sent)
            new_tweets = [t for t in todays_tweets if t[1] not in sent_tweet_ids[username]]
            if new_tweets:
                for tweet, tweet_id, media in reversed(new_tweets):
                    cleaned_text = clean_and_format_tweet_text(tweet, media)
                    caption = (
                        f"🧑‍💻 *{username}* just tweeted:\n\n"
                        f"{cleaned_text}\n\n"
                        f"🔗 [View on Twitter](https://twitter.com/{username}/status/{tweet_id})"
                    )
                    sent = False
                    if media:
                        for m in media:
                            if m.type == "photo":
                                try:
                                    image_data = await download_image_async(m.url)
                                    await bot.send_photo(
                                        chat_id=TELEGRAM_CHAT_ID,
                                        photo=image_data,
                                        caption=caption,
                                        parse_mode="Markdown"
                                    )
                                    sent = True
                                except Exception as ex:
                                    print(f"Failed to send image: {ex}")
                            elif m.type == "video":
                                await bot.send_message(
                                    chat_id=TELEGRAM_CHAT_ID,
                                    text=f"{caption}\n\n[Video Tweet: Open in Twitter]",
                                    parse_mode="Markdown"
                                )
                                sent = True
                            elif m.type == "animated_gif":
                                await bot.send_message(
                                    chat_id=TELEGRAM_CHAT_ID,
                                    text=f"{caption}\n\n[GIF Tweet: Open in Twitter]",
                                    parse_mode="Markdown"
                                )
                                sent = True
                    if not sent:
                        await bot.send_message(
                            chat_id=TELEGRAM_CHAT_ID,
                            text=caption,
                            parse_mode="Markdown"
                        )
                    print(f"Forwarded @{username}'s tweet: {tweet_id}")
                    sent_tweet_ids[username].add(tweet_id)
            else:
                print(f"No new tweets for today from @{username}.")
            last_checked[username] = now
            await asyncio.sleep(2)

        # Sleep logic for free API safety
        if len(TWITTER_USERNAMES) == 1:
            username = TWITTER_USERNAMES[0]
            now = time.time()
            time_to_wait = RATE_LIMIT_INTERVAL - (now - last_checked[username])
            if time_to_wait > 0:
                print(f"Sleeping {int(time_to_wait)} seconds before next check.")
                await asyncio.sleep(time_to_wait)
        else:
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
