

import marimo

__generated_with = "0.13.0"
app = marimo.App(width="full")


@app.cell
def _():
    from _test import assert_seq, test
    import marimo as mo  # noqa
    from operator import add, mul, neg

    from itercat import (
        batch,
        cumulate,
        filter,
        map,
        mapargs,
        reduce,
        step,
    )
    return (
        add,
        assert_seq,
        batch,
        cumulate,
        filter,
        map,
        mapargs,
        mul,
        neg,
        reduce,
        step,
        test,
    )


@app.cell
def _():
    iterations = {"empty": [], "numbers": [5, 0, 8, 2, -1]}
    return (iterations,)


@app.cell
def _(step):
    @step
    async def increment(nums):
        async for num in nums:
            yield num + 1
    return (increment,)


@app.cell
async def _(assert_seq, increment, iterations, test):
    for _name_seq, _seq, _incr in [
        ("once", increment, 1),
        ("thrice", increment | increment | increment, 3),
    ]:
        for _name_src, _src in iterations.items():
            with test(f"{_name_src}-incr-{_name_seq}"):
                _it = iter(_src) > _seq
                assert hasattr(_it, "__anext__")
                await assert_seq(_it, [_n + _incr for _n in _src])
    return


@app.cell
async def _(assert_seq, increment, test):
    with test("notation_increment_thrice"):
        await assert_seq([3, 0, -2] > increment | increment | increment, [6, 3, 1])
    return


@app.cell
async def _(assert_seq, map, test):
    with test("map-numbers"):
        await assert_seq([3, 0, -2] > map(lambda x: x * 2), [6, 0, -4])
    return


@app.cell
async def _(assert_seq, map, test):
    with test("map-tuples"):
        await assert_seq([(2, 3), (3, -8, 9), ()] > map(len), [2, 3, 0])
    return


@app.cell
async def _(assert_seq, map, test):
    with test("map-empty"):
        await assert_seq([] > map(lambda x: x + 1), [])
    return


@app.cell
async def _(assert_seq, increment, map, test):
    with test("map-composed"):
        await assert_seq([2, 3, -5] > map(lambda x: x * 2) | increment, [5, 7, -9])
    return


@app.cell
async def _(add, assert_seq, mapargs, test):
    with test("mapargs-add"):
        await assert_seq([(0, 7), (8, -2), (1, 3)] > mapargs(add), [7, 6, 4])
    return


@app.cell
async def _(assert_seq, mul, reduce, test):
    with test("reduce-mul"):
        await assert_seq([2, 8, -1] > reduce(mul, 1), [-16])
    return


@app.cell
async def _(assert_seq, mul, reduce, test):
    with test("reduce-mul-single-item"):
        await assert_seq([2] > reduce(mul), [2])
    return


@app.cell
async def _(assert_seq, mul, reduce, test):
    with test("reduce-mul-no-item"):
        await assert_seq([] > reduce(mul, 3), [3])
    with test("reduce-mul-no-item-no-initial"):
        await assert_seq([] > reduce(mul), [])
    return


@app.cell
async def _(assert_seq, reduce, test):
    with test("reduce-changing-input-type"):
        await assert_seq([4, 5, 6] > reduce(lambda lst, x: [x, *lst], []), [[6, 5, 4]])
    return


@app.cell
async def _(assert_seq, filter, test):
    with test("filter"):
        await assert_seq([4, -2, 0, 1, -1] > filter(lambda x: x < 0), [-2, -1])
    return


@app.cell
async def _(add, assert_seq, filter, map, neg, reduce, test):
    with test("map-filter-reduce"):
        _seq = map(neg) | filter(lambda x: x > 0) | reduce(add, 0)
        await assert_seq((4, -2, 0, 1, -1) > _seq, [3])
    return


@app.cell
async def _(add, assert_seq, cumulate, test):
    with test("cumulate-no-initial"):
        await assert_seq([3, 4, 5] > cumulate(add), [3, 7, 12])
    return


@app.cell
async def _(assert_seq, cumulate, mul, test):
    with test("cumulate-initial"):
        await assert_seq([3, 4, 5] > cumulate(mul, -1), [-1, -3, -12, -60])
    return


@app.cell
async def _(assert_seq, cumulate, mul, test):
    with test("cumulate-empty"):
        await assert_seq([] > cumulate(mul), [])
    with test("cumulate-empty-with-initial"):
        await assert_seq([] > cumulate(mul, 88), [88])
    return


@app.cell
async def _(assert_seq, batch, test):
    with test("batch-no-remainder"):
        await assert_seq([2, 3, 4, 5, 6, 7] > batch(3), [(2, 3, 4), (5, 6, 7)])
    return


@app.cell
async def _(assert_seq, batch, test):
    with test("batch-with-remainder"):
        await assert_seq([2, 3, 4, 5] > batch(3), [(2, 3, 4), (5,)])
    return


@app.cell
def _(batch, test):
    for n in [0, -2]:
        with test(f"batch-bad-size-{n}"):
            try:
                batch(n)
            except ValueError:
                pass
            else:
                assert False, n
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
