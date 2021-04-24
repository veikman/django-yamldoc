# -*- coding: utf-8 -*-
r"""Functions for prepopulating YAML.

For example, to get a YAML document with an empty title field ready to be
filled in by a human editor, you would write a lacuna to a text file, without
YAML serialization:

    with open(path, ...) as f:
        for key, value in dict(title=lacuna(), ...).items():
            f.write(f'{key}: {value}\n')

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

from typing import List, Tuple

#######################
# INTERFACE FUNCTIONS #
#######################


def placeholder(template: str, indentation: str = '  ', level: int = 1):
    """Produce a placeholder for human input in YAML."""
    return template.format(level * indentation)


def lacuna(**kwargs) -> str:
    """Produce a placeholder for a string."""
    return placeholder('|-\n{}', **kwargs)


def empty_list(**kwargs) -> str:
    """Produce a placeholder for a list of short strings."""
    return placeholder("\n{}- ''", **kwargs)


def map(entries: List[Tuple[str, str]] = None, **kwargs) -> str:
    """Produce a placeholder for a map of short strings."""
    if entries is None:
        entries = [('', '')]
    block = '\n{0}'.join(f"'{k}': '{v}'" for k, v in entries)
    return placeholder(f'\n{{0}}{block}', **kwargs)
