# Copyright (c) 2017 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import os
import inspect

from . import (
    __version__, utils, extractors, downloaders,
    get_extractor, get_downloader,
)

import halo
import tqdm
import click
import colorama


CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help']
)


class TqdmDownload(tqdm.tqdm):

    def download_update(self, download_id: str, current: int, total: int):
        if self.total != total:
            self.total = total
        self.update(current - self.n)


@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.pass_context
def cli(ctx: click.Context):
    """ The command-line interface to the Qetch framework.
    """

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_usage())

    ctx.obj = ctx.params


@click.command(
    'list',
    short_help='Lists available extractors',
    context_settings={'ignore_unknown_options': True}
)
@click.pass_context
def cli_list(ctx: click.Context):
    for (extractor_name, extractor_class,) in inspect.getmembers(
        extractors,
            predicate=inspect.isclass
    ):
        print(extractor_name)


@click.command(
    'download',
    short_help='Downloads the extracted content from a url'
)
@click.argument('url', type=str)
@click.option('--max-fragments', '-mf', default=1, type=int)
@click.option('--max-connections', '-mc', default=8, type=int)
@click.pass_context
def cli_download(
    ctx: click.Context, url: str,
    max_fragments: int=1, max_connections: int=8,
):
    # TODO: add --all flag
    # TODO: add --output flag
    extractor = get_extractor(url, init=True)
    for content_list in extractor.extract(url):
        content = sorted(
            content_list,
            key=lambda x: x.quality, reverse=True
        )[0]
        downloader = get_downloader(content, init=True)
        if isinstance(downloader, downloaders._common.BaseDownloader):
            to_filepath = os.path.join(os.getcwd(), content.uid)
            if not os.path.isdir(os.path.dirname(to_filepath)):
                # TODO: report missing parent directory error
                raise NotADirectoryError()
            with TqdmDownload(
                desc=f'Downloading {content.uid}',
                total=content.get_size(),
                unit='B',
                unit_scale=True,
                bar_format=(
                    '{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}'
                )
            ) as pbar:
                downloader.download(
                    content, to_filepath,
                    progress_hook=pbar.download_update,
                    max_fragments=max_fragments,
                    max_connections=max_connections
                )


# add commands to base cli group
cli.add_command(cli_list)
cli.add_command(cli_download)

if __name__ == '__main__':
    cli()
