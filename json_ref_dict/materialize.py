from os import path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from jsonpointer import JsonPointer

from json_ref_dict.uri import parse_segment, URI
from json_ref_dict.ref_dict import RefDict, RefList


identity: Callable[[Any], Any] = lambda x: x


RefContainer = TypeVar("RefContainer", RefDict, RefList)


def _next_path(current_path: str) -> Callable[[str], str]:
    """Factory for updating path.

    Example:
    ```
    get = _next_path("/foo")
    get("bar")
    >>> "/foo/bar"
    ```
    """

    def _wrap(segment: str):
        return path.join(current_path, segment)

    return _wrap


class _RepeatCache(NamedTuple):
    """Items at `repeats` are duplicates of `source`.

    A naming abstraction to help understand the shared state in
    recursion for `materialize`.
    """

    source: JsonPointer
    repeats: Set[JsonPointer]


class MaterializeConf(NamedTuple):
    """Config class for materializing schemas."""

    value_map: Callable[[Any], Any] = identity
    include_keys: Optional[Set[str]] = None
    exclude_keys: Optional[Set[str]] = None
    context_labeller: Optional[Callable[[str], Tuple[str, Any]]] = None

    def match_key(self, key: str) -> bool:
        if self.include_keys and key not in (self.include_keys or set()):
            return False
        if self.exclude_keys and key in (self.exclude_keys or set()):
            return False
        return True

    def label(self, item: RefDict) -> Dict[str, Any]:
        if callable(self.context_labeller):
            return dict(
                # False positive.
                # pylint: disable=not-callable
                [self.context_labeller(str(item.uri))]
            )
        return {}


def materialize(
    item: RefContainer,
    include_keys: Iterable[str] = None,
    exclude_keys: Iterable[str] = None,
    value_map: Callable[[Any], Any] = identity,
    context_labeller: Callable[[str], Tuple[str, Any]] = None,
) -> Union[List, Dict]:
    """Convert a `RefDict` or `RefList` to a regular `dict` or `list`.

    Recursively resolves at least once for each URI, and then assigns
    duplicates as a post-step.

    If there are cyclical references in `item`, these are converted to
    cyclical references in the respective standard container type. As
    such, the interface behaviour of the resulting container will be
    the same as the parameter passed, but will not perform any IO in
    the background to lazily resolve references.

    :param item: The `RefDict` or `RefContainer` to materialize.
    :param include_keys: Optionally specify the set of keys to keep.
        If provided, keys not present will not be returned.
    :param exclude_keys: Optionally specify a set of keys to exclude.
        If provided, these keys will not be returned.
    :param value_map: Optionally specify a transformation to apply to
        non-dict/list values of the data documentation.
    :param context_labeller: Optionally specify a callable to annotate
        schema document from the source URI of its location.
    :return: Standard `dict` or `list` with all references resolved
        eagerly.
    """
    conf = MaterializeConf(
        include_keys=set(include_keys) if include_keys else None,
        exclude_keys=set(exclude_keys or tuple()),
        value_map=value_map,
        context_labeller=context_labeller,
    )
    repeats: Dict[URI, _RepeatCache] = {}
    materialized = _materialize_recursive(conf, repeats, "/", item)
    for duplicate in repeats.values():
        if duplicate.source.path == "/":
            value = materialized
        else:
            value = duplicate.source.resolve(materialized)
        for repeat in duplicate.repeats:
            repeat.set(materialized, value)
    return materialized


def _materialize_recursive(
    conf: MaterializeConf,
    repeats: Dict[URI, _RepeatCache],
    pointer: str,
    item: Any,
) -> Any:
    """Recursive function for materializing RefDict/RefList objects.

    Keeps track of previously seen items, and stores a reference on
    repeats. Cyclical references are avoided this way, and must be
    added in afterwards (see `materialize`).

    :param conf: `MaterializeConf` object specifying any transformations
        to perform.
    :param repeats: Shared mutable dictionary for keeping track of
        items which appear multiple times (sometimes in the same path).
    :param pointer: Pointer of the current item relative to the first
        call.
    :param item: The data object to operate on.
    :return: The materialized version of `item`, or `None` if this URI
        has already been traversed elsewhere.
    """
    # End-cases
    if not isinstance(item, (RefDict, RefList)):
        return conf.value_map(item)
    if item.uri in repeats:
        repeats[item.uri][1].add(JsonPointer(pointer))
        return None
    # Keep a record of walking this URI and recurse through the
    # contained items.
    repeats[item.uri] = _RepeatCache(source=JsonPointer(pointer), repeats=set())
    recur = lambda seg, data: _materialize_recursive(
        conf, repeats, _next_path(pointer)(parse_segment(seg)), data
    )
    if isinstance(item, RefList):
        return [recur(str(idx), subitem) for idx, subitem in enumerate(item)]
    return {
        **conf.label(item),
        **{
            key: recur(key, value)
            for key, value in item.items()
            if conf.match_key(key)
        },
    }
