from collections.abc import AsyncIterable, Iterator
from contextlib import contextmanager
import itertools as it
import marimo as mo
from marimo._plugins.core.web_component import JSONType
import pdb
from types import TracebackType
from typing import cast, Protocol, Self, TypeVar


S = TypeVar("S", covariant=True)
T = TypeVar("T", contravariant=True)


class Reporter(Protocol):

    def pass_test(self, tst: "test") -> None:
        ...

    def error_raised(self, tst: "test", value: Exception, tb: TracebackType) -> bool:
        ...


class ReporterMarimo:

    def pass_test(self, tst: "test") -> None:
        print(f"{tst.name}: ✅")

    def error_raised(self, tst: "test", value: Exception, tb: TracebackType) -> bool:
        if tst.debug:
            pdb.post_mortem(tb)
        return isinstance(value, SeqAssertionError)


class test:
    reporter: Reporter = ReporterMarimo()

    def __init__(self, name: str, debug: bool = False) -> None:
        self.name = name
        self.debug = debug

    def __enter__(self) -> Self:
        return self

    def __exit__(self, typ: type, value: Exception, tb: TracebackType) -> bool:
        if typ is None:
            self.reporter.pass_test(self)
            return False
        else:
            return self.reporter.error_raised(self, value, tb)


class SeqAssertionError(AssertionError):
    pass


async def assert_seq(seq: AsyncIterable[T], expected: list[T]) -> None:
    result: list[T] = []
    async for x in seq:
        result.append(x)

    if not (result == expected):
        mo.output.append(mo.md(f"**{chr(128721)} Results don't match expectations**"))
        mo.output.append(
            mo.ui.table(
                [
                    cast(dict[str, JSONType], {"expected": str(x), "result": str(r)})
                    for x, r in it.zip_longest(expected, result, fillvalue="")
                ]
            )
        )
        raise SeqAssertionError()


async def consume(elements: AsyncIterable[T]) -> None:
    async for _ in elements:
        pass


@contextmanager
def assert_raises(type_exc: type[Exception]) -> Iterator[None]:
    try:
        yield
    except Exception as err:
        if isinstance(err, type_exc):
            pass
        else:
            raise
    else:
        assert False, (
            f"Iterating through the sequence was supposed to raise {type_exc.__name__}"
        )
