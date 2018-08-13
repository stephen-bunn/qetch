# Copyright (c) 2018 Stephen Bunn <stephen@bunn.io>
# MIT License <https://opensource.org/licenses/MIT>

import json
from typing import Any, Tuple, Callable
from functools import update_wrapper
from contextlib import contextmanager
from pathlib import Path

from .. import __version__
from ..auth import AuthRegistry

import click
from tqdm import tqdm
from plumbum import colors
from log_symbols import LogSymbols
from yaspin import yaspin, spinners

COLOR_STYLES = dict(
    warning="fg yellow",
    success="fg green bold",
    highlight="bg yellow",
    error="fg red bold",
    fatal="bg red bold",
    info="fg cyan",
    debug="dim",
)


def load_colors(style: dict = COLOR_STYLES):
    colors.load_stylesheet(style)


@contextmanager
def auth_registry(filepath: str):
    filepath = Path(filepath)

    def init():
        with filepath.open("w") as stream:
            json.dump({}, stream)

    if not filepath.is_file():
        init()
    registry = None
    with filepath.open("r") as stream:
        try:
            json.load(stream)
        except json.JSONDecodeError:
            init()
        stream.seek(0)
        registry = AuthRegistry.from_dict(json.load(stream))
    yield registry
    with filepath.open("w") as stream:
        json.dump(registry.to_dict(), stream)


@contextmanager
def build_spinner(
    *args,
    report: bool = True,
    reraise: bool = False,
    success_msg: str = None,
    error_msg: str = None,
    **kwargs,
) -> yaspin:
    spinner = yaspin(*args, **kwargs)
    try:
        spinner.start()
        yield spinner
        if report:
            if not success_msg:
                success_msg = LogSymbols.SUCCESS.value
            spinner.ok(colors.success | success_msg)
    except Exception as exc:
        if not error_msg:
            error_msg = f"{exc!s} {LogSymbols.ERROR.value}"
        spinner.fail(colors.error | error_msg)
        if reraise:
            raise exc
    finally:
        spinner.stop()


@contextmanager
def build_progressbar(*args, **kwargs) -> tqdm:
    yield tqdm(*args, **kwargs)


def use_auth_registry(filepath: str) -> Callable:
    def wrapper(func: Callable) -> Callable:
        @click.pass_context
        def func_wrapper(ctx: click.Context, *args, **kwargs) -> Any:
            with auth_registry(filepath) as registry:
                return ctx.invoke(func, registry, *args, **kwargs)

        return update_wrapper(func_wrapper, func)

    return wrapper


def use_spinner(*yaspin_args, **yaspin_kwargs) -> Callable:
    def wrapper(func: Callable) -> Callable:
        @click.pass_context
        def func_wrapper(ctx: click.Context, *args, **kwargs) -> Any:
            with build_spinner(*yaspin_args, **yaspin_kwargs) as spinner:
                return ctx.invoke(func, spinner, *args, **kwargs)

        return update_wrapper(func_wrapper, func)

    return wrapper


def format_auth_entry(extractor_name: str, auth_configuration: Tuple) -> str:
    return (
        f"{colors.bold & colors.info | extractor_name} "
        f"({colors.debug | auth_configuration[0]}, "
        f"{colors.debug | '*' * len(auth_configuration[-1])})"
    )


def get_help(context: click.Context, command: str=None) -> str:
    help_content = context.get_help()
    replacement_dict = {
        f"Usage: {__version__.__name__}": (
            f"{colors.bold | 'Usage:'} "
            f"{colors.bold & colors.cyan | __version__.__name__}"
        ),
        "Options:": (colors.bold | "Options:"),
        "Commands:": (colors.bold | "Commands:"),
    }
    if command == "auth":
        replacement_dict.update({
            " add ": (colors.bold & colors.green | " add "),
            " list ": (colors.bold & colors.cyan | " list "),
            " remove ": (colors.bold & colors.red | " remove ")
        })
    else:
        replacement_dict.update({
            " auth ": (colors.bold & colors.magenta | " auth "),
            " download ": (colors.bold & colors.green | " download ")
        })
    for (source, target) in replacement_dict.items():
        help_content = help_content.replace(source, target)
    return help_content
