
API Reference
=============

This section documents the public Python API provided by the `gnubg-nn-pypi` package — the GNUBG **neural network evaluation library** (position analysis, cube decisions, rollouts), not the full GNU Backgammon application. It includes functions for evaluating positions, loading neural nets, and accessing internal neural net state.

gnubg.bearoff_id_2_pos(id) -> Tuple[int, int, int, int, int, int]
-----------------------------------------------------------------

.. function:: bearoff_id_2_pos(id)

   Converts a bearoff ID into a 6-point position tuple using the internal GNU Backgammon bearoff database.

   :param id: Either an integer ID or a 6-element sequence representing the bearoff state.
   :type id: int or Sequence[int]
   :returns: A tuple of six integers representing the number of checkers on each of the first six points.

   The returned tuple maps the bearoff configuration for a single player. This is useful for reconstructing endgame positions
   or feeding inputs into evaluation functions that rely on bearoff-specific features.

   :raises TypeError: If the input is not a valid integer or 6-element sequence.

   **Example:**

   .. code-block:: python

      >>> gnubg.bearoff_id_2_pos(42)
      (0, 1, 0, 2, 3, 9)

gnubg.bearoff_probabilities(id) -> Tuple[float, ...]
----------------------------------------------------

.. function:: bearoff_probabilities(id)

   Returns the probability distribution of winning in *n* moves from a given bearoff position.

   :param id: Either a bearoff ID integer or a 6-element tuple representing a bearoff state.
   :type id: int or Sequence[int]
   :returns: A tuple of floats representing the probabilities of bearing off in exactly 1, 2, ..., N moves.

   The returned tuple may be padded with leading zeros if the bearoff record starts later than move 1.
   The actual data is retrieved from the compiled GNU Backgammon bearoff database.

   :raises TypeError: If the input is not a valid bearoff ID or 6-tuple.

   **Example:**

   .. code-block:: python

      >>> gnubg.bearoff_probabilities(42)
      (0.0, 0.0, 0.15, 0.33, 0.52)

   In this example, the probabilities of bearing off in 3, 4, and 5 moves are 15%, 33%, and 52%, respectively.

gnubg.best_move(pos, dice1, dice2, n=0, s='O', b=False, r=False, list=False, reduced=False)
-------------------------------------------------------------------------------------------

.. function:: best_move(pos, dice1, dice2, n=0, s='O', b=False, r=False, list=False, reduced=False)

   Calculates the best move(s) for a given board state and dice roll using ply-based neural network evaluation.

   :param pos: A 2x25 board array representing the full game state for both players.
   :type pos: list[list[int]]
   :param dice1: First die roll (1–6).
   :type dice1: int
   :param dice2: Second die roll (1–6).
   :type dice2: int
   :param n: Evaluation depth (ply). Default is 0-ply.
   :type n: int
   :param s: Which side to move ('X' or 'O'). Default is 'O'.
   :type s: str
   :param b: Return the new board position after move if True.
   :type b: bool
   :param r: Return resign suggestion value (0/1/2) if True.
   :type r: bool
   :param list: Include a full list of alternate legal moves and their evaluations.
   :type list: bool
   :param reduced: Use reduced evaluation (faster, less accurate).
   :type reduced: bool

   :returns: If `b`, `r`, or `list` are all False, returns a tuple of move steps:
             ``[(from, to), (from, to), ...]``

             If any of `b`, `r`, or `list` is True, returns a tuple:
             ``(best_move, board_str?, resign_code?, move_list?)`` depending on flags.

   :raises ValueError: On invalid dice, ply depth, or side specification.

   **Examples**

   .. code-block:: python

      >>> gnubg.best_move(pos, 2, 1)
      [(6, 5), (13, 11)]

      >>> gnubg.best_move(pos, 6, 6, n=2, b=True, r=True, list=True)
      (
         [(6, 12), (8, 14), (13, 19), (1, 7)],
         'board string after move...',
         0,
         [
            ('position_id', (13, 19, 6, 12, 1, 7, 8, 14), (0.90, 0.35, 0.12, 0.01, 0.00), 0.031),
            ...
         ]
      )

   The full move list includes all reasonable alternatives with their evaluation probabilities and match scores.

gnubg.board_from_position_id(pos_id) -> List[List[int]]
--------------------------------------------------------

