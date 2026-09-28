import logging
import os
from pathlib import Path
import shutil
from textwrap import dedent

from PIL import Image
import bpy
from luna_kit.gameobjectdata import GameObjectData
from luna_kit.loc import LOC
from luna_kit.pvr import PVR

from .config import Config, load_config
from .crop import crop_image
from .discord_bot import DiscordBot
from .pony_renderer import PonyRenderer
from .scene_setup import init_blend


class BatchRenderer:
    ponies: list[str]
    output_folder: Path
    game_folder: Path
    game_object_data: GameObjectData
    loc: LOC
    discord_post: bool

    config: Config

    bot: DiscordBot | None = None
    
    
    def __init__(
        self,
        ponies: list[str],
        game_folder: str | Path,
        output: str | Path | None = None,
        discord_post: bool = False,
        config_path: str | Path = 'config.yaml',
    ) -> None:
        self.ponies = list(ponies)
        self.game_folder = Path(game_folder)
        self.discord_post = discord_post
        self.config = load_config(config_path)

        if output:
            self.config.render.output = str(output)
        
        self.output_folder = Path(self.config.render.output)

        if self.output_folder.is_file():
            raise NotADirectoryError(f'Output folder must be directory {self.output_folder}')
        if not self.game_folder.is_dir():
            raise NotADirectoryError("Game folder doesn't exist or is a file")
        
        self.game_object_data = GameObjectData(self.game_folder/'gameobjectdata.xml')
        self.loc = LOC(self.game_folder/'english.loc')

        if self.config.discord.token:
            try:
                self.bot = DiscordBot(self.config.discord.token)
                self.bot.start()
            except:
                logging.exception('Cannot log into discord')
                self.bot = None
        else:
            self.bot = None
            

    def start(self):
        if not self.ponies:
            print('No ponies to render, quitting')
            return
        
        init_blend(self.config)

        failed: list[str] = []

        for pony_id in self.ponies:
            if not self.render_pony(pony_id):
                failed.append(pony_id)
        
        print('Done!')
        if failed:
            print(f"failed: {', '.join(failed)}")
        
    
    def render_pony(self, pony_id: str):
        pony_obj = self.game_object_data.get_object(pony_id)
        if not pony_obj:
            print(f'Cannot find pony: {pony_id}')
            return False

        name = self.loc.translate(pony_obj.get('Name', {}).get('Unlocal', pony_id))
        description = self.loc.translate(pony_obj.get('Description', {}).get('Unlocal', pony_id))
        output = self.output_folder/pony_id/f'{pony_id}_turnaround.webp'
        input = self.game_folder/f"{pony_obj["Model"]["MediumLOD"]}.rk"

        if not input.is_file():
            print(f'Cannot find model for {pony_id}')
            return False
        
        if output.exists():
            os.remove(output)

        pony_renderer = PonyRenderer(
            pony = pony_id,
            name = name,
            input = input,
            output = output,
            config = self.config,
            bot = self.bot,
        )

        pony_renderer.start()

        if output.is_file():
            logging.info('Render finished')

            full_2d_output = self.output_folder/pony_id/f'{pony_id}_2d.webp'
            portrait_output = self.output_folder/pony_id/f'{pony_id}_portrait.webp'

            self.crop_game_image(pony_obj.get('Icon', {}).get('Url', ''), full_2d_output)
            self.crop_game_image(pony_obj.get('Shop', {}).get('Icon', ''), portrait_output)

            images = [output]
            if full_2d_output.exists():
                images.append(full_2d_output)
            if portrait_output.exists():
                images.append(portrait_output)


            if self.discord_post and self.bot and self.config.discord.output_channels:
                logging.info('Sending to discord')
                
                self.bot.send_message(
                    dedent(f"""\
                    ## [{name}](<https://all-the-ponies.com/pony/{pony_id}/>)
                    > {description}
                    """),
                    self.config.discord.output_channels,
                    files = images,
                )
        else:
            logging.error(f'Failed to render {pony_id}')
            return False


        return True
    

    def crop_game_image(self, game_path: str, dest: str | Path):
        used_filename: str | Path | None = None
        dest = Path(dest)

        source_paths = set[str]()
        path = str(game_path)
        path = path.strip()
        path = path.replace('\\', '/')
        source_paths.add(path.removeprefix('/'))
        source_paths.add(os.path.basename(path))
        

        for filename in source_paths:
            name = os.path.splitext(filename)[0]

            if os.path.exists(self.game_folder/(name + '.png')):
                used_filename = self.game_folder/(name + '.png')
            elif os.path.exists(self.game_folder/(name + '.pvr')):
                used_filename = self.game_folder/(name + '.pvr')
            else:
                found_paths = list(self.game_folder.glob(name + '.*', case_sensitive = False))
                if len(found_paths):
                    for path in found_paths:
                        if path.suffix == '.png' or (path.suffix == '.pvr' and '.alpha' not in path.name):
                            used_filename = path
                            break

            if used_filename is not None:
                used_game_name = filename
                break
        
        rel_path = dest.relative_to(self.output_folder).as_posix()
        
        if used_filename is not None:
            if used_filename.suffix == '.pvr':
                image = PVR(used_filename).image
            else:
                image = Image.open(used_filename)
            
            if image:
                image = crop_image(image)
                image.save(dest)

        else:
            logging.error(f'Could not find {game_path}, {rel_path}')
