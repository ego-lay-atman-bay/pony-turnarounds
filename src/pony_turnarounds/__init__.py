from argparse import ArgumentParser
import logging

from .batch_renderer import BatchRenderer




def main() -> None:
    argparser = ArgumentParser()

    argparser.add_argument(
        '-g', '--game-folder',
        dest = 'game_folder',
        help = 'Game folder',
        required = True,
    )

    argparser.add_argument(
        '-o', '--output',
        dest = 'output',
        help = 'Output folder, can be set in config.yaml',
    )

    argparser.add_argument(
        'ponies',
        help = 'List of pony ids to render',
        nargs = '+',
    )

    argparser.add_argument(
        '--no-discord-post',
        action = 'store_true',
        dest = 'no_discord_post',
    )

    argparser.add_argument(
        '--no-wiki-upload',
        action = 'store_true',
        dest = 'no_wiki_upload',
    )

    args = argparser.parse_args()

    logging.basicConfig(level = logging.INFO)

    renderer = BatchRenderer(
        ponies = args.ponies,
        game_folder = args.game_folder,
        output = args.output,
        discord_post = not args.no_discord_post,
        wiki_upload = not args.no_wiki_upload,
        config_path = 'config.yaml',
    )
    renderer.start()

if __name__ == "__main__":
    main()
