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

import logging
import os
import string
import subprocess
from argparse import ArgumentParser
from pathlib import Path
from typing import Any, Dict, Generator, Optional

import django.core.management.base
from yamlwrap import dump, load, transform

from yamldoc.util.file import (count_lines, date_of_last_edit, existing_dir,
                               existing_file, find_assets)
from yamldoc.util.misc import Raw


class LoggingLevelCommand(django.core.management.base.BaseCommand):
    """A command that uses Django's verbosity for general logging."""

    def handle(self, **kwargs):
        """Adapt Django's standard verbosity argument for general use."""
        logging.basicConfig(level=10 * (4 - kwargs['verbosity']))


class _RawTextCommand(LoggingLevelCommand):
    """Abstract base class for YAML processors."""

    _default_folder: Optional[Path] = None
    _default_file: Optional[Path] = None
    _file_prefix: Optional[str] = None
    _file_ending = '.yaml'

    def add_arguments(self, parser: ArgumentParser):
        self._add_selection_arguments(parser)
        return parser

    def _add_selection_arguments(self, parser: ArgumentParser):
        selection = parser.add_mutually_exclusive_group()
        selection.add_argument('-F',
                               '--select-folder',
                               metavar='PATH',
                               type=existing_dir,
                               default=self._default_folder,
                               help='Find file(s) in non-default folder')
        selection.add_argument('-f',
                               '--select-file',
                               metavar='PATH',
                               type=existing_file,
                               default=self._default_file,
                               help='Act on single file')
        return selection

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

    def _deserialize_text(self, text: str, **kwargs) -> Raw:
        return load(text, **kwargs)

    def _parse_file(self, filepath: Path) -> Raw:
        logging.debug(f'Parsing {filepath}.')
        assert isinstance(filepath, Path)
        return self._deserialize_text(filepath.read_text())

    def _serialize_to_text(self, data: Raw, **kwargs) -> str:
        return dump(data, **kwargs)

    def _get_assets(self,
                    select_folder=None,
                    select_file=None,
                    **_) -> Generator[Path, None, None]:
        """Find YAML documents to work on."""
        assert select_folder or select_file
        return find_assets(select_folder,
                           selection=select_file,
                           pred=self._filepath_is_relevant)

    def _filepath_is_relevant(self, path: Path) -> bool:
        """Return a Boolean for whether or not a found file is relevant.

        This is a predicate function for find_assets().

        """
        if not path.is_file():
            # This is expected only if the user indicates a specific file on an
            # invalid path. Globbing is not expected to return non-files.
            logging.warning(f"Not a file: {path}.")
            return False
        if self._file_prefix and not path.name.startswith(self._file_prefix):
            logging.debug(f"Wrong prefix in file name: {path}.")
            return False
        if self._file_ending and not path.suffix == self._file_ending:
            logging.debug(f"Wrong suffix in file name: {path}.")
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

    def add_arguments(self, parser: ArgumentParser):
        """Add additional CLI arguments for raw text sources."""
        parser = super().add_arguments(parser)
        self._add_action_arguments(parser)
        return parser

    def _add_action_arguments(self, parser):
        action = parser.add_mutually_exclusive_group()
        action.add_argument('-t',
                            '--template',
                            action='store_true',
                            help='Add a template for a new data object')

        if self._can_describe:
            s = 'Create new document about subject'
            if self._takes_subject:
                action.add_argument('--describe',
                                    metavar='SUBJECT',
                                    type=Path,
                                    help=s)
            else:
                action.add_argument('--describe', action='store_true', help=s)

        if self._can_update:
            s = 'Update from changes in subject'
            if self._takes_subject:
                action.add_argument('-u',
                                    '--update',
                                    metavar='SUBJECT',
                                    type=Path,
                                    help=s)
            else:
                action.add_argument('-u',
                                    '--update',
                                    action='store_true',
                                    help=s)

        action.add_argument('-s',
                            '--standardize',
                            action='store_true',
                            help='Batch preparation for revision control')
        action.add_argument('--wrap',
                            action='store_true',
                            help='Split long paragraphs for readability')
        action.add_argument('--unwrap',
                            action='store_true',
                            help='Join long paragraphs into single lines')
        return action

    def _handle(self,
                select_folder=None,
                select_file=None,
                template=None,
                describe=None,
                update=None,
                wrap=False,
                unwrap=False,
                standardize=False,
                **kwargs):
        line = 1

        if template:
            if not select_file:
                logging.error('No filepath for template.')
                return

            if (self._should_open_file_at_end(template)
                    and os.path.exists(select_file) and not wrap
                    and not unwrap):
                # Prepare to open the file where the new material begins.
                line = count_lines(select_file) + 1

            if not self._append_template(select_file):
                # Editing aborted or validation failed etc.
                logging.warning('Template not appended.')
                return

        if describe or update:
            if not select_file:
                logging.error('No filepath for description.')
                return

            self._compose(describe or update, bool(update), select_file)

        if standardize:
            unwrap = wrap = True

        if select_file and not wrap and not unwrap:
            if (line == 1 and self._should_open_file_at_end(template)
                    and os.path.exists(select_file)):
                # Prepare to open the file at the very end.
                line = count_lines(select_file)

            subprocess.call(['editor', str(select_file), f'+{line}'])
        else:
            for path in self._get_assets(select_folder=select_folder,
                                         select_file=select_file):
                self._transform(unwrap, wrap, path)

    def _should_open_editor(self):
        """Determine whether to open a text editor. A stub."""
        return True

    def _should_open_file_at_end(self, template):
        """Filter for whether or not to do manual editing from the bottom."""
        return bool(template)

    def _append_template(self, filepath: Path, **kwargs) -> bool:
        with open(filepath, mode='a', encoding='utf-8') as f:
            self._write_template(f, **kwargs)
        return True

    def _write_template(self, open_file, **kwargs):
        pass

    def _compose(self, subject: Optional[Path], is_update: bool,
                 filepath: Path):
        """Compose a document on a subject."""
        old_yaml = None
        if is_update:
            if not filepath.is_file():
                logging.error('File for prior description does not exist.')
                return

            old_yaml = filepath.read_text()
        else:
            if not filepath.is_file():
                logging.error('File for new description already exists.')
                return

        new_yaml = self._data_from_subject(subject, old_yaml=old_yaml)
        self._write_spec(filepath, self._serialize_to_text(new_yaml))

    def _data_from_subject(self,
                           subject: Optional[Path],
                           old_yaml=None) -> Dict[str, Any]:
        """Update a specification (description) from its actual subject.

        Take an optional unparsed YAML text string representing a previous
        version of the specification.

        """
        raise NotImplementedError

    def _write_spec(self, path: Path, new_yaml: Optional[str], mode='w'):
        if not new_yaml:
            logging.info(f'Not writing to {path}: No new YAML.')
            return
        with path.open(mode=mode) as f:
            f.write(new_yaml)

    def _transform(self, unwrap: bool, wrap: bool, path: Path, **kwargs):
        """Transform the contents of one YAML file.

        If contents are changed, rewrite the file in place.

        """
        logging.debug(f'Transforming {path}.')
        assert path.is_file()
        new = transform(path.read_text(),
                        unwrap=unwrap,
                        wrap=wrap,
                        loader=self._deserialize_text,
                        dumper=self._serialize_to_text,
                        **kwargs)
        self._write_spec(path, new)


class RawTextRefinementCommand(_RawTextCommand):
    """A command that instantiates models from raw text sources."""

    help = 'Create database object(s) from YAML file(s)'

    _key_mtime_date = 'date_updated'

    def add_arguments(self, parser: ArgumentParser):
        """Add additional CLI arguments for refinement."""
        parser = super().add_arguments(parser)
        parser.add_argument('--additive',
                            action='store_true',
                            help='Do not clear relevant table(s) first')
        return parser

    def _handle(self, *args, additive=None, **kwargs):
        if not additive:
            self._clear_database()

        self._create(**kwargs)

    def _clear_database(self):
        self._model.objects.all().delete()

    def _create(self, **kwargs):
        files = tuple(self._get_assets(**kwargs))
        assert files
        self._model.create_en_masse(tuple(map(self._parse_file, files)))

    def _note_date_updated(self, data: Dict[str, Any],
                           filepath: Path) -> Dict[str, Any]:
        key = self._key_mtime_date
        if key not in data:
            data[key] = date_of_last_edit(filepath)

        return data
