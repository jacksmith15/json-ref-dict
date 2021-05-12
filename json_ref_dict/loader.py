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
    CONTENT_PARSER: Parser = json.load  # type: ignore


class Loader:

    slots = ("loaders", "default")

    loaders: Deque[DocumentLoader]

    @classmethod
    def default_loader(cls, func: DocumentLoader) -> DocumentLoader:
        return cls(func)

    def __init__(self, default: DocumentLoader):
        self.loaders = deque()
        self.default = default

    def __iter__(self):
        return iter(self.loaders)

    def clear(self):
        self.loaders.clear()

    def register(self, loader: DocumentLoader) -> DocumentLoader:
        """LIFO registration
        """
        if loader in self.loaders:
            raise ValueError(f"{loader} is already a known loader.")
        self.loaders.appendleft(loader)
        return loader

    def unregister(self, loader: DocumentLoader):
        if loader not in self.loaders:
            raise ValueError(f"{loader} is not a known loader.")
        self.loaders.remove(loader)

    @lru_cache(maxsize=None)
    def __call__(self, base_uri: str) -> JSONSchema:
        if self.loaders:
            for loader in self.loaders:
                loaded = loader(base_uri)
                if loaded is not ...:
                    return loaded
        return self.default(base_uri)


@Loader.default_loader
def get_document(base_uri: str) -> JSONSchema:
    """Load a document based on URI root."""
    try:
        return _read_document_content(base_uri)
    except Exception as exc:
        raise DocumentParseError(
            f"Failed to load uri '{base_uri}'.") from exc


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
        parser = _get_parser(conn)
        content = parser(conn)
    return content


def _get_parser(conn) -> Callable:
    """Identify the best parser based on connection.
    """
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
        content_type = dict(
            conn.getheaders()).get("Content-Type", content_type)
    return cgi.parse_header(content_type)[0]
