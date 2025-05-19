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
    Never,
    Optional,
    Protocol,
    overload,
    TypeVar,
    Union
)


S = TypeVar("S", contravariant=True)
T = TypeVar("T", covariant=True)
U = TypeVar("U")


class _EndOfIteration:
    pass


_end_of_iteration = _EndOfIteration()


def iter_through_thread(it: AsyncIterable[T]) -> Iterator[T]:
    q: Queue[T | _ExceptionInIteration | _EndOfIteration] = Queue()

    async def transfer_to_queue():
        try:
            async for x in aiter(it):
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
class _ExceptionInIteration:
    exception: Exception


class IteratorBicolor(Protocol[T]):

    def __aiter__(self) -> AsyncIterator[T]:
        ...

    def __iter__(self) -> Iterator[T]:
        ...


def is_iterator_bicolor(x: Any) -> bool:
    if not hasattr(x, "__iter__"):
        return False
    return any(hasattr(x, attr) for attr in ["__aiter__", "__anext__"])


@dataclass
class WrapperBicolor(Generic[T]):
    _aiterable: AsyncIterable[T]

    @property
    def _aiter(self) -> AsyncIterator[T]:
        return aiter(self._aiterable)

    def __aiter__(self) -> AsyncIterator[T]:
        return self._aiter

    def __iter__(self) -> Iterator[T]:
        yield from iter_through_thread(self._aiter)


Input = (
    AsyncIterable[T] | AsyncIterator[T] | Iterable[T] | Iterator[T] | IteratorBicolor[T]
)


def as_iterator_bicolor(input: Input[T]) -> IteratorBicolor[T]:
    if is_iterator_bicolor(input):
        return cast(IteratorBicolor[T], input)
    elif any(hasattr(input, attr) for attr in ["__anext__", "__aiter__"]):
        return WrapperBicolor(cast(AsyncIterable[T], input))
    elif hasattr(input, "__iter__"):
        async def _iter():
            for x in input:
                yield x
        return WrapperBicolor(_iter())
    raise ValueError(f"Can't iterate over input: {repr(input)}")


Link = Callable[[AsyncIterable[S]], AsyncIterator[T]]


@dataclass
class Chain(Generic[S, T]):
    links: list[Link]

    def __or__(self, tail: "Chain[T, U]") -> "Chain[S, U]":
        if not isinstance(tail, Chain):
            return NotImplemented
        return Chain[S, U](self.links + tail.links)

    def __lt__(self, input: Input[S]) -> IteratorBicolor[T]:
        i_: AsyncIterable = as_iterator_bicolor(input)
        for link in self.links:
            i_ = link(i_)
        return WrapperBicolor(i_)


def link(fn: Link[S, T]) -> Chain[S, T]:
    return Chain([fn])


def map(function: Callable[[S], T]) -> Chain[S, T]:
    @link
    async def _map(elements: AsyncIterable[S]) -> AsyncIterator[T]:
        async for x in aiter(elements):
            yield function(x)

    return _map


def mapargs(function: Callable[..., T]) -> Chain[Iterable, T]:
    @link
    async def _mapargs(elements: AsyncIterable[Iterable]) -> AsyncIterator[T]:
        async for xs in aiter(elements):
            yield function(*xs)

    return _mapargs


Cumulation = Callable[[U, T], U]


@overload
def cumulate(cumulation: Cumulation[U, T], initial: U) -> Chain[T, U]:
    ...


@overload
def cumulate(cumulation: Cumulation[T, T], initial: Optional[T]) -> Chain[T, T]:
    ...


def cumulate(cumulation, initial=None):
    @link
    async def _cumulate(elements):
        elements_ = aiter(elements)
        try:
            if initial is None:
                snowball = await anext(elements_)
            else:
                snowball = initial

            yield snowball
            async for snowflake in elements_:
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


Predicate = Callable[[T], bool]


def filter(predicate: Predicate[T]) -> Chain[T, T]:
    @link
    async def _filter(elements: AsyncIterable[T]) -> AsyncIterator[T]:
        async for x in aiter(elements):
            if predicate(x):
                yield x

    return _filter


def batch(n: int) -> Chain[T, tuple[T, ...]]:
    if n < 1:
        raise ValueError(f"The batch size must be at least 1 (got {n})")

    @link
    async def _batch(elements: AsyncIterable[T]) -> AsyncIterator[tuple[T, ...]]:
        b: list[T] = []
        async for x in aiter(elements):
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
    async def _ngrams(elements: AsyncIterable[T]) -> AsyncIterator[tuple[T, ...]]:
        ngram: list[T] = []
        elements_ = aiter(elements)
        try:
            for _ in range(n):
                ngram.append(await anext(elements_))
            yield tuple(ngram)

            async for x in elements_:
                del ngram[0]
                ngram.append(x)
                yield tuple(ngram)
        except StopAsyncIteration:
            pass

    return _ngrams


