from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar


S = TypeVar("S")
T = TypeVar("T")
U = TypeVar("U")


class Filter(Protocol[S, T]):

    def __call__(self, input: Iterator[S]) -> Iterator[T]:
        ...


@dataclass
class Sequence(Generic[S, T]):
    filters: list[Filter]

    def __or__(self, tail: "Sequence[T, U]") -> "Sequence[S, U]":
        return type(self)(self.filters + tail.filters)

    def __lt__(self, iteration: Iterator[S]) -> Iterator[T]:
        assert hasattr(iteration, "__next__")
        i_: Iterator[Any] = iteration
        for filter in self.filters:
            i_ = filter(i_)
        return i_


def sequence(fn: Filter[S, T]) -> Sequence[S, T]:
    return Sequence([fn])
