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

from collections.abc import Callable, Generator, Hashable
from typing import Optional, TypeGuard, Union, cast

import django.apps
from django.db.models import Field, ForeignObjectRel, Model

from yamldoc.models import MarkupField

########################
# LOCAL COMPOUND TYPES #
########################

ACL = frozenset[Union[type[Model], str]]  # Access control list.
FieldSelector = Callable[[Model], tuple[Field, ...]]
Identifier = Callable[[type[Model]], Hashable]
Node = tuple[Model, Field, Optional[str]]
Screen = Callable[[type[Model]], bool]
Traversal = Generator[Node, None, None]

############
# INTERNAL #
############


def _identityfier(m: type[Model]) -> Hashable:
    """Act as a type-annotated identity function and Identifier."""
    return cast(Hashable, m)


def _apps_from_site():
    return django.apps.apps.all_models.values()


###################
# FIELD SELECTION #
###################


def get_explicit_fields(subject_model: Model) -> tuple[Field, ...]:
    """Identify fields on passed model that may contain cookable markup.

    Interesting fields are found through an explicit opt-in
    "fields_with_markup" attribute. If no such data is available, raise
    AttributeError.

    Unfortunately, Django’s Model._meta (Meta) is locked down and does not
    accept this attribute.

    This function is a workaround for the fact that Django does not support
    reclassing (replacing) fields inherited from third-party parent model
    classes with yamldoc’s MarkupField.

    """
    return subject_model.fields_with_markup  # type: ignore[attr-defined]


def classbased_selector(
    allowlist: tuple[type[Field], ...],
) -> Callable[[Model], tuple[Field, ...]]:
    """Close over an allowlist as a fallback to get_explicit_fields."""
    assert allowlist  # isinstance does not accept an empty tuple.

    def is_allowed(field: Field | ForeignObjectRel) -> TypeGuard[Field]:
        return isinstance(field, allowlist)

    def field_selector(subject_model: Model) -> tuple[Field, ...]:
        try:
            return get_explicit_fields(subject_model)
        except AttributeError:  # No metadata specifically on markup.
            pass  # Fall back to inspection.

        return tuple(filter(is_allowed, subject_model._meta.get_fields()))

    return field_selector


markup_field_selector: FieldSelector = classbased_selector((MarkupField,))

###################
# MODEL SELECTION #
###################


def qualified_class_name(cls: type[Model]) -> str:
    """Return a string uniquely identifying a class (not cls.__qualname__).

    Produce the same name that __str__ on a type object does, without the
    "<class '...'>" wrapper.

    This function is an example of the Identifier interface. It is meant as a
    convenience for cases where direct references to models are not available
    for the definition of an ACL, for whatever reason.

    """
    return cls.__module__ + '.' + cls.__name__


def screen_from_acl(
    allow: ACL = frozenset(),
    deny: ACL = frozenset(),
    identifier: Identifier = _identityfier,
) -> Screen:
    """Define a Screen from mutually exclusive sets of models."""
    assert not (allow and deny)

    if deny:
        return lambda model: identifier(model) not in deny

    if allow:
        return lambda model: identifier(model) in allow

    # Default to include all.
    return lambda model: True


def screen_from_field_selector(
    field_selector: FieldSelector = markup_field_selector,
) -> Screen:
    """Define a Screen from a preliminary traversal.

    By default, the Screen will select those models that have any MarkupField
    on them, which is usually what you want.

    """

    def top_levels():
        for app_ in _apps_from_site():
            yield from filter(field_selector, app_.values())

    return screen_from_acl(allow=frozenset(top_levels()))


##############
# GENERATORS #
##############


def site(**kwargs) -> Traversal:
    """Traverse fields in the database of the current site."""
    for app_ in _apps_from_site():
        yield from app(app_, **kwargs)


def app(
    app_,
    screen: Optional[Screen] = None,
    field_selector=markup_field_selector,
) -> Traversal:
    """Traverse fields in the database of one app.

    The app here is expected to be packaged as if by site(). There is no
    Application class in Django 3.2.

    The default field_selector is effectively a no-op.

    """
    if screen is None:
        screen = screen_from_field_selector()
    for model_ in filter(screen, app_.values()):
        yield from model(model_, field_selector)


def model(
    model_: type[Model],
    field_selector: Callable[[type[Model]], tuple[Field, ...]],
) -> Traversal:
    """Traverse selected fields in the database table of passed model."""
    assert field_selector is not None
    field_allowlist: frozenset[Field] = frozenset(field_selector(model_))
    for instance_ in model_.objects.all():
        yield from instance(instance_, field_allowlist)


def instance(instance_: Model, field_allowlist: frozenset[Field]) -> Traversal:
    """Traverse selected fields on passed instance of a model."""
    for field in field_allowlist:
        yield (instance_, field, getattr(instance_, field.name))
