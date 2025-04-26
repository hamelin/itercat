from collections.abc import AsyncIterable, AsyncIterator, Iterable, Iterator
from dataclasses import dataclass
from typing import (
    Callable,
    cast,
    Generic,
    Optional,
    overload,
    TypeVar,
    Union
)


S = TypeVar("S", contravariant=True)
T = TypeVar("T", covariant=True)
U = TypeVar("U")
Transform = Callable[[AsyncIterator[S]], AsyncIterator[T]]
Predicate = Callable[[T], bool]
Cumulation = Callable[[U, T], U]
Input = Union[AsyncIterable[T], AsyncIterator[T], Iterable[T], Iterator[T]]


def as_iterator(input: Input[T]) -> AsyncIterator[T]:
    if hasattr(input, "__anext__"):
        return cast(AsyncIterator[T], input)
    elif hasattr(input, "__aiter__"):
        return aiter(cast(AsyncIterable[T], input))
    elif hasattr(input, "__iter__"):
        async def _iter():
            for x in input:
                yield x
        return _iter()
    raise ValueError(f"Can't iterate over input: {repr(input)}")


@dataclass
class Sequence(Generic[S, T]):
    filters: list[Transform]

    def __or__(self, tail: "Sequence[T, U]") -> "Sequence[S, U]":
        if not isinstance(tail, Sequence):
            return NotImplemented
        return Sequence[S, U](self.filters + tail.filters)

    def __lt__(self, input: Input[S]) -> AsyncIterator[T]:
        i_: AsyncIterator = as_iterator(input)
        for filter in self.filters:
            i_ = filter(i_)
        return i_


def step(fn: Transform[S, T]) -> Sequence[S, T]:
    return Sequence([fn])


def map(function: Callable[[S], T]) -> Sequence[S, T]:
    @step
    async def _map(elements: AsyncIterator[S]) -> AsyncIterator[T]:
        async for x in elements:
            yield function(x)

    return _map


def mapargs(function: Callable[..., T]) -> Sequence[Iterable, T]:
    @step
    async def _mapargs(elements: AsyncIterator[Iterable]) -> AsyncIterator[T]:
        async for xs in elements:
            yield function(*xs)

    return _mapargs


@overload
def cumulate(cumulation: Cumulation[U, T], initial: U) -> Sequence[T, U]:
    ...


@overload
def cumulate(cumulation: Cumulation[T, T], initial: Optional[T]) -> Sequence[T, T]:
    ...


def cumulate(cumulation, initial=None):
    @step
    async def _cumulate(elements):
        try:
            if initial is None:
                snowball = await anext(elements)
            else:
                snowball = initial

            yield snowball
            async for snowflake in elements:
                snowball = cumulation(snowball, snowflake)
                yield snowball
        except StopAsyncIteration:
            pass

    return _cumulate


@overload
def reduce(cumulation: Cumulation[U, T], initial: U) -> Sequence[T, U]:
    ...


@overload
def reduce(cumulation: Cumulation[T, T], initial: Optional[T]) -> Sequence[T, T]:
    ...


def reduce(cumulation, initial=None):
    @step
    async def _reduce(elements):
        last = None
        async for x in elements > cumulate(cumulation, initial):
            last = x
        if last is not None:
            yield last

    return _reduce


def filter(predicate: Predicate[T]) -> Sequence[T, T]:
    @step
    async def _filter(elements: AsyncIterator[T]) -> AsyncIterator[T]:
        async for x in elements:
            if predicate(x):
                yield x

    return _filter


def batch(n: int) -> Sequence[T, tuple[T, ...]]:
    if n < 1:
        raise ValueError(f"The batch size must be at least 1 (got {n})")

    @step
    async def _batch(elements: AsyncIterator[T]) -> AsyncIterator[tuple[T, ...]]:
        b: list[T] = []
        async for x in elements:
            b.append(x)
            if len(b) == n:
                yield tuple(b)
                b.clear()
        else:
            if b:
                yield tuple(b)

    return _batch


__all__ = [
    "cumulate",
    "filter",
    "map",
    "mapargs",
    "reduce",
    "Sequence",
    "step",
    "Transform",
]
