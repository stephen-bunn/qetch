# Copyright (c) 2018 Stephen Bunn <stephen@bunn.io>
# MIT License <https://opensource.org/licenses/MIT>

import os
import contextlib
from typing import Any, Tuple
from pathlib import Path

import tqdm
import click
import yaspin
import yaspin.spinners
import click_completion
from plumbum import colors

from . import exceptions, __version__, get_extractor, get_downloader
from .auth import AuthRegistry

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
CURRENT_SPINNER = None
CURRENT_PROGRESS_BAR = None
click_completion.init()


def _build_spinner(ctx: click.Context, text: str, right: bool = True):
    global CURRENT_SPINNER
    if ctx.obj.get("quiet", False):
        # NOTE: ExitStack is essentially a null context manager
        return contextlib.ExitStack()
    CURRENT_SPINNER = yaspin.yaspin(
        spinner=getattr(yaspin.spinners.Spinners, ctx.params.get("spinner", "dots")),
        text=text,
        right=right,
    )
    return CURRENT_SPINNER


def _build_progress_bar(ctx: click.Context, **kwargs):
    global CURRENT_PROGRESS_BAR
    CURRENT_PROGRESS_BAR = tqdm.tqdm(total=100.0, **kwargs)
    return CURRENT_PROGRESS_BAR


def _parse_auth(ctx: click.Context, value: Any) -> Tuple[str, str]:
    return tuple([_.strip() for _ in value.split(",")])


def _validate_spinner(ctx: click.Context, param: str, value: Any):
    spinner_names = list(yaspin.spinners.Spinners._asdict().keys())
    if value not in spinner_names:
        raise click.BadParameter(f"spinner {value!r} does not exist, {spinner_names!r}")
    return value


def _validate_auth(ctx: click.Context, param: str, value: Any):
    if value:
        parsed = _parse_auth(ctx, value)
        if len(parsed) != 2:
            raise click.BadParameter(
                f"auth {value!r} cannot be parsed correctly, {parsed!r}"
            )
        return value


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
    "download",
    short_help="Download content from a URL",
    context_settings={"ignore_unknown_options": True},
)
@click.argument("url")
@click.option(
    "-d",
    "--directory",
    type=str,
    default=os.getcwd(),
    help="Output directory",
)
@click.option(
    "-a",
    "--auth",
    type=str,
    default=None,
    help="Authentication tuple",
    callback=_validate_auth,
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
    ctx: click.Context,
    url: str,
    directory: str = None,
    auth: str = None,
    spinner: str = None,
):
    registry = None
    if isinstance(auth, str) and len(auth) > 0:
        registry = AuthRegistry()

    directory = Path(directory)
    with _build_spinner(ctx, "getting extractor ...") as spinner:
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

        if isinstance(registry, AuthRegistry):
            registry[extractor] = _parse_auth(ctx, auth)
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

            with _build_progress_bar(
                ctx,
                desc=f"downloading {colors.cyan & colors.bold | content.uid}",
                bar_format="{desc} ... {percentage:3.0f}% |{bar}| [ETA {remaining}]",
            ) as progress_bar:
                downloader.download(
                    content,
                    directory.joinpath(f"{content.uid}.{content.extension}"),
                    progress_hook=lambda _, current, total: progress_bar.update(
                        ((current / total) * 100.0) - progress_bar.n
                    ),
                )


cli.add_command(cli_download)


if __name__ in "__main__":
    cli()
