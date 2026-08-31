Overview
========

**`gnubg-nn`** is a Python package that provides bindings to the **GNUBG neural network evaluation library** — the same engine used by the full `GNU Backgammon <https://www.gnu.org/software/gnubg/>`_ application for position analysis and cube decisions, but as a standalone library. This package is the neural network library only; it is not the full backgammon application (GUI, match play). It allows developers and researchers to evaluate backgammon positions using the same logic and weights that power one of the strongest backgammon AIs in existence.

This package is ideal for:

- AI/ML researchers working with game engines
- Developers building backgammon apps or bots
- Hobbyists analyzing positions and match play
- Students exploring neural networks in classical games

Features
--------

- Evaluate positions using GNUBG-trained neural networks
- Load and use official GNUBG weights -- including holding several nets
  in one process at once (``net_load``/``net_use``/``net_save``)
- Generate GNUBG-style 250-feature input vectors from Position IDs
- Access low-level evaluation scores: win/gammon/backgammon probabilities
- Cube decisions (``evaluate_cube_decision``) and one-checker races
  (``one_checker_race``)
- Train neural-net weights against labeled position data (``Trainer``)
- A full self-play training pipeline (``gnubg_nn.training``): self-play
  a net against a fixed reference net, mine the positions where they
  disagree, train on the disagreements, and score against real rollout
  benchmark files -- plus tools to download GNU Backgammon's own
  published reference net, benchmarks, and training data. See
  :doc:`training`.
- Python 3 bindings to the native GNUBG neural network library

Why this library?
-----------------

GNU Backgammon (GNUBG) is a free and open-source world-class backgammon application. Its evaluation pipeline combines neural nets, equity lookups, and rollout simulations. With `gnubg-nn-pypi`, you get the **neural network evaluation library** from GNUBG in Python — the same logic used by the full application — so you can integrate it into scripts and tools without running the full GUI or CLI.

About Backgammon
-----------------

Backgammon is a two-player strategy game combining tactics, probability, and positional play. Each player moves 15 checkers across a 24-point board based on dice rolls. The goal is to bear off all checkers before your opponent. Advanced play involves doubling stakes, calculating equity, and leveraging game-theoretic principles — making it an ideal testbed for AI.

🛈 See :doc:`rules` for a summary of backgammon rules, or the `GNU Backgammon Manual <https://www.gnu.org/software/gnubg/manual/>`_ for full detail.
