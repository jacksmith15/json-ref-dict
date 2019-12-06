"""Declares `RefDict` type, for loading JSONSchema documents with references.

`RefDict` accepts a Base URI, and then lazily loads local or remote
references when accessed, allowig it to be treated as a normal
dictionary.

If `yaml` is installed, loading of yaml schemas is supported, otherwise
standard library `json` is used.
"""
from json_ref_dict.exceptions import JSONRefParseError
from json_ref_dict.uri import URI
from json_ref_dict.ref_pointer import RefPointer, resolve_uri
from json_ref_dict.ref_dict import RefDict


__version__ = "0.1.0"
