import pandas as pd
import streamlit as st


# --- 1. The Core Analysis Logic (Slightly Updated) ---
def analyze_opening_performance(
    games_df: pd.DataFrame, moves_df: pd.DataFrame, username: str
) -> pd.DataFrame:
    user_games = games_df[
        (games_df["white"] == username) | (games_df["black"] == username)
    ].copy()
    if user_games.empty:
        return pd.DataFrame()

    user_games["user_color"] = user_games.apply(
        lambda row: "White" if row["white"] == username else "Black", axis=1
    )

    opening_moves = moves_df[
        (moves_df["ply"] <= 30) & (moves_df["eval_cp"].notna())
    ].copy()
    opening_moves = opening_moves.merge(
        user_games[["game_id", "opening", "user_color"]], on="game_id", how="inner"
    )

    first_evals = opening_moves.groupby("game_id").first().reset_index()
    last_evals = opening_moves.groupby("game_id").last().reset_index()

    eval_shifts = pd.merge(
        first_evals[["game_id", "opening", "user_color", "eval_cp"]],
        last_evals[["game_id", "eval_cp"]],
        on="game_id",
        suffixes=("_start", "_end"),
    )

    eval_shifts["advantage_shift"] = eval_shifts.apply(
        lambda row: (
            row["eval_cp_end"] - row["eval_cp_start"]
            if row["user_color"] == "White"
            else row["eval_cp_start"] - row["eval_cp_end"]
        ),
        axis=1,
    )

    opening_stats = (
        eval_shifts.groupby("opening")
        .agg(
            games_played=("game_id", "count"),
            avg_advantage_shift=("advantage_shift", "mean"),
        )
        .reset_index()
    )

    # We remove the hardcoded filter here so Streamlit can control it dynamically
    return opening_stats


# --- 2. The Streamlit UI ---
st.set_page_config(page_title="Chess Repertoire Analyzer", layout="wide")

st.title("♟️ Repertoire & Performance Analyzer")

# --- Dynamic Sidebar Controls ---
st.sidebar.header("Filters & Settings")
username = st.sidebar.text_input("Username", value="MasterOfSkillIssues")

# This is the magic slider that fixes your edge case problem
min_games = st.sidebar.slider(
    "Minimum Games Played",
    min_value=1,
    max_value=100,
    value=15,
    help="Increase this to filter out rare openings and one-off gambits.",
)

# A toggle to isolate gambits
focus_gambits = st.sidebar.checkbox("🔪 Isolate Gambits Only")


@st.cache_data
def load_data():
    try:
        games = pd.read_csv("games.csv")
        moves = pd.read_csv("moves.csv")
        return games, moves
    except FileNotFoundError:
        st.error("Data files not found.")
        return pd.DataFrame(), pd.DataFrame()


games_df, moves_df = load_data()

if not games_df.empty and not moves_df.empty:
    stats_df = analyze_opening_performance(games_df, moves_df, username)

    if not stats_df.empty:
        # 1. Apply the user's minimum games filter
        stats_df = stats_df[stats_df["games_played"] >= min_games]

        # 2. Apply the Gambit filter using Regex string matching
        if focus_gambits:
            stats_df = stats_df[
                stats_df["opening"].str.contains("Gambit", case=False, na=False)
            ]

        if stats_df.empty:
            st.warning("No openings match your current filter criteria.")
        else:
            # --- SECTION 1: POPULARITY (Volume) ---
            st.subheader("🔥 Most Played Openings")
            st.markdown("Your core repertoire based purely on volume.")

            # Sort by volume
            popular_openings = stats_df.sort_values(
                by="games_played", ascending=False
            ).head(10)

            st.bar_chart(
                popular_openings.set_index("opening")["games_played"], color="#3498db"
            )

            st.markdown("---")

            # --- SECTION 2: PERFORMANCE (Advantage Shift) ---
            st.subheader("📈 Performance (First 15 Moves)")

            # Re-sort by performance
            stats_df = stats_df.sort_values(by="avg_advantage_shift", ascending=False)

            best_openings = stats_df.head(5)
            worst_openings = stats_df.tail(5).sort_values(
                by="avg_advantage_shift", ascending=True
            )

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Best Openings (Advantage Gained)**")
                st.dataframe(
                    best_openings.style.format({"avg_advantage_shift": "{:+.0f} cp"}),
                    hide_index=True,
                    use_container_width=True,
                )

            with col2:
                st.markdown("**Worst Openings (Advantage Lost)**")
                st.dataframe(
                    worst_openings.style.format({"avg_advantage_shift": "{:+.0f} cp"}),
                    hide_index=True,
                    use_container_width=True,
                )
