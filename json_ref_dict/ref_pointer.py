from collections import abc
from functools import lru_cache
from typing import Any, Dict, List, NoReturn, Optional, Tuple, Union
from urllib.parse import unquote

from jsonpointer import JsonPointer, JsonPointerException, _nothing

from json_ref_dict.exceptions import DocumentParseError
from json_ref_dict.loader import get_document
from json_ref_dict.uri import URI, parse_segment


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
        if not (
            isinstance(doc, abc.Mapping) and isinstance(doc.get("$ref"), str)
        ):
            return False, None
        remote_uri = self.uri.relative(doc["$ref"]).get(
            *[parse_segment(part) for part in self.parts[parts_idx + 1 :]]
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
        has_remote, remote = self.resolve_remote(doc, -1)
        if has_remote:
            return remote
        for idx, part in enumerate(self.parts):
            if not part:
                continue
            try:
                try:
                    doc = self.walk(doc, part)
                except JsonPointerException:
                    doc = self.walk(doc, unquote(part))
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

    def to_last(self, doc: Any) -> Tuple[Any, Union[str, int]]:
        """Resolves pointer until the last step.

        :return: (sub-doc, last-step).
        """
        result = RefPointer(self.uri.back()).resolve(doc)
        part = self.get_part(result, self.parts[-1])
        return result, part


@lru_cache(maxsize=None)
def resolve_uri(uri: URI) -> Union[List, Dict, None, bool, str, int, float]:
    """Find the value for a given URI.

    Loads the document and resolves the pointer, bypsasing refs.
    Utilises `lru_cache` to avoid re-loading multiple documents.
    """
    try:
        document = get_document(uri.root)
    except DocumentParseError as exc:
        raise DocumentParseError(
            f"Failed to load base document of {uri}."
        ) from exc
    return RefPointer(uri).resolve(document)
