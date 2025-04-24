

import marimo

__generated_with = "0.13.0"
app = marimo.App(width="full")


@app.cell
def _():
    from _test import test
    from itercat import map, reduce, sink, step
    import marimo as mo  # noqa
    from operator import add, mul
    return add, map, mul, reduce, sink, step, test


@app.cell
def _():
    iterations = {"empty": [], "numbers": [5, 0, 8, 2, -1]}
    return (iterations,)


@app.cell
def _(step):
    @step
    def increment(nums):
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
            with test(f"{_name_src}-incr-{_name_seq}"):
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
def _(map, test):
    with test("map-on-tuples-fail"):
        try:
            for _ in iter([(1, 2)]) > map(lambda p: p[0]):
                pass
            assert False, "Should not get here"
        except TypeError:
            pass
    return


@app.cell
def _(map, test):
    with test("map-on-tuples-success"):
        _result = list(iter([(1, 2)]) > map(lambda p: p[0], flatten_args=False))
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
            > map(_counts_args, variable_input=True)
        )
        _expected = [(1, 0), (3, 0), (0, 0), (2, 1)]
        assert _result == _expected
    return


@app.cell
def _(map, sink, test):
    with test("map-sink"):
        _result = iter([4, 8, -2]) > map(lambda x: x + 1) | sink(sum)
        _expected = 13
        assert _result == _expected
    return


@app.cell
def _(sink, test):
    with test("sink-alone"):
        _result = iter([4, 8, -2]) > sink(sum)
        _expected = 10
        assert _result == _expected
    return


@app.cell
def _(mul, reduce, test):
    with test("reduce-mul"):
        _result = iter([2, 8, -1]) > reduce(mul, 1)
        _expected = -16
        assert _result == _expected
    return


@app.cell
def _(mul, reduce, test):
    with test("reduce-mul-single-item"):
        _result = iter([2]) > reduce(mul)
        _expected = 2
        assert _result == _expected
    return


@app.cell
def _(mul, reduce, test):
    with test("reduce-mul-no-item"):
        _result = iter([]) > reduce(mul, 3)
        _expected = 3
        assert _result == _expected
    return


@app.cell
def _(reduce, test):
    with test("reduce-changing-input-type"):
        _result = iter([4, 5, 6]) > reduce(lambda lst, x: [x, *lst], [])
        _expected = [6, 5, 4]
        assert _result == _expected
    return


if __name__ == "__main__":
    app.run()
