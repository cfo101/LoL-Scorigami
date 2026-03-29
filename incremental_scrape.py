import requests
import pandas as pd
import time
import datetime
import os

SAVE_PATH = "all_time_all_leagues.csv"
BUFFER_DAYS = 1


def query_leaguepedia(params):
    url = "https://lol.fandom.com/api.php"
    base_params = {
        "action": "cargoquery",
        "format": "json",
        "limit": "500",
    }
    base_params.update(params)

    response = requests.get(url, params=base_params, timeout=30)
    data = response.json()

    if "cargoquery" not in data:
        print(f"Unexpected response: {data}")
        return None

    return data["cargoquery"]


def query_all(params):
    all_results = []
    offset = 0

    while True:
        current_params = params.copy()
        current_params["offset"] = offset

        while True:
            results = query_leaguepedia(current_params)
            if results is None:
                print("Rate limited or bad response, waiting 30 seconds...")
                time.sleep(30)
            else:
                break

        all_results.extend(results)
        print(f"  fetched {len(all_results)} rows so far...")

        if len(results) < 500:
            break

        offset += 500
        time.sleep(3)

    return all_results


def parse_gamelength(gl):
    try:
        parts = gl.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return None


def clean_df(df):
    df = df.copy()

    df["Team1Kills"] = pd.to_numeric(df["Team1Kills"], errors="coerce")
    df["Team2Kills"] = pd.to_numeric(df["Team2Kills"], errors="coerce")
    df["DateTime UTC"] = pd.to_datetime(df["DateTime UTC"], errors="coerce")

    df["gamelength_seconds"] = df["Gamelength"].apply(parse_gamelength)

    # filter out remakes / bad rows. games shouldnt end before 9 minutes so this should be safe
    df = df[df["gamelength_seconds"] > 900].copy()
    df = df.dropna(subset=["Team1Kills", "Team2Kills", "Winner", "DateTime UTC"]).copy()

    def build_score(row):
        t1k = int(row["Team1Kills"])
        t2k = int(row["Team2Kills"])
        return (t1k, t2k) if str(row["Winner"]) == "1" else (t2k, t1k)

    df["score"] = df.apply(build_score, axis=1)

    df = df.sort_values(["DateTime UTC", "GameId"]).reset_index(drop=True)

    # recompute all-time frequency across the FULL combined dataset
    score_counts = df["score"].value_counts()
    df["scorigami"] = df["score"].map(score_counts) == 1
    
    

    return df


def fetch_all_games():
    print("Scraping all historical games...")

    results = query_all({
        "tables": "ScoreboardGames",
        "fields": "GameId, Tournament, Team1, Team2, Team1Kills, Team2Kills, Winner, DateTime_UTC=DateTime UTC, Gamelength",
        "orderby": "DateTime_UTC"
    })

    rows = [r["title"] for r in results]
    df = pd.DataFrame(rows)

    print(f"Total games fetched: {len(df)}")
    return df


def fetch_new_games(latest_dt):
    buffer_dt = latest_dt - pd.Timedelta(days=BUFFER_DAYS)
    buffer_dt_str = buffer_dt.strftime("%Y-%m-%d %H:%M:%S")

    print(f"Latest stored game: {latest_dt}")
    print(f"Using {BUFFER_DAYS}-day buffer. Scraping games after: {buffer_dt_str}")

    results = query_all({
        "tables": "ScoreboardGames",
        "fields": "GameId, Tournament, Team1, Team2, Team1Kills, Team2Kills, Winner, DateTime_UTC=DateTime UTC, Gamelength",
        "where": f"DateTime_UTC >= '{buffer_dt_str}'",
        "orderby": "DateTime_UTC"
    })

    rows = [r["title"] for r in results]
    df = pd.DataFrame(rows)

    print(f"Rows fetched with buffer: {len(df)}")
    return df


# -----------------------------
# MAIN LOGIC
# -----------------------------

if os.path.exists(SAVE_PATH):
    print("Existing file found. Loading old data...")
    existing_df = pd.read_csv(SAVE_PATH)

    existing_df["DateTime UTC"] = pd.to_datetime(existing_df["DateTime UTC"], errors="coerce")
    
    # preserve existing scraped_at if it exists
    if "scraped_at" not in existing_df.columns:
        existing_df["scraped_at"] = pd.NaT

    latest_dt = existing_df["DateTime UTC"].max()

    if pd.isna(latest_dt):
        print("Could not read latest date from existing file. Rebuilding from scratch...")
        raw_df = fetch_all_games()
        clean_full_df = clean_df(raw_df)
        clean_full_df["scraped_at"] = datetime.datetime.now()
        clean_full_df.to_csv(SAVE_PATH, index=False)
        print(f"Saved rebuilt dataset to: {SAVE_PATH}")
    else:
        new_df = fetch_new_games(latest_dt)

        if new_df.empty:
            print("No rows returned from incremental scrape.")
        else:
            # stamp only the new rows before combining
            new_df["scraped_at"] = datetime.datetime.now()

            combined_df = pd.concat([existing_df, new_df], ignore_index=True)

            # deduplicate by GameId — keep "last" so new scraped_at wins for updated rows
            combined_df = combined_df.drop_duplicates(subset=["GameId"], keep="last")

            clean_full_df = clean_df(combined_df)
            clean_full_df.to_csv(SAVE_PATH, index=False)

            print(f"Updated file saved to: {SAVE_PATH}")
            print(f"Total games after update: {len(clean_full_df)}")
            print(f"Unique scores: {clean_full_df['score'].nunique()}")
            print(f"Scorigami games: {clean_full_df['scorigami'].sum()}")

else:
    print("No existing file found.")
    raw_df = fetch_all_games()
    clean_full_df = clean_df(raw_df)
    clean_full_df["scraped_at"] = datetime.datetime.now()
    clean_full_df.to_csv(SAVE_PATH, index=False)

    print(f"Saved full dataset to: {SAVE_PATH}")
    print(f"Total games: {len(clean_full_df)}")
    print(f"Unique scores: {clean_full_df['score'].nunique()}")
    print(f"Scorigami games: {clean_full_df['scorigami'].sum()}")