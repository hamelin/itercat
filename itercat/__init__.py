from collections.abc import Iterable, Iterator
from dataclasses import dataclass
import functools as ft
from typing import Any, Callable, cast, Generic, TypeVar, Union


S = TypeVar("S", contravariant=True)
T = TypeVar("T", covariant=True)
U = TypeVar("U")
Transform = Callable[[Iterator[S]], Iterator[T]]
Predicate = Callable[[T], bool]
Input = Union[Iterable[T], Iterator[T]]


def as_iterator(input: Input[T]) -> Iterator[T]:
    if hasattr(input, "__next__"):
        return cast(Iterator[T], input)
    elif hasattr(input, "__iter__"):
        return iter(input)
    raise ValueError("Given input was neither an iterator nor an iterable.")


@dataclass
class Sequence(Generic[S, T]):
    filters: list[Transform]

    def __or__(self, tail: "Sequence[T, U]") -> "Sequence[S, U]":
        if not isinstance(tail, Sequence):
            return NotImplemented
        return Sequence[S, U](self.filters + tail.filters)

    def __lt__(self, input: Input[S]) -> Iterator[T]:
        i_: Iterator[Any] = as_iterator(input)
        for filter in self.filters:
            i_ = filter(i_)
        return i_


def step(fn: Transform[S, T]) -> Sequence[S, T]:
    return Sequence([fn])


map_ = map


def map(function: Callable[[S], T]) -> Sequence[S, T]:
    @step
    def _map(elements: Iterator[S]) -> Iterator[T]:
        return map_(function, elements)

    return _map


def mapargs(function: Callable[..., T]) -> Sequence[Iterable, T]:
    @step
    def _mapargs(elements: Iterator[Iterable]) -> Iterator[T]:
        return map_(lambda x: function(*x), elements)

    return _mapargs


class _Dummy:
    pass


_dummy = _Dummy()


def reduce(
    function: Callable[[U, T], U],
    initial: Union[U, _Dummy] = _dummy
) -> Sequence[T, U]:
    @step
    def _reduce(elements: Iterator[T]) -> Iterator[U]:
        if initial is _dummy:
            yield ft.reduce(function, elements)  # type: ignore
        else:
            yield ft.reduce(function, elements, initial)  # type: ignore

    return _reduce


filter_ = filter


def filter(predicate: Predicate[T]) -> Sequence[T, T]:
    @step
    def _filter(elements: Iterator[T]) -> Iterator[T]:
        return filter_(predicate, elements)

    return _filter


__all__ = [
    "filter",
    "map",
    "mapargs",
    "reduce",
    "Sequence",
    "step",
    "Transform",
]
