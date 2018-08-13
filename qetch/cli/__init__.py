# Copyright (c) 2018 Stephen Bunn <stephen@bunn.io>
# MIT License <https://opensource.org/licenses/MIT>

import os
from typing import Tuple
from pathlib import Path

from .. import __version__, exceptions, get_extractor, get_downloader
from ..auth import AuthRegistry
from . import utils

import click
import click_completion
from yaspin.yaspin import Yaspin
from plumbum import colors


CONFIG_DIR = Path.home() / f".{__version__.__name__}"
AUTH_PATH = CONFIG_DIR / "auth.json"

click_completion.init()


@click.group(invoke_without_command=True)
@click.option(
    "-h", "--help", "help_flag", is_flag=True, default=False, help="Show help."
)
@click.option("-q", "--quiet", is_flag=True, default=False, help="Silent output.")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Verbose output.")
@click.option(
    "--completion", is_flag=True, default=False, help="Enable shell completion."
)
@click.version_option(prog_name=__version__.__name__, version=__version__.__version__)
@click.pass_context
def cli(
    ctx: click.Context,
    help_flag: bool = False,
    quiet: bool = False,
    verbose: bool = False,
    completion: bool = False
):
    if ctx.invoked_subcommand is None or help_flag:
        click.echo(utils.get_help(ctx))
    if completion:
        print(click_completion.get_code(shell='fish', prog_name=__version__.__name__))
    ctx.obj = ctx.params


@click.group("auth", invoke_without_command=True)
@click.option(
    "-h", "--help", "help_flag", is_flag=True, default=False, help="Show help."
)
@click.pass_context
def cli_auth(ctx: click.Context, help_flag: bool = False):
    """Manage authentication entries.
    """
    if ctx.invoked_subcommand is None or help_flag:
        click.echo(utils.get_help(ctx, "auth"))


@click.command("list", short_help="List all authentication entries")
@utils.use_auth_registry(AUTH_PATH)
@utils.use_spinner(text="listing authentication entries...", right=True, report=False)
def cli_auth_list(spinner: Yaspin, registry: AuthRegistry):
    if len(registry.values()) <= 0:
        raise ValueError(f"no authentication entries")
    for (extractor, configuration) in registry.items():
        spinner.write(utils.format_auth_entry(extractor, configuration))


@click.command("add", short_help="Add a new authentication entry")
@click.argument("extractor", type=str)
@click.argument("key", type=str)
@click.argument("secret", type=str)
@utils.use_auth_registry(AUTH_PATH)
@utils.use_spinner(text="adding entry...", right=True, report=False)
def cli_auth_add(
    spinner: Yaspin, registry: AuthRegistry, extractor: str, key: str, secret: str
):
    if extractor in registry:
        raise ValueError(f"entry for {extractor} already exists")
    spinner.text = f"adding {colors.info | extractor} entry..."
    registry[extractor] = (key, secret)
    spinner.ok(utils.format_auth_entry(extractor, (key, secret)))


@click.command("remove", short_help="Remove an existing authentication entry")
@click.argument("extractor")
@utils.use_auth_registry(AUTH_PATH)
@utils.use_spinner(text="removing entry...", right=True)
def cli_auth_remove(spinner: Yaspin, registry: AuthRegistry, extractor: str):
    if extractor not in registry:
        raise ValueError(f"no entry for {extractor} exists")
    spinner.text = f"removing {colors.info | extractor} entry..."
    del registry[extractor]


@click.command("download", short_help="Download content from a URL.")
@click.argument("url")
@click.option(
    "-d",
    "--directory",
    "out_dir",
    type=str,
    default=os.getcwd(),
    help="Output directory.",
)
@utils.use_auth_registry(AUTH_PATH)
@utils.use_spinner(text="downloading...", right=True)
@click.pass_context
def cli_download(
    ctx: click.Context, spinner: Yaspin, registry: AuthRegistry, url: str, out_dir: str
):
    out_dir = Path(out_dir)
    spinner.text = f"getting extractor..."
    try:
        extractor = get_extractor(url)
        spinner.ok(colors.success | extractor.__name__)
    except exceptions.ExtractionError:
        raise ValueError(f"no extractor for {colors.debug | url}")

    extractor = extractor()
    spinner.text = "extracting..."
    spinner.start()
    try:
        content_list = list(extractor.extract(url))
        spinner.ok(colors.success | f"{len(content_list)} content")
    except exceptions.AuthenticationError:
        raise ValueError(f"missing auth for {colors.debug | extractor.name}")

    spinner.text = "getting downloader..."
    spinner.start()

    downloader = None
    for content_variants in content_list:
        content = content_variants[0]
        if not downloader:
            downloader = get_downloader(content)
            spinner.ok(colors.success | downloader.__name__)
            downloader = downloader()

        write_to = out_dir / f"{content.uid}.{content.extension}"
        spinner.text = f"downloading {colors.info | content.uid}..."
        with utils.build_progressbar(
            desc=spinner.text,
            total=100.0,
            leave=False,
            bar_format=("{desc} {percentage:3.0f}% ┃{bar}┃ [ETA {remaining}]"),
        ) as progess_bar:
            downloader.download(
                content,
                write_to,
                progress_hook=lambda _, current, total: progess_bar.update(
                    ((current / total) * 100.0) - progess_bar.n
                ),
            )

        spinner.text = f"downloaded to {colors.debug | write_to.as_posix()}..."
        spinner.start()


utils.load_colors()
cli_auth.add_command(cli_auth_list)
cli_auth.add_command(cli_auth_add)
cli_auth.add_command(cli_auth_remove)
cli.add_command(cli_auth)
cli.add_command(cli_download)


if __name__ in "__main__":
    cli()
