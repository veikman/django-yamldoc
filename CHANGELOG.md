# Change log
This log follows the conventions of
[keepachangelog.com](http://keepachangelog.com/). It picks up from version 1.0.0.

## [Unreleased]
Nothing yet.

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

[Unreleased]: https://github.com/veikman/yamldoc/compare/v1.1.0...HEAD
[Version 1.1.0]: https://github.com/veikman/yamldoc/compare/v1.0.2...v1.1.0
[Version 1.0.2]: https://github.com/veikman/yamldoc/compare/v1.0.1...v1.0.2
[Version 1.0.1]: https://github.com/veikman/yamldoc/compare/v1.0.0...v1.0.1
