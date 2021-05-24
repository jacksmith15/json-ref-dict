import cgi
import os
import pathlib
import posixpath
from collections import deque
from functools import lru_cache
import json
import mimetypes
from os import getcwd, path
from typing import Any, Callable, Dict, IO, Deque
from urllib.parse import urlparse
from urllib.request import urlopen

from json_ref_dict.exceptions import DocumentParseError


JSONSchema = Dict[str, Any]
Parser = Callable[[IO], JSONSchema]
DocumentLoader = Callable[[str], JSONSchema]

try:
    import yaml

    CONTENT_PARSER: Parser = yaml.safe_load
except ImportError:  # pragma: no cover
    CONTENT_PARSER = json.load  # pragma: no cover


class Loader:
    """Document loader singleton.

    Supports registering new loaders which are used when resolving remote
    references. Loaders are attempted in order of most recent first,
    stopping when one succeeds.

    Loaders should return ``...`` (Ellipsis) to defer to the next loader.

    Example:

    .. code:: python

        from json_ref_dict.loader import loader

        @loader.register
        def _load_with_auth(base_uri: str) -> Dict[str, Any]:
            if base_uri.startswith(PRIVATE_DOMAIN):
                return requests.get(
                    base_uri, headers=custom_auth_headers
                ).json()
            return ...

    The default loader fetches using urlopen, and parses either yaml or
    json.
    """

    __slots__ = ("_loaders", "_default")

    _loaders: Deque[DocumentLoader]

    def __init__(self, default: DocumentLoader):
        self._loaders = deque()  # allows playing with order.
        self._default = default

    def __iter__(self):
        return iter(self._loaders)

    def clear(self):
        """Clear any custom loaders."""
        return self._loaders.clear()

    def cache_clear(self):
        """Clear the cache on the default loader."""
        self._default.cache_clear()

    def register(self, loader_: DocumentLoader):
        if loader_ in self._loaders:
            raise ValueError(f"{loader_} is already a known loader.")
        self._loaders.appendleft(loader_)
        return loader_

    def unregister(self, loader_: DocumentLoader):
        if loader_ not in self._loaders:
            raise ValueError(f"{loader_} is not a known loader.")
        self._loaders.remove(loader_)

    def __call__(self, base_uri: str) -> JSONSchema:
        if self._loaders:
            for loader_ in self._loaders:
                loaded = loader_(base_uri)
                if loaded is not ...:
                    return loaded
        return self._default(base_uri)


@lru_cache(maxsize=None)
def default_get_document(base_uri: str) -> JSONSchema:
    """Load a document based on URI root."""
    try:
        return _read_document_content(base_uri)
    except Exception as exc:
        raise DocumentParseError(f"Failed to load uri '{base_uri}'.") from exc


def _read_document_content(base_uri: str) -> Dict[str, Any]:
    """Resolve document content from the base URI.
    If the URI has no scheme, assume local filesystem loading, appending
    the current working directory if the path is not absolute.
    Defers to `urllib` and may raise any exceptions from
    `urllib.request.urlopen`.
    :return: Raw content found at the URI.
    """
    if os.name == "nt" and path.isfile(base_uri) and path.isabs(base_uri):
        # https://bugs.python.org/issue42215
        # Windows paths drives are incorrectly detected as an uri schema, check
        # if is an existing file and convert to file://
        base_uri = pathlib.Path(base_uri).as_uri()
    url = urlparse(base_uri)
    if not url.scheme:
        prefix = "" if base_uri.startswith("/") else getcwd()
        base_uri = pathlib.Path(posixpath.join(prefix, base_uri)).as_uri()
    with urlopen(base_uri) as conn:
        _loader = _get_loader(conn)
        content = _loader(conn)
    return content


def _get_loader(conn) -> Callable:
    """Identify the best loader based on connection."""
    content_type = _get_content_type(conn)
    if "json" in content_type:
        return json.load
    return CONTENT_PARSER  # Fall back to default (yaml if installed)


def _get_content_type(conn) -> str:
    """Pull out mime type from a connection.
    Prefer explicit header if available, otherwise guess from url.
    """
    content_type = mimetypes.guess_type(conn.url)[0] or ""
    if hasattr(conn, "getheaders"):
        content_type = dict(conn.getheaders()).get("Content-Type", content_type)
    return cgi.parse_header(content_type)[0]


# Can possibly be hotswitched by patching.
loader: Loader = Loader(default_get_document)

# backward compatibility
get_document: Loader = loader
