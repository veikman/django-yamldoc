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

import logging
import os
from collections import OrderedDict
from typing import Any, Dict

from django.db.models import Model
from yamlwrap import transform as transform_yaml

#######################
# INTERFACE FUNCTIONS #
#######################


def find_files(root_folder: str, identifier=lambda _: True, single_file=None):
    """Generate relative paths of asset files with prefix, under a folder.

    If a "single_file" argument is provided, it is assumed to be a relative
    path to a single file. This design is intended for ease of use with a CLI
    that takes both folder and file arguments, but should not be considered
    a stable API.

    """
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
