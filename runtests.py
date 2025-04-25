from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from pygments import highlight
from pygments.lexers.python import PythonTracebackLexer
from pygments.formatters import TerminalFormatter
import sys
from traceback import format_exception
from types import TracebackType


path_suite = Path(__file__).parent / "test"
if not path_suite.is_dir():
    print(f"ERROR: {path_suite} is not a valid directory or cannot be read in")
    sys.exit(2)
sys.path.append(str(path_suite))
from _test import test  # noqa


_Issue = tuple[test, Exception]


class ReporterTerminal:

    def __init__(self, issues: list[_Issue]) -> None:
        self.issues = issues

    def pass_test(self, tst: test) -> None:
        print(".", end="")
        sys.stdout.flush()

    def error_raised(self, tst: test, ex: Exception, tb: TracebackType) -> bool:
        print("X" if isinstance(ex, AssertionError) else "E", end="")
        sys.stdout.flush()
        self.issues.append((tst, ex))
        return True


issues: dict[str, list[_Issue]] = {}
for p in path_suite.iterdir():
    name = p.name
    try:
        if p.is_file() and "app = marimo.App" in p.read_text("utf-8"):
            name_module = f"test.{p.with_suffix('').name}"
            loader = SourceFileLoader(name_module, str(p.absolute()))
            spec = spec_from_loader(name_module, loader)
            if spec is None:
                raise RuntimeError(f"Can't make module spec for test {name}")
            module_test = module_from_spec(spec)
            loader.exec_module(module_test)
            if hasattr(module_test, "app"):
                print(f"{name}: ", end="")
                issues[name] = []
                test.reporter = ReporterTerminal(issues[name])
                module_test.app.run()
                print()
    except ImportError:
        print(f"ERROR: problem while importing test notebook {name}")
        raise
    except IOError:
        print(f"ERROR: cannot read file {p}")
        raise

print()
has_issue = False
for name, issues_ in issues.items():
    if issues_:
        has_issue = True
        print()
        heading = (
            f"Notebook {name}: {len(issues_)} issue{'s' if len(issues_) > 1 else ''}"
        )
        print("=" * len(heading))
        print(heading)
        print("=" * len(heading))
        print()

        for tst, exc in issues_:
            print(f"--- Test {tst.name} ---\n")
            print(
                highlight(
                    "".join(format_exception(exc)),
                    PythonTracebackLexer(),
                    TerminalFormatter()
                )
            )

sys.exit(11 if has_issue else 0)
