# -*- coding: utf-8 -*-
"""Miscellaneous utility functions.

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

from typing import Any, Callable, Dict, Tuple

import django.utils.html
import django.utils.text
import unidecode
from django.template.defaultfilters import slugify as default_slugify

#######################
# INTERFACE FUNCTIONS #
#######################


# Raw represents data for a Django model, stored in serialized text format.
Raw = Dict[str, Any]


def slugify(string):
    """Return a slug representing passed string."""
    clean = django.utils.html.strip_tags(str(string))
    if not clean:
        s = 'Failed to slugify "{}": Nothing left after HTML tags.'
        raise ValueError(s.format(string))

    # The following imitates django-taggit.
    slug = default_slugify(unidecode.unidecode(clean))

    if not slug:
        s = 'Failed to slugify "{}": Put in {}, got nothing back.'
        raise ValueError(s.format(string, clean))

    return slug


def copy_in_order(a: Raw, b: Raw) -> Raw:
    """Copy all entries in a to b in their existing order. Return b.

    It is assumed here that b already contains some of the entries from a in a
    significant order, but not necessarily all, and/or some entries not in a.

    """
    for k in a:
        b[k] = a[k]
    return b


def field_order_fn(fields: Tuple[str],
                   finalizer: Callable[[Raw, Raw], Raw] = copy_in_order):
    """Close over a mapping function for yamlwrap.

    “fields” is expected to be tuple(f.name for f in model._meta.fields) or an
    equivalent tuple of strings naming significant database fields in a
    preferred order for storage in YAML.

    With the default “finalizer”, preserve even those entries that are not
    named in “fields”, but put them after “fields”, without changing their
    internal order.

    """
    def order(fragment: Raw) -> Raw:
        """Produce a dictionary for replacement of another.

        Any metadata or raw data not named like database fields is retained,
        with its internal order unchanged.

        """
        ordered: Raw = {}
        for f in fields:
            try:
                ordered[f] = fragment[f]
            except KeyError:
                pass
        return finalizer(fragment, ordered)
    return order


def unique_alphabetizer(key: str):
    """Close over a mapping function for yamlwrap."""
    def order(fragment: Raw):
        """Sort raw data for a field alphabetically and remove duplicates."""
        if key in fragment:
            fragment[key] = sorted(set(fragment[key]))
        return fragment
    return order


alphabetize_tags = unique_alphabetizer('tags')  # Example.
