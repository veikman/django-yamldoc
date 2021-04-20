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

import django.utils.html
import django.utils.text
import unidecode
from django.template.defaultfilters import slugify as default_slugify

#######################
# INTERFACE FUNCTIONS #
#######################


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
