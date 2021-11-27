# Change log
This log follows the conventions of
[keepachangelog.com](http://keepachangelog.com/). It picks up from version 1.0.0.

## [Unreleased]
Nothing yet.

### New
- When content is added to a source file through a template, and an editor is
  started to complete that addition, the file is now opened at the start of the
  new addition, not at the very end.
- `_append_template` now returns a `bool` so that callers can react to it being
  cancelled.

## [Version 1.3.0]
### Added
- CLI arguments for selecting files and folders now automatically resolve to
  absolute paths, the prior existence of which is now checked.
- Added the use of (de)serializing methods new in v1.2.0 as keyword
  arguments new in yamlwrap v2.1.0.
- Added keyword argument passing to (de)serializing methods new in
  v1.2.0.
- Support for Git as a means of dating the last edit made to a source file.
- Debug logging from the filepath predicate method new in v1.2.0.

## [Version 1.2.0]
### Changed
- Marked `yamldoc.utils.file.transform` as deprecated because it uses an
  internal property of the model passed to it.
- Marked `yamldoc.management.misc.DocumentRefinementCommand` as deprecated
  because it’s needlessly inheritance-based. Its only useful contributed
  functionality has been generalized and moved to its parent class,
  `RawTextRefinementCommand`, as `_note_date_updated`.
- Migrated for compatibility with `pathlib`.
    - Set the default type of `--select-*`, and `--describe`/`--update` CLI
      arguments to `Path`.
    - Marked `yamldoc.utils.file.find_files` and several methods of the
      management command models (`_new_filepath`, `_get_files`,
      `_file_identifier`, `_describe`, `_transform`) as
      deprecated because they use `str` for file paths.
- Default folders and files for management commands are now noted in their
  argument parsers, instead of being compared later.
- Changed the way management commands compose mutually exclusively groups.
  Methods that previously took such groups now take parsers instead, and
  are no longer stubs. In the absence of overrides, overall behaviour has
  not changed.

### Added
- Partial replacements for `yamldoc.utils.file.transform` in
  `yamldoc.utils.misc`.
- `pathlib`-based replacements for methods mentioned above as deprecated,
  except for `_new_filepath` which has no replacement.
- Functions to serialize/deserialize YAML are now more easily configurable
  through new, small instance methods of `_RawTextCommand`.

### Fixed
- Performance: Delayed computation of file length for determining where to open
  it.

## [Version 1.1.0]
### Changed
- Increased the maximum length of Document.title from 100 to 255.
    - Set a matching explicit length on Document.slug.

## [Version 1.0.2]
### Fixed
- As a consequence of Document being acknowledged as an abstract model in
  v1.0.1, the migration file for `yamldoc` was removed, fixing problems
  migrating concrete classes inheriting from Document.

## [Version 1.0.1]
### Fixed
- Clarified programmatically that Document is an abstract model.
- Changed where `yamldoc` looks for an optional `fields_with_markup` property,
  from model metadata (where it is not allowed to exist in contemporary
  Django), to direct composition onto the model class.

[Unreleased]: https://github.com/veikman/yamldoc/compare/v1.3.0...HEAD
[Version 1.3.0]: https://github.com/veikman/yamldoc/compare/v1.2.0...v1.3.0
[Version 1.2.0]: https://github.com/veikman/yamldoc/compare/v1.1.0...v1.2.0
[Version 1.1.0]: https://github.com/veikman/yamldoc/compare/v1.0.2...v1.1.0
[Version 1.0.2]: https://github.com/veikman/yamldoc/compare/v1.0.1...v1.0.2
[Version 1.0.1]: https://github.com/veikman/yamldoc/compare/v1.0.0...v1.0.1
