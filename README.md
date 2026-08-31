<p align="center">
<img src="https://raw.githubusercontent.com/StonesAndDice/gnubg-nn-pypi/refs/heads/main/img/banner.png">
</p>

# GNUBG Neural Networks (gnubg-nn)

[![PyPI Downloads](https://img.shields.io/pypi/dm/gnubg-nn.svg?label=PyPI%20downloads)](https://pypi.org/project/gnubg-nn/)
[![Build & test wheels](https://github.com/StonesAndDice/gnubg-nn-pypi/actions/workflows/build_and_test.yml/badge.svg?branch=main)](https://github.com/StonesAndDice/gnubg-nn-pypi/actions/workflows/build_and_test.yml)
[![C/C++ Lint](https://github.com/StonesAndDice/gnubg-nn-pypi/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/StonesAndDice/gnubg-nn-pypi/actions/workflows/lint.yml)
[![Branch naming](https://github.com/StonesAndDice/gnubg-nn-pypi/actions/workflows/branch.yaml/badge.svg?branch=main)](https://github.com/StonesAndDice/gnubg-nn-pypi/actions/workflows/branch.yaml)
[![Release to PyPI](https://github.com/StonesAndDice/gnubg-nn-pypi/actions/workflows/release.yml/badge.svg)](https://github.com/StonesAndDice/gnubg-nn-pypi/actions/workflows/release.yml)
[![GitHub issues](https://img.shields.io/github/issues/StonesAndDice/gnubg-nn-pypi.svg)](https://github.com/StonesAndDice/gnubg-nn-pypi/issues)
[![License](https://img.shields.io/badge/license-GPL%20v2-blue.svg)](https://github.com/StonesAndDice/gnubg-nn-pypi/blob/main/LICENSE)
[![Stack Overflow](https://img.shields.io/badge/stackoverflow-Ask%20questions-blue.svg)](https://stackoverflow.com/questions/tagged/gnubg)

**GNUBG Neural Networks** (this package, `gnubg-nn`) is a *library* that provides Python bindings to the GNUBG neural-network evaluation engine — the same engine used for position analysis and cube decisions in the full [GNU Backgammon](https://www.gnu.org/software/gnubg/) application, but packaged as a standalone library for use in scripts, analysis tools, and applications. It is not the full backgammon game (GUI, match play, etc.).

## Quick Start

`gnubg_nn` is a native Python extension module that wraps the GNUBG neural-net evaluation library, so you can call 
the same position-analysis and cube-decision routines that power the full GNU Backgammon application from any Python 3.10+ script or application. It’s ideal for batch processing, data-science workflows, or building custom tools and UIs.

### Installation

> **Important:** The PyPI package name is `gnubg-nn`, not `gnubg`. Installing `gnubg` will install the unrelated full GNU Backgammon application. The correct command is:

```bash
pip install gnubg-nn
```

Then import it as:

```python
import gnubg_nn
```

> **Note:** The engine (neural-network weights, bear-off tables, etc.) initialises automatically on import — you do **not** need to call `initnet()`.

### Getting Started

```python
import gnubg_nn

# Convert a 14-char Base64 Position ID to a 2x25 board
board = gnubg_nn.board_from_position_id("4HPwATDgc/ABMA")

# Evaluate win/gammon/backgammon probabilities at 2 plies
probs = gnubg_nn.probabilities(board, gnubg_nn.p_0plus1)
win, win_gammon, win_bg, lose_gammon, lose_bg = probs

print(f"Win: {win:.3f}, Gammon: {win_gammon:.3f}, Backgammon: {win_bg:.3f}")

# Find the best move for an opening 6-5 roll
moves = gnubg_nn.moves(board, 6, 5)
best = gnubg_nn.best_move(board, 6, 5)  # default args: a move list, [(from, to), ...]
print(f"Best move: {best}")
```

### Training the Neural Network

You can also train the neural network weights against labeled position data using the `Trainer` class:

```python
import gnubg_nn

# Create a trainer from a list of training positions
# Each entry: 20-char position key (letters A-P only) + 5 space-separated
# probability values -- get real keys from key_of_board()/moves(), not
# hand-typed strings.
training_data = [
    "OAHDPAABDAOAHDPAABDA 0.5 0.1 0.05 0.1 0.05",  # position key + probs
    "OAHDPAABDAOAHDPAABBC 0.6 0.15 0.08 0.08 0.04",
]

trainer = gnubg_nn.Trainer(training_data)

# Check initial training errors (RMS + max error for 6 metrics)
errors = trainer.errors()
print(f"Initial error: {errors[2]:.4f}")

# Train for one epoch at learning rate 0.01
trainer.train(0.01)

# Check errors after training
errors = trainer.errors()
print(f"After training: {errors[2]:.4f}")
```

The `Trainer` class supports options for training against the pruned net, ignoring backgammon components, and restricting to specific neural net inputs. See the API documentation for details.

### Self-Play Training

The `gnubg_nn.training` subpackage builds on `Trainer` (above) and `net_load`/`net_use` (multiple nets held in one process) to provide a full self-play training pipeline: play a net against a fixed reference net, mine the positions where they disagree, and train on the disagreements — plus tools to download GNU Backgammon's own published reference net, rollout benchmarks, and training data, and to score a net against real rollout ground truth. Installing this package also installs two console scripts, `gnubg-nn-download` and `gnubg-nn-buildnet`:

```bash
gnubg-nn-download ./gnubg-data
gnubg-nn-buildnet my-net.weights ./gnubg-data/nngnubg.weights \
    ./training-data.dat ./gnubg-data/contact.bm --class contact --cycles 20
```

See the "Training" page on [ReadTheDocs](https://gnubg.readthedocs.io/en/latest/training.html) (source: [`docs/training.rst`](https://github.com/StonesAndDice/gnubg-nn-pypi/blob/main/docs/training.rst)) for the full walkthrough.

That’s all you need to get up and running! For detailed API docs, advanced build options, and configuration, see the 
sections below or visit the full documentation on [ReadTheDocs](https://gnubg.readthedocs.io/en/latest/).

* **ReadTheDocs** [https://gnubg.readthedocs.io/en/latest/](https://gnubg.readthedocs.io/en/latest/)
* **GNU Backgammon (full application):** [https://www.gnu.org/software/gnubg/](https://www.gnu.org/software/gnubg/)
* **Original Documentation:** [http://www.gnubg.org/documentation/doku.php?id=gnu_backgammon_faq](http://www.gnubg.org/documentation/doku.php?id=gnu_backgammon_faq)
* **Mailing list:** [https://lists.gnu.org/mailman/listinfo/gnubg](https://lists.gnu.org/mailman/listinfo/gnubg)
* **Source code:** [https://github.com/StonesAndDice/gnubg-nn-pypi](https://github.com/StonesAndDice/gnubg-nn-pypi)
* **GNUBG Neural Networks (gnubg-nn) upstream:** [https://git.savannah.gnu.org/cgit/gnubg/gnubg-nn.git](https://git.savannah.gnu.org/cgit/gnubg/gnubg-nn.git)
* **Contributing:** [https://savannah.gnu.org/people/](https://savannah.gnu.org/people/)
* **Credits:** [https://git.savannah.gnu.org/cgit/gnubg.git/tree/credits.sh](https://git.savannah.gnu.org/cgit/gnubg.git/tree/credits.sh)

It provides:

* **Engine initialization & data loading** (neural-net weights, opening-book, bear-off tables)
* **Position classification** (`classify`) & **public-evaluation best move** (`pub_best_move`)
* **Board ↔ ID conversions** (`board_from_position_id`, `board_from_position_key`, `key_of_board`, `position_id`)
* **Dice utilities** (`roll`) & **cube utilities** (`best_move`, `pub_eval_score`)
* **Bear-off tools** (`bearoff_id_2_pos`, `bearoff_probabilities`) & **one-checker race** (`one_checker_race`)
* **Legal-move enumeration** (`moves`) & **probabilistic evaluation** (`probabilities`)
* **Monte-Carlo rollouts** (`rollout`, `cubeful_rollout`)
* **Cube decisions** (`evaluate_cube_decision`)
* **Equity lookup** (`equities.value(xAway, oAway)`)
* **Multiple nets in one process** (`net_load`, `net_use`, `net_save`) — hold a trainee net and a fixed reference net at once
* **Neural-net training** (`Trainer` class for tuning weights against labeled positions)
* **Self-play training pipeline** (`gnubg_nn.training` subpackage: self-play, disagreement mining, real-rollout-benchmark scoring, and downloading GNU Backgammon's published training data — plus the `gnubg-nn-buildnet`/`gnubg-nn-download` console scripts)
* **Runtime engine tuning** via the `set` submodule

## 🧪 Platform Compatibility

Wheels actually published to PyPI, per `.github/workflows/release.yml`'s build matrix:

| Python Version | Linux x86\_64<br>(glibc ≥ 2.17) | macOS arm64<br>(Apple Silicon) | Windows x86\_64 |
|----------------| ------------------------------- | ------------------------------- |-----------------|
| **3.13**       | ✅                               | ✅                               | ✅               |
| **3.12**       | ✅                               | ✅                               | ✅               |
| **3.11**       | ✅                               | ✅                               | ✅               |
| **3.10**       | ✅                               | ✅                               | ✅               |

### Notes:

* ✅ = Built and published
* No Linux i686, macOS x86\_64 (Intel), or Python 3.14 wheels are published yet — `pip install gnubg-nn` on an Intel Mac currently has no prebuilt wheel to install. Tracked as a follow-up, not a documentation issue: widening this is a real CI change (new build targets, new toolchain risk), not just a table correction.
* If you're on an unsupported platform, `pip install gnubg-nn` will attempt a source build (requires a C/C++ toolchain and Meson).

## Testing

The test suite lives in this repo's `tests/` directory (not shipped in the installed package) and runs with pytest. From a repo checkout:

```bash
pip install pytest
pytest tests/
```
## AI-Assisted Development

Parts of this project were developed with the assistance of generative AI tools.

Specifically, the following models were used:

- **GPT-4o** (OpenAI ChatGPT)
- **o4-mini-high** (OpenAI ChatGPT)
- **Haiku 4.5** (Anthropic)
- **Opus 4.8** (Anthropic)

These models were used to assist with code generation, documentation drafting, and architectural guidance. All outputs were reviewed and curated by a human before inclusion.

> ⚠️ **Disclaimer:**  
> Although human-reviewed, some AI-generated content may contain mistakes, inaccuracies, or outdated practices. Contributors and users should critically assess all code, comments, and documentation. We welcome corrections and improvements via pull requests or issues.

## Code of Conduct

Please read the [Code of Conduct](https://github.com/StonesAndDice/gnubg-nn-pypi/blob/main/CONDUCT.md) to learn how to interact positively.

## Contributing

Your expertise and enthusiasm are welcome! You can contribute by:

* Reviewing and testing pull requests
* Reporting and triaging issues
* Improving documentation, tutorials, and examples
* Enhancing engine parameters or submodules
* Maintaining website or branding assets
* Translating materials
* Assisting with outreach and onboarding
* Writing grant proposals or helping with fundraising

For more information, see our [Contributing Guide](https://github.com/StonesAndDice/gnubg-nn-pypi/blob/main/CONTRIBUTING.md). If you’re unsure where to start, open an issue or join the discussion on our mailing list!

## Acknowledgments

This project builds upon the extensive work of the GNU Backgammon (GNUBG) community. The *gnubg-nn* library is the neural network evaluation component; the full backgammon application (GUI, match play, etc.) is maintained separately. We specifically acknowledge the 
[pygnubg](https://git.savannah.gnu.org/cgit/gnubg/gnubg-nn.git/tree/py) program developed by Joseph Heled.

We express our gratitude to all contributors who have dedicated their time and expertise to the development of the GNUBG neural network library and its Python bindings.

- **AUTHORS.md**: A list of primary contributors to the `gnubg-nn-pypi` project can be found [here](https://github.com/StonesAndDice/gnubg-nn-pypi/blob/main/AUTHORS.md).
- **GNU Backgammon (full project) credits.sh**: For a comprehensive list of contributors to the full GNUBG application, please refer to the [credits.sh](https://git.savannah.gnu.org/cgit/gnubg.git/tree/credits.sh) file.

We also thank the broader GNUBG community, including testers, translators, and mailing list participants, for their invaluable support.

