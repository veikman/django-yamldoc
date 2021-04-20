# -*- coding: utf-8 -*-
"""Utilities for traversing Django apps down to text fields.

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
from typing import (Callable, FrozenSet, Generator, Optional, Set, Tuple, Type,
                    Union)

import django.apps
from django.conf import settings
from django.db.models import Field, Model

########################
# LOCAL COMPOUND TYPES #
########################


Denylist = Set[Union[Type[Model], str]]
Node = Tuple[Model, str, Optional[str]]
Traversal = Generator[Node, None, None]


###################
# MINOR FUNCTIONS #
###################


def qualified_class_name(cls: Type) -> str:
    """Return a string uniquely identifying a class (not cls.__qualname__).

    Produce the same name that __str__ on a type object does, without the
    "<class '...'>" wrapper.

    This function is meant as part of a workaround for the difficulty of
    importing all the classes into a Django settings module that should
    be banned from treatment for markup.

    """
    return cls.__module__ + "." + cls.__name__


##############
# GENERATORS #
##############


def site(model_denylist: Optional[Denylist] = None, **kwargs) -> Traversal:
    """Traverse fields in the database of the current site.

    Default to denylisting and ordering according to site settings.

    """
    if model_denylist is None:
        try:
            model_denylist: Denylist = settings.MARKUP_MODEL_DENYLIST
        except AttributeError:
            model_denylist: Denylist = {}

    for app_ in django.apps.apps.all_models.values():
        yield from app(app_, model_denylist, **kwargs)


def app(app_, model_denylist: Denylist, namefinder=qualified_class_name,
        field_selector=lambda x: ()) -> Traversal:
    """Traverse fields in the database of one app.

    The app here is expected to be packaged as if by site(). There is no
    Application class in Django 3.2.

    The default field_selector is effectively a no-op.

    """
    for model_ in app_.values():
        # Not skipping superclasses would create trouble with Django's
        # handling of inheritance (through a OneToOne on the child class).
        if model_ in model_denylist or namefinder(model) in model_denylist:
            logging.debug(f'Not traversing {model}: Denylisted.')
            continue

        yield from model(model_, field_selector)


def model(model_: Type[Model],
          field_selector: Callable[[Type[Model]],
                                   Tuple[Type[Field]]]) -> Traversal:
    """Traverse selected fields in the database table of passed model."""
    assert field_selector is not None
    field_allowlist: FrozenSet[Field] = frozenset(field_selector(model_))
    for instance_ in model_.objects.all():
        yield from instance(instance_, field_allowlist)


def instance(instance_: Model, field_allowlist: FrozenSet[Field]) -> Traversal:
    """Traverse selected fields on passed instance of a model."""
    for field in field_allowlist:
        yield (instance_, field, getattr(instance_, field.name))
