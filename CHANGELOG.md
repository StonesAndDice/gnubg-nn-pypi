## [Unreleased] - 1.1.0a7
### Changed
- Fix README Quick Start: corrects function names (`board_from_position_id`, `best_move`, `moves`) and import (`import gnubg_nn`)
- Add prominent package-name warning in README: `gnubg-nn` not `gnubg`
- Document that the engine auto-initialises on import; `initnet()` is not required
- Add Migration / Legacy Names section to API docs mapping old `pygnubg` names to new names
- Add Package Name warning section to API docs
- Add deprecated aliases `boardfromkey`, `boardfromid`, `bestmove` for backwards compatibility
- Expose additional utility functions in `__all__`: `eq2mwc`, `mwc2eq`, `eq2mwc_stderr`, `mwc2eq_stderr`, `luckrating`, `errorrating`, `parsemove`, `movetupletostring`, `full_version`, `short_version`, `git_revision`

## [1.1.0a6] - 2026-04-30
### Changed
- Clarify docs: GNUBG Neural Networks is the library, not the full game (fixes #40)
- Add opening rolls and opening replies tests (fixes #42)

## [1.1.0a4] - 2026-04-01
### Changed
- Use PYPI_TEST_TOKEN for TestPyPI (fixes #38)
- Fix release: drop cp38/cp39 for `requires-python >=3.10`, clean `CIBW_SKIP` (fixes #36)
- Use correct Twine token per release environment (fixes #34)
- Rename compiled extension module to `_gnubg_nn` (fixes #31)
- New module structure with updated packaging

## [1.1.0a2] - 2025-11-01
### Added
- Cube Decision Evaluation support (`evaluate_cube_decision`)
- Windows support for Python versions beyond 3.10 (fixes #8)
- ReadTheDocs documentation site
- Dynamic version generation

### Changed
- Linting fixes across C/C++ source files
- Improved documentation: updated module comments and project docs
- Simplified Getting Started section in README and RTD landing page

## [1.1.0a1] - 2025-05-25
### Initial Release
- First public release of the GNUBG Python extension module.
- Includes:
    - Python bindings to GNUBG neural network evaluation (via `ctypes`)
    - Meson build system support for Windows and Linux
    - Exported key C functions from `gnubgmodule.cpp`
    - Example input vector evaluation pipeline
    - Early support for Position ID to input vector generation