async def _enumerate(elements: AsyncIterable[T]) -> AsyncIterator[tuple[int, T]]:
    i = 0
    elements_ = aiter(elements)
    try:
        while True:
            yield i, await anext(elements_)
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
    async def _slice_(elements: AsyncIterable[T]) -> AsyncIterator[T]:
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
    async def _tail(elements: AsyncIterable[T]) -> AsyncIterator[T]:
        the_tail: list[T] = []
        async for x in aiter(elements):
            the_tail.append(x)
            if len(the_tail) > n:
                the_tail.pop(0)
        for x in the_tail:
            yield x

    return _tail


def cut(predicate: Predicate[T]) -> Chain[T, T]:
    @link
    async def _cut(elements: AsyncIterable[T]) -> AsyncIterator[T]:
        async for x in aiter(elements):
            if not predicate(x):
                break
            yield x

    return _cut


def clamp(predicate: Predicate[T]) -> Chain[T, T]:
    @link
    async def _clamp(elements: AsyncIterable[T]) -> AsyncIterator[T]:
        elements_ = aiter(elements)
        async for x in elements_:
            if predicate(x):
                continue
            yield x
            break
        async for x in elements_:
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


def with_name(name: str) -> Labeler[U, str]:
    return lambda _: name


strip: Chain[Tagged[_Label, U], U] = map(lambda tagd: tagd.data)  # type: ignore


@link
async def sort(elements: AsyncIterable[Comparable]) -> AsyncIterator[Comparable]:
    elems_all: list[Comparable] = []
    async for x in aiter(elements):
        elems_all.append(x)
    for n in sorted(elems_all):
        yield n


@link
async def reverse(elements: AsyncIterable[U]) -> AsyncIterator[U]:
    elems_all: list[U] = []
    async for x in aiter(elements):
        elems_all.append(x)
    for x in elems_all[::-1]:
        yield x


def extend(*segments: Union[Iterable[U], AsyncIterable[U]]) -> Chain[U, U]:
    @link
    async def _extend(head: AsyncIterable[U]) -> AsyncIterator[U]:
        for segment in [head, *segments]:
            if hasattr(segment, "__aiter__"):
                async for x in aiter(cast(AsyncIterable[U], segment)):
                    yield x
            elif hasattr(segment, "__iter__"):
                for x in iter(segment):
                    yield x
            else:
                raise ValueError(
                    "One of the segments to extend the iteration is not iterable",
                    segment
                )

    return _extend


class TaggedIterable(Tagged[_Label, AsyncIterable[U]]):

    def __aiter__(self) -> AsyncIterator[U]:
        return cast(AsyncIterator[U], self.data)

    def __iter__(self) -> Iterator[U]:
        yield from iter_through_thread(
            aiter(cast(AsyncIterable[U], self.data))
        )


class concurrently:

    def __init__(
        self,
        *iterations_anon: AsyncIterable[Any],
        **iterations_named: AsyncIterable[Any]
    ) -> None:
        self._iterations_anon = iterations_anon
        self._iterations_named = iterations_named

    async def __aiter__(self) -> AsyncIterator[AsyncIterable[Any]]:
        for iteration in self._iterations_anon:
            yield as_iterator_bicolor(iteration)
        for name, iteration in self._iterations_named.items():
            yield TaggedIterable(name, as_iterator_bicolor(iteration))

    def __iter__(self) -> Iterator[AsyncIterable[Any]]:
        yield from iter_through_thread(aiter(self))


drain: Chain[Never, Never] = filter(lambda x: False)


@link
async def truncate(iterable: AsyncIterable[Never]) -> AsyncIterator[Never]:
    x: Never
    async for x in aiter(iterable):
        break
    if False:
        yield None

# TBD:
#
# permutations
# combinations
# combinations_with_replacement
#
# Multisequences:
#
# mix (tagged mixing)
# interleave
# zip, zip_longest, separate
# product
# join.inner, join.outer, join.left, join.anti
# groupby
# apply
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
    "concurrently",
    "cut",
    "cumulate",
    "drain",
    "extend",
    "filter",
    "head",
    "is_iterator_bicolor",
    "IteratorBicolor",
    "Link",
    "link",
    "map",
    "mapargs",
    "name",
    "ngrams",
    "reduce",
    "reverse",
    "sort",
    "slice_",
    "strip",
    "tag",
    "Tagged",
    "TaggedIterable",
    "tail",
    "truncate",
    "value_at",
    "with_name",
    "WrapperBicolor",
]
