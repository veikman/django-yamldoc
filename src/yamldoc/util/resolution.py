# -*- coding: utf-8 -*-
"""Collected utilities for resolution of text markup.

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

from functools import partial
from typing import Callable, Optional

from django.db.models import Model
from markdown import markdown
from yamlwrap import unwrap

from yamldoc.util.markup import Inline
from yamldoc.util.traverse import Node, site

########################
# LOCAL COMPOUND TYPES #
########################


Resolver = Callable[[Model, Optional[str]], Optional[str]]


#############
# TRAVERSAL #
#############


def map_resolver(resolver: Resolver, **kwargs):
    """Map a markup resolution function (a resolver) over a Django site."""
    return map(partial(visit_field, resolver), site(**kwargs))


def visit_field(resolver: Resolver, node: Node):
    """Resolve markup in one field of one instance."""
    instance, field, prior_contents = node
    new_contents = None
    if prior_contents is not None:
        new_contents = resolver(instance, prior_contents)
    if new_contents is None and not field.null:
        # "The Django convention is to use the empty string...”
        new_contents = ''
    setattr(instance, field.name, new_contents)
    instance.save()


#############
# RESOLVERS #
#############

# Complete and partial markup resolution functions.


def markdown_on_string(raw: str) -> str:
    """Convert markdown to HTML with specific extensions.

    This requires the raw input to be unwrapped already.

    """
    extensions = ['markdown.extensions.footnotes',
                  'markdown.extensions.toc']
    return markdown(raw, extensions=extensions)


def inline_on_string(raw: str, **kwargs) -> str:
    """Resolve all registered Inline Ovid markup in passed string."""
    return Inline.collective_sub(raw, **kwargs)


def combo(instance: Model, raw: str) -> str:
    """Act as an example resolver for resolve_markup.

    The order of operations here is intended for inline internal markup to be
    able to produce new Markdown. It doesn’t have to be that way.

    The ORM instance being processed by resolve_markup is passed as a keyword
    argument to each Ovid-registered function, as expected in
    yamldoc.util.markup’s examples.

    """
    return markdown_on_string(inline_on_string(unwrap(raw), subject=instance))
