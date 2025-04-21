

import marimo

__generated_with = "0.13.0"
app = marimo.App(width="full")


@app.cell
def _():
    from _test import test
    import itercat as cat
    import marimo as mo
    return cat, test


@app.cell
def _(cat, test):
    with test("hello"):
        assert cat.hello_world() == "Hello world"
    return


@app.cell
def _(test):
    with test("hey"):
        assert "hey" == "hey"
    return


@app.cell
def _(test):
    with test("one", debug=True):
        assert 1 == 1
    return


if __name__ == "__main__":
    app.run()
