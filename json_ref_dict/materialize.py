from os import path
from typing import Any, Callable, Dict, List, NamedTuple, Set, TypeVar, Union

from jsonpointer import JsonPointer

from json_ref_dict.uri import URI
from json_ref_dict.ref_dict import RefDict, RefList


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


def materialize(item: RefContainer) -> Union[List, Dict]:
    """Convert a `RefDict` or `RefList` to a regular `dict` or `list`.

    Recursively resolves at least once for each URI, and then assigns
    duplicates as a post-step.

    If there are cyclical references in `item`, these are converted to
    cyclical references in the respective standard container type. As
    such, the interface behaviour of the resulting container will be
    the same as the parameter passed, but will not perform any IO in
    the background to lazily resolve references.

    :param item: The `RefDict` or `RefContainer` to materialize.
    :return: Standard `dict` or `list` with all references resolved
        eagerly.
    """
    repeats: Dict[URI, _RepeatCache] = {}
    materialized = _materialize_recursive(repeats, "/", item)
    for duplicate in repeats.values():
        if duplicate.source.path == "/":
            value = materialized
        else:
            value = duplicate.source.resolve(materialized)
        for repeat in duplicate.repeats:
            repeat.set(materialized, value)
    return materialized


def _materialize_recursive(
    repeats: Dict[URI, _RepeatCache], pointer: str, item: Any
) -> Any:
    """Recursive function for materializing RefDict/RefList objects.

    Keeps track of previously seen items, and stores a reference on
    repeats. Cyclical references are avoided this way, and must be
    added in afterwards (see `materialize`).
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
        return item
    if item.uri in repeats:
        repeats[item.uri][1].add(JsonPointer(pointer))
        return None
    # Keep a record of walking this URI and recurse through the
    # contained items.
    repeats[item.uri] = _RepeatCache(source=JsonPointer(pointer), repeats=set())
    recur = lambda seg, data: _materialize_recursive(
        repeats, _next_path(pointer)(seg), data
    )
    if isinstance(item, RefList):
        return [recur(str(idx), subitem) for idx, subitem in enumerate(item)]
    return {key: recur(key, value) for key, value in item.items()}
