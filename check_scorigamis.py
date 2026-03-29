import pandas as pd
import ast
import os
import tweepy
from pathlib import Path

TIER1_PATH = r"C:\Users\carte\Desktop\LOL Scorigami\all_time_tier1.csv"
LAST_CHECKED_PATH = r"C:\Users\carte\Desktop\LOL Scorigami\last_checked.txt"

# X/Twitter credentials from environment variables
client = tweepy.Client(
    consumer_key=os.environ.get("X_API_KEY"),
    consumer_secret=os.environ.get("X_API_SECRET"),
    access_token=os.environ.get("X_ACCESS_TOKEN"),
    access_token_secret=os.environ.get("X_ACCESS_SECRET")
)

def send_tweet(message):
    try:
        client.create_tweet(text=message)
        print(f"Tweeted: {message}")
    except Exception as e:
        print(f"Tweet failed: {e}")

# load tier1 data
tier1_games = pd.read_csv(TIER1_PATH)
tier1_games["score"] = tier1_games["score"].apply(ast.literal_eval)
tier1_games["DateTime UTC"] = pd.to_datetime(tier1_games["DateTime UTC"])
tier1_games["scraped_at"] = pd.to_datetime(tier1_games["scraped_at"])

# get last checked timestamp
if Path(LAST_CHECKED_PATH).exists():
    with open(LAST_CHECKED_PATH, "r") as f:
        last_checked = pd.Timestamp(f.read().strip())
    print(f"Last checked: {last_checked}")
else:
    last_checked = pd.Timestamp.now() - pd.Timedelta(minutes=30)
    print(f"No last_checked.txt found. Using 30 minute lookback: {last_checked}")

# find games that appeared in the dataset since last check
new_games = tier1_games[tier1_games["scraped_at"] > last_checked].copy()

print(f"New games found since last check: {len(new_games)}")

if len(new_games) == 0:
    print("No new games since last check.")
else:
    print(f"\nNew games:")
    for _, row in new_games.iterrows():
        w, l = row["score"]
        score_count = len(tier1_games[tier1_games["score"] == row["score"]])

        if row["scorigami"]:
            status = "SCORIGAMI! First time this score has ever happened"
            tweet = (
                f"SCORIGAMI! 🎉\n"
                f"{row['Team1']} vs {row['Team2']}\n"
                f"Final score: {w}-{l}\n"
                f"This kill score has never been seen before in Tier 1 LoL!\n"
                f"({row['Tournament']})"
            )
            send_tweet(tweet)
        else:
            status = f"Seen {score_count} times before"

        print(f"  {w}-{l} | {row['Tournament']} | {row['Team1']} vs {row['Team2']} | {row['DateTime UTC']} | {status}")

# update last checked timestamp
with open(LAST_CHECKED_PATH, "w") as f:
    f.write(str(pd.Timestamp.now()))

print(f"\nLast checked updated to: {pd.Timestamp.now()}")

send_tweet("LoL Scorigami bot is online! 🎉")
