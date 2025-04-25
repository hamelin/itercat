from collections.abc import Iterable, Iterator
from dataclasses import dataclass
import functools as ft
from typing import Any, Callable, Generic, TypeVar, Union


S = TypeVar("S", contravariant=True)
T = TypeVar("T", covariant=True)
U = TypeVar("U")
Transform = Callable[[Iterator[S]], Iterator[T]]
Consumer = Callable[[Iterator[T]], U]
Predicate = Callable[[T], bool]


@dataclass
class Sequence(Generic[S, T]):
    filters: list[Transform]

    def __or__(self, tail: "Sequence[T, U]") -> "Sequence[S, U]":
        if not isinstance(tail, Sequence):
            return NotImplemented
        return Sequence[S, U](self.filters + tail.filters)

    def __lt__(self, iteration: Iterator[S]) -> Iterator[T]:
        assert hasattr(iteration, "__next__")
        i_: Iterator[Any] = iteration
        for filter in self.filters:
            i_ = filter(i_)
        return i_


@dataclass
class Terminal(Generic[S, T, U]):
    sequence: Sequence[S, T]
    consume: Consumer[T, U]

    def __lt__(self, iteration: Iterator[S]) -> U:
        return self.consume(iteration > self.sequence)


@dataclass
class sink(Generic[T, U]):
    consume: Consumer[T, U]

    def __ror__(self, sequence: Sequence[S, T]) -> Terminal[S, T, U]:
        return Terminal[S, T, U](sequence=sequence, consume=self.consume)

    def __lt__(self, iteration: Iterator[T]) -> U:
        return iteration > Terminal[T, T, U](
            sequence=Sequence[T, T](filters=[]),
            consume=self.consume
        )


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
) -> sink[T, U]:
    if initial is _dummy:
        return sink(
            lambda iteration: ft.reduce(function, iteration)  # type: ignore
        )
    return sink(
        lambda iteration: ft.reduce(function, iteration, initial)  # type: ignore
    )


filter_ = filter


def filter(predicate: Predicate[T]) -> Sequence[T, T]:
    @step
    def _filter(elements: Iterator[T]) -> Iterator[T]:
        return filter_(predicate, elements)

    return _filter


__all__ = [
    "Consumer",
    "filter",
    "map",
    "mapargs",
    "reduce",
    "Sequence",
    "sink",
    "step",
    "Transform",
]
