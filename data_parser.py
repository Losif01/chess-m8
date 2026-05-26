import uuid
from dataclasses import dataclass

import chess.pgn
import pandas as pd


# We use a dataclass to neatly bundle our two dataframes together
@dataclass
class ChessDataset:
    games: pd.DataFrame
    moves: pd.DataFrame


def parse_analyzed_pgn(file_path: str) -> ChessDataset:
    games_data = []
    moves_data = []

    with open(file_path, "r", encoding="utf-8") as pgn_file:
        while True:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break

            headers = game.headers

            # 1. Ensure every game has a unique ID to link the DataFrames
            # Lichess provides GameId, but if it's missing, we generate one
            game_id = headers.get("GameId", str(uuid.uuid4()))

            # --- Extract Game Metadata ---
            games_data.append(
                {
                    "game_id": game_id,
                    "date": headers.get("Date"),
                    "white": headers.get("White"),
                    "black": headers.get("Black"),
                    "white_elo": headers.get("WhiteElo"),
                    "black_elo": headers.get("BlackElo"),
                    "opening": headers.get("Opening"),
                    "result": headers.get("Result"),
                }
            )

            # --- Extract Move-by-Move Analysis ---
            ply_count = 0

            for node in game.mainline():
                ply_count += 1

                # node.turn() returns the color to move *next*.
                # So the piece that just moved is the opposite.
                color_moved = "Black" if node.turn() == chess.WHITE else "White"

                # Extract evaluation (Centipawns).
                # mate_score=10000 converts "Mate in 3" to +/- 10000 so Pandas can do math on it
                eval_obj = node.eval()
                eval_cp = None
                if eval_obj is not None:
                    # Always normalize the score from White's perspective
                    eval_cp = eval_obj.white().score(mate_score=10000)

                moves_data.append(
                    {
                        "game_id": game_id,
                        "ply": ply_count,
                        "move_number": (ply_count + 1) // 2,
                        "color": color_moved,
                        "san": node.san(),
                        "eval_cp": eval_cp,
                        "clock_seconds": node.clock(),
                    }
                )

    # Convert our lists of dictionaries into Pandas DataFrames
    games_df = pd.DataFrame(games_data)
    moves_df = pd.DataFrame(moves_data)

    # Clean up numeric types
    games_df["white_elo"] = pd.to_numeric(games_df["white_elo"], errors="coerce")
    games_df["black_elo"] = pd.to_numeric(games_df["black_elo"], errors="coerce")

    return ChessDataset(games=games_df, moves=moves_df)


# --- Execution ---
if __name__ == "__main__":
    analyzed_file = "analyzed_total.pgn"
    print("Loading data into relational dfs...")

    dataset = parse_analyzed_pgn(analyzed_file)

    print(f"\nLoaded {len(dataset.games)} games and {len(dataset.moves)} total moves.")
    print("\n--- Moves DataFrame Preview ---")
    print(dataset.moves[["game_id", "ply", "color", "san", "eval_cp"]].head(6))
    dataset.games.to_csv("games.csv", index=False)
    dataset.moves.to_csv("moves.csv", index=False)
