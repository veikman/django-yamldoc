# -*- coding: utf-8 -*-
"""Collected utilities for registration and use of text markup.

The site-internal markup supported here is based on Ovid.

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

import logging
import os
import re
from typing import Optional

import django.conf
from django.db.models import Model
from ovid.inspecting import SignatureShorthand

from . import misc

###########
# CLASSES #
###########


# A registry for site-internal markup.
# Multiline support here should be considered unstable. It may be expensive
# and works poorly with functions that only generate e.g. <span>, without
# taking paragraphs into account and duplicating the span across each.
Inline = SignatureShorthand.variant_class(flags=re.DOTALL)


#########################
# REPLACEMENT FUNCTIONS #
#########################

# Generic internal markup for static documents.
# Call Inline.register on these as needed.


def br(subject: Optional[Model] = None):
    """Return a line break.

    This is a workaround for the way that pyaml.dump interacts with
    lines in YAML that end with Markdown's soft break ("  ").

    The presence of any line terminated with a space provokes pyaml
    to choose a flow-styled scalar representation even when pyaml.dump
    is explicitly set to use the '|' block style. The result makes
    affected documents far harder to edit.

    """
    return '<br />'


def media(path_fragment, subject: Optional[Model] = None,
          label: Optional[str] = None, transclude: Optional[bool] = None):
    """Link to media."""
    if not label:
        label = path_fragment

    if transclude:
        # Produce the full contents of e.g. an SVG file. No label.
        filepath = os.path.join(django.conf.settings.MEDIA_ROOT,
                                path_fragment)
        try:
            with open(filepath, mode='r', encoding='utf-8') as f:
                repl = f.read()
        except UnicodeDecodeError:
            logging.error('Failed to read Unicode from {}.'.format(filepath))
            raise
    else:
        # Produce a link.
        root = django.conf.settings.MEDIA_URL
        href = root + path_fragment
        repl = '<a href="{}">{}</a>'.format(href, label)

    return repl


def static(path_fragment: str, subject: Optional[Model] = None,
           label: Optional[str] = None):
    """Link to a static file."""
    if not label:
        label = path_fragment

    # Produce a link.
    root = django.conf.settings.STATIC_URL
    href = root + path_fragment
    repl = '<a href="{}">{}</a>'.format(href, label)

    return repl


def table_of_contents(subject: Optional[Model] = None, heading='Contents'):
    """Produce Markdown for a TOC with a heading that won’t appear in it."""
    return '<h2 id="{s}">{h}</h2>\n[TOC]'.format(s=misc.slugify(heading),
                                                 h=heading)
