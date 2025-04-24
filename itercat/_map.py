from typing import Any, Callable, TypeVar


T = TypeVar("T")
Function = Callable[..., T]
Application = Callable[[Any], T]
Process = Callable[[Function[T], Any], tuple[T, "Process[T]"]]


def choose_how_to_apply(func: Function[T], x: Any) -> Application[T]:
    if isinstance(x, tuple):
        if len(x) == 2 and isinstance(x[0], tuple) and isinstance(x[1], dict):
            return lambda a: func(*a[0], **a[1])
        else:
            return lambda a: func(*a)
    elif isinstance(x, dict):
        return lambda a: func(**a)
    return lambda a: func(a)


def apply_function_variable(func: Function[T], x: Any) -> tuple[T, Process[T]]:
    return choose_how_to_apply(func, x)(x), apply_function_variable


def apply_function_uniform(func: Function[T], x: Any) -> tuple[T, Process[T]]:
    application = choose_how_to_apply(func, x)

    def apply_cached(func_: Function[T], x: Any) -> tuple[T, Process[T]]:
        if func_ is not func:
            raise RuntimeError(
                f"Process should always be using the function {func}, "
                f"this time it used {func_}"
            )
        return application(x), apply_cached

    return apply_cached(func, x)


# This is a private module.
__all__: list[str] = []
