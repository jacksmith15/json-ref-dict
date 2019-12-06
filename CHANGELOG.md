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

[Unreleased]: https://github.com/jacksmith15/json-ref-dict/compare/initial..HEAD

[Keep a Changelog]: http://keepachangelog.com/en/1.0.0/
[Semantic Versioning]: http://semver.org/spec/v2.0.0.html
[Unreleased]: http://github.com/jacksmith15/json-ref-dict/compare/0.1.0..HEAD
[0.1.0]: http://github.com/jacksmith15/json-ref-dict/compare/0.0.0..0.1.0
