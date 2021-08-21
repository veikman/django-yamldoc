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
import logging
import os
import warnings
from argparse import ArgumentTypeError
from collections import OrderedDict
from pathlib import Path
from subprocess import run
from typing import Any, Callable, Dict, Generator, Optional

from django.db.models import Model
from yamlwrap import transform as transform_yaml

#######################
# INTERFACE FUNCTIONS #
#######################


def find_assets(root: Path, pattern: str = "**/*.yaml",
                selection: Optional[Path] = None,
                pred: Callable[[Path], bool] = lambda _: True
                ) -> Generator[Path, None, None]:
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


def find_files(root_folder: str, identifier=lambda _: True, single_file=None
               ) -> Generator[str, None, None]:
    """Generate relative paths of asset files with prefix, under a folder.

    Similar to find_assets, but based on os.walk and strings.

    """
    warnings.warn(
        "“yamldoc.util.file.find_files” is deprecated in favour of "
        "“find_assets”.",
        DeprecationWarning
    )

    if single_file:
        if identifier(single_file):
            yield single_file
        return

    for dirpath, _, filenames in os.walk(root_folder):
        logging.debug('Searching for files in {}.'.format(dirpath))
        for f in filenames:
            if identifier(f):
                yield os.path.join(dirpath, f)


def transform(model: Model, raw: str, **kwargs):
    """Close over a model to mould YAML after that model."""
    assert model

    # This function uses the internal _meta property and will therefore be
    # removed in a future major release.
    warnings.warn(
        '“yamldoc.util.file.transform” is deprecated in favour of using '
        '“yamldoc.util.misc.field_order_fn” and “.alphabetize_tags” '
        'as demonstrated in “yamldoc.management.misc”.',
        DeprecationWarning
    )

    def order_assetmap(fragment: Dict[str, Any]) -> OrderedDict:
        """Produce an ordered dictionary for replacement of a regular one.

        The passed dictionary should correspond to a model instance.
        The ordering is based on the model’s schema and is meant to simplify
        human editing of YAML.

        The yaml module saves an OrderedDict as if it were a regular dict,
        but does respect its ordering, until it is loaded again.

        """
        ordered = OrderedDict()
        for f in (f.name for f in model._meta.fields):
            if f in fragment:
                ordered[f] = fragment[f]
        for f in fragment:
            # Any metadata or raw data not named like database fields.
            if f not in ordered:
                ordered[f] = fragment[f]

        if 'tags' in ordered:
            # Sort alphabetically and remove duplicates.
            ordered['tags'] = sorted(set(ordered['tags']))

        return ordered

    return transform_yaml(raw, map_fn=order_assetmap, **kwargs)


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
