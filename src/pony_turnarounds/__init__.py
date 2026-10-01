from argparse import ArgumentParser
import logging
from pathlib import Path

from luna_kit.gameobjectdata import GameObjectData

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
        '-p', '--ponies',
        dest = 'ponies',
        help = 'List of pony ids to render',
        nargs = '+',
        default = [],
    )

    argparser.add_argument(
        '-r', '--range',
        dest = 'range',
        nargs = 2,
        help = 'Specify a range of ponies to render',
        metavar = ('FROM', 'TO'),
    )

    argparser.add_argument(
        '--no-discord-post',
        action = 'store_true',
        dest = 'no_discord_post',
        help = 'Do not post results to discord',
    )

    argparser.add_argument(
        '--no-wiki-upload',
        action = 'store_true',
        dest = 'no_wiki_upload',
        help = 'Do not post results to wiki',
    )

    argparser.add_argument(
        '-l', '--log-level',
        dest = 'log_level',
        choices = list[str](logging.getLevelNamesMapping().keys()),
        default = 'INFO',
        help = 'Change the log level',
    )

    args = argparser.parse_args()

    logging.basicConfig(
        level = logging.getLevelNamesMapping().get(args.log_level.upper(), logging.INFO),
    )

    try:


        ponies: list[str] = args.ponies
        game_folder = Path(args.game_folder)

        gameobjectdata = GameObjectData(game_folder/'gameobjectdata.xml')

        if args.range:
            ponies.extend(get_pony_range(args.range[0], args.range[1], gameobjectdata))
        
        ponies = list(set(ponies))


        renderer = BatchRenderer(
            ponies = ponies,
            game_folder = game_folder,
            output = args.output,
            discord_post = not args.no_discord_post,
            wiki_upload = not args.no_wiki_upload,
            config_path = 'config.yaml',
        )
        renderer.start()
    except Exception as e:
        if logging.getLogger().level < logging.INFO:
            raise
        else:
            logging.error(f"{e}")


def get_pony_range(start: str, end: str, gameobjectdata: GameObjectData):
    all_ponies: list[str] = list(gameobjectdata['Pony'].keys())
    if start not in all_ponies or end not in all_ponies:
        raise KeyError("Start or end pony does not exist")
    
    start_index = all_ponies.index(start)
    end_index = all_ponies.index(end)

    ponies = all_ponies[min(start_index, end_index) : max(start_index, end_index) + 1]

    if start_index > end_index:
        ponies.reverse()
    
    return ponies

if __name__ == "__main__":
    main()
