<h1 align="center">
<img src="https://raw.githubusercontent.com/StonesAndDice/gnubg-nn-pypi/refs/heads/main/img/banner.png">

GNUBG Neural Networks (gnubg-nn)
</h1>

[![PyPI Downloads](https://img.shields.io/pypi/dm/gnubg-nn.svg?label=PyPI%20downloads)](https://pypi.org/project/gnubg-nn/)
[![Build & test wheels](https://github.com/StonesAndDice/gnubg-nn-pypi/actions/workflows/build_and_test.yml/badge.svg?branch=main)](https://github.com/StonesAndDice/gnubg-nn-pypi/actions/workflows/build_and_test.yml)
[![C/C++ Lint](https://github.com/StonesAndDice/gnubg-nn-pypi/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/StonesAndDice/gnubg-nn-pypi/actions/workflows/lint.yml)
[![Branch naming](https://github.com/StonesAndDice/gnubg-nn-pypi/actions/workflows/branch.yaml/badge.svg?branch=main)](https://github.com/StonesAndDice/gnubg-nn-pypi/actions/workflows/branch.yaml)
[![Release to PyPI](https://github.com/StonesAndDice/gnubg-nn-pypi/actions/workflows/release.yml/badge.svg)](https://github.com/StonesAndDice/gnubg-nn-pypi/actions/workflows/release.yml)
[![GitHub issues](https://img.shields.io/github/issues/StonesAndDice/gnubg-nn-pypi.svg)](https://github.com/StonesAndDice/gnubg-nn-pypi/issues)
[![License](https://img.shields.io/badge/license-GPL%20v2-blue.svg)](#license)
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
best = gnubg_nn.best_move(board, 6, 5)
print(f"Best move key: {best}")
```

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
* **Bear-off tools** (`bearoff_id_2_pos`, `bearoff_probabilities`)
* **Legal-move enumeration** (`moves`) & **probabilistic evaluation** (`probabilities`)
* **Monte-Carlo rollouts** (`rollout`, `cubeful_rollout`)
* **Equity lookup** (`equities.value(xAway, oAway)`)
* **Runtime engine tuning** via the `set` submodule

## 🧪 Platform Compatibility

| Python Version | Linux x86\_64<br>(glibc ≥ 2.17) | Linux i686<br>(glibc ≥ 2.12) | macOS universal2  | Windows x86\_64 |
|----------------| ------------------------------- | ---------------------------- |-------------------|-----------------|
| **3.14**       | ✅                               | ✅                            | ✅ (macOS ≥ 10.14) | ✅               |
| **3.13**       | ✅                               | ✅                            | ✅ (macOS ≥ 10.14) | ✅               |
| **3.12**       | ✅                               | ✅                            | ✅ (macOS ≥ 10.14) | ✅               |
| **3.11**       | ✅                               | ✅                            | ✅ (macOS ≥ 10.9)  | ✅               |
| **3.10**       | ✅                               | ✅                            | ✅ (macOS ≥ 10.9)  | ✅               |

### Notes:

* ✅ = Built and available
* ❌ = Not built
* macOS universal2 = Supports both ARM64 and x86-64 architectures

## Testing

gnubg-nn-pypi has some basic unit testing. After installation, run:

```bash
python3 -m unittest discover -s gnubg_nn.tests
```
## AI-Assisted Development

Parts of this project were developed with the assistance of generative AI tools.

Specifically, the following models were used:

- **GPT-4o** (OpenAI ChatGPT)
- **o4-mini-high** (OpenAI ChatGPT)

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

