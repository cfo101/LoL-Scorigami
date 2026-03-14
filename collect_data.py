import pandas as pd

df = pd.read_csv(
    r"C:\Users\carte\Downloads\2026_LoL_esports_match_data_from_OraclesElixir.csv",
    dtype=str
)

teams = df[df["position"] == "team"].copy()

# include result here
teams = teams[["gameid", "teamname", "side", "kills", "date", "league", "result"]]

teams["kills"] = pd.to_numeric(teams["kills"], errors="coerce")
teams["result"] = pd.to_numeric(teams["result"], errors="coerce")
df["date"] = pd.to_datetime(df["date"])

# sort for consistency
teams = teams.sort_values(["date", "gameid", "side"])

# collapse to one row per game
games = (
    teams.groupby(["gameid", "date", "league"])
    .agg({
        "kills": list,
        "teamname": list,
        "side": list,
        "result": list
    })
    .reset_index()
)

games = games.rename(columns={
    "kills": "kills_list",
    "teamname": "teams",
    "side": "sides",
    "result": "results"
})

# keep only proper 2-team games
games = games[games["kills_list"].apply(len) == 2].copy()

# split columns
games["kills_a"] = games["kills_list"].str[0]
games["kills_b"] = games["kills_list"].str[1]

games["team_a"] = games["teams"].str[0]
games["team_b"] = games["teams"].str[1]

games["result_a"] = games["results"].str[0]
games["result_b"] = games["results"].str[1]

# winner from result, not kills
games["winner"] = games.apply(
    lambda x: x["team_a"] if x["result_a"] == 1 else x["team_b"],
    axis=1
)

# normalized score for scorigami
games["score"] = games.apply(
    lambda x: tuple(sorted([x["kills_a"], x["kills_b"]], reverse=True)),
    axis=1
)

games = games.sort_values("date").reset_index(drop=True)

print(games.head())

seen_scores = set()
scorigami_flags = []

for score in games["score"]:
    if score not in seen_scores:
        scorigami_flags.append(True)
        seen_scores.add(score)
    else:
        scorigami_flags.append(False)

games["scorigami"] = scorigami_flags

print(games.head())
