

import marimo

__generated_with = "0.13.0"
app = marimo.App(width="full")


@app.cell
def _():
    from _test import assert_raises, assert_seq, consume, test
    import itertools as it
    import marimo as mo  # noqa
    from math import sqrt
    from operator import add, mul, neg

    from itercat import (
        batch,
        clamp,
        cut,
        cumulate,
        extend,
        filter,
        head,
        link,
        map,
        mapargs,
        ngrams,
        reduce,
        reverse,
        sort,
        slice_,
        strip,
        tag,
        Tagged,
        tail,
    )
    return (
        Tagged,
        add,
        assert_raises,
        assert_seq,
        batch,
        clamp,
        consume,
        cumulate,
        cut,
        extend,
        filter,
        head,
        it,
        link,
        map,
        mapargs,
        mul,
        neg,
        ngrams,
        reduce,
        reverse,
        slice_,
        sort,
        sqrt,
        strip,
        tag,
        tail,
        test,
    )


@app.cell
def _():
    iterations = {"empty": [], "numbers": [5, 0, 8, 2, -1]}
    return (iterations,)


@app.cell
def _(link):
    @link
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
    for _n in [0, -2]:
        with test(f"batch-bad-size_{_n}"):
            try:
                batch(_n)
            except ValueError:
                pass
            else:
                assert False, _n
    return


@app.cell
async def _(assert_seq, ngrams, test):
    _nums = list(range(6))
    for _n, _expected in [
        (1, [(0,), (1,), (2,), (3,), (4,), (5,)]),
        (2, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]),
        (3, [(0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5)]),
        (4, [(0, 1, 2, 3), (1, 2, 3, 4), (2, 3, 4, 5)]),
        (5, [(0, 1, 2, 3, 4), (1, 2, 3, 4, 5)]),
        (6, [(0, 1, 2, 3, 4, 5)]),
        (7, []),
    ]:
        with test(f"ngrams-{_n}"):
            await assert_seq(_nums > ngrams(_n), _expected)
    return


@app.cell
def _(ngrams, test):
    with test("ngrams-n-too-small"):
        try:
            ngrams(0)
        except ValueError:
            pass
        else:
            assert False
    return


@app.cell
async def _(assert_raises, assert_seq, consume, slice_, test):
    _nums = list(range(12))
    for _start, _stop, _step, _expected in [
        (4, None, 1, [0, 1, 2, 3]),
        (8, 10, 1, [8, 9]),
        (3, 10, 3, [3, 6, 9]),
        (5, 10, 2, [5, 7, 9]),
        (7, 20, 1, [7, 8, 9, 10, 11]),
        (5, 5, 1, []),
        (8, 3, 1, []),
        (6, 6, 6, []),
        (0, -1, 1, []),
    ]:
        with test(f"slice-{_start}-{_stop}-{_step}"):
            await assert_seq(_nums > slice_(_start, _stop, _step), _expected)

    with test("slice-step-0"):
        with assert_raises(ValueError):
            await consume(_nums > slice_(4, step=0))
    with test("slice-step-negative"):
        with assert_raises(ValueError):
            await consume(_nums > slice_(4, 0, step=-1))
    with test("slice-start-negative"):
        with assert_raises(ValueError):
            await consume(_nums > slice_(-2, 10))
    return


@app.cell
def _():
    letters = list("abcdefghijklmnopqrstuvqrstuvwxyz")
    letters_few = letters[:3]
    return letters, letters_few


@app.cell
async def _(
    assert_raises,
    assert_seq,
    consume,
    head,
    letters,
    letters_few,
    test,
):
    for _n, _expected in [(5, list("abcde")), (0, [])]:
        with test(f"head-{_n}"):
            await assert_seq(letters > head(_n), _expected)

    with test("head-negative"):
        with assert_raises(ValueError):
            await consume(letters > head(-1))

    with test("head-short"):
        await assert_seq(letters_few > head(5), letters_few)
    return


@app.cell
async def _(
    assert_raises,
    assert_seq,
    consume,
    letters,
    letters_few,
    tail,
    test,
):
    for _n, _expected in [(5, list("vwxyz")), (0, [])]:
        with test(f"tail-{_n}"):
            await assert_seq(letters > tail(_n), _expected)

    with test("tail-negative"):
        with assert_raises(ValueError):
            await consume(letters > tail(-1))

    with test("tail-short"):
        await assert_seq(letters_few > tail(5), letters_few)
    return


