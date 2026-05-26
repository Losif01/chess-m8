# chess profile analyzer
this is just a small project i made in leisure to get my opening mistakes, and i plan to expand it in colaboration with lichess API, i may highlight later what lichess misses that i think would matter and add it to the project

## core philosophy
- A game is in the opening phase as long as the number of moves played is less than 15
- A mistake is a move that results in a ACPL diff of 1
- An opening is failed if the resulting ACPL diff is more than 1.5 on move 15

## Features

- **Memory-Efficient Parsing:** Uses `python-chess` generators to stream massive PGN files without blowing up your RAM.
    
- **Automated Engine Analysis:** Connects to a local Stockfish binary to calculate and inject `[%eval]` tags into unanalyzed games.
    
- **Relational Data Mapping:** Flattens nested PGN structures into two analysis-ready Pandas DataFrames: `games` (metadata) and `moves` (ply-by-ply evaluations).
    
- **Streamlit UI:** An interactive web UI to filter your repertoire by volume, isolate gambits, and visualize your best/worst openings based on engine evaluation shifts.

## Prerequisites

- **Python 3.12+**
    
- **[uv](https://github.com/astral-sh/uv)** (An extremely fast Python package and project manager)
    
- **Stockfish** (Required for the analysis pipeline)
    
    - _Linux/Fedora:_ `sudo dnf install stockfish` (Binary usually at `/usr/bin/stockfish`)
        
    - _Debian/Ubuntu Server:_ `sudo apt install stockfish` (Binary usually at `/usr/games/stockfish`)

    - _Windows:_ `winget install -e --id Stockfish.Stockfish` (Binary usually at `C:\Program Files\Stockfish\stockfish.exe`)

1. Clone the repository:
    ``` bash
    git clone https://github.com/Losif01/chess-m8.git
    cd chess-m8
    ```
    
2. Install dependencies using `uv` (this will automatically create your `.venv` and install `chess`, `pandas`, `pydantic`, and `streamlit`):
    ``` bash
    uv sync
    ```


## Usage 

This project is broken into two main phases: Heavy Computation (if you have unanalyzed PGNs) and Data Visualization. please move to the next step if you downloaded analyzed games only from lichess.

### 1. Engine Analysis 

Analyzing thousands of games takes time. i personally passed this to a home server using `tmux` so it can run in the background. if you don't have a home server, you can still run this locally.

Ensure your Stockfish binary path is correctly set in `main.py`, then run:

``` bash
uv run main.py
```

This will read your `<<unanalyzed>>.pgn`, evaluate every position, and output a new `analyzed.pgn` complete with `[%eval]` tags.

### 2. The Streamlit Dashboard

Once your games are analyzed and converted into the relational DataFrames (`games.csv` and `moves.csv`), fire up the dashboard to analyze your repertoire.

``` bash
uv run streamlit run app.py
```

- **Default Target Username:** `MasterOfSkillIssues` (Change this to your username, please don't use my lichess my username).
    
- **Volume Filter:** Adjust the minimum games slider to filter out one-off edge cases.
    
- **Gambit Toggle:** Instantly isolate your gambit lines using regex string matching.
    

## Data Architecture

To mimic the analytics capabilities of platforms like Lichess, the data is split relationally:

- **`games_df`**: 1 Row = 1 Game. Contains Metadata (Event, White, Black, Result, Date).
    
- **`moves_df`**: 1 Row = 1 Move (Ply). Contains the exact move text (SAN), clock time, and centipawn evaluation (`eval_cp`) normalized to White's perspective.

By joining these tables on `game_id`, the Pandas logic can easily calculate the evaluation delta between Move 1 and Move 15 for any specific opening.

## Contributing

Pull requests are welcome! If you want to add blunder-detection algorithms (e.g., flagging any move with an evaluation drop > 300cp) or support for importing directly from the Lichess API, feel free to open an issue.

## License

MIT License
