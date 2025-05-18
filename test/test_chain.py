import marimo

__generated_with = "0.13.9"
app = marimo.App(width="full", app_title="Unit tests on basic chains")

with app.setup:
    import itertools as it
    import marimo as mo  # noqa
    from math import sqrt
    from operator import add, mul, neg
    import pytest

    from itercat import (  # type: ignore
        batch,
        clamp,
        cut,
        cumulate,
        extend,
        filter,
        head,
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
        value_at,
    )
    from _test import increment


@app.function
@pytest.mark.parametrize(
    "elements,chain",
    it.product([[], [5, 0, 8, 2, -1]], [increment, increment | increment | increment])
)
def test_simple_chain(elements, chain):
    ait = elements > chain
    assert hasattr(ait, "__aiter__")
    assert list(ait) == [n + len(chain.links) for n in elements]


@app.function
def test_notation_increment_thrice():
    assert [6, 3, 1] == list([3, 0, -2] > increment | increment | increment)


@app.function
def test_map_numbers():
    assert [6, 0, -4] == list([3, 0, -2] > map(lambda x: x * 2))


@app.function
def test_map_empty():
    assert [] == list([] > map(lambda x: x + 1))


@app.function
def test_map_composed():
    assert [5, 7, -9] == list([2, 3, -5] > map(lambda x: x * 2) | increment)


@app.function
def test_mapargs_add():
    assert [7, 6, 4] == list([(0, 7), (8, -2), (1, 3)] > mapargs(add))


@app.function
def test_reduce_mul():
    assert [-16] == list([2, 8, -1] > reduce(mul, 1))


@app.function
def test_reduce_mul_single_item():
    assert [2] == list([2] > reduce(mul))


@app.function
def test_reduce_mul_no_item():
    assert [3] == list([] > reduce(mul, 3))


@app.function
def test_reduce_mul_no_item_no_initial():
    assert [] == list([] > reduce(mul))


@app.function
def test_reduce_changing_input_type():
    assert [[6, 5, 4]] == list([4, 5, 6] > reduce(lambda lst, x: [x, *lst], []))


@app.function
def test_filter():
    assert [-2, -1] == list([4, -2, 0, 1, -1] > filter(lambda x: x < 0))


@app.function
def test_map_filter_reduce():
    _seq = map(neg) | filter(lambda x: x > 0) | reduce(add, 0)
    assert [3] == list((4, -2, 0, 1, -1) > _seq)


@app.function
def test_cumulate_no_initial():
    assert [3, 7, 12] == list([3, 4, 5] > cumulate(add))


@app.function
def test_cumulate_initial():
    assert [-1, -3, -12, -60] == list([3, 4, 5] > cumulate(mul, -1))


@app.function
@pytest.mark.parametrize("initial,expected", [(88, [88]), (None, [])])
def test_cumulate_empty(initial, expected):
    assert expected == list([] > cumulate(mul, initial))


@app.function
@pytest.mark.parametrize(
    "elements,expected",
    [
        ([2, 3, 4, 5, 6, 7], [(2, 3, 4), (5, 6, 7)]),
        ([2, 3, 4, 5], [(2, 3, 4), (5,)]),
    ],
)
def test_batch_3(elements, expected):
    assert expected == list(elements > batch(3))


@app.function
@pytest.mark.parametrize("size", [0, -2])
def test_batch_bad_size(size):
    with pytest.raises(ValueError):
        batch(size)


@app.function
@pytest.mark.parametrize(
    "n,expected",
    [
        (1, [(0,), (1,), (2,), (3,), (4,), (5,)]),
        (2, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]),
        (3, [(0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5)]),
        (4, [(0, 1, 2, 3), (1, 2, 3, 4), (2, 3, 4, 5)]),
        (5, [(0, 1, 2, 3, 4), (1, 2, 3, 4, 5)]),
        (6, [(0, 1, 2, 3, 4, 5)]),
        (7, []),
    ],
)
def test_ngrams(n, expected):
    assert expected == list(range(6) > ngrams(n))


@app.function
def test_ngrams_n_too_small():
    with pytest.raises(ValueError):
        ngrams(0)


@app.function
@pytest.mark.parametrize(
    "start,stop,step,expected",
    [
        (4, None, 1, [0, 1, 2, 3]),
        (8, 10, 1, [8, 9]),
        (3, 10, 3, [3, 6, 9]),
        (5, 10, 2, [5, 7, 9]),
        (7, 20, 1, [7, 8, 9, 10, 11]),
        (5, 5, 1, []),
        (8, 3, 1, []),
        (6, 6, 6, []),
        (0, -1, 1, []),
    ],
)
def test_slice(start, stop, step, expected):
    assert expected == list(range(12) > slice_(start, stop, step))


