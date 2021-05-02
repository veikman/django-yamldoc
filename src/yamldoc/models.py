"""Models and related generic code for text-based databases.

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

from django.db import models, transaction

from yamldoc.util.misc import slugify


class MarkupField(models.TextField):
    """A text field expected to contain markup when first instantiated."""


class UploadableMixin():
    """A mix-in for making Django models text-based."""

    @classmethod
    @transaction.atomic
    def create_en_masse(cls, raws):
        """Create a mass of objects from raw data out of text files.

        Hierarchical relationships between objects are held over until all
        objects have been registered.

        """
        logging.debug('Instantiating {} en masse.'.format(cls))
        cls._finishing(cls._instantiate_en_masse(raws))

    @classmethod
    def _instantiate_en_masse(cls, raws):
        """Instantiate model en masse."""
        by_pk = dict()
        for raw_data, instance in cls._iterate_over_raw_data(raws):
            by_pk[instance.pk] = raw_data

        return by_pk

    @classmethod
    def _iterate_over_raw_data(cls, raws):
        """Assume each object in the raws describes one instance."""
        for item in raws:
            new = cls.create(**item)
            yield item, new

    @classmethod
    def _finishing(cls, by_pk):
        """Add finishing touches after mass instantiation.

        Take a mapping of model instance primary keys to raw data items.

        This default implementation notes hierarchical relationships
        between parent and child objects. It expects:

        * A field pointing to a parent object, named "parent_object".
        * A "slug" field.
        * For references to parents to be stored in text as strings that, when
          slugified, correspond to genuine parent slugs.

        """
        # Add parents, which we presume are now saved.
        for pk, item in by_pk.items():
            sluggable = item.get('parent_object')
            if not sluggable:
                continue

            slug = slugify(sluggable)
            try:
                parent = cls.objects.get(slug=slug)
            except cls.DoesNotExist:
                s = 'Stated parent “{}” not found.'
                logging.error(s.format(sluggable))
                continue

            if parent.pk == pk:
                s = 'Item is its own parent: “{}”.'
                logging.error(s.format(sluggable))
                continue

            child = cls.objects.get(pk=pk)
            child.parent_object = parent
            child.save()

    @classmethod
    def create(cls, title='', parent_object=None, tags=None, **kwargs):
        """Ignore parent object, because it may not be saved yet.

        Assume that any tags are to be managed as if by Taggit.

        """
        slug = slugify(title)
        new = cls.objects.create(title=title, slug=slug, **kwargs)
        if tags:
            new.tags.set(*tags)
        return new


class UploadableListMixin(UploadableMixin):
    """A variation for records kept within lists."""

    @classmethod
    def _iterate_over_raw_data(cls, raws):
        """Override parent method.

        Assume each object in the raws is a flat list describing one instance.

        """
        for iterable in raws:
            yield from super()._iterate_over_raw_data(iterable)


class Document(models.Model, UploadableMixin):
    """A general document model."""

    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255)

    subtitle = models.TextField()

    summary = MarkupField()

    ingress = MarkupField()
    body = MarkupField()

    date_created = models.DateField()
    date_updated = models.DateField()

    # Paths to any JavaScript files needed to present the content.
    scripts = models.TextField()

    parent_object = models.ForeignKey('self', related_name='children',
                                      null=True, on_delete=models.CASCADE)

    class Meta():
        """Model metadata."""

        abstract = True
        ordering = ['date_created', 'title']
