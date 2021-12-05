# -*- coding: utf-8 -*-
"""Functions for text files of serialized data.

This module is concerned with the maintenance of text for use on Django sites.
In particular, with the maintenance of text files formatted with YAML and open
to programmatic manipulation (grep etc.).

Author: Viktor Eikman <viktor.eikman@gmail.com>

-------

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <https://www.gnu.org/licenses/>.

"""

###########
# IMPORTS #
###########

import datetime
from argparse import ArgumentTypeError
from pathlib import Path
from subprocess import run
from typing import Callable, Generator, Optional

#######################
# INTERFACE FUNCTIONS #
#######################


def count_lines(path: Path) -> int:
    """Count the number of lines of text in passed file."""
    assert path.is_file()
    with path.open(mode='rb') as f:
        return 1 + sum(1 for line in f)


def find_assets(
    root: Path,
    pattern: str = "**/*.yaml",
    selection: Optional[Path] = None,
    pred: Callable[[Path],
                   bool] = lambda _: True) -> Generator[Path, None, None]:
    """Generate paths to asset files, recursively globbing a directory.

    If a “selection” argument is provided, screen only that path, even if it
    does not lie under the root directory. This design is intended for ease of
    use with a CLI that takes both folder and file arguments.

    """
    if selection:
        if pred(selection):
            yield selection
        return

    yield from filter(pred, root.glob(pattern))


def date_of_last_edit(path: Path) -> datetime.date:
    """Find the date when passed file was last edited."""
    return datetime.date.fromtimestamp(timestamp_of_last_edit(path))


def timestamp_of_last_edit(path: Path) -> float:
    """Find the second since Epoch when passed file was last edited.

    Prefer a VCS (Git only) timestamp and fall back to the file system.

    """
    cmd = ['git', 'log', '--max-count=1', '--format=%ct', '--', str(path)]
    git = run(cmd, capture_output=True, cwd=path.parent)
    if git.stdout and not git.returncode:
        # The output should be the timestamp of committing the last change.
        return float(git.stdout.strip())
    return path.stat().st_mtime


def existing_file(candidate: str):
    """Convert a CLI argument to an absolute file path."""
    path = Path(candidate).resolve()
    if not path.is_file():
        raise ArgumentTypeError(f"Not a file: {path}")
    return path


def existing_dir(candidate: str):
    """Convert a CLI argument to an absolute folder path."""
    path = Path(candidate).resolve()
    if not path.is_dir():
        raise ArgumentTypeError(f"Not a folder: {path}")
    return path