@app.function
@pytest.mark.parametrize("start,stop,step", [(0, 10, 0), (0, 10, -1), (-2, 10, 1)])
def test_slice_illegal_arguments(start, stop, step):
    with pytest.raises(ValueError):
        slice_(start, stop, step)


@app.function
def letters_():
    yield list("abcdefghijklmnopqrstuvqrstuvwxyz")


@app.function
def letters_few_():
    for letters in letters_():
        yield letters[:3]


@app.function
@pytest.mark.parametrize("n,expected", [(5, list("abcde")), (0, [])])
def test_head(n, expected):
    for letters in letters_():
        assert expected == list(letters > head(n))


@app.function
def test_head_negative():
    with pytest.raises(ValueError):
        head(-1)


@app.function
def test_head_short():
    for letters_few in letters_few_():
        assert letters_few == list(letters_few > head(10))


@app.function
@pytest.mark.parametrize("n,expected", [(5, list("vwxyz")), (0, [])])
def test_tail(n, expected):
    for letters in letters_():
        assert expected == list(letters > tail(n))


@app.function
def test_tail_negative():
    with pytest.raises(ValueError):
        tail(-1)


@app.function
def test_tail_short():
    for letters_few in letters_few_():
        assert letters_few == list(letters_few > tail(10))


@app.function
def test_cut():
    assert list(range(10)) == list(it.count(0) > cut(lambda x: x < 10))


@app.function
def test_clamp():
    assert [1, 0, 0, 2] == list([0, 0, 0, 0, 1, 0, 0, 2] > clamp(lambda x: x == 0))


@app.function
def test_tag_numbers():
    assert [
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
    ] == list(
        range(10) > tag(lambda n: "zero-mod3" if n % 3 == 0 else "other")
    )


@app.function
def test_tag_records_by_index():
    assert [
        Tagged[str, tuple[str, int, str]]("asdf", ("asdf", 23, "qwer")),
        Tagged[str, tuple[str, int, str]]("zxcv", ("zxcv", 8, "ghgh")),
        Tagged[str, tuple[str, int, str]]("asdf", ("asdf", 2, "poiu")),
    ] == list(
        [("asdf", 23, "qwer"), ("zxcv", 8, "ghgh"), ("asdf", 2, "poiu")]
        > tag(value_at(0))
    )


@app.function
def test_strip():
    assert [8, 12, 9, 0] == list(
        [
            Tagged[str, int]("b", 8),
            Tagged[str, int]("a", 12),
            Tagged[str, int]("a", 9),
            Tagged[str, int]("b", 0),
        ]
        > strip
    )


@app.function
def test_sort():
    assert ["asdf", "ghgh", "poiu", "qwer", "zxcv"] == list(
        ["zxcv", "ghgh", "poiu", "asdf", "qwer"] > sort
    )


@app.function
def cplxs_():
    yield [5 + 8j, 0 + 2j, 5 - 7j, 1.0]


@app.cell
def _():
    for cplxs in cplxs_():
        print(cplxs)
    return


@app.function
def test_sort_complex_not_comparable():
    for cplxs in cplxs_():
        with pytest.raises(TypeError):
            cplxs[0] < cplxs[1]
        with pytest.raises(TypeError):
            list(cplxs > sort)
    assert True


@app.function
def test_sort_tagged_uncomparable():
    for cplxs in cplxs_():
        assert [
            Tagged[float, complex](1.0, 1.0),
            Tagged[float, complex](2.0, 0 + 2j),
            Tagged[float, complex](sqrt(25 + 49), 5 - 7j),
            Tagged[float, complex](sqrt(25 + 64), 5 + 8j),
        ] == list(cplxs > tag(abs) | sort)


@app.function
def strings_():
    yield


@app.function
@pytest.mark.parametrize("iteration", [[["qwer", "asdf", "zxcv", "tyty"]], cplxs_()])
def test_reverse(iteration):
    for values in iteration:
        assert list(reversed(values)) == list(values > reverse)


@app.function
def test_extend():
    async def _iter():
        yield 8
        yield 7

    assert [2, 3, 4, 8, 7, 1, 2, 8] == list([2, 3, 4] > extend(_iter(), [1, 2, 8]))


if __name__ == "__main__":
    app.run()
