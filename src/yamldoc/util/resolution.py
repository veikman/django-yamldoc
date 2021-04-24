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
from typing import Callable, Optional, Tuple, Type

from django.db.models import Field, Model
from markdown import markdown
from yamlwrap import unwrap

from yamldoc.models import MarkupField
from yamldoc.util.markup import Inline
from yamldoc.util.traverse import Node, site

########################
# LOCAL COMPOUND TYPES #
########################


Resolver = Callable[[Model, Optional[str]], Optional[str]]


###################
# FIELD SELECTION #
###################


def get_explicit_fields(model: Model) -> Tuple[Type[Field]]:
    """Identify fields on passed model that may contain cookable markup.

    Interesting fields are found through an explicit opt-in
    "fields_with_markup" attribute. If no such data is available, raise
    AttributeError.

    This is a workaround for the fact that Django does not support reclassing
    (replacing) fields inherited from third-party parent model classes with
    yamldoc’s MarkupField.

    """
    return model._meta.fields_with_markup


def classbased_selector(allowlist: Tuple[Type[Field]]):
    """Close over an allowlist as a fallback to get_explicit_fields."""
    assert allowlist  # isinstance does not accept an empty tuple.

    def field_selector(model: Model) -> Tuple[Type[Field]]:
        try:
            return get_explicit_fields(model)
        except AttributeError:  # No metadata specifically on markup.
            pass  # Fall back to inspection.
        return tuple(filter(lambda f: isinstance(f, allowlist),
                            model._meta.get_fields()))
    return field_selector


#############
# TRAVERSAL #
#############


def map_resolver(resolver: Resolver,
                 field_selector=classbased_selector((MarkupField,)),
                 **kwargs):
    """Map a markup resolution function (a resolver) over a Django site."""
    return map(partial(visit_field, resolver),
               site(field_selector=field_selector, **kwargs))


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
