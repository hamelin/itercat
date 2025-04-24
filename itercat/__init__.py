from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar

from ._map import apply_function_uniform, apply_function_variable, Function


S = TypeVar("S", contravariant=True)
T = TypeVar("T", covariant=True)
U = TypeVar("U")
Filter = Callable[[Iterator[S]], Iterator[T]]


@dataclass
class Sequence(Generic[S, T]):
    filters: list[Filter]

    def __or__(self, tail: "Sequence[T, U]") -> "Sequence[S, U]":
        return Sequence[S, U](self.filters + tail.filters)

    def __lt__(self, iteration: Iterator[S]) -> Iterator[T]:
        assert hasattr(iteration, "__next__")
        i_: Iterator[Any] = iteration
        for filter in self.filters:
            i_ = filter(i_)
        return i_


def sequence(fn: Filter[S, T]) -> Sequence[S, T]:
    return Sequence([fn])


def map(
    function: Function[T],
    flatten_args: bool = True,
    variable_input: bool = False
) -> Sequence[S, T]:
    @sequence
    def _map(elements: Iterator[S]) -> Iterator[T]:
        process = (
            apply_function_variable
            if variable_input
            else apply_function_uniform
        )
        for x in elements:
            y, process = process(function, x, flatten_args)  # type: ignore
            yield y

    return _map


__all__ = [
    "Filter",
    "map",
    "Sequence",
    "sequence",
]
