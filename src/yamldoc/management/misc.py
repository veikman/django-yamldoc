# -*- coding: utf-8 -*-
"""Standardized base classes for management commands.

Not being placed in a “commands” folder, these do not hook into Django’s site
CLI.

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

import datetime
import logging
import os
import re
import string
import subprocess

import django.core.management.base
from yamlwrap import dump, load

from yamldoc.util.file import find_files, transform


class LoggingLevelCommand(django.core.management.base.BaseCommand):
    """A command that uses Django's verbosity for general logging."""

    def handle(self, **kwargs):
        """Adapt Django's standard verbosity argument for general use."""
        logging.basicConfig(level=10 * (4 - kwargs['verbosity']))


class _RawTextCommand(LoggingLevelCommand):
    """Abstract base class for YAML processors."""

    _default_folder = None
    _default_file = None
    _file_prefix = None
    _file_ending = '.yaml'

    def add_arguments(self, parser):
        selection = parser.add_mutually_exclusive_group()
        selection.add_argument('-F', '--select-folder',
                               help='Find document(s) in non-default folder'),
        selection.add_argument('-f', '--select-file',
                               help='Act on single document'),
        self._add_selection_arguments(selection)

    def _add_selection_arguments(self, group):
        pass

    def handle(self, *args, **kwargs):
        """Handle command.

        This is an override to make full arguments available to overrides.

        Inheritors can't simply call super() for this effect without
        bundling together all of the keyword arguments manually.

        """
        self._args = kwargs
        super().handle(*args, **kwargs)
        self._handle(**kwargs)

    def _handle(self, **kwargs):
        raise NotImplementedError()

    def _get_files(self, folder=None, file=None, **kwargs):
        """Find YAML documents to work on."""
        folder = folder or self._default_folder
        file = file or self._default_file
        assert folder or file
        files = tuple(find_files(folder, single_file=file,
                                 identifier=self._file_identifier,
                                 **kwargs))
        if not files:
            logging.error('No eligible files.')
        return files

    def _file_identifier(self, filename):
        """Return a Boolean for whether or not a found file is relevant."""
        basename = os.path.basename(filename)
        if self._file_prefix:
            if not basename.startswith(self._file_prefix):
                return False
        if self._file_ending:
            if not basename.endswith(self._file_ending):
                return False
        return True


