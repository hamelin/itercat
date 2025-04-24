from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar

from ._map import apply_function_uniform, apply_function_variable, Function


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


def map(function: Function[T], is_input_variable: bool = False) -> Sequence[S, T]:
    @sequence
    def _map(elements: Iterator[S]) -> Iterator[T]:
        process = (
            apply_function_variable
            if is_input_variable
            else apply_function_uniform
        )
        for x in elements:
            y, process = process(function, x)
            yield y

    return _map


@sequence
def entuple(elements: Iterator[T]) -> Iterator[tuple[T]]:
    for x in elements:
        yield (x,)


__all__ = [
    "entuple",
    "Filter",
    "map",
    "Sequence",
    "sequence",
]