.. function:: board_from_position_id(pos_id)

   Converts a GNU Backgammon Position ID string into a 2x25 board matrix representing both players' checkers.

   :param pos_id: A 14-character GNUBG Position ID string (e.g., "4HPwATDgc/ABMA").
   :type pos_id: str
   :returns: A nested list of integers in the shape ``[2][25]``. The first sublist represents the X side, the second the O side.
             Each list contains 25 elements:
             - Points 1–24: checker counts
             - Index 0: off or bar position (varies by GNUBG convention)

   :raises ValueError: If the input string is malformed or of the wrong length.

   **Example**

   .. code-block:: python

      >>> gnubg.board_from_position_id("4HPwATDgc/ABMA")
      [
         [0, 0, 0, 2, 0, 0, ..., 5],  # X's checkers
         [0, 0, 0, 0, 3, 2, ..., 0]   # O's checkers
      ]

   This output represents the internal format used by GNUBG to evaluate and simulate moves on the board.

gnubg.board_from_position_key(key) -> List[List[int]]
-----------------------------------------------------

.. function:: board_from_position_key(key)

   Converts a GNUBG board key string (e.g. from a move list or match log) into a 2x25 matrix representing both players' checkers.

   :param key: A GNUBG position key string (e.g., "X0uASbDgc/ABMA:MAAAABAAIAAA").
   :type key: str
   :returns: A nested list ``[2][25]`` representing the board for the X and O sides.

   Each sublist contains:
   - Index 1–24: points on the board
   - Index 0: special off/bar/checker area (GNUBG convention)

   :raises ValueError: If the position key is invalid or not parseable.

   **Example**

   .. code-block:: python

      >>> gnubg.board_from_position_key("X0uASbDgc/ABMA:MAAAABAAIAAA")
      [
         [0, 0, 0, 2, 0, 0, ..., 5],  # X's side
         [0, 0, 0, 0, 3, 2, ..., 0]   # O's side
      ]

   This is a lower-level equivalent of `board_from_position_id`, used when working with full match position keys.

Position Class Constants
------------------------

These integer constants represent how a backgammon position is classified by GNUBG's internal logic. You can use them with
:func:`classify_position` or interpret output from analysis modules.

.. data:: c_bearoff

   Indicates a bearoff position where one or both players are removing checkers from their home board.

   :value: integer (e.g. 0 or 4 depending on GNUBG compile-time settings)

.. data:: c_race

   A position where no checkers are in contact and both players are racing to bear off.

   :value: integer constant

.. data:: c_crashed

   A position where one side is blocked and checker distribution is lopsided (e.g. trapped behind a prime).

.. data:: c_contact

   Default classification for general positions with live contact between players' checkers.

.. data:: c_over

   The game is over. No moves are available.

.. data:: c_backcontain

   (Optional) A special class for backgame or containment scenarios, used if GNUBG is compiled with `CONTAINMENT_CODE`.

**Example**

.. code-block:: python

   cls = gnubg.classify_position(board)
   if cls == gnubg.c_bearoff:
       print("Bearoff phase")
   elif cls == gnubg.c_contact:
       print("Still in contact")

gnubg.classify(board) -> int
----------------------------

.. function:: classify(board)

   Classifies a board position into one of GNUBG’s internal position types such as contact, race, or bearoff.

   :param board: A 2x25 list of integers representing the checker layout for both players.
   :type board: list[list[int]]
   :returns: An integer constant corresponding to one of:

     - :data:`gnubg.c_contact`
     - :data:`gnubg.c_race`
     - :data:`gnubg.c_crashed`
     - :data:`gnubg.c_bearoff`
     - :data:`gnubg.c_over`
     - :data:`gnubg.c_backcontain` (if compiled with support)

   :raises ValueError: If the board input is not a valid 2x25 structure.

   **Example**

   .. code-block:: python

      >>> cls = gnubg.classify(board)
      >>> if cls == gnubg.c_race:
      ...     print("This is a race position.")

gnubg.cubeful_rollout(pos, ngames=576, side='X', ply=0) -> Tuple[float, ...]
----------------------------------------------------------------------------

.. function:: cubeful_rollout(pos, ngames=576, side='X', ply=0)

   Performs a cubeful rollout on a given backgammon position using GNUBG’s rollout engine.

   This function simulates a large number of games from the specified position using lookahead (ply) and cube handling,
   returning statistical estimates such as win/gammon/backgammon rates.

   :param pos: A position object or board suitable for GNUBG's AnalyzeBoard (e.g. 2x25 board or position ID).
   :type pos: object
   :param ngames: Number of rollout simulations to run (default: 576).
   :type ngames: int
   :param side: The player on turn, either `'X'` or `'O'`.
   :type side: str
   :param ply: The number of plies (0, 1, or 2) to use in lookahead during each rollout simulation.
   :type ply: int

   :returns: A tuple of 13 floats with rollout statistics:

     1. win percentage
     2. win gammon %
     3. win backgammon %
     4. lose %
     5. lose gammon %
     6. lose backgammon %
     7. equity
     8. equity (cubeful)
     9. standard error
     10. confidence interval
     11. cube decisions
     12. take point
     13. gammon value

   :raises ValueError: If the side is not 'X' or 'O', or if the board cannot be parsed.

   **Example**

   .. code-block:: python

      >>> gnubg.cubeful_rollout(board, ngames=1024, side='O', ply=1)
      (0.49, 0.21, 0.02, 0.51, 0.18, 0.01, -0.081, -0.079, 0.0031, ..., 0.26)

   These results can be used to evaluate cube decisions, risk/reward, and overall strategy in match play or money games.

equities.value(x_away, o_away) -> float
---------------------------------------

.. function:: equities.value(x_away, o_away)

   Returns the match equity for the given score in a match using the currently loaded Match Equity Table (MET).

   :param x_away: Number of points player X needs to win the match (0–25).
   :type x_away: int
   :param o_away: Number of points player O needs to win the match (0–25).
   :type o_away: int
   :returns: A float representing the match-winning chance (MWC) for player X at the specified score.

   This function queries the preloaded MET and returns the normalized equity for the match situation.
   It's primarily useful in match play for cube decision logic and overall strategic evaluation.

   :raises ValueError: If either score is outside the 0–25 range.

   **Example**

   .. code-block:: python

      >>> equities.value(3, 2)
      0.638

   In this example, if X is 3-away and O is 2-away, X has a 63.8% chance of winning the match.

gnubg.key_of_board(board) -> str
--------------------------------

.. function:: key_of_board(board)

   Converts a 2×25 board array into a GNUBG position key string (used for position lookup, storage, and export).

   :param board: A 2×25 nested list representing the full game state for both players.
   :type board: list[list[int]]
   :returns: A 20-character GNUBG position key string (uppercase A–Z).

   This function performs the reverse of :func:`board_from_position_key`. The key string encodes the board state for fast comparison,
   storage, and referencing in GNUBG tools and formats (like match logs and move records).

   :raises ValueError: If the input is not a valid 2×25 board.

   **Example**

   .. code-block:: python

      >>> gnubg.key_of_board([
      ...   [0, 0, 0, 2, ..., 5],
      ...   [0, 0, 0, 0, ..., 0]
      ... ])
      'X0uASbDgc/ABMA:MAAAABAAIAAA'

   This output can be used with GNUBG's `board_from_position_key` to reconstruct the board from its key.

gnubg.moves(board, die1, die2, verbose=False) -> Tuple[...]
------------------------------------------------------------

.. function:: moves(board, die1, die2, verbose=False)

   Generates all legal move options from a given board state and dice roll.

   :param board: A 2×25 nested list representing the full board state for both players.
   :type board: list[list[int]]
   :param die1: First die roll (1–6).
   :type die1: int
   :param die2: Second die roll (1–6).
   :type die2: int
   :param verbose: If True, returns each move as a tuple of position key and move steps. If False, returns just the position keys.
   :type verbose: bool

   :returns: A tuple of legal move options. The format depends on `verbose`:
      - If `verbose=False` (default): ``(key1, key2, ...)``
        where each key is a 20-character GNUBG position key string.
      - If `verbose=True`: ``((key1, [(from, to), ...]), ...)``

   :raises ValueError: If the board or dice are invalid.

   **Example**

   .. code-block:: python

      >>> gnubg.moves(board, 3, 1)
      ('X1uASbDgc/ACMA:MAAAABAAIAAA', 'X2uASbDgc/ABMA:MAAAABAAIAAA', ...)

      >>> gnubg.moves(board, 6, 4, verbose=True)
      (
        ('X1uASbDgc/ABMA:MAAAABAAIAAA', [(13, 19), (8, 14)]),
        ('X2uASbDgc/ACMA:MAAAABAAIAAA', [(6, 12), (13, 19)]),
        ...
      )

   This is the core legal move generator used internally by GNUBG before move filtering or evaluation.

gnubg.one_checker_race(pips) -> Optional[Tuple[float, float]]
----------------------------------------------------------------

.. function:: one_checker_race(pips)

   Estimates the win probability and standard deviation for a simple one-checker bearoff race using GNUBG’s analytical model.

   :param pips: The number of pips (points) remaining to bear off a single checker.
   :type pips: int
   :returns: A tuple ``(equity, std_dev)`` of floats if calculable, or ``None`` if the pip count is unsupported.

   This function uses GNUBG’s built-in analytical model `ocr()` to evaluate highly simplified race endgames, typically used in special training positions or theoretical studies.

   :raises ValueError: If the pip count is not an integer or out of range.

   **Example**

   .. code-block:: python

      >>> gnubg.one_checker_race(10)
      (0.273, 0.065)

   This indicates a 27.3% chance of winning from a 10-pip position with the standard deviation of outcomes at ~0.065.

Ply Evaluation Strategy Constants
---------------------------------

These constants are used to identify evaluation modes or neural net paths selected during multi-ply rollout, pruning, or classification strategies in GNUBG.

.. data:: p_0plus1

   Hybrid evaluation: 0-ply followed by 1-ply filtering (`1+½` strategy).

.. data:: p_1sbear

   1-ply evaluation with bearoff filtering.

.. data:: p_1srace

   1-ply evaluation in race-only scenarios.

.. data:: p_bearoff

   Position falls into exact bearoff category (database-driven evaluation).

.. data:: p_osr

   One-sided race evaluation (special case of bearoff or non-contact).

.. data:: p_prune

   Evaluation strategy using pruned neural networks for speed.

.. data:: p_race

   Standard race-only neural network evaluation.

These are typically returned internally by rollout routines or may be useful for logging/debugging advanced evaluations.

**Example**

.. code-block:: python

   eval_type = gnubg.p_1srace
   if rollout_result_type == gnubg.p_prune:
       print("Used pruned network evaluation")

gnubg.position_id(board) -> str
-------------------------------

.. function:: position_id(board)

   Converts a 2×25 backgammon board array into a 14-character GNUBG Position ID string.

   :param board: A nested list representing the full board state for both players.
   :type board: list[list[int]]
   :returns: A 14-character Position ID string (base64 encoded), suitable for evaluation, storage, or UI display.

   This is the inverse of :func:`board_from_position_id`. The Position ID is a compact string uniquely representing a board state.

   :raises ValueError: If the input is not a valid 2×25 list.

   **Example**

   .. code-block:: python

      >>> gnubg.position_id([
      ...   [0, 0, 0, 2, ..., 5],
      ...   [0, 0, 0, 0, ..., 0]
      ... ])
      '4HPwATDgc/ABMA'

   This Position ID can be passed to GNUBG-compatible tools or used in analysis pipelines.

gnubg.probabilities(board, ply, nr=1296) -> Tuple[float, float, float, float, float]
-------------------------------------------------------------------------------------

.. function:: probabilities(board, ply, nr=1296)

   Calculates win probabilities and related equity values for a given board using the specified evaluation strategy.

   :param board: A 2×25 list representing the backgammon board state for both players.
   :type board: list[list[int]]
   :param ply: Evaluation mode, must be one of:
      - :data:`gnubg.p_osr`
      - :data:`gnubg.p_bearoff`
      - :data:`gnubg.p_prune`
      - :data:`gnubg.p_1sbear`
      - :data:`gnubg.p_race`
      - :data:`gnubg.p_0plus1`
      - :data:`gnubg.p_1srace`
   :type ply: int
   :param nr: Number of rollouts (used for OSR race mode). Default is 1296.
   :type nr: int, optional

   :returns: A tuple of five floats: ``(win, win_gammon, win_backgammon, lose_gammon, lose_backgammon)``

   These values represent the outcome probabilities under the given evaluation logic.

   :raises RuntimeError: If the board is not a race in `p_osr` mode or the OS bearoff DB is unavailable.
   :raises ValueError: On invalid board structure.

   **Example**

   .. code-block:: python

      >>> gnubg.probabilities(board, gnubg.p_prune)
      (0.637, 0.182, 0.042, 0.103, 0.036)

   These outputs help guide move selection, cube decisions, or match strategy depending on the game's phase.

gnubg.pub_best_move(board, die1, die2) -> List[int]
---------------------------------------------------

.. function:: pub_best_move(board, die1, die2)

   Returns the best move from a given board and dice roll using GNUBG’s public evaluation function (non-ply-based, non-neural).

   :param board: A 2×25 board array representing the full game state.
   :type board: list[list[int]]
   :param die1: First die roll (1–6).
   :type die1: int
   :param die2: Second die roll (1–6).
   :type die2: int
   :returns: A flat list of integers representing the move: ``[from1, to1, from2, to2, ...]``

   Each index is 1-based and refers to points on the backgammon board. The number of pairs returned depends on the number of checkers moved.

   :raises ValueError: If the board is not valid.
   :raises RuntimeError: If no valid move is found.

   **Example**

   .. code-block:: python

      >>> gnubg.pub_best_move(board, 6, 1)
      [13, 19, 8, 9]

   This represents two moves: checker from 13→19 and from 8→9.

gnubg.pub_eval_score(board) -> float
------------------------------------

.. function:: pub_eval_score(board)

   Computes a simple evaluation score for the current position using GNUBG’s public (non-neural) evaluation model.

   This is a fast heuristic score used in early filtering, testing, or simpler bots.

   :param board: A 2×25 board array representing the full backgammon position.
   :type board: list[list[int]]
   :returns: A float evaluation score. Positive values favor player X; negative values favor player O.

   :raises ValueError: If the input is not a valid 2×25 board.

   **Example**

   .. code-block:: python

      >>> gnubg.pub_eval_score(board)
      -0.172

   This indicates that player O is slightly favored in the current position.

Rollout Type Constants
----------------------

These constants define how GNUBG classifies or initiates rollout evaluations for a given position.

.. data:: ro_auto

   Automatically detect the appropriate rollout type (e.g., contact, race, or bearoff) based on position classification.

.. data:: ro_race

   Force a race-type rollout, typically used when both players are in a pure bear-off race and contact is no longer possible.

.. data:: ro_bearoff

   Use precomputed bearoff databases during rollout; only valid if both players are in known bearoff configurations.

.. data:: ro_over

   Indicates that the game is over (no rollout needed or possible).

**Example**

.. code-block:: python

   rollout_type = gnubg.ro_auto
   if rollout_type == gnubg.ro_race:
       print("Running race-specific rollout")

gnubg.roll() -> Tuple[int, int]
-------------------------------

.. function:: roll()

   Simulates a roll of two six-sided dice using GNUBG’s internal RNG and rules.

   :returns: A tuple of two integers in the range 1–6: ``(die1, die2)``

   This function can be used for simulating games, testing move generators, or interactive play scenarios.

   **Example**

   .. code-block:: python

      >>> gnubg.roll()
      (3, 5)

gnubg.rollout(pos, ngames=1296, n=0, level=gnubg.ro_auto, nt=500, std=False) -> Union[Tuple[float, ...], Tuple[Tuple[float, ...], Tuple[float, ...]]]
------------------------------------------------------------------------------------------------------------------------------------------------------

.. function:: rollout(pos, ngames=1296, n=0, level=gnubg.ro_auto, nt=500, std=False)

   Performs a cubeless rollout simulation of a backgammon position using GNUBG’s AnalyzeBoard logic.

   This simulates many games (default 1296) from the specified position, using a specified ply depth and rollout mode.

   :param pos: A board object (2×25 list or structured input accepted by GNUBG).
   :type pos: object
   :param ngames: Number of games to simulate (default 1296).
   :type ngames: int
   :param n: Number of plies to evaluate at (0, 1, or 2).
   :type n: int
   :param level: Rollout type. Must be one of:
      - :data:`gnubg.ro_auto`
      - :data:`gnubg.ro_race`
      - :data:`gnubg.ro_bearoff`
      - :data:`gnubg.ro_over`
   :type level: int
   :param nt: Truncation threshold (default 500 games).
   :type nt: int
   :param std: If True, also return standard deviation (std error) values.
   :type std: bool

   :returns: Either a 5-tuple of outcome probabilities or a 2-tuple with both means and standard deviations:
      - ``(win, win_gammon, win_backgammon, lose_gammon, lose_backgammon)``
      - or: ``((...), (stddevs...))`` if `std=True`

   :raises ValueError: If `ngames` is zero or negative.

   **Example**

   .. code-block:: python

      >>> gnubg.rollout(board)
      (0.44, 0.21, 0.01, 0.31, 0.03)

      >>> gnubg.rollout(board, std=True)
      ((0.44, 0.21, 0.01, 0.31, 0.03), (0.03, 0.02, 0.01, 0.02, 0.01))

   This function provides accurate statistical approximations of long-term game outcomes from a given position.

gnubg.set
---------

The `set` submodule provides configuration methods for adjusting internal GNUBG simulation behavior and evaluation settings.

.. module:: gnubg.set
   :synopsis: Low-level controls for simulation setup.

Available Methods
-----------------

.. function:: set.seed(seed)

   Set the seed for the internal pseudo-random number generator used in dice rolls and rollouts.

   :param seed: A positive integer seed value.
   :type seed: int

.. function:: set.shortcuts(flags)

   Enable or disable evaluation shortcuts used in simulation (used internally for debugging or performance tuning).

   :param flags: Integer bitmask to control shortcut behavior.
   :type flags: int

.. function:: set.osdb(enabled)

   Enable or disable the use of the One-Sided Bearoff Database.

   :param enabled: True to enable, False to disable.
   :type enabled: bool

.. function:: set.ps(flags)

   Set pruning/move filtering flags.

   :param flags: Integer bitmask for move filters.
   :type flags: int

.. function:: set.equities(table_id)

   Select the match equity table to use.

   :param table_id: An integer referring to a preloaded MET.
   :type table_id: int

.. function:: set.score(x_away, o_away)

   Set the current match score for X and O.

   :param x_away: Points X needs to win the match (0–25).
   :param o_away: Points O needs to win the match.
   :type x_away: int
   :type o_away: int

.. function:: set.cube(owner, value, centered)

   Set the cube state for evaluation.

   :param owner: `'X'`, `'O'`, or `'C'` (centered).
   :param value: Cube value (1, 2, 4, ...).
   :param centered: Boolean indicating if the cube is centered.
   :type owner: str
   :type value: int
   :type centered: bool

**Example**

.. code-block:: python

   import gnubg.set as gset

   gset.seed(42)
   gset.score(3, 2)
   gset.cube('O', 2, False)

Engine Initialisation
---------------------

The GNUBG neural-network engine (weights, bearoff tables, opening book) is initialised **automatically when you import the package**. You do not need to call any initialisation function:

.. code-block:: python

   import gnubg_nn  # engine ready immediately

If you encounter examples from the original ``pygnubg`` library that call ``initnet()`` or ``gnubg.initnet()``, those calls are not needed and will raise ``AttributeError`` — simply remove them.

Migration from pygnubg / Legacy Names
--------------------------------------

The ``gnubg-nn`` package modernises function names relative to the original ``pygnubg`` library. If you are porting old code, use the following mapping:

.. list-table::
   :header-rows: 1
   :widths: 40 40 20

   * - Old name (pygnubg)
     - New name (gnubg-nn)
     - Notes
   * - ``initnet()``
     - *(not needed)*
     - Auto-called on import
   * - ``boardfromkey(key)``
     - ``board_from_position_key(key)``
     - 20-char A–Z key
   * - ``boardfromid(id)``
     - ``board_from_position_id(id)``
     - 14-char Base64 Position ID
   * - ``keyofboard(board)``
     - ``key_of_board(board)``
     -
   * - ``posid(board)`` / ``id(board)``
     - ``position_id(board)``
     -
   * - ``bestmove(...)``
     - ``best_move(...)``
     -
   * - ``pubbestmove(board, d1, d2)``
     - ``pub_best_move(board, d1, d2)``
     -

Deprecated aliases (``boardfromkey``, ``boardfromid``, ``bestmove``) are available in ``gnubg_nn`` for backwards compatibility but will be removed in a future release.

Package Name
------------

.. warning::

   The PyPI package name is ``gnubg-nn``, **not** ``gnubg``. Installing ``gnubg`` installs the unrelated full GNU Backgammon application package, which exposes a different and incompatible API. Always install with::

      pip install gnubg-nn

   and import with::

      import gnubg_nn