class RawTextEditingCommand(_RawTextCommand):
    """A command that edits raw text (YAML) document files."""

    help = 'Edit raw text'

    _model = None
    _can_describe = False
    _can_update = False
    _takes_subject = True

    _filename_character_whitelist = string.ascii_letters + string.digits

    def add_arguments(self, parser):
        """Add additional CLI arguments for raw text sources."""
        super().add_arguments(parser)

        action = parser.add_mutually_exclusive_group()
        action.add_argument('-t', '--template', action='store_true',
                            help='Add a template for a new data object')

        if self._can_describe:
            s = 'Create new document about subject'
            if self._takes_subject:
                action.add_argument('--describe', metavar='SUBJECT', help=s)
            else:
                action.add_argument('--describe', action='store_true', help=s)

        if self._can_update:
            s = 'Update from changes in subject'
            if self._takes_subject:
                action.add_argument('-u', '--update', metavar='SUBJECT',
                                    help=s)
            else:
                action.add_argument('-u', '--update', action='store_true',
                                    help=s)

        action.add_argument('-s', '--standardize', action='store_true',
                            help='Batch preparation for revision control'),
        action.add_argument('--wrap', action='store_true',
                            help='Split long paragraphs for readability'),
        action.add_argument('--unwrap', action='store_true',
                            help='Join long paragraphs into single lines')
        self._add_action_arguments(action)

    def _add_action_arguments(self, group):
        pass

    def _handle(self, select_folder=None, select_file=None,
                template=None, describe=None, update=None,
                wrap=False, unwrap=False, standardize=False, **kwargs):
        filepath = select_file or self._default_file

        if filepath:
            if os.path.exists(filepath):
                with open(filepath, mode='r', encoding='utf-8') as f:
                    eof = sum(1 for line in f) + 1
            else:
                eof = 1

        if template:
            if not filepath:
                logging.error('No filepath for template.')
                return

            self._append_template(filepath)

        if describe or update:
            if not filepath:
                logging.error('No filepath for description.')
                return

            self._describe(describe or update, bool(update), filepath)

        if standardize:
            unwrap = wrap = True

        if filepath and not any((wrap, unwrap)):
            if self._should_open_file_at_end(template):
                line = eof
            else:
                line = 1

            subprocess.call(['editor', filepath, f'+{line}'])
        else:
            if not wrap or unwrap or filepath:
                logging.info('Transforming all without standardization.')
            self._transform(select_folder or self._default_folder, filepath,
                            unwrap=unwrap, wrap=wrap)

    def _should_open_editor(self):
        """Determine whether to open a text editor. A stub."""
        return True

    def _should_open_file_at_end(self, template):
        """Filter for whether or not to do manual editing from the bottom."""
        return bool(template)

    def _append_template(self, filepath, **kwargs):
        with open(filepath, mode='a', encoding='utf-8') as f:
            self._write_template(f, **kwargs)

    def _write_template(self, open_file, **kwargs):
        pass

    def _describe(self, subject, is_update, filepath):
        """Compose a document on a subject."""
        if is_update:
            if not os.path.exists(filepath):
                logging.error('File for prior description does not exist.')
                return

            with open(filepath, mode='r', encoding='utf-8') as f:
                old_yaml = f.read()
        else:
            if os.path.exists(filepath):
                logging.error('File for new description already exists.')
                return

            old_yaml = None

        new_yaml = self._data_from_subject(subject, old_yaml=old_yaml)
        self._write_spec(filepath, dump(new_yaml))

    def _data_from_subject(self, subject, old_yaml=None):
        """Update a specification (description) from its actual subject.

        Take an optional unparsed YAML text string representing a previous
        version of the specification.

        """
        raise NotImplementedError

    def _data_manipulation(self, data):
        """General manipulation of data, e.g. from Internet searches."""
        pass

    def _transform(self, folder, filepath, **kwargs):
        """Transform YAML documents for editing or source control."""
        for filepath in self._get_files(folder=folder, file=filepath):
            with open(filepath, mode='r', encoding='utf-8') as f:
                old_yaml = f.read()

            new_yaml = transform(self._model, old_yaml,
                                 postdescent_fn=self._data_manipulation,
                                 **kwargs)
            self._write_spec(filepath, new_yaml)

    def _write_spec(self, filepath, new_yaml, mode='w'):
        if new_yaml:
            with open(filepath, mode=mode, encoding='utf-8') as f:
                f.write(new_yaml)
        else:
            s = 'Abstaining from writing to {}: No change in YAML.'
            logging.info(s.format(filepath))

    def _new_filepath(self, fragment, folder):
        folder_override, _, filename = os.path.split(fragment)
        if self._file_prefix:
            filename = '_'.join((self._file_prefix, filename))
        filename = f'{filename}.yaml'
        blacklist = f'[^{self._filename_character_whitelist}]'
        filename = filename.format(re.sub(blacklist, '', filename))
        folder = folder_override or folder or self._default_folder
        return os.path.join(folder, filename)


class RawTextRefinementCommand(_RawTextCommand):
    """A command that instantiates models from raw text sources."""

    help = 'Create database object(s) from YAML file(s)'

    def add_arguments(self, parser):
        """Add additional CLI arguments for refinement."""
        super().add_arguments(parser)
        parser.add_argument('--additive', action='store_true',
                            help='Do not clear relevant table(s) first'),

    def _handle(self, *args, additive=None, **kwargs):
        if not additive:
            self._clear_database()

        self._create(**kwargs)

    def _clear_database(self):
        self._model.objects.all().delete()

    def _create(self, select_folder=None, select_file=None, **kwargs):
        files = tuple(self._get_files(folder=select_folder, file=select_file))
        assert files
        self._model.create_en_masse(tuple(map(self._parse_file, files)))

    def _parse_file(self, filepath):
        logging.debug('Parsing {}.'.format(filepath))
        with open(filepath, mode='r', encoding='utf-8') as f:
            return load(f.read())


class DocumentRefinementCommand(RawTextRefinementCommand):
    """A specialist on documents corresponding to single model instances."""

    def _parse_file(self, filepath):
        data = super()._parse_file(filepath)

        if 'date_updated' not in data:
            mtime = os.path.getmtime(filepath)
            date_updated = datetime.date.fromtimestamp(mtime)
            data['date_updated'] = date_updated

        return data
