import pandas as pd
import ast
import os
import tweepy
from pathlib import Path

TIER1_PATH = "all_time_tier1.csv"
LAST_CHECKED_PATH = "last_checked.txt"
TWEETED_GAMES_PATH = "tweeted_games.txt"

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

# load already tweeted game IDs
if Path(TWEETED_GAMES_PATH).exists():
    with open(TWEETED_GAMES_PATH, "r") as f:
        tweeted_ids = set(f.read().splitlines())
else:
    tweeted_ids = set()

print(f"Already tweeted {len(tweeted_ids)} games")

# only look at games scraped in the last 24 hours to avoid processing entire history
recent_cutoff = pd.Timestamp.now() - pd.Timedelta(hours=24)
recent_games = tier1_games[tier1_games["scraped_at"] > recent_cutoff].copy()
new_games = recent_games[~recent_games["GameId"].isin(tweeted_ids)].copy()

print(f"New games found to tweet: {len(new_games)}")

if len(new_games) == 0:
    print("No new games to tweet.")
else:
    print(f"\nNew games:")
    for _, row in new_games.iterrows():
        w, l = row["score"]
        score_count = len(tier1_games[tier1_games["score"] == row["score"]])

        if row["scorigami"]:
            unique_score_count = tier1_games["score"].nunique()
            status = f"SCORIGAMI! That is the {unique_score_count}th unique score in Tier 1 League of Legends"
            tweet = (
                f"{row['Team1']} vs {row['Team2']} ({w}-{l})\n"
                f"SCORIGAMI! That is the {unique_score_count}th unique score in Tier 1 League of Legends 🎉"
            )
        else:
            status = f"No scorigami, that score has happened {score_count} times"
            tweet = (
                f"{row['Team1']} vs {row['Team2']} ({w}-{l})\n"
                f"No scorigami, that score has happened {score_count} times"
            )

        send_tweet(tweet)
        tweeted_ids.add(str(row["GameId"]))
        print(f"  {w}-{l} | {row['Tournament']} | {row['Team1']} vs {row['Team2']} | {row['DateTime UTC']} | {status}")

# save updated tweeted game IDs
with open(TWEETED_GAMES_PATH, "w") as f:
    f.write("\n".join(tweeted_ids))

print(f"\nTweeted games list updated: {len(tweeted_ids)} total")

# still update last_checked for reference
with open(LAST_CHECKED_PATH, "w") as f:
    f.write(str(pd.Timestamp.now()))

print(f"Last checked updated to: {pd.Timestamp.now()}")