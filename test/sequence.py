

import marimo

__generated_with = "0.13.2"
app = marimo.App(width="full")


@app.cell
def _():
    from _test import assert_seq, test
    from itercat import filter, map, mapargs, reduce, step
    import marimo as mo  # noqa
    from operator import add, mul, neg
    return add, assert_seq, filter, map, mapargs, mul, neg, reduce, step, test


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
def _(assert_seq, increment, iterations, test):
    for _name_seq, _seq, _incr in [
        ("once", increment, 1),
        ("thrice", increment | increment | increment, 3),
    ]:
        for _name_src, _src in iterations.items():
            with test(f"{_name_src}-incr-{_name_seq}"):
                _it = iter(_src) > _seq
                assert hasattr(_it, "__next__")
                assert_seq(_it, [_n + _incr for _n in _src])
    return


@app.cell
def _(assert_seq, increment, test):
    with test("notation_increment_thrice"):
        assert_seq([3, 0, -2] > increment | increment | increment, [6, 3, 1])
    return


@app.cell
def _(assert_seq, map, test):
    with test("map-numbers"):
        assert_seq([3, 0, -2] > map(lambda x: x * 2), [6, 0, -4])
    return


@app.cell
def _(assert_seq, map, test):
    with test("map-tuples"):
        assert_seq([(2, 3), (3, -8, 9), ()] > map(len), [2, 3, 0])
    return


@app.cell
def _(assert_seq, map, test):
    with test("map-empty"):
        assert_seq([] > map(lambda x: x + 1), [])
    return


@app.cell
def _(assert_seq, increment, map, test):
    with test("map-composed"):
        assert_seq([2, 3, -5] > map(lambda x: x * 2) | increment, [5, 7, -9])
    return


@app.cell
def _(add, assert_seq, mapargs, test):
    with test("mapargs-add"):
        assert_seq([(0, 7), (8, -2), (1, 3)] > mapargs(add), [7, 6, 4])
    return


@app.cell
def _(assert_seq, mul, reduce, test):
    with test("reduce-mul"):
        assert_seq([2, 8, -1] > reduce(mul, 1), [-16])
    return


@app.cell
def _(assert_seq, mul, reduce, test):
    with test("reduce-mul-single-item"):
        assert_seq([2] > reduce(mul), [2])
    return


@app.cell
def _(assert_seq, mul, reduce, test):
    with test("reduce-mul-no-item"):
        assert_seq([] > reduce(mul, 3), [3])
    return


@app.cell
def _(assert_seq, reduce, test):
    with test("reduce-changing-input-type"):
        assert_seq([4, 5, 6] > reduce(lambda lst, x: [x, *lst], []), [[6, 5, 4]])
    return


@app.cell
def _(assert_seq, filter, test):
    with test("filter"):
        assert_seq([4, -2, 0, 1, -1] > filter(lambda x: x < 0), [-2, -1])
    return


@app.cell
def _(add, assert_seq, filter, map, neg, reduce, test):
    with test("map-filter-reduce"):
        _seq = map(neg) | filter(lambda x: x > 0) | reduce(add, 0)
        assert_seq((4, -2, 0, 1, -1) > _seq, [3])
    return


if __name__ == "__main__":
    app.run()
