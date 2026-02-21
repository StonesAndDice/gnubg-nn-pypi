Contributing Guide for gnubg-nn-pypi
====================================

Thank you for considering contributing to gnubg-nn-pypi, the Python bindings
for the **GNUBG neural-network evaluation library**. This package is the neural
network library (position analysis, cube decisions, rollouts) — not the full
GNU Backgammon application (GUI, match play).

This project integrates with the upstream GNUBG C/C++ code, maintained
separately by the GNU Backgammon team.

You can contribute to either:

1. **The full GNUBG project (C/C++ application and core)**
2. **The gnubg-nn-pypi project (Python bindings to the neural network library)**

Please read the relevant section(s) below based on your area of interest.

-----------------------------------------
1. Contributing to the full GNUBG project
-----------------------------------------

The upstream GNU Backgammon application and engine are maintained at:
- Source: https://git.savannah.gnu.org/cgit/gnubg/gnubg.git
- Contributor registration: https://savannah.gnu.org/people/

If you'd like to contribute to core engine features, neural network logic,
or C/C++ code:
- Familiarize yourself with the existing codebase, especially files like
  `analyze.cc`, `danalyze.cc`, and `bearoff.c`.
- Discuss proposed changes via the mailing list:  
  https://lists.gnu.org/mailman/listinfo/gnubg
- Follow GNU project coding and license guidelines (GPL v2).

---------------------------------------------
2. Contributing to gnubg-nn-pypi (Python API)
---------------------------------------------

The `gnubg-nn-pypi` project exposes the GNUBG neural network evaluation library to Python.

GitHub Repo: https://github.com/StonesAndDice/gnubg-nn-pypi

You can contribute by:

- **Reporting Bugs:**  
  File an issue at https://github.com/StonesAndDice/gnubg-nn-pypi/issues

- **Writing Code:**
    - Fork the repository and create a feature branch.
    - Write clear, tested, and documented code.
    - Follow PEP8 conventions.
    - Submit a pull request with a clear explanation of your change.

- **Testing & Validation:**
    - Run: `python3 -m unittest discover -s gnubg_nn.tests`
    - Add new unit tests if you're introducing new features.

- **Improving Documentation:**
    - Propose updates to the README or inline docstrings.
    - Suggest usage examples or tutorials.

- **Helping with Outreach or Translations:**  
  We welcome translated materials, packaging help, and educational outreach.

--------------------------------
Licensing and Code Ownership
--------------------------------

All contributions must be compatible with GPL v2.

By submitting a pull request, you affirm that your contributions are your own
original work, or that you have permission to contribute them under the
project's license.

---------------------
Need Help?
---------------------

Please reach out via:
- GitHub Issues: https://github.com/StonesAndDice/gnubg-nn-pypi/issues
- Mailing List: https://lists.gnu.org/mailman/listinfo/gnubg

Thank you for contributing to the GNUBG neural network library and the broader GNUBG community!
