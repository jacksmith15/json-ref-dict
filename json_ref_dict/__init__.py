"""Declares `RefDict` type, for loading JSONSchema documents with references.

`RefDict` accepts a Base URI, and then lazily loads local or remote
references when accessed, allowig it to be treated as a normal
dictionary.

If `yaml` is installed, loading of yaml schemas is supported, otherwise
standard library `json` is used.
"""
from collections import UserDict, UserList
from functools import lru_cache, singledispatch
from os import path
import re
from typing import Any, Callable, Dict, List, NamedTuple, TypeVar, Union

CONTENT_LOADER: Callable[[str], Dict]

try:
    import yaml

    CONTENT_LOADER = yaml.safe_load
except ImportError:
    import json

    CONTENT_LOADER = json.loads


__version__ = "0.0.0"


JSON_REF_REGEX = r"^((?P<uri_base>.*)\/)?(?P<uri_name>.*)#(?P<pointer>\/.*)$"
T = TypeVar("T", List, Dict, int, float, str, bool, None)


class ParseError(Exception):
    """Failed to parse a document."""


class URI(NamedTuple):
    """URI for a schema or subschema."""

    uri_base: str
    uri_name: str
    pointer: str

    @classmethod
    def from_string(cls, string: str) -> "URI":
        """Contruct from string."""
        match = re.match(JSON_REF_REGEX, string)
        if not match:
            raise ParseError(f"Couldn't parse '{string}' as a valid reference.")
        return URI(**match.groupdict())

    @property
    def root(self):
        """String representation excluding the JSON pointer."""
        return path.join(self.uri_base, self.uri_name)

    def relative(self, reference: str) -> "URI":
        """Get a new URI relative to the current root."""
        if not reference.split("#")[0]:  # Local reference.
            return URI(self.uri_base, self.uri_name, reference.split("#")[1])
        # Remote reference.
        return self.from_string(path.join(self.uri_base, reference))

    def get(self, pointer_segment: str) -> "URI":
        """Get a new URI representing a member of the current URI."""
        return self.__class__(
            uri_base=self.uri_base,
            uri_name=self.uri_name,
            pointer=path.join(self.pointer, pointer_segment),
        )

    def __repr__(self) -> str:
        """String representation of the URI."""
        return path.join(self.uri_base, self.uri_name) + f"#{self.pointer}"


class RefDict(UserDict):  # pylint: disable=too-many-ancestors
    """Dictionary for abstracting ref resolution in JSONSchemas.

    Accepts a base URI as its argument, and subsequently can be
    accessed as any other dictionary. Behaviour propagates to
    nested items.
    """

    def __init__(self, uri: Union[str, URI], *args, **kwargs):
        """On instantiation, retrieve the data from the URI."""
        self.uri = URI.from_string(uri) if isinstance(uri, str) else uri
        value = _get_uri(self.uri)
        if not isinstance(value, dict):
            raise TypeError(
                f"The value at '{uri}' is not an object. Got '{value}'."
            )
        super().__init__(**value)

    def __getitem__(self, key: str):
        """Propagate ref resolution behaviour to nested objects."""
        item = super().__getitem__(key)
        uri = self.uri.get(key)
        return propagate(uri, item)


class RefList(UserList):  # pylint: disable=too-many-ancestors
    """List for abstracting ref resolution in JSONSchemas.

    Accepts a base URI as its argument, and subsequently can be
    accessed as any other list. Behaviour propagates to
    nested items.
    """

    def __init__(self, uri: Union[str, URI], *args, **kwargs):
        """On instantiation, retrieve the data from the URI."""
        self.uri = URI.from_string(uri) if isinstance(uri, str) else uri
        value = _get_uri(self.uri)
        if not isinstance(value, list):
            raise TypeError(
                f"The value at '{uri}' is not an array. Got '{value}'."
            )
        super().__init__(value)

    def __getitem__(self, index: Union[int, slice]):
        """Propagate ref resolution behaviour to nested objects."""
        if isinstance(index, slice):
            raise TypeError(
                "JSON pointers do not support slice indexes!"
            )
        item = super().__getitem__(index)
        uri = self.uri.get(str(index))
        return propagate(uri, item)


def propagate(uri: URI, value: Any):
    """Ref resolution and propagation of behaviours on __getitem__."""
    if isinstance(value, dict):
        if "$ref" in value:
            return RefDict(uri.relative(value["$ref"]))
        return RefDict(uri)
    if isinstance(value, list):
        return RefList(uri)
    return value


@lru_cache(maxsize=None)
def _get_uri(uri: URI) -> T:
    """Find the value for a given URI.

    Loads the document and resolves the pointer, bypsasing refs.
    Utilises `lru_cache` to avoid re-loading multiple documents.
    """
    document = get_document(uri)
    return _resolve_in_document(uri, document)


@lru_cache(maxsize=None)
def get_document(uri: URI):
    """Load a document based on URI root.

    Currently assumes the URI is a filesystem URI.
    """
    with open(uri.root) as file:
        content = file.read()
    try:
        return CONTENT_LOADER(content)
    except Exception as exc:
        raise ParseError(
            f"Failed to load uri '{uri}', couldn't parse '{uri.root}'"
        ) from exc


def _get_bypass_ref(uri: URI, data: Union[List, Dict], breadcrumb: str) -> T:
    """Get a key from a document, resolving refs on the result if present."""
    output = _get_breadcrumb(data, breadcrumb)
    if isinstance(output, dict) and "$ref" in output:
        return _get_uri(uri.relative(output["$ref"]))
    return output


def _resolve_in_document(uri: URI, document: Dict):
    """Resolve a JSON Pointer in a document.

    Bypasses refs by deferring to `_get_bypass_ref`.
    :raises KeyError: if the JSON pointer isn't resolvable.
    :return: the value of the JSON Pointer from the root of a given
        document.
    """
    breadcrumbs = uri.pointer.strip("/").split("/")
    output = document
    for idx, breadcrumb in enumerate(breadcrumbs):
        if not breadcrumb:
            continue
        try:
            output = _get_bypass_ref(uri, output, breadcrumb)
        except (KeyError, ValueError) as exc:
            raise KeyError(
                f"Failed to parse '{uri}'. Couldn't resolve "
                f"{breadcrumbs[:idx + 1]}"
            ) from exc
    return output


@singledispatch
def _get_breadcrumb(data: Any, breadcrumb: str) -> T:
    """Single dispatch to resolve JSON Pointer fragments."""
    raise ValueError(
        f"Cannot retrieve member of non-array/object item {data}."
    )

@_get_breadcrumb.register(dict)
def _get_breadcrumb_dict(data: Dict, breadcrumb: str) -> T:
    """If the data is a dict, simply attempt to get the member."""
    return data[breadcrumb]

@_get_breadcrumb.register(list)
def _get_breadcrumb_list(data: List, breadcrumb: str) -> T:
    """If the data is an array, ensure the fragment is an int."""
    try:
        index = int(breadcrumb)
    except ValueError as exc:
        raise ValueError(
            f"Got string index {breadcrumb} for array element."
        ) from exc
    return data[index]
