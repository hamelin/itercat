

import marimo

__generated_with = "0.13.0"
app = marimo.App(width="full")


@app.cell
def _():
    from _test import test
    from itercat import map, mapargs, reduce, sink, step
    import marimo as mo  # noqa
    from operator import add, mul
    return add, map, mapargs, mul, reduce, sink, step, test


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
    with test("map-numbers"):
        _result = list(iter([3, 0, -2]) > map(lambda x: x * 2))
        _expected = [6, 0, -4]
        assert _result == _expected
    return


@app.cell
def _(map, test):
    with test("map-tuples"):
        _result = list(iter([(2, 3), (3, -8, 9), ()]) > map(len))
        _expected = [2, 3, 0]
        assert _result == _expected
    return


@app.cell
def _(map, test):
    with test("map-empty"):
        _result = list(iter([]) > map(lambda x: x + 1))
        _expected = []
        assert _result == _expected
    return


@app.cell
def _(increment, map, test):
    with test("map-composed"):
        _result = list(iter([2, 3, -5]) > map(lambda x: x * 2) | increment)
        _expected = [5, 7, -9]
        assert _result == _expected
    return


@app.cell
def _(add, mapargs, test):
    with test("mapargs-add"):
        _result = list(iter([(0, 7), (8, -2), (1, 3)]) > mapargs(add))
        _expected = [7, 6, 4]
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
