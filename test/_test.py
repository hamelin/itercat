import pdb
from types import TracebackType
from typing import Protocol, Self


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
        return False


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


