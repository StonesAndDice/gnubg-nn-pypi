#!/usr/bin/env python3
"""
Print a backgammon board from a gnubg Position ID.

Usage:
    python examples/print_board.py <position_id>

Examples:
    python examples/print_board.py 4HPwATDgc/ABMA
    python examples/print_board.py "4HPwATDgc/ABMA:other-stuff"  # (match ID part ignored)

Board layout:
    - Row 0 = X's checkers, Row 1 = O's checkers
    - Indices 0-23 = points 1-24 on the board
    - Index 24 = bar (captured pieces)
"""

import sys
import argparse
import gnubg_nn


def print_board(position_id: str):
    """Convert position ID to board and print a simple point-by-point listing."""
    pos_id = position_id.strip()

    # Handle combined position:match IDs (split on : or whitespace, use first part)
    if ":" in pos_id or " " in pos_id:
        parts = pos_id.replace(":", " ").split()
        pos_id = parts[0]
        if len(parts) > 1:
            print(f"Note: Match ID '{' '.join(parts[1:])}' is not supported (position ID only).\n")

    try:
        board = gnubg_nn.board_from_position_id(pos_id)
    except Exception as e:
        print(f"Error: Failed to parse position ID '{pos_id}'", file=sys.stderr)
        print(f"  {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

    # Print board summary
    print(f"Position ID: {pos_id}")
    print(f"Board layout: 2x25 array (X on row 0, O on row 1)")
    print()

    # Print each player's checkers
    for player_idx, player_name in enumerate(("X", "O")):
        print(f"Player {player_name}:")
        has_checkers = False
        for point_idx in range(24):
            count = board[player_idx][point_idx]
            if count > 0:
                has_checkers = True
                point_num = point_idx + 1
                print(f"  Point {point_num:2d}: {count:2d} checker{'s' if count != 1 else ''}")

        # Bar
        bar_count = board[player_idx][24]
        if bar_count > 0:
            has_checkers = True
            print(f"  Bar:        {bar_count:2d} checker{'s' if bar_count != 1 else ''}")

        if not has_checkers:
            print("  (No checkers on board)")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Print a backgammon board from a gnubg Position ID",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("position_id", help="14-character gnubg Position ID (base64)")
    args = parser.parse_args()

    print_board(args.position_id)


if __name__ == "__main__":
    main()