@app.cell
async def _(assert_seq, cut, it, test):
    with test("cut"):
        await assert_seq(it.count(0) > cut(lambda x: x < 10), list(range(10)))
    return


@app.cell
async def _(assert_seq, clamp, test):
    with test("clamp"):
        await assert_seq([0, 0, 0, 0, 1, 0, 0, 2] > clamp(lambda x: x == 0), [1, 0, 0, 2])
    return


@app.cell
async def _(Tagged, assert_seq, tag, test):
    with test("tag-numbers"):
        await assert_seq(
            range(10) > tag(lambda n: "zero-mod3" if n % 3 == 0 else "other"),
            [
                Tagged[str, int]("zero-mod3", 0),
                Tagged[str, int]("other", 1),
                Tagged[str, int]("other", 2),
                Tagged[str, int]("zero-mod3", 3),
                Tagged[str, int]("other", 4),
                Tagged[str, int]("other", 5),
                Tagged[str, int]("zero-mod3", 6),
                Tagged[str, int]("other", 7),
                Tagged[str, int]("other", 8),
                Tagged[str, int]("zero-mod3", 9),
            ],
        )
    return


@app.cell
async def _(Tagged, assert_seq, tag, test):
    with test("tag-records-by-index"):
        await assert_seq(
            [("asdf", 23, "qwer"), ("zxcv", 8, "ghgh"), ("asdf", 2, "poiu")] > tag(0),
            [
                Tagged[str, tuple[str, int, str]]("asdf", ("asdf", 23, "qwer")),
                Tagged[str, tuple[str, int, str]]("zxcv", ("zxcv", 8, "ghgh")),
                Tagged[str, tuple[str, int, str]]("asdf", ("asdf", 2, "poiu")),
            ],
        )
    return


@app.cell
async def _(Tagged, assert_seq, strip, test):
    with test("strip"):
        await assert_seq(
            [
                Tagged[str, int]("b", 8),
                Tagged[str, int]("a", 12),
                Tagged[str, int]("a", 9),
                Tagged[str, int]("b", 0),
            ]
            > strip,
            [8, 12, 9, 0],
        )
    return


@app.cell
async def _(assert_seq, sort, test):
    with test("sort"):
        await assert_seq(
            ["zxcv", "ghgh", "poiu", "asdf", "qwer"] > sort,
            ["asdf", "ghgh", "poiu", "qwer", "zxcv"]
        )
    return


@app.cell
async def _(assert_raises, consume, sort, test):
    cplxs = [5 + 8j, 0 + 2j, 5 - 7j, 1.0]
    with test("complex-not-comparable"):
        with assert_raises(TypeError):
            cplxs[0] < cplxs[1]
    with test("sort-uncomparable-typeerror"):
        with assert_raises(TypeError):
            await consume(cplxs > sort)
    return (cplxs,)


@app.cell
async def _(Tagged, assert_seq, cplxs, sort, sqrt, tag, test):
    with test("sort-tagged-uncomparable"):
        await assert_seq(
            cplxs > tag(abs) | sort,
            [
                Tagged[float, complex](1.0, 1.0),
                Tagged[float, complex](2.0, 0 + 2j),
                Tagged[float, complex](sqrt(25 + 49), 5 - 7j),
                Tagged[float, complex](sqrt(25 + 64), 5 + 8j),
            ],
        )

    return


@app.cell
async def _(assert_seq, cplxs, reverse, test):
    for name, data in [("strings", ["qwer", "asdf", "zxcv", "tyty"]), ("complexes", cplxs)]:
        with test(f"reverse-{name}"):
            await assert_seq(data > reverse, list(reversed(data)))
    return


@app.cell
async def _(assert_seq, extend, test):
    async def _iter():
        yield 8
        yield 7

    with test("extend"):
        await assert_seq([2, 3, 4] > extend(_iter(), [1, 2, 8]), [2, 3, 4, 8, 7, 1, 2, 8])
    return


if __name__ == "__main__":
    app.run()
