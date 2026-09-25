from pathlib import Path

import bpy
from luna_kit.gameobjectdata import GameObjectData
from luna_kit.loc import LOC

from .pony_renderer import PonyRenderer
from .scene_setup import init_blend
from .discord_bot import DiscordBot


class BatchRenderer:
    ponies: list[str]
    output_folder: Path
    game_folder: Path
    game_object_data: GameObjectData
    loc: LOC
    discord_post: bool
    
    
    def __init__(
        self,
        ponies: list[str],
        game_folder: str,
        output: str,
        discord_post: bool = False,
    ) -> None:
        self.ponies = list(ponies)
        self.game_folder = Path(game_folder)
        self.output_folder = Path(output)
        self.discord_post = discord_post

        if self.output_folder.is_file():
            raise NotADirectoryError(f'Output folder must be directory {self.output_folder}')
        if not self.game_folder.is_dir():
            raise NotADirectoryError("Game folder doesn't exist or is a file")
        
        self.game_object_data = GameObjectData(self.game_folder/'gameobjectdata.xml')
        self.loc = LOC(self.game_folder/'english.loc')

        self.bot = DiscordBot()

    def start(self):
        if not self.ponies:
            print('No ponies to render, quitting')
            return
        
        init_blend()

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
        output = self.output_folder/f'{pony_id}.webp'
        input = self.game_folder/f"{pony_obj["Model"]["MediumLOD"]}.rk"

        if not input.is_file():
            print(f'Cannot find model for {pony_id}')
            return False

        pony_renderer = PonyRenderer(
            pony = pony_id,
            name = name,
            input = input,
            output = output,
            bot = self.bot,
        )

        pony_renderer.start()

        return True
            
