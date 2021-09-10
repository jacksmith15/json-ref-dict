from collections import abc
from functools import lru_cache
from typing import Any, Dict, List, NoReturn, Optional, Tuple, Union
from urllib.parse import unquote

from jsonpointer import JsonPointer, JsonPointerException, _nothing

from json_ref_dict.exceptions import DocumentParseError
from json_ref_dict.loader import get_document, JSONSchema
from json_ref_dict.uri import URI, parse_segment

ResolvedValue = Union[List, Dict, None, bool, str, int, float]
UriValuePair = Tuple[URI, ResolvedValue]


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
        remote_uri, value = self.resolve_remote_with_uri(doc, parts_idx)
        return remote_uri is not None, value

    def resolve_remote_with_uri(
        self, doc: Any, parts_idx: int
    ) -> Tuple[Optional[URI], Optional[Any]]:
        """Defer resolution of references to a new RefPointer.

        :param doc: document element.
        :param parts_idx: index of the reference part reached.
        :return: tuple indicating (1) if doc was a ref (the ref URI returned)
            and (2) what that ref value was.
        """
        if not (
            isinstance(doc, abc.Mapping) and isinstance(doc.get("$ref"), str)
        ):
            return None, None
        remote_uri = self.uri.relative(doc["$ref"]).get(
            *[parse_segment(part) for part in self.parts[parts_idx + 1 :]]
        )

        resolved_remote_uri, value = resolve_uri_to_urivalue_pair(remote_uri)
        return resolved_remote_uri, value

    def resolve(self, doc: Any, default: Any = _nothing) -> Any:
        """Resolves the pointer against doc and returns the referenced object.

        If any remotes are found, then resolution is deferred to a new
        pointer instance in that reference scope and resolving continued,
        until the value is found.

        :param doc: The document in which to start resolving the pointer.
        :param default: The value to return if the pointer fails. If not
            passed, an exception will be raised.
        :return: The value of the pointer in the containing document.
            The document may be different from the one given in as an argument.
        :raises JsonPointerException: if `default` is not set and pointer
            could not be resolved.
        """
        _, value = self.resolve_with_uri(doc, default)
        return value

    get = resolve

    def resolve_with_uri(
        self, doc: Any, default: Any = _nothing
    ) -> Tuple[URI, Any]:
        """Resolves the pointer, starting from given doc

        The resolver recurses references and, as a result, may end up on
        a different document than the one given in as an argument. The URI for
        the document containing the value is returned together with the value.

        :param doc: The document with which to start resolving the pointer.
        :param default: The value to return if the pointer fails. If not
            passed, an exception will be raised.
        :return: The updated URI and the value of the pointer
            in the located document.
        :raises JsonPointerException: if `default` is not set and pointer
            could not be resolved.
        """
        remote_uri, remote = self.resolve_remote_with_uri(doc, -1)
        if remote_uri is not None:
            return remote_uri, remote
        for idx, part in enumerate(self.parts):
            if not part:
                continue
            try:
                try:
                    doc = self.walk(doc, part)
                except JsonPointerException:
                    doc = self.walk(doc, unquote(part))
                remote_uri, remote = self.resolve_remote_with_uri(doc, idx)
                if remote_uri is not None:
                    return remote_uri, remote
            except JsonPointerException:
                if default is _nothing:
                    raise
                return self.uri, default
        return self.uri, doc

    def set(self, doc: Any, value: Any, inplace: bool = True) -> NoReturn:
        """`RefPointer` is read-only."""
        raise NotImplementedError("Cannot edit distributed schema.")

    def to_last(self, doc: Any) -> Tuple[Any, Union[str, int]]:
        """Resolves pointer until the last step.

        :return: (sub-doc, last-step).
        """
        result = RefPointer(self.uri.back()).resolve(doc)
        part = self.get_part(result, self.parts[-1])
        return result, part


def nested_lru_cache(nested_cache_funcs, *args, **kwargs):
    """Implement lru_cache that also resets the underlying document cache.

    URI resolver functions share a common document cache that
    is implemented with lru_cache.
    Cache clearing on the resolve-functions needs to reset
    the underlying cache with a custom cache_clear implementation.
    """

    def decorator(func):
        func = lru_cache(*args, **kwargs)(func)
        orig_cache_clear = func.cache_clear

        def _custom_clear():
            for func in nested_cache_funcs:
                func.cache_clear()
            orig_cache_clear()

        func.cache_clear = _custom_clear
        return func

    return decorator


@lru_cache(maxsize=None)
def _resolve_cached_root_doc(uri: URI) -> JSONSchema:
    try:
        return get_document(uri.root)
    except DocumentParseError as exc:
        raise DocumentParseError(
            f"Failed to load base document of {uri}."
        ) from exc


@nested_lru_cache([_resolve_cached_root_doc], maxsize=None)
def resolve_uri_to_urivalue_pair(uri: URI) -> UriValuePair:
    """Find the value-containing URI and actual value for a given starting URI.

    The starting URI can point to another document than where the final
    value is found. This method returns a valid URI to the containing document.

    Loads the document and resolves the pointer, bypassing refs.
    Utilises `lru_cache` to avoid re-loading multiple documents.

    :return: URI to the document containing the value, and the value itself.

    :raises DocumentParseError: if the input URI root does not point to
        a valid document.
    """
    document = _resolve_cached_root_doc(uri)
    pointer = RefPointer(uri)
    remote_uri, value = pointer.resolve_with_uri(document)
    return remote_uri if remote_uri else uri, value


@nested_lru_cache([resolve_uri_to_urivalue_pair], maxsize=None)
def resolve_uri(uri: URI) -> ResolvedValue:
    """Find the value for a given URI.

    Loads the document and resolves the pointer, bypassing refs.
    """
    _, value = resolve_uri_to_urivalue_pair(uri)
    return value
