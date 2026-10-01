import logging
import os
from pathlib import Path
import time
from typing import Literal

from PIL import Image
import bpy
from luna_kit.gameobjectdata import GameObjectData
from luna_kit.model.rk import RKModel

from .config import Config
from .discord_bot import DiscordBot
from .scene_setup import cleanup_scene
from .typings import RenderEngine
from .utils import check_addon, open_file


class PonyRenderer:
    pony: str
    name: str
    input: Path
    output: Path
    config: Config
    bot: DiscordBot | None = None

    rk: RKModel

    frames: list[Image.Image]
    temp_file_paths: list[str]

    
    def __init__(
        self,
        pony: str,
        name: str,
        input: Path,
        output: Path,
        config: Config,
        bot: DiscordBot | None = None,
    ) -> None:
        self.pony = pony
        self.name = name
        self.input = input
        self.output = output
        self.bot = bot
        self.config = config

        self.rk = RKModel(input)
        self.frames = []
        self.temp_file_paths = []

    
    def start(self):
        self.load()

        if self.has_translucency():
            self._cycles_review()
        else:
            scene: bpy.types.Scene = bpy.context.scene
            scene.render.engine = 'BLENDER_EEVEE'
            self.render_turnaround()

    
    def load(self):
        cleanup_scene()
        scene: bpy.types.Scene = bpy.context.scene
        scene.frame_end = self.config.render.frames


        bpy.ops.import_scene.rk_data( # type: ignore
            filepath = str(self.input),
            shader_method = 'unlit',
            eyes_state = 'OPEN',
        )
        bpy.ops.rk.add_turnaround_driver() # type: ignore
        bpy.ops.rk.fit_camera(margin = self.config.render.camera_margin) # type: ignore
        if bpy.ops.rk.set_uv_scroll_frames.poll(): # type: ignore
            bpy.ops.rk.set_uv_scroll_frames(cycles = self.config.render.scrolling_texture_cycles) # type: ignore

    
    def render_turnaround(self):
        scene: bpy.types.Scene = bpy.context.scene
        scene.render.filepath = bpy.app.tempdir

        bpy.app.handlers.render_post.append(self._on_frame_render) # type: ignore
        bpy.app.handlers.render_cancel.append(self._render_canceled)

        scene.render.image_settings.media_type = 'IMAGE'
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGBA'
        scene.render.use_render_cache = False
        scene.render.use_overwrite = True

        print(f'Rendering {self.pony}')

        bpy.ops.render.render(animation = True)
        self._remove_handlers()
        print(f'Finished rendering {self.pony}')
        self.write_output()
    
    def write_output(self):
        if not len(self.frames):
            print(f'Failed to write output for {self.pony}')
            return
        
        self.output.parent.mkdir(parents = True, exist_ok = True)

        print(f'Saving to {self.output}')
        
        self.frames[0].save(
            self.output,
            save_all = True,
            append_images = self.frames[1:],
            duration = int((1 / (bpy.context.scene.render.fps / bpy.context.scene.render.fps_base)) * 1000),
            loop = 0,
            disposal = 2,
            lossless = False,
            quality = 80,
            method = 2,
        )


    def _on_frame_render(self, scene: bpy.types.Scene, _):
        file_path = scene.render.frame_path(frame=scene.frame_current)
        self.temp_file_paths.append(file_path)
        with Image.open(file_path) as img:
            self.frames.append(img.convert("RGBA"))

    
    def _render_canceled(self, scene: bpy.types.Scene):
        self._remove_handlers()
    
    def _remove_handlers(self):
        if self._on_frame_render in bpy.app.handlers.render_post:
            bpy.app.handlers.render_post.remove(self._on_frame_render) # type: ignore
        
        if self._render_canceled in bpy.app.handlers.render_cancel:
            bpy.app.handlers.render_cancel.remove(self._render_canceled)
        
    
    def _cycles_review(self):
        logging.info('Asking for render engine')

        engine = self.config.render.translucent_engine

        if self.config.render.ask_review:
            scene: bpy.types.Scene = bpy.context.scene
            scene.render.engine = 'CYCLES'  # type: ignore[reportAttributeAccessIssue]
            review_path = Path(bpy.app.tempdir)/f'{self.pony}_review.png'
            scene.render.filepath = str(review_path)
            scene.render.image_settings.media_type = 'IMAGE'
            scene.render.image_settings.file_format = 'PNG'
            scene.render.image_settings.color_mode = 'RGBA'
            scene.render.use_render_cache = False
            scene.render.use_overwrite = True

            scene.frame_set(self.config.render.review_frame)

            bpy.ops.render.render(write_still = True)

            engine: RenderEngine = 'CYCLES'

            if self.bot and self.config.discord.review_channel and self.config.discord.approver_user:
                reviewed_engine = self.bot.ask_render_engine(
                    review_path,
                    self.config.discord.review_channel,
                    self.config.discord.approver_user,
                    timeout = self.config.discord.preview_timeout or 30,
                )

                engine = reviewed_engine if reviewed_engine else 'CYCLES'
            else:
                open_file(review_path)
                engine = 'CYCLES' if input("Use CYCLES (Y/n)? ").lower() not in ['n', 'no', 'f', 'false'] else 'BLENDER_EEVEE'
        
        scene.render.engine = engine # type: ignore[reportAttributeAccessIssue]
        self.render_turnaround()

    def has_translucency(self):
        for material in self.rk.materials:
            image = material.properties.image()
            if not image or not image.has_transparency_data:
                logging.debug('Has no alpha')
                continue
            hist = image.getchannel("A").histogram()
            if any(count > 0 for count in hist[3:254]):
                return True
        
        return False

