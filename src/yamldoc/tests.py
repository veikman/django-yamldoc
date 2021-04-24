# -*- coding: utf-8 -*-
"""App unit tests.

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

from dataclasses import dataclass

import django.template.defaultfilters
from django.test import TestCase

from yamldoc.models import Document, MarkupField
from yamldoc.util.file import transform
from yamldoc.util.markup import Inline
from yamldoc.util.misc import slugify
from yamldoc.util.placeholder import lacuna
from yamldoc.util.placeholder import map as placemap
from yamldoc.util.resolution import combo, map_resolver, markdown_on_string
from yamldoc.util.traverse import classbased_selector, get_explicit_fields


class _CookingMarkdown(TestCase):

    def test_two_single_line_paragraphs(self):
        s = 'Line 1.\n\nLine 2.'
        ref = '<p>Line 1.</p>\n<p>Line 2.</p>'
        self.assertEqual(ref, markdown_on_string(s))

    def test_minor_indentation_is_ignored(self):
        # This is normal behaviour for Python's markdown.
        # Not a consequence of the site's paragraph wrapping/unwrapping.
        s = 'Line 1.\n\n  Line 2.'
        ref = '<p>Line 1.</p>\n<p>Line 2.</p>'
        self.assertEqual(ref, markdown_on_string(s))

    def test_major_indentation_is_noted(self):
        s = 'Line 1.\n\n    Line 2.'
        ref = ('<p>Line 1.</p>\n'
               '<pre><code>Line 2.\n</code></pre>')
        self.assertEqual(ref, markdown_on_string(s))

    def test_flat_sparse_bullet_list(self):
        s = ('* Bullet A.\n'
             '\n'
             '* Bullet B.')
        ref = ('<ul>\n'
               '<li>\n'
               '<p>Bullet A.</p>\n'
               '</li>\n'
               '<li>\n'
               '<p>Bullet B.</p>\n'
               '</li>\n'
               '</ul>')
        self.assertEqual(ref, markdown_on_string(s))

    def test_flat_dense_bullet_list(self):
        s = ('* Bullet A.\n'
             '* Bullet B.')
        ref = ('<ul>\n'
               '<li>Bullet A.</li>\n'
               '<li>Bullet B.</li>\n'
               '</ul>')
        self.assertEqual(ref, markdown_on_string(s))

    def test_nested_sparse_bullet_list(self):
        # As with <pre> above, this needs four spaces of indentation.
        s = ('* Bullet Aa.\n'
             '\n'
             '    * Bullet Ab.')
        ref = ('<ul>\n'
               '<li>\n'
               '<p>Bullet Aa.</p>\n'
               '<ul>\n'
               '<li>Bullet Ab.</li>\n'
               '</ul>\n'
               '</li>\n'
               '</ul>')
        self.assertEqual(ref, markdown_on_string(s))

    def test_nested_dense_bullet_list(self):
        s = ('* Bullet A.\n'
             '    * Bullet B.')
        ref = ('<ul>\n'
               '<li>Bullet A.<ul>\n'
               '<li>Bullet B.</li>\n'
               '</ul>\n'
               '</li>\n'
               '</ul>')
        self.assertEqual(ref, markdown_on_string(s))


class _CookingInternalMarkup(TestCase):

    def test_multiline(self):
        def mask(s):
            return s

        Inline(mask)

        s0 = """Uh {{mask|huh.

        Nu}} uh."""
        s1 = """Uh huh.

        Nu uh."""
        self.assertEqual(Inline.collective_sub(s0), s1)


class _CookingStructure(TestCase):

    class _PseudoModel():
        class _meta():
            @dataclass
            class _PseudoField():
                name: str
            fields = (_PseudoField('a'),
                      _PseudoField('c'),
                      _PseudoField('b'))

    def test_sort_single_object_with_model(self):
        o = ("b: 2\n"
             "a: 1\n"
             "c: 3")
        ref = ("a: 1\n"
               "c: 3\n"
               "b: 2\n")
        self.assertEqual(ref, transform(self._PseudoModel, o))

    def test_sort_list(self):
        o = ("- b: 2\n"
             "  a: 1\n"
             "- c: 3\n")
        ref = ("- a: 1\n"
               "  b: 2\n"
               "- c: 3\n")
        self.assertEqual(ref, transform(self._PseudoModel, o))


class _ExplicitFieldSelection(TestCase):
    def test_absence_of_metadata(self):
        with self.assertRaises(AttributeError):
            get_explicit_fields(Document)


class _ClassBasedFieldSelection(TestCase):
    def test_minimal(self):
        with self.assertRaises(AssertionError):
            classbased_selector({})

    def test_mismatch(self):
        f = classbased_selector((int,))
        self.assertEqual(f(Document), ())

    def test_fair_weather(self):
        f = classbased_selector((MarkupField,))
        self.assertEqual(f(Document),
                         tuple(f for f in Document._meta.fields
                               if f.name in {'summary', 'ingress', 'body'}))


class _CookingSite(TestCase):

    def test_chain(self):
        raws = dict(title='Cove, Oregon',
                    body='**Cove** is a city\nin Union County.\n',
                    date_created='2016-08-03',
                    date_updated='2016-08-04')
        doc = Document.create(**raws)

        ref = '**Cove** is a city\nin Union County.\n'
        self.assertEqual(ref, doc.body,
                         msg='Text mutated in document creation.')

        # Depending on the Django project wherein yamldoc is tested,
        # traverse.app may fail to include Document.
        # TODO: Overwrite settings for testing.
        list(map_resolver(combo))

        # At this point, as of Django 3.2, doc.refresh_from_db() is inadequate
        # to retrieve the value set by map_resolver(). Query instead.
        doc = Document.objects.get(id=1)

        ref = 'Cove, Oregon'
        self.assertEqual(ref, doc.title)
        ref = ''  # Not null.
        self.assertEqual(ref, doc.summary)
        ref = '<p><strong>Cove</strong> is a city in Union County.</p>'
        self.assertEqual(ref, doc.body)


class _Other(TestCase):

    def _compose(self, base):
        # Trivial semi-realistic template production.
        composite = dict(key=base)
        return '\n'.join(f'{k}: {v}' for k, v in composite.items())

    def test_placeholder_lacuna0(self):
        ref = "key: |-\n"
        self.assertEqual(ref, self._compose(lacuna(level=0)))

    def test_placeholder_lacuna1(self):
        ref = "key: |-\n  "
        self.assertEqual(ref, self._compose(lacuna()))

    def test_placeholder_lacuna2(self):
        ref = "key: |-\n    "
        self.assertEqual(ref, self._compose(lacuna(level=2)))

    def test_placeholder_map_simple(self):
        entries = [('Blip McCracken', 'at your service')]
        ref = "key: \n  'Blip McCracken': 'at your service'"
        self.assertEqual(ref, self._compose(placemap(entries=entries)))

    def test_placeholder_map_complex(self):
        entries = [('', 'concierge'), ('', 'steward'), ('se lakne', '')]
        ref = ("key: \n    '': 'concierge'\n    '': 'steward'"
               "\n    'se lakne': ''")
        self.assertEqual(ref, self._compose(placemap(entries=entries,
                                                     level=2)))

    def test_slugification(self):
        s = 'This <em>sentence</em> has <span class="vague">some</span> HTML'
        ref = 'this-sentence-has-some-html'
        self.assertEqual(ref, slugify(s))

    def test_strip(self):
        s = 'A salute to <a href="www.plaid.com">plaid</a>.'
        ref = 'A salute to plaid.'
        self.assertEqual(ref, django.template.defaultfilters.striptags(s))

    def test_markdown_multiline(self):
        s = ('# A', '', '## a', '', '* li', '', 'p', '')
        ref = ('<h1 id="a">A</h1>', '<h2 id="a_1">a</h2>',
               '<ul>', '<li>li</li>', '</ul>',
               '<p>p</p>')

        self.assertEqual('\n'.join(ref),
                         markdown_on_string('\n'.join(s)))
