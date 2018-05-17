# Copyright (c) 2018 Stephen Bunn <stephen@bunn.io>
# MIT License <https://opensource.org/licenses/MIT>

import os
import json
import contextlib
from typing import Any, Tuple
from pathlib import Path
from contextlib import contextmanager

import attr
import tqdm
import click
import yaspin.spinners
import click_completion
from plumbum import colors
from log_symbols import LogSymbols
from yaspin.yaspin import Yaspin

from . import exceptions, __version__, get_extractor, get_downloader
from .auth import AuthRegistry

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
CURRENT_SPINNER = None
CURRENT_PROGRESS_BAR = None

CONFIG_DIR = Path.home() / ".qetch"
AUTH_PATH = CONFIG_DIR / "auth.json"
AUTH_REGISTRY = None

click_completion.init()


def _build_spinner(text: str = None, spinner: str = "dots", right: bool = True):
    global CURRENT_SPINNER

    if not isinstance(CURRENT_SPINNER, Yaspin):
        CURRENT_SPINNER = yaspin.yaspin()

    CURRENT_SPINNER.spinner = getattr(yaspin.spinners.Spinners, spinner)
    CURRENT_SPINNER.text = text
    CURRENT_SPINNER.right = right

    return CURRENT_SPINNER


def _build_progress_bar(ctx: click.Context, **kwargs):
    global CURRENT_PROGRESS_BAR
    CURRENT_PROGRESS_BAR = tqdm.tqdm(total=100.0, **kwargs)
    return CURRENT_PROGRESS_BAR


def _validate_spinner(ctx: click.Context, param: str, value: Any):
    spinner_names = list(yaspin.spinners.Spinners._asdict().keys())
    if value not in spinner_names:
        raise click.BadParameter(f"spinner {value!r} does not exist, {spinner_names!r}")
    return value


def _init_config():
    if not CONFIG_DIR.is_dir():
        CONFIG_DIR.mkdir(parents=True)
    if not AUTH_PATH.is_file():
        with AUTH_PATH.open("w") as stream:
            json.dump({}, stream)


@contextmanager
def _auth_registry():
    global AUTH_REGISTRY

    if not isinstance(AUTH_REGISTRY, AuthRegistry):
        if not AUTH_PATH.is_file():
            _init_config()
        with AUTH_PATH.open("r") as stream:
            AUTH_REGISTRY = AuthRegistry.from_dict(json.load(stream))

    yield AUTH_REGISTRY


@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.option("-q", "--quiet", is_flag=True, default=False, help="Silent output")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Verbose output")
@click.version_option(prog_name=__version__.__name__, version=__version__.__version__)
@click.pass_context
def cli(ctx: click.Context, quiet: bool = False, verbose: bool = False):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_usage())
    ctx.obj = ctx.params


@click.command(
    "auth",
    short_help="Provide authentication for an extractor",
    context_settings={"ignore_unknown_options": True},
)
@click.argument("extractor", required=False)
@click.option(
    "-l",
    "--list",
    "list_entries",
    is_flag=True,
    help="List stored authentication entries",
)
@click.option(
    "-a",
    "--add",
    type=(str, str),
    default=(None, None),
    required=False,
    help="Add an authentication entry",
)
@click.pass_context
def cli_auth(
    ctx: click.Context,
    extractor: str = None,
    list_entries: bool = False,
    add: Tuple[str, str] = None,
):
    with _build_spinner("managing authentication registry ...") as spinner:
        with _auth_registry() as registry:
            if list_entries:
                spinner.text = "listing authentication registry ..."
                for (key, value) in registry.items():
                    spinner.write(
                        (
                            f"{colors.bold | key} "
                            f"({colors.cyan & colors.bold | ', '.join(value)})"
                        )
                    )
            else:
                if not extractor:
                    spinner.fail(colors.red & colors.bold | f"extractor required")
                    ctx.exit(1)
                if add:
                    (key, value) = add
                    registry[extractor] = add
                    spinner.write(
                        (
                            f"added {colors.cyan & colors.bold | key}, "
                            f"{colors.cyan & colors.bold | value} for "
                            f"{colors.bold | extractor}"
                        )
                    )
            spinner.ok(colors.green & colors.bold | LogSymbols.SUCCESS.value)
        with AUTH_PATH.open("w") as stream:
            json.dump(registry.to_dict(), stream)


@click.command(
    "download",
    short_help="Download content from a URL",
    context_settings={"ignore_unknown_options": True},
)
@click.argument("url")
@click.option(
    "-d", "--directory", type=str, default=os.getcwd(), help="Output directory"
)
@click.option(
    "--spinner",
    type=str,
    default="dots",
    help="Spinner type",
    show_default=True,
    callback=_validate_spinner,
)
@click.pass_context
def cli_download(
    ctx: click.Context, url: str, directory: str = None, spinner: str = None
):
    directory = Path(directory)
    with _auth_registry():
        with _build_spinner("getting extractor ...") as spinner:
            try:
                extractor = get_extractor(url)
                spinner.ok(colors.green & colors.bold | extractor.__name__)
            except exceptions.ExtractionError:
                spinner.fail(
                    colors.red
                    & colors.bold
                    | f"no extractor for {colors.cyan & colors.bold | url}"
                )
                ctx.exit(1)

            extractor = extractor()

            spinner.text = "extracting ..."
            spinner.start()
            try:
                content_list = list(extractor.extract(url))
                spinner.ok(colors.green & colors.bold | f"{len(content_list)} content")
            except exceptions.AuthenticationError:
                spinner.fail(
                    colors.red
                    & colors.bold
                    | f"missing auth for {colors.white & colors.bold | extractor.name}"
                )
                ctx.exit(1)

            spinner.text = "getting downloader ..."
            spinner.start()

            downloader = None
            for content_variants in content_list:
                content = content_variants[0]  # NOTE: choose best quality by default
                if not downloader:
                    downloader = get_downloader(content)
                    spinner.ok(colors.green & colors.bold | downloader.__name__)
                    downloader = downloader()

                downloading_text = (
                    f"downloading {colors.cyan & colors.bold | content.uid} ..."
                )
                with _build_progress_bar(
                    ctx,
                    desc=downloading_text,
                    bar_format=("{desc} {percentage:3.0f}% ┃{bar}┃ [ETA {remaining}]"),
                    leave=False,
                ) as progress_bar:
                    if not directory.is_dir():
                        spinner.write(
                            colors.dim | f"creating directory {directory.as_posix()!r}"
                        )
                        directory.mkdir(parents=True)
                    downloader.download(
                        content,
                        directory.joinpath(f"{content.uid}.{content.extension}"),
                        progress_hook=lambda _, current, total: progress_bar.update(
                            ((current / total) * 100.0) - progress_bar.n
                        ),
                    )
                spinner.text = downloading_text
                spinner.start()
                spinner.ok(colors.green & colors.bold | LogSymbols.SUCCESS.value)


cli.add_command(cli_auth)
cli.add_command(cli_download)


if __name__ in "__main__":
    cli()
