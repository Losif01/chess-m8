import time

import chess.engine
import chess.pgn
import pandas as pd


def extract_games_to_dataframe(file_path: str) -> pd.DataFrame:
    """
    Parses a PGN file using python-chess and extracts metadata
    and move statistics into a Pandas DataFrame.
    """
    games_data = []

    # Open the file once. python-chess will read it sequentially.
    with open(file_path, "r", encoding="utf-8") as pgn_file:
        while True:
            # read_game() automatically grabs the next game in the file
            game = chess.pgn.read_game(pgn_file)

            # If it returns None, we've hit the end of the file
            if game is None:
                break

            # The headers are stored in a dictionary-like object
            headers = game.headers

            # Extract the mainline moves (ignoring alternative variations)
            mainline = list(game.mainline_moves())

            # Build a dictionary for this specific game
            game_dict = {
                "event": headers.get("Event", None),
                "date": headers.get("Date", None),
                "white": headers.get("White", None),
                "black": headers.get("Black", None),
                "result": headers.get("Result", None),
                "white_elo": headers.get("WhiteElo", None),
                "black_elo": headers.get("BlackElo", None),
                "eco": headers.get("ECO", None),
                "opening": headers.get("Opening", None),
                "time_control": headers.get("TimeControl", None),
                "termination": headers.get("Termination", None),
                # --- Derived Game Attributes ---
                # Total number of ply (half-moves)
                "total_ply": len(mainline),
                # We can even ask python-chess to format the moves back into standard text
                "move_text": game.board().variation_san(mainline) if mainline else "",
            }

            games_data.append(game_dict)

    # Convert the list of dictionaries directly into a DataFrame
    df = pd.DataFrame(games_data)

    # Optional cleanup: Convert Elo strings to numeric, forcing errors to NaN
    df["white_elo"] = pd.to_numeric(df["white_elo"], errors="coerce")
    df["black_elo"] = pd.to_numeric(df["black_elo"], errors="coerce")

    return df


def analyze_pgn_file(
    input_file: str, output_file: str, engine_path: str, time_limit: float = 0.1
):
    """
    Reads games from a PGN, analyzes each move with Stockfish,
    and writes the annotated games to a new file.
    """
    # 1. Boot up Stockfish
    # We use a context manager (with) so the engine process is safely killed when done
    with chess.engine.SimpleEngine.popen_uci(engine_path) as engine:
        with (
            open(input_file, "r", encoding="utf-8") as unanalyzed_file,
            open(output_file, "w", encoding="utf-8") as analyzed_file,
        ):
            game_count = 0

            while True:
                # Read the next game
                game = chess.pgn.read_game(unanalyzed_file)
                if game is None:
                    break

                game_count += 1
                print(
                    f"Analyzing Game {game_count}: {game.headers.get('White')} vs {game.headers.get('Black')}..."
                )

                # Set up a board to track the state as we step through the moves
                board = game.board()

                # Iterate through the actual moves in the game
                for node in game.mainline():
                    # Push the move onto our tracking board
                    board.push(node.move)

                    # 2. Ask Stockfish for its opinion
                    # We limit the engine to a specific amount of time per move
                    limit = chess.engine.Limit(time=time_limit)
                    info = engine.analyse(board, limit)

                    # 3. Extract the score from White's perspective
                    # pov(chess.WHITE) ensures standard +1.5 (White is winning) format
                    score = info["score"]

                    # 4. Inject the [%eval ] tag into the PGN node
                    node.set_eval(score)

                # 5. Write the newly analyzed game to the output file
                # The string representation of 'game' now includes all the [%eval] tags
                print(game, file=analyzed_file, end="\n\n")

                # Optional: Force the file to save to disk after every game
                # so you don't lose data if you cancel the script halfway through.
                analyzed_file.flush()


# --- Execution ---
if __name__ == "__main__":
    STOCKFISH_PATH = "change this to your stockfish binarypath"
    INPUT_PGN = "go to lichess and download your games (use this file only with games with no analysis)"
    OUTPUT_PGN = "analyzed.pgn"
    start_time = time.time()
    # 0.1 seconds per move is a good baseline for fast but decent analysis
    analyze_pgn_file(INPUT_PGN, OUTPUT_PGN, STOCKFISH_PATH, time_limit=0.1)

    elapsed = round(time.time() - start_time, 2)
    print(f"\n Elapsed time: {elapsed / 60} minutes")
