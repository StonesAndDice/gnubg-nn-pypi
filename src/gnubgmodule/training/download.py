"""Download GNU Backgammon's published reference net, benchmark rollouts,
and training data from https://alpha.gnu.org/gnu/gnubg/nn-training/.

These are the same files the original ``gnubg-nn`` project's own training
scripts assumed you'd already fetched by hand (see ``doc/gnubg-nn.texi``'s
"Training and Benchmark Data Files" chapter) -- this module just automates
that download, using only the standard library (no new dependency for what
is, mechanically, "GET a URL, decompress it").

Layout on the server (confirmed by hand, not assumed -- the two version
directories are NOT mirrors of each other):

* ``1.01/nets/nngnubg.weights.bz2`` -- the reference net.
* ``1.00/benchmarks/{contact,race,crashed}.bm.bz2`` -- rollout benchmark
  files, see :mod:`gnubg_nn.training.referr`.
* ``1.00/training_data/{contact,race,crashed}-train-data.bz2`` -- rollout-
  labeled training positions, see :mod:`gnubg_nn.training.train`.

Every file on the server also has a detached ``.sig`` GPG signature
alongside it; ``verify_signature=True`` (the default) downloads that too
so you can check it yourself (this module doesn't attempt GPG verification
itself -- that's a real dependency for a check most callers won't act on
programmatically, so it's left as a file on disk instead).
"""

from __future__ import annotations

import bz2
import urllib.request
from pathlib import Path
from typing import Iterable, Optional

BASE_URL = "https://alpha.gnu.org/gnu/gnubg/nn-training"

#: Position classes with published benchmark/training-data files.
CLASSES = ("contact", "race", "crashed")


def _download(url: str, dest: Path) -> Path:
    """Fetch ``url`` to ``dest`` (creating parent directories), returning
    ``dest``. Raises :class:`urllib.error.URLError` (or an HTTP error
    subclass of it) on failure -- not caught here, since a caller
    downloading several files needs to know which one failed."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:  # noqa: S310 -- fixed https host
        dest.write_bytes(response.read())
    return dest


def _download_and_decompress(url: str, dest: Path) -> Path:
    """Fetch a ``.bz2`` file and write its decompressed contents to
    ``dest`` (which should NOT include the ``.bz2`` suffix)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:  # noqa: S310 -- fixed https host
        compressed = response.read()
    dest.write_bytes(bz2.decompress(compressed))
    return dest


def _maybe_fetch_signature(url: str, dest: Path, verify_signature: bool) -> None:
    if verify_signature:
        _download(url + ".sig", Path(str(dest) + ".sig"))


def download_reference_net(
    dest_dir: Path | str, *, version: str = "1.01", verify_signature: bool = True
) -> Path:
    """Download GNU Backgammon's own published reference net
    (``nngnubg.weights``) into ``dest_dir``.

    :param dest_dir: Directory to write ``nngnubg.weights`` into (created
        if it doesn't exist).
    :param version: Server-side version directory. ``1.01`` is the only
        version confirmed to carry a ``nets/`` subdirectory as of writing.
    :param verify_signature: Also download the detached ``.sig`` file
        alongside it, for you to verify by hand (not verified here).
    :returns: Path to the downloaded, decompressed weights file.
    """
    dest_dir = Path(dest_dir)
    url = f"{BASE_URL}/{version}/nets/nngnubg.weights.bz2"
    dest = dest_dir / "nngnubg.weights"
    _maybe_fetch_signature(url, dest, verify_signature)
    return _download_and_decompress(url, dest)


def download_benchmark(
    position_class: str,
    dest_dir: Path | str,
    *,
    version: str = "1.00",
    verify_signature: bool = True,
) -> Path:
    """Download one class's rollout benchmark file (``<class>.bm``) into
    ``dest_dir`` -- see :func:`gnubg_nn.training.referr.benchmark_error`.

    :param position_class: One of :data:`CLASSES` (``"contact"``,
        ``"race"``, or ``"crashed"``).
    :raises ValueError: If ``position_class`` isn't one of :data:`CLASSES`.
    """
    if position_class not in CLASSES:
        raise ValueError(f"position_class must be one of {CLASSES}, got {position_class!r}")
    dest_dir = Path(dest_dir)
    url = f"{BASE_URL}/{version}/benchmarks/{position_class}.bm.bz2"
    dest = dest_dir / f"{position_class}.bm"
    _maybe_fetch_signature(url, dest, verify_signature)
    return _download_and_decompress(url, dest)


def download_training_data(
    position_class: str,
    dest_dir: Path | str,
    *,
    version: str = "1.00",
    verify_signature: bool = True,
) -> Path:
    """Download one class's rollout-labeled training data
    (``<class>-train-data``) into ``dest_dir`` -- see
    :mod:`gnubg_nn.training.train`.

    :param position_class: One of :data:`CLASSES`.
    :raises ValueError: If ``position_class`` isn't one of :data:`CLASSES`.
    """
    if position_class not in CLASSES:
        raise ValueError(f"position_class must be one of {CLASSES}, got {position_class!r}")
    dest_dir = Path(dest_dir)
    url = f"{BASE_URL}/{version}/training_data/{position_class}-train-data.bz2"
    dest = dest_dir / f"{position_class}-train-data"
    _maybe_fetch_signature(url, dest, verify_signature)
    return _download_and_decompress(url, dest)


def download_all(
    dest_dir: Path | str,
    *,
    classes: Iterable[str] = CLASSES,
    verify_signature: bool = True,
) -> list[Path]:
    """Convenience wrapper: download the reference net plus every class's
    benchmark and training data into ``dest_dir``.

    :returns: Every downloaded file's path, reference net first.
    """
    dest_dir = Path(dest_dir)
    paths = [download_reference_net(dest_dir, verify_signature=verify_signature)]
    for position_class in classes:
        paths.append(
            download_benchmark(position_class, dest_dir, verify_signature=verify_signature)
        )
        paths.append(
            download_training_data(position_class, dest_dir, verify_signature=verify_signature)
        )
    return paths


def _main(argv: Optional[list] = None) -> int:
    """CLI entry point -- see ``gnubg-nn-download --help``."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download GNU Backgammon's published reference net, "
        "benchmark rollouts, and training data."
    )
    parser.add_argument(
        "dest_dir", type=Path, help="Directory to download files into (created if needed)."
    )
    parser.add_argument(
        "--classes",
        nargs="+",
        choices=CLASSES,
        default=list(CLASSES),
        help="Which position classes to fetch benchmark/training data for (default: all).",
    )
    parser.add_argument(
        "--no-signatures",
        action="store_true",
        help="Skip downloading the .sig files alongside each asset.",
    )
    args = parser.parse_args(argv)

    for path in download_all(
        args.dest_dir, classes=args.classes, verify_signature=not args.no_signatures
    ):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = [
    "BASE_URL",
    "CLASSES",
    "download_reference_net",
    "download_benchmark",
    "download_training_data",
    "download_all",
]
