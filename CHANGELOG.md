# Changelog

## v0.3.0
- New `ignore_case` option to ignore concept name casing when looking for
  mappings via homonyms.
- Mapping path files are now written in YAML format and no longer omit 'Maps
  to value' results.

## v0.2.0
- New `update_all` option to update mappings that are not being replaced, but
  do have updated properties (e.g. domain_id has changed).
- Added support for Python 3.14.

## v0.1.1
Fixed issue where logging statements where absent when calling from Python directly.

## v0.1.0
First release.
