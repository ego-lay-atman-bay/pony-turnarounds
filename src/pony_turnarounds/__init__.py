from argparse import ArgumentParser

from .batch_renderer import BatchRenderer




def main() -> None:
    argparser = ArgumentParser()

    argparser.add_argument(
        'game_folder',
        help = 'Game folder',
    )

    argparser.add_argument(
        'output_folder',
        help = 'Output folder',
    )

    argparser.add_argument(
        'ponies',
        help = 'List of pony ids to render',
        nargs = '+',
    )

    argparser.add_argument(
        '-f', '--frames',
        dest = 'frames',
        default = 100,
        type = int,
        help = 'Number of frames for the animation',
    )

    args = argparser.parse_args()

    renderer = BatchRenderer(
        ponies = args.ponies,
        game_folder = args.game_folder,
        output = args.output_folder,
        discord_post = False,
        n_frames = args.frames,
    )
    renderer.start()

if __name__ == "__main__":
    main()
