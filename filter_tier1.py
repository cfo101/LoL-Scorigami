import pandas as pd
import ast

all_games = pd.read_csv(r"C:\Users\carte\Desktop\LOL Scorigami\all_time_all_leagues.csv")

# filter to tier1 games based on tournament name, excluding certain keywords. As time progresses tier one leagues may change, but these are what have been chosen for now.
tier1_keywords = [
    "LCK", "LPL", "LEC", "LCS", "LCP",
    "CBLOL", "MSI", "Worlds",
    "First Stand" 
]

exclude_keywords = [
    "Academy", "Challengers", "CL", "AS ",
    "2nd Division", "Promotion", "LDL", "LSPL",
    "NA Academy", "EU LCS Academy", "LPLOL",
    "Proving Grounds", "Fan Clash", "All-Star",
    "Rift Rivals", "Game Changers", "LJL", "VCS"
]

def is_tier1(tournament):
    if pd.isna(tournament):
        return False
    has_tier1 = any(kw in tournament for kw in tier1_keywords)
    is_excluded = any(kw in tournament for kw in exclude_keywords)
    return has_tier1 and not is_excluded

tier1_games = all_games[all_games["Tournament"].apply(is_tier1)].copy()
tier1_games = tier1_games.reset_index(drop=True)

tier1_games["score"] = tier1_games["score"].apply(ast.literal_eval)
score_counts = tier1_games["score"].value_counts()
tier1_games["scorigami"] = tier1_games["score"].map(score_counts) == 1

print(f"Total tier1 games: {len(tier1_games)}")
print(f"Unique scores: {tier1_games['score'].nunique()}")
print(f"True scorigamis: {tier1_games['scorigami'].sum()}")

tier1_games.to_csv(r"C:\Users\carte\Desktop\LOL Scorigami\all_time_tier1.csv", index=False)
print("Saved to all_time_tier1.csv")