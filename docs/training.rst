Training
========

``gnubg_nn.training`` trains a net against GNU Backgammon's own published
rollout data, or against a fixed reference net via self-play. It's a
Python 3 port of the original ``gnubg-nn`` project's ``scripts/train/*.py``
tools (Python 2, ``pygnubg``-only) -- see each submodule's own docstring
for exactly what changed and what was deliberately left out.

Installing this package also installs two command-line tools,
``gnubg-nn-download`` and ``gnubg-nn-buildnet``.

Step 1: get real training data
-------------------------------

GNU Backgammon publishes a reference net, rollout benchmark files, and
rollout-labeled training positions at
https://alpha.gnu.org/gnu/gnubg/nn-training/. ``gnubg_nn.training.download``
fetches them for you (stdlib only, no extra dependency):

.. code-block:: bash

   gnubg-nn-download ./gnubg-data

This downloads (into ``./gnubg-data``):

* ``nngnubg.weights`` -- the reference net, used as the fixed comparison
  point for self-play disagreement mining.
* ``contact.bm`` / ``race.bm`` / ``crashed.bm`` -- rollout benchmark files,
  one per game phase. These carry **real rollout ground truth** (positions
  played out many times with genuine random dice, not any net's own
  opinion), which is what makes them meaningful for measuring progress --
  see :func:`gnubg_nn.training.referr.benchmark_error`.
* ``contact-train-data`` / ``race-train-data`` / ``crashed-train-data`` --
  rollout-labeled positions, directly usable as training data.

Or use the download functions from Python instead of the CLI:

.. code-block:: python

   from gnubg_nn.training import download_all
   download_all("./gnubg-data")

**The two version directories on the server are not mirrors of each
other** -- confirmed by hand while building this module, not assumed:
``1.01/`` only has ``nets/``; ``1.00/`` only has ``benchmarks/`` and
``training_data/``. The download functions already point at the right
version for each asset type; you shouldn't need to think about this
unless you're fetching something this module doesn't cover.

Step 2: train against a real rollout benchmark
------------------------------------------------

.. code-block:: bash

   gnubg-nn-buildnet \
       my-net.weights \
       ./gnubg-data/nngnubg.weights \
       ./my-net-training-data.dat \
       ./gnubg-data/contact.bm \
       --class contact --cycles 20 --positions-per-cycle 500

Each cycle:

1. Self-plays games, driven by ``my-net.weights``'s own 0-ply move choice.
2. At every position in the target game phase, checks whether
   ``my-net.weights`` and the reference net (``nngnubg.weights`` here)
   disagree on the cube decision or the best move by more than
   ``--equity-threshold`` (default ``0.02``).
3. Labels every disagreement with the *reference* net's own evaluation and
   appends it to the training-data file.
4. Trains ``my-net.weights`` on the accumulated file.
5. Scores the result against the real benchmark (``contact.bm``) and saves
   it as the new best checkpoint only if that real-benchmark score
   actually improved.

**Why step 5 checks a real benchmark, not just the training data's own
error**: this project's own development hit exactly the trap this avoids.
An earlier run judged progress by the trainee's error on its own
training data (or against a proxy benchmark built from one net's own
0-ply opinions) and it looked like training had plateaued or even
regressed -- when measured against real rollout data instead, the same
checkpoints were improving the whole time. A net's error on the data it
was just trained on tells you it fit that data; it doesn't tell you
whether it got closer to how backgammon actually plays out. Always
evaluate against ``benchmark_error()`` on a real ``.bm`` file for that.

Step 2, from Python
--------------------

.. code-block:: python

   from gnubg_nn.training import run_cycles

   run_cycles(
       "my-net.weights",
       "./gnubg-data/nngnubg.weights",
       "./my-net-training-data.dat",
       "./gnubg-data/contact.bm",
       target_class_name="contact",
       cycles=20,
       positions_per_cycle=500,
   )

Or use the pieces directly for more control -- ``self_play_and_mine()``,
``train()``, and ``benchmark_error()`` are all independently usable:

.. code-block:: python

   import gnubg_nn
   from gnubg_nn.training import (
       DisagreementMiningConfig, self_play_and_mine, train, benchmark_error,
   )

   trainee = gnubg_nn.net_load("my-net.weights")
   reference = gnubg_nn.net_load("./gnubg-data/nngnubg.weights")

   config = DisagreementMiningConfig(target_class=gnubg_nn.c_contact, target_positions=500)
   mined = self_play_and_mine(trainee, reference, config)

   result = train(mined.new_lines, trainee)
   print(result.best_errors)

   gnubg_nn.net_use(trainee)
   print(benchmark_error("./gnubg-data/contact.bm"))

Holding two nets in one process
---------------------------------

Disagreement mining needs to compare a trainee net against a fixed
reference net position-by-position -- :func:`gnubg_nn.net_load` and
:func:`gnubg_nn.net_use` exist specifically for this (added alongside
this module): ``net_load(path)`` loads a weights file into an independent
handle without disturbing whatever's currently active; ``net_use(handle)``
switches which loaded net subsequent calls (``probabilities()``,
``best_move()``, ``evaluate_cube_decision()``, etc.) use.

.. code-block:: python

   import gnubg_nn

   a = gnubg_nn.net_load("net-a.weights")
   b = gnubg_nn.net_load("net-b.weights")

   gnubg_nn.net_use(a)
   probs_a = gnubg_nn.probabilities(board, 0)

   gnubg_nn.net_use(b)
   probs_b = gnubg_nn.probabilities(board, 0)

Keep a Python reference to any handle you make active with ``net_use()``
for as long as you need it active -- once every reference to a handle is
gone, its memory is freed, and a handle you've made active but no longer
hold a reference to would leave the engine pointing at freed memory. In
practice this only matters if you deliberately discard a handle
(``del handle``, or letting a local variable that was made active go out
of scope) while still expecting to evaluate positions with it -- normal
usage, like the examples on this page, doesn't run into it.

Class-specific notes
----------------------

* **Race** positions mostly hinge on cube decisions, not move choice
  (there's often only one sensible move) -- expect the cube-error numbers
  to move a lot more than the move-error number during race training.
* **Crashed** and **contact** training tend to find far more disagreements
  per self-play game than race does, especially early on, so
  ``--positions-per-cycle`` fills up faster for those classes.
* None of this trains the *prune* nets (the small, cheap move-filter nets
  some search implementations use for a fast first pass) -- only the main
  race/crashed/contact evaluation nets.

API reference
--------------

See :doc:`api` for the full ``gnubg_nn`` API (``net_load``/``net_use``/
``net_save``, ``probabilities``, ``best_move``, etc.) that
``gnubg_nn.training`` is built on. The training-specific functions
documented above are the whole public surface of ``gnubg_nn.training``.
