import asyncio
from collections.abc import (
    AsyncIterable,
    AsyncIterator,
    Callable,
    Hashable,
    Iterable,
    Iterator,
)
from dataclasses import dataclass
from queue import Queue
from threading import Thread
from typing import (
    Any,
    cast,
    Generic,
    Optional,
    Protocol,
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


class _EndOfIteration:
    pass


_end_of_iteration = _EndOfIteration()


@dataclass
class _ExceptionInIteration:
    exception: Exception


class IteratorBicolor(Protocol[T]):

    def __aiter__(self) -> AsyncIterator[T]:
        ...

    def __iter__(self) -> Iterator[T]:
        ...


def iter_through_thread(it: AsyncIterator[T]) -> Iterator[T]:
    q: Queue[Union[T, _ExceptionInIteration, _EndOfIteration]] = Queue()

    async def transfer_to_queue():
        try:
            async for x in it:
                q.put(x)
            q.put(_end_of_iteration)
        except Exception as ex:
            q.put(_ExceptionInIteration(ex))

    def run_transfer():
        asyncio.run(transfer_to_queue())

    th = Thread(target=run_transfer)
    th.start()
    while (_x := q.get()) is not _end_of_iteration:
        if isinstance(_x, _ExceptionInIteration):
            raise cast(_ExceptionInIteration, _x).exception
        yield cast(T, _x)
    th.join()


@dataclass
class _WrapperAsyncIterator(Generic[T]):
    _aiter: AsyncIterator[T]

    def __aiter__(self) -> AsyncIterator[T]:
        return self._aiter

    def __iter__(self) -> Iterator[T]:
        yield from iter_through_thread(self._aiter)


@dataclass
class Chain(Generic[S, T]):
    links: list[Transform]

    def __or__(self, tail: "Chain[T, U]") -> "Chain[S, U]":
        if not isinstance(tail, Chain):
            return NotImplemented
        return Chain[S, U](self.links + tail.links)

    def __lt__(self, input: Input[S]) -> IteratorBicolor[T]:
        i_: AsyncIterator = as_iterator(input)
        for link in self.links:
            i_ = link(i_)
        return _WrapperAsyncIterator(i_)


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


_Comparable = TypeVar("_Comparable", bound="Comparable")


class Comparable(Protocol):

    def __eq__(self, other: Any) -> bool:
        ...

    def __lt__(self: _Comparable, other: _Comparable) -> bool:
        ...


class Label(Comparable, Hashable, Protocol):
    pass


_Label = TypeVar("_Label", bound=Label)


@dataclass
class Tagged(Generic[_Label, U]):
    label: _Label
    data: U

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.label == other.label

    def __lt__(self: "Tagged[_Label, U]", other: "Tagged[_Label, U]") -> bool:
        return self.label < other.label


Labeler = Callable[[U], _Label]


def tag(labeler: Labeler[U, _Label]) -> Chain[U, Tagged[_Label, U]]:
    return map(lambda x: Tagged[_Label, U](labeler(x), x))


Index = TypeVar("Index", int, str, contravariant=True)


class Indexable(Protocol[Index]):

    def __getitem__(self, index: Index) -> Any:
        ...


def value_at(index: Index) -> Labeler[Indexable[Index], Label]:
    def _at(indexable: Indexable[Index]) -> Label:
        return cast(Label, indexable[index])

    return _at


strip: Chain[Tagged[_Label, U], U] = map(lambda tagd: tagd.data)  # type: ignore


@link
async def sort(elements: AsyncIterator[Comparable]) -> AsyncIterator[Comparable]:
    elems_all: list[Comparable] = []
    async for x in elements:
        elems_all.append(x)
    for n in sorted(elems_all):
        yield n


@link
async def reverse(elements: AsyncIterator[U]) -> AsyncIterator[U]:
    elems_all: list[U] = []
    async for x in elements:
        elems_all.append(x)
    for x in elems_all[::-1]:
        yield x


def extend(*segments: Union[Iterable[U], AsyncIterable[U]]) -> Chain[U, U]:
    @link
    async def _extend(head: AsyncIterator[U]) -> AsyncIterator[U]:
        for segment in [head, *segments]:
            if hasattr(segment, "__aiter__"):
                async for x in segment:
                    yield x
            elif hasattr(segment, "__iter__"):
                for x in segment:
                    yield x
            else:
                raise ValueError(
                    "One of the segments to extend the iteration is not iterable",
                    segment
                )

    return _extend


# TBD:
#
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
    "extend",
    "filter",
    "head",
    "link",
    "map",
    "mapargs",
    "ngrams",
    "reduce",
    "reverse",
    "sort",
    "slice_",
    "strip",
    "tag",
    "Tagged",
    "tail",
    "Transform",
    "value_at",
]
