
Core Concepts
=============

This section introduces the key internal concepts and data structures used by the `gnubg-nn-pypi` library. They are drawn from the GNUBG neural network evaluation code (the same logic used by the full GNU Backgammon application, but exposed here as a standalone library).

Position ID
-----------

A **Position ID** encodes the entire backgammon board state into a short alphanumeric string. It includes:
- Number and position of checkers on each point
- Checkers on the bar
- Checkers borne off

It is base64-encoded and typically 14 characters long. The GNUBG neural network library uses Position IDs for fast hashing and analysis.

You can convert between Position IDs and board state programmatically using this package's helper tools.

Match ID
--------

A **Match ID** encodes the current game state in a match, including:
- Match scores
- Cube value and ownership
- Whose turn it is
- Crawford game status

Match IDs are crucial for match-aware equity calculations and cubeful evaluations.

Neural Networks
---------------

The GNUBG neural network library uses multiple neural networks to evaluate different game phases:

- **Contact net** – for standard gameplay with both players interacting
- **Race net** – for bear-off races
- **Crashed net** – for lopsided or closed positions
- **Prune variants** – reduced-size networks for faster evaluation

Each network takes a **250-element input vector**, extracted from the board state. The vector includes:
- Point occupation per side (e.g., 6 checkers on point 13)
- Bar and off checkers
- Board control and pip counts
- Normalized weights

Each net outputs probabilities for:
- Winning the game
- Winning by gammon or backgammon
- Losing (and its type)

Bearoff Databases
-----------------

Bearoff databases provide **exact equity values** for endgame positions.

Types:
- **One-sided**: equity when only one player has checkers
- **Two-sided**: both players have checkers

The library can use in-memory or disk-based bearoff databases (loaded at startup), used when positions match supported database shapes.

- Supported up to 15 checkers on first 6 points
- Optional support for **Hypergammon** (3-checker variant)

Evaluation Flow
---------------

When evaluating a position, the library follows these steps:

1. **Classify** the position: race, crashed, or contact
2. If in **bearoff DB**, return exact equity
3. Otherwise, use the **appropriate neural net**
4. Optionally, apply **cubeful adjustment** using match state and equity tables

Additional logic may include:
- **Rollouts**: Monte Carlo simulations of many playouts
- **Move filters**: Only analyze top N moves
- **Noise injection**: Simulate human-like variability
- **Evaluation depth**: 0-ply, 1-ply, or 2-ply lookahead

These mechanisms allow the library to evaluate complex decisions with high precision.

