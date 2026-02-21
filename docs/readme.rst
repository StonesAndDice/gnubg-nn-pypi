.. image:: https://raw.githubusercontent.com/StonesAndDice/gnubg-nn-pypi/refs/heads/main/img/gerwinski-gnu-head.png
   :alt: GNUBG Neural Networks
   :align: center
   :width: 200px

GNUBG Neural Networks
=====================

This package provides the **neural network evaluation library** from the GNU Backgammon project — not the full backgammon application (GUI, match play). Use it to evaluate positions and cube decisions in Python.

.. image:: https://img.shields.io/pypi/dm/gnubg-nn-pypi.svg?label=PyPI%20downloads
   :target: https://pypi.org/project/gnubg-nn-pypi/
   :alt: PyPI Downloads

.. image:: https://img.shields.io/conda/dn/conda-forge/gnubg-nn-pypi.svg?label=Conda%20downloads
   :target: https://anaconda.org/conda-forge/gnubg-nn-pypi/
   :alt: Conda Downloads

.. image:: https://img.shields.io/github/issues/gnubg/gnubg-nn-pypi.svg
   :target: https://github.com/StonesAndDice/gnubg-nn-pypi/issues
   :alt: GitHub Issues

.. image:: https://img.shields.io/badge/license-GPL%20v2-blue.svg
   :target: #license
   :alt: GPL v2 License

.. image:: https://img.shields.io/badge/stackoverflow-Ask%20questions-blue.svg
   :target: https://stackoverflow.com/questions/tagged/gnubg
   :alt: Ask on Stack Overflow

**gnubg-nn** is a library that provides Python bindings to the GNUBG neural-network evaluation engine — the same engine used in the full GNU Backgammon application, but as a standalone library for scripts and tools.

**Project Links**

- **GNU Backgammon (full application):** https://www.gnu.org/software/gnubg/
- **Documentation:** http://www.gnubg.org/documentation/doku.php?id=gnu_backgammon_faq
- **Mailing list:** https://lists.gnu.org/mailman/listinfo/gnubg
- **Source code:** https://github.com/StonesAndDice/gnubg-nn-pypi
- **GNUBG Neural Networks (gnubg-nn) upstream:** https://git.savannah.gnu.org/cgit/gnubg/gnubg-nn.git
- **Contributing:** https://savannah.gnu.org/people/
- **Credits (full GNUBG project):** https://git.savannah.gnu.org/cgit/gnubg.git/tree/credits.sh

**Features**

- **Engine initialization & data loading** (neural-net weights, opening-book, bear-off tables)
- **Position classification** (``classify``) & **public-evaluation best move** (``pub_best_move``)
- **Board ↔ ID conversions** (``board_from_position_id``, ``board_from_position_key``, ``key_of_board``, ``position_id``)
- **Dice utilities** (``roll``) & **cube utilities** (``best_move``, ``pub_eval_score``)
- **Bear-off tools** (``bearoff_id_2_pos``, ``bearoff_probabilities``)
- **Legal-move enumeration** (``moves``) & **probabilistic evaluation** (``probabilities``)
- **Monte-Carlo rollouts** (``rollout``, ``cubeful_rollout``)
- **Equity lookup** (``equities.value(xAway, oAway)``)
- **Runtime engine tuning** via the ``set`` submodule

Testing
-------

After installation, run basic unit tests with:

.. code-block:: bash

   python3 -m unittest discover -s gnubg_nn.tests

AI-Assisted Development
-----------------------

Parts of this project were developed with the assistance of generative AI tools.

Specifically, the following models were used:

- **GPT-4o** (OpenAI ChatGPT)
- **o4-mini-high** (OpenAI ChatGPT)

These models were used to assist with code generation, documentation drafting, and architectural guidance. All outputs were reviewed and curated by a human before inclusion.

.. warning::

   Although human-reviewed, some AI-generated content may contain mistakes, inaccuracies, or outdated practices. Contributors and users should critically assess all code, comments, and documentation. We welcome corrections and improvements via pull requests or issues.

Code of Conduct
---------------

Please read the `Code of Conduct <https://github.com/StonesAndDice/gnubg-nn-pypi/blob/main/CONDUCT.md>`_
to learn how to interact positively.

Contributing
------------

Your expertise and enthusiasm are welcome! You can contribute by:

- Reviewing and testing pull requests
- Reporting and triaging issues
- Improving documentation, tutorials, and examples
- Enhancing engine parameters or submodules
- Maintaining website or branding assets
- Translating materials
- Assisting with outreach and onboarding
- Writing grant proposals or helping with fundraising

For more information, see our `Contributing Guide <https://github.com/StonesAndDice/gnubg-nn-pypi/blob/main/CONTRIBUTING.md>`_.
If you’re unsure where to start, open an issue or join the discussion on our mailing list!

Acknowledgments
---------------

This project builds upon the extensive work of the GNU Backgammon (GNUBG) community. The *gnubg-nn* library is the neural network evaluation component; the full backgammon application is maintained separately. Specifically the
`pygnubg <https://git.savannah.gnu.org/cgit/gnubg/gnubg-nn.git/tree/py>`_ program developed by Joseph Heled.

We express our gratitude to all contributors who have dedicated their time and expertise to the development of the GNUBG neural network library and its Python bindings.

- **AUTHORS.md**: A list of primary contributors to the `gnubg-nn-pypi` project can be found `here <https://github.com/StonesAndDice/gnubg-nn-pypi/blob/main/AUTHORS.md>`_.
- **GNU Backgammon (full project) credits.sh**: For a comprehensive list of contributors to the full GNUBG application, see the `credits.sh <https://git.savannah.gnu.org/cgit/gnubg.git/tree/credits.sh>`_ file.

We also thank the broader GNUBG community, including testers, translators, and mailing list participants, for their invaluable support.
