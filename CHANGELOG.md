# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog] and this project adheres to
[Semantic Versioning].

Types of changes are:
* **Security** in case of vulnerabilities.
* **Deprecated** for soon-to-be removed features.
* **Added** for new features.
* **Changed** for changes in existing functionality.
* **Removed** for now removed features.
* **Fixed** for any bug fixes.

## [Unreleased]

## [0.4.2] - 2020-03-08
### Fixed
* Fixed bug when parsing JSON containing tabs with `pyyaml`
  installed.

## [0.4.1] - 2020-03-08
### Fixed
* Fixed issue where pure address references with no pointers
  are rejected.
* Fixed issue with relative remote references independent of a
  base absolute URI.

## [0.4.0] - 2019-12-10
### Added
* New optional parameter to `materialize`:
    - `context_labeller` - factory for generating annotation on
      objects in the document from their source URI.

### Fixed
* Allow `'$ref'` key to be passed as a non-reference if not a
  string.

## [0.3.0] - 2019-12-10
### Added
* Three new optional parameters to `materialize`:
    - `include_keys` - set of keys to include in the materialized
      document.
    - `exclude_keys` - set of keys to exclude from the materialized
      document.
    - `value_map` - operation to apply to items of the document.

## [0.2.1] - 2019-12-06
### Fixed
* Fixed `long_description_content_type` in `setup.py`

## [0.2.0] - 2019-12-06
### Fixed
* Regular expression in release tool.

### Added
* `materialize` function for resolving all references in a single step.

## [0.1.0] - 2019-12-06
### Added
* Project started :)
* Added `RefDict` class for loading related schemas by URI.
* Added File-system loading support.
* Added `RefPointer`. Subclasses `jsonpointer.JsonPointer` and traverses
  references.
* Added general document loading by URI (deferring to
  `urllib.request.urlopen`).

## [0.0.0]
Nothing here.

[Unreleased]: http://github.com/jacksmith15/json-ref-dict/compare/0.4.2..HEAD
[0.4.2]: http://github.com/jacksmith15/json-ref-dict/compare/0.4.1..0.4.2
[0.4.1]: http://github.com/jacksmith15/json-ref-dict/compare/0.4.0..0.4.1
[0.4.0]: http://github.com/jacksmith15/json-ref-dict/compare/0.3.0..0.4.0
[0.3.0]: http://github.com/jacksmith15/json-ref-dict/compare/0.2.1..0.3.0
[0.2.1]: http://github.com/jacksmith15/json-ref-dict/compare/0.2.0..0.2.1
[0.2.0]: http://github.com/jacksmith15/json-ref-dict/compare/0.1.0..0.2.0
[0.1.0]: http://github.com/jacksmith15/json-ref-dict/compare/initial..0.1.0

[Keep a Changelog]: http://keepachangelog.com/en/1.0.0/
[Semantic Versioning]: http://semver.org/spec/v2.0.0.html
