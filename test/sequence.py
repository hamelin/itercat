

import marimo

__generated_with = "0.13.0"
app = marimo.App(width="full")


@app.cell
def _():
    from _test import test
    from collections.abc import Iterator
    from itercat import entuple, map, sequence
    import marimo as mo
    from operator import add
    return Iterator, add, entuple, map, sequence, test


@app.cell
def _():
    iterations = {"empty": [], "numbers": [5, 0, 8, 2, -1]}
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
def _(map, test):
    with test("map-simple"):
        _result = list(iter([3, 0, -2]) > map(lambda x: x * 2))
        _expected = [6, 0, -4]
        assert _result == _expected
    return


@app.cell
def _(add, map, test):
    with test("map-tuple"):
        _result = list(iter([(2, 3), (3, -8), (0, 77)]) > map(add))
        _expected = [5, -5, 77]
        assert _result == _expected
    return


@app.function
def axpy(a, x, y=0):
    return a * x + y


@app.cell
def _(map, test):
    with test("map-args-kwargs"):
        _result = list(
            iter([((5, 8), {}), ((0, 9), {"y": -2}), ((4,), {"y": 8, "x": -2})]) > map(axpy)
        )
        _expected = [40, -2, 0]
        assert _result == _expected
    return


@app.cell
def _(map, test):
    with test("map-on-empty"):
        _result = list(iter([]) > map(axpy))
        _expected = []
        assert _result == _expected
    return


@app.cell
def _(entuple, test):
    with test("entuple"):
        _result = list(iter([5, 6, 8, ()]) > entuple)
        _expected = [(5,), (6,), (8,), ((),)]
        assert _result == _expected
    return


@app.cell
def _(map, test):
    with test("map-on-tuples-fail"):
        try:
            for x in iter([(1, 2)]) > map(lambda p: p[0]):
                pass
            assert False, "Should not get here"
        except TypeError:
            pass
    return


@app.cell
def _(entuple, map, test):
    with test("map-on-tuples-success"):
        _result = list(iter([(1, 2)]) > entuple | map(lambda p: p[0]))
        _expected = [1]
        assert _result == _expected
    return


@app.cell
def _(map, test):
    def _counts_args(*args, **kwargs):
        return (len(args), len(kwargs))


    with test("map-variable-elements"):
        _result = list(
            iter(
                [
                    8,
                    (4, 9, 0),
                    ((), {}),
                    ((3, 1), {"a": 5}),
                ]
            )
            > map(_counts_args, is_input_variable=True)
        )
        _expected = [(1, 0), (3, 0), (0, 0), (2, 1)]
        assert _result == _expected
    return


if __name__ == "__main__":
    app.run()
