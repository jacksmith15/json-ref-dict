"""Declares `RefDict` type, for loading JSONSchema documents with references.

`RefDict` accepts a Base URI, and then lazily loads local or remote
references when accessed, allowig it to be treated as a normal
dictionary.

If `yaml` is installed, loading of yaml schemas is supported, otherwise
standard library `json` is used.
"""
from collections import abc, UserDict, UserList
from functools import lru_cache, singledispatch
from os import path
import re
from typing import (
    Any,
    Callable,
    Dict,
    List,
    NamedTuple,
    NoReturn,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from jsonpointer import JsonPointer, JsonPointerException, _nothing

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
        if not isinstance(reference, str):
            raise ParseError(f"Got invalid value for '$ref': {reference}.")
        if not reference.split("#")[0]:  # Local reference.
            return URI(self.uri_base, self.uri_name, reference.split("#")[1])
        # Remote reference.
        return self.from_string(path.join(self.uri_base, reference))

    def get(self, *pointer_segments: str) -> "URI":
        """Get a new URI representing a member of the current URI."""
        return self.__class__(
            uri_base=self.uri_base,
            uri_name=self.uri_name,
            pointer=path.join(self.pointer, *pointer_segments),
        )

    def back(self) -> "URI":
        """Pop a segment from the pointer."""
        segments = self.pointer.split("/")
        pointer = path.join("/", *segments[:-1])
        return self.__class__(
            uri_base=self.uri_base, uri_name=self.uri_name, pointer=pointer
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
        value = resolve_uri(self.uri)
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
        value = resolve_uri(self.uri)
        if not isinstance(value, list):
            raise TypeError(
                f"The value at '{uri}' is not an array. Got '{value}'."
            )
        super().__init__(value)

    def __getitem__(self, index: Union[int, slice]):
        """Propagate ref resolution behaviour to nested objects."""
        if isinstance(index, slice):
            raise TypeError("JSON pointers do not support slice indexes!")
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


class RefPointer(JsonPointer):
    """Subclass of `JsonPointer` which accepts full URI.

    When references are encountered, resolution is deferred to a new
    `RefPointer` with a new URI context to support reference nesting.
    """

    def __init__(self, uri: Union[str, URI]):
        self.uri = URI.from_string(uri) if isinstance(uri, str) else uri
        super().__init__(self.uri.pointer)

    def resolve_remote(
        self, doc: Any, parts_idx: int
    ) -> Tuple[bool, Optional[Any]]:
        """Defer resolution of references to a new RefPointer.

        :param doc: document element.
        :param parts_idx: index of the reference part reached.
        :return: tuple indicating (1) if doc was a ref and (2) what
            that ref was.
        """
        if not (isinstance(doc, abc.Mapping) and "$ref" in doc):
            return False, None
        remote_uri = self.uri.relative(doc["$ref"]).get(
            *self.parts[parts_idx + 1 :]
        )
        return True, resolve_uri(remote_uri)

    def resolve(self, doc: Any, default: Any = _nothing) -> Any:
        """Resolves the pointer against doc and returns the referenced object.

        If any remotes are found, then resolution is deferred to a new
        pointer instance in that reference scope.

        :param doc: The document in which to resolve the pointer.
        :param default: The value to return if the pointer fails. If not
            passed, an exception will be raised.
        :return: The value of the pointer in this document.
        :raises JsonPointerException: if `default` is not set and pointer
            could not be resolved.
        """
        for idx, part in enumerate(self.parts):
            if not part:
                continue
            try:
                doc = self.walk(doc, part)
                has_remote, remote = self.resolve_remote(doc, idx)
                if has_remote:
                    return remote
            except JsonPointerException:
                if default is _nothing:
                    raise
                return default
        return doc

    get = resolve

    def set(self, doc: Any, value: Any, inplace: bool = True) -> NoReturn:
        """`RefPointer` is read-only."""
        raise NotImplementedError("Cannot edit distributed schema.")

    def to_last(
        self, doc: Any
    ) -> Tuple[Any, Union[str, int]]:
        """Resolves pointer until the last step.

        :return: (sub-doc, last-step).
        """
        result = RefPointer(self.uri.back()).resolve(doc)
        part = self.get_part(result, self.parts[-1])
        return result, part


@lru_cache(maxsize=None)
def resolve_uri(uri: URI) -> T:
    """Find the value for a given URI.

    Loads the document and resolves the pointer, bypsasing refs.
    Utilises `lru_cache` to avoid re-loading multiple documents.
    """
    try:
        document = get_document(uri.root)
    except ParseError:
        raise ParseError(f"Failed to load base document of {uri}.")
    return RefPointer(uri).resolve(document)


@lru_cache(maxsize=None)
def get_document(base_uri: str):
    """Load a document based on URI root.

    Currently assumes the URI is a filesystem URI.
    """
    with open(base_uri) as file:
        content = file.read()
    try:
        return CONTENT_LOADER(content)
    except Exception as exc:
        raise ParseError(f"Failed to load uri '{base_uri}'.") from exc
