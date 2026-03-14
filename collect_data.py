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
    lambda x: (int(x["kills_a"]), int(x["kills_b"])) if x["result_a"] == 1
              else (int(x["kills_b"]), int(x["kills_a"])),
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

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import mplcursors
from matplotlib.patches import Patch

MAX_KILLS = 70
grid = np.zeros((MAX_KILLS, MAX_KILLS), dtype=int)

for _, row in games.iterrows():
    w = int(row["score"][0])
    l = int(row["score"][1])
    if w < MAX_KILLS and l < MAX_KILLS:
        grid[w, l] += 1

cmap_data = [
    (0,   "#e8e8e0"),
    (1,   "#1d9e75"),
    (2,   "#5dcaa5"),
    (5,   "#9fe1cb"),
    (9,   "#b5d4f4"),
    (14,  "#378add"),
    (999, "#185fa5"),
]

def get_color(n):
    for threshold, color in reversed(cmap_data):
        if n >= threshold:
            return mcolors.to_rgba(color)
    return mcolors.to_rgba(cmap_data[0][1])

img = np.zeros((MAX_KILLS, MAX_KILLS, 4))
for w in range(MAX_KILLS):
    for l in range(MAX_KILLS):
        if grid[w, l] > 0:
            img[w, l] = get_color(grid[w, l])
        else:
            img[w, l] = mcolors.to_rgba("#e8e8e0")  # never seen, no transparency

img = np.flipud(img)

fig, ax = plt.subplots(figsize=(12, 10))
im = ax.imshow(img, aspect="equal", origin="upper",
               extent=[-0.5, MAX_KILLS - 0.5, -0.5, MAX_KILLS - 0.5])

ax.set_xlabel("Loser kills", fontsize=12)
ax.set_ylabel("Winner kills", fontsize=12)
ax.set_title("2026 LoL Pro Scorigami — kill score combinations", fontsize=14)
ax.set_xlim(-0.5, MAX_KILLS - 0.5)
ax.set_ylim(-0.5, MAX_KILLS - 0.5)

def hover_text(w, l):
    
    n = grid[w, l]
    if n == 0:
        return f"{w}–{l}\nNever happened"
    elif n == 1:
        return f"{w}–{l}\n1× — Scorigami!"
    else:
        return f"{w}–{l}\n{n} times"

cursor = mplcursors.cursor(im, hover=True)

def on_hover(sel):
    x, y = sel.target
    l = int(round(x))
    w = int(round(y))
    text = hover_text(w, l)
    if text:
        sel.annotation.set_text(text)
        sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)
    else:
        sel.annotation.set_visible(False)

cursor.connect("add", on_hover)
legend_elements = [
    Patch(facecolor="#1d9e75", label="1× (scorigami!)"),
    Patch(facecolor="#5dcaa5", label="2×"),
    Patch(facecolor="#9fe1cb", label="3–5×"),
    Patch(facecolor="#b5d4f4", label="6–9×"),
    Patch(facecolor="#378add", label="10–14×"),
    Patch(facecolor="#185fa5", label="15+×"),
    Patch(facecolor="#e8e8e0", label="Never seen"),
]
ax.legend(handles=legend_elements, loc="upper left", fontsize=9)

plt.tight_layout()
plt.savefig("scorigami_2026.png", dpi=150, bbox_inches="tight")
plt.show()