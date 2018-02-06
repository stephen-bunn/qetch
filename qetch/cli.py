# Copyright (c) 2017 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import os
import inspect
import contextlib
from typing import (Tuple, List,)

from . import (
    __version__, utils, exceptions, extractors, downloaders,
    get_extractor, get_downloader, IGNORED_EXTRACTORS, IGNORED_DOWNLOADERS,
)
from .auth import (AuthRegistry,)

import tqdm
import click
import colorama
from yaspin import (yaspin,)
from yaspin.spinners import (Spinners,)

(CF, CB, CS,) = (colorama.Fore, colorama.Back, colorama.Style,)
CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help']
)


class TqdmDownload(tqdm.tqdm):

    def download_update(self, download_id: str, current: int, total: int):
        if self.total != total:
            self.total = total
        self.update(current - self.n)


def validate_spinner(ctx: click.Context, param: str, value: str) -> str:
    spinner_names = list(Spinners._asdict().keys())
    if value not in spinner_names:
        raise click.BadParameter((
            f"spinner {value!r} does not exist, {spinner_names!r}"
        ))
    return value


@contextlib.contextmanager
def build_spinner(ctx: click.Context, text: str, silent: bool=True, **kwargs):
    if ctx.obj.get('quiet', False):
        return contextlib.ExitStack()

    kwargs.update({
        'spinner': getattr(
            Spinners,
            ctx.params.get('spinner', 'dots')
        ),
        'right': ctx.params.get('right', False)
    })
    spinner = yaspin(text=text, **kwargs)
    try:
        spinner.start()
        yield spinner
        spinner.ok(f'{CS.BRIGHT}{CF.GREEN}✔{CS.RESET_ALL} ')
    except Exception as exc:
        spinner.text += f' {CS.DIM}[{exc}]{CS.RESET_ALL}'
        spinner.fail(f'{CS.BRIGHT}{CF.RED}✗{CS.RESET_ALL} ')
        if not silent:
            raise exc
    finally:
        spinner.stop()


@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.option(
    '--quiet', '-q',
    is_flag=True, type=bool, default=False, help='Disable spinners.'
)
@click.option(
    '--spinner',
    type=str, default='dots', help='Customize spinner type.',
    show_default=True, callback=validate_spinner
)
@click.version_option(
    prog_name=__version__.__name__,
    version=__version__.__version__
)
@click.pass_context
def cli(
    ctx: click.Context,
    quiet: bool=False, spinner: str='dots'
):
    """ The command-line interface to the Qetch framework.
    """

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_usage())

    ctx.obj = ctx.params


@click.command(
    'list',
    short_help='Lists extractors.'
)
@click.option(
    'handle_url', '--handles',
    type=str, help='List extractors that can handle a url.'
)
@click.pass_context
def cli_list(ctx: click.Context, handle_url: str=None):
    # TODO: clean up extractor listing between different options
    # handle listing extractors that can handle a url
    if isinstance(handle_url, str) and len(handle_url) > 0:
        for (extractor_name, extractor_class,) in \
                inspect.getmembers(extractors, predicate=inspect.isclass):
            if extractor_class not in IGNORED_EXTRACTORS:
                with build_spinner(
                    ctx, f'{CS.BRIGHT}{extractor_class.name}{CS.RESET_ALL}'
                ):
                    if not extractor_class.can_handle(handle_url):
                        raise Exception((f'cannot handle'))
    else:
        for (extractor_name, extractor_class,) in \
                inspect.getmembers(extractors, predicate=inspect.isclass):
            if extractor_class not in IGNORED_EXTRACTORS:
                print((
                    f'{CS.BRIGHT}{extractor_name}{CS.RESET_ALL} '
                    f'{CS.DIM}({extractor_class.name}){CS.RESET_ALL}'
                ))


@click.command(
    'download',
    short_help='Downloads the extracted content from a url.'
)
@click.argument('url', type=str)
@click.option(
    '--max-fragments', '-mf',
    type=int, default=1, show_default=True,
    help='The number of fragments to download in parallel.'
)
@click.option(
    '--max-connections', '-mc',
    type=int, default=1, show_default=True,
    help='The number of connections to allow per/fragment.'
)
@click.option(
    '--auth', '-a',
    type=click.Tuple([str, str, str]), default=[], multiple=True,
    help='Auth config tuple (extractor.name, key/username, secret/password).'
)
@click.option(
    'extract_all', '--extract-all', '-ea',
    is_flag=True, type=bool, default=False,
    help='Extract all qualities of content (otherwise extracts best quality).'
)
@click.option(
    'output_format', '--output', '-o',
    type=str, default='{content.uid}.{content.extension}',
    show_default=True,
    help='Download content out to a specific filepath format.'
)
@click.pass_context
def cli_download(
    ctx: click.Context, url: str,
    max_fragments: int=None, max_connections: int=None,
    auth: List[Tuple[str, str, str]]=None,
    extract_all: bool=None, output_format: str=None
):
    # TODO: add option to select range of content to download
    # initialize authentication registry with provided configurations
    AuthRegistry(**{
        entry[0]: (entry[1], entry[-1],)
        for entry in auth
    })

    url_repr = f'{CS.BRIGHT}{CF.CYAN}{url}{CS.RESET_ALL}'
    # determine appropriate extractor for a given url
    with build_spinner(
        ctx, f'determining extractor for {url_repr}'
    ) as spinner:
        extractor = get_extractor(url, init=True)
        spinner.text = (
            f'extractor {CS.BRIGHT}{extractor.name}{CS.RESET_ALL} '
            f'{CS.DIM}({", ".join(extractor.handles.keys())}){CS.RESET_ALL}'
        )

    content_list = []
    # extract available content from the url
    with build_spinner(
        ctx, f'extracting content from {url_repr}'
    ) as spinner:
        try:
            content_list = list(extractor.extract(url))
            spinner.text = (
                f'extracted {CS.BRIGHT}{len(content_list)}{CS.RESET_ALL} '
                f'content'
            )
        except exceptions.AuthenticationError as exc:
            raise Exception((
                f'no authentication provided, '
                f'requires {extractor.authentication.value}'
            ))
        except exceptions.ExtractionError as exc:
            raise Exception(('invalid authentication'))

    if len(content_list) > 0:
        # handle downloading content
        for extracted_content in content_list:
            if not extract_all:
                extracted_content = [sorted(
                    extracted_content,
                    key=lambda content: content.quality, reverse=True
                )[0]]
            for content in extracted_content:
                downloader = get_downloader(content, init=True)
                to_filepath = utils.normalize_path(
                    output_format.format(content=content)
                )
                with TqdmDownload(
                    desc=(
                        f'{CS.BRIGHT}downloading {CF.GREEN}{content.uid}'
                        f'{CS.RESET_ALL}'
                    ),
                    total=content.get_size(),
                    unit='B', unit_scale=True,
                    bar_format=(
                        '{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}'
                    ),
                    leave=False
                ) as progress_bar:
                    downloader.download(
                        content, to_filepath,
                        progress_hook=progress_bar.download_update,
                        max_fragments=max_fragments,
                        max_connections=max_connections
                    )

                # display content was downloaded through empty spinner
                with build_spinner(
                    ctx, (
                        f'downloaded {CS.BRIGHT}{CF.GREEN}{content.uid}'
                        f'{CS.RESET_ALL} {CS.DIM}({to_filepath}){CS.RESET_ALL}'
                    )
                ) as spinner:
                    pass


# add commands to base cli group
cli.add_command(cli_list)
cli.add_command(cli_download)

if __name__ == '__main__':
    cli()
