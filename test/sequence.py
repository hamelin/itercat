

import marimo

__generated_with = "0.13.0"
app = marimo.App(width="full")


@app.cell
def _():
    from _test import test
    from collections.abc import Iterator
    from itercat import sequence
    import marimo as mo
    return Iterator, sequence, test


@app.cell
def _():
    iterations = {
        "empty": [],
        "numbers": [5, 0, 8, 2, -1]
    }
    return (iterations,)


@app.cell
def _(Iterator, sequence):
    @sequence
    def increment(nums: Iterator[int]) -> Iterator[int]:
        for num in nums:
            yield num + 1
    return (increment,)


@app.cell
def _(increment, iterations, test):
    for _name_seq, _seq, _incr in [
        ("once", increment, 1),
        ("thrice", increment | increment | increment, 3),
    ]:
        for _name_src, _src in iterations.items():
            with test(f"{_name_src}-incr-{_name_seq}") as _t:
                _it = iter(_src) > _seq
                assert hasattr(_it, "__next__")
                _expected = [_n + _incr for _n in _src]
                assert list(_it) == _expected
    return


@app.cell
def _(increment, test):
    with test("notation_increment_thrice"):
        assert list(iter([3, 0, -2]) > increment | increment | increment) == [6, 3, 1]
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
