from collections.abc import (
    AsyncIterable,
    AsyncIterator,
    Callable,
    Hashable,
    Iterable,
    Iterator,
    Sequence as _Sequence_,
)
from dataclasses import dataclass
from typing import (
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
class Chain(Generic[S, T]):
    filters: list[Transform]

    def __or__(self, tail: "Chain[T, U]") -> "Chain[S, U]":
        if not isinstance(tail, Chain):
            return NotImplemented
        return Chain[S, U](self.filters + tail.filters)

    def __lt__(self, input: Input[S]) -> AsyncIterator[T]:
        i_: AsyncIterator = as_iterator(input)
        for filter in self.filters:
            i_ = filter(i_)
        return i_


def link(fn: Transform[S, T]) -> Chain[S, T]:
    return Chain([fn])


def map(function: Callable[[S], T]) -> Chain[S, T]:
    @link
    async def _map(elements: AsyncIterator[S]) -> AsyncIterator[T]:
        async for x in elements:
            yield function(x)

    return _map


def mapargs(function: Callable[..., T]) -> Chain[Iterable, T]:
    @link
    async def _mapargs(elements: AsyncIterator[Iterable]) -> AsyncIterator[T]:
        async for xs in elements:
            yield function(*xs)

    return _mapargs


@overload
def cumulate(cumulation: Cumulation[U, T], initial: U) -> Chain[T, U]:
    ...


@overload
def cumulate(cumulation: Cumulation[T, T], initial: Optional[T]) -> Chain[T, T]:
    ...


def cumulate(cumulation, initial=None):
    @link
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
def reduce(cumulation: Cumulation[U, T], initial: U) -> Chain[T, U]:
    ...


@overload
def reduce(cumulation: Cumulation[T, T], initial: Optional[T]) -> Chain[T, T]:
    ...


def reduce(cumulation, initial=None):
    @link
    async def _reduce(elements):
        last = None
        async for x in elements > cumulate(cumulation, initial):
            last = x
        if last is not None:
            yield last

    return _reduce


def filter(predicate: Predicate[T]) -> Chain[T, T]:
    @link
    async def _filter(elements: AsyncIterator[T]) -> AsyncIterator[T]:
        async for x in elements:
            if predicate(x):
                yield x

    return _filter


def batch(n: int) -> Chain[T, tuple[T, ...]]:
    if n < 1:
        raise ValueError(f"The batch size must be at least 1 (got {n})")

    @link
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


def ngrams(n: int) -> Chain[T, tuple[T, ...]]:
    if n < 1:
        raise ValueError(f"The size must be at least 1 (got {n})")

    @link
    async def _ngrams(elements: AsyncIterator[T]) -> AsyncIterator[tuple[T, ...]]:
        ngram: list[T] = []
        try:
            for _ in range(n):
                ngram.append(await anext(elements))
            yield tuple(ngram)

            async for x in elements:
                del ngram[0]
                ngram.append(x)
                yield tuple(ngram)
        except StopAsyncIteration:
            pass

    return _ngrams


async def _enumerate(elements: AsyncIterator[T]) -> AsyncIterator[tuple[int, T]]:
    i = 0
    try:
        while True:
            yield i, await anext(elements)
            i += 1
    except StopAsyncIteration:
        pass


def slice_(
    n: int,
    stop: Optional[int] = None,
    step: int = 1
) -> Chain[T, T]:
    if step < 1:
        raise ValueError(f"Step must be at least 1; got {step}")
    if stop is None:
        start, end = 0, n
    else:
        start, end = n, stop
    if start < 0:
        raise ValueError(f"Start of the slice must be at least 0; got {start}")

    @link
    async def _slice_(elements: AsyncIterator[T]) -> AsyncIterator[T]:
        enum = _enumerate(elements)
        try:
            while True:
                i, last = await anext(enum)
                if i == start:
                    break

            while i < end:
                yield last
                for _ in range(step):
                    i, last = await anext(enum)
        except StopAsyncIteration:
            pass

    return _slice_


def head(n: int) -> Chain[T, T]:
    if n < 0:
        raise ValueError(f"n must be positive (got {n})")

    return slice_(0, n, 1)


def tail(n: int) -> Chain[T, T]:
    if n < 0:
        raise ValueError(f"n must be positive (got {n})")

    @link
    async def _tail(elements: AsyncIterator[T]) -> AsyncIterator[T]:
        the_tail: list[T] = []
        async for x in elements:
            the_tail.append(x)
            if len(the_tail) > n:
                the_tail.pop(0)
        for x in the_tail:
            yield x

    return _tail


def cut(predicate: Predicate[T]) -> Chain[T, T]:
    @link
    async def _cut(elements: AsyncIterator[T]) -> AsyncIterator[T]:
        async for x in elements:
            if not predicate(x):
                break
            yield x

    return _cut


def clamp(predicate: Predicate[T]) -> Chain[T, T]:
    @link
    async def _clamp(elements: AsyncIterator[T]) -> AsyncIterator[T]:
        async for x in elements:
            if predicate(x):
                continue
            yield x
            break
        async for x in elements:
            yield x

    return _clamp


Tagged = tuple[Hashable, T]
Tagger = Callable[[T], Hashable]


@overload
def tag(tagger: Tagger[U]) -> Chain[U, Tagged[U]]:
    ...


@overload
def tag(tagger: Union[int, str]) -> Chain[_Sequence_, Tagged[_Sequence_]]:
    ...


def tag(tagger):
    if hasattr(tagger, "__call__"):
        tagger_ = cast(Tagger[U], tagger)
    else:
        index = int(tagger) if hasattr(tagger, "__int__") else str(tagger)

        def tagger_(x: _Sequence_) -> Hashable:
            return x[index]
    return map(lambda x: (tagger_(x), x))


strip: Chain[Tagged[T], T] = map(lambda tagd: tagd[1])  # type: ignore
# TBD:
#
# tag, strip
# sort
# reverse
# permutations
# combinations
# combinations_with_replacement
# extend
#
# Multisequences:
#
# gather/mix (tagged mixing)
# interleave
# zip, zip_longest, separate
# product
# join.inner, join.outer, join.left, join.anti
# groupby
# cond
# select
# cat
# dup
#
# Text:
#
# read, write (files)
# lines
# split
# glue (join)


__all__ = [
    "batch",
    "Chain",
    "clamp",
    "cut",
    "cumulate",
    "filter",
    "head",
    "link",
    "map",
    "mapargs",
    "ngrams",
    "reduce",
    "slice_",
    "strip",
    "tag",
    "tail",
    "Transform",
]
