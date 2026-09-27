import asyncio
import logging
from pathlib import Path
import threading
from typing import Literal, Optional, TypeAlias

import discord


RenderEngine: TypeAlias = Literal['BLENDER_EEVEE', 'CYCLES']

USER = 673981139995852830


class EngineChoiceView(discord.ui.View):
    def __init__(
        self, *,
        result: asyncio.Future[RenderEngine],
        user: int,
    ):
        super().__init__(timeout = None)
        self.result = result
        self.user_id = user
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "You can't approve renders",
                ephemeral=True,
            )
            return False
        return True
    
    async def _choose(self, interaction: discord.Interaction, engine: RenderEngine):
        self.disable()
        
        await interaction.response.edit_message(
            content = f"Rendering the full animation with **{engine}**.",
            view = self,
        )
        if not self.result.done():
            self.result.set_result(engine)
        
        self.stop()
    
    @discord.ui.button(label = "CYCLES", style = discord.ButtonStyle.primary)
    async def cycles_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._choose(interaction, 'CYCLES')

    @discord.ui.button(label = "EEVEE", style = discord.ButtonStyle.secondary)
    async def eevee_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._choose(interaction, 'BLENDER_EEVEE')
    
    def disable(self):
        self.cycles_button.disabled = True
        self.eevee_button.disabled = True


class DiscordBot:
    def __init__(self, token: str) -> None:
        self.token = token
        
        intents = discord.Intents.default()
        self.bot = discord.Client(intents = intents)
        self.bot.event(self.on_ready)
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self.loop: asyncio.AbstractEventLoop | None = None
        self._start_task: asyncio.Task | None = None

    def start(self):
        self._thread = threading.Thread(
            target = self._start_bot,
            name = 'discord-bot',
            daemon = True,
        )

        self._thread.start()

        ready = self._ready.wait(timeout = 10)

        if not ready:
            raise TimeoutError('Discord bot did not get ready in time')
        elif ready and self._start_task and not self.bot.is_ready() and (exception := self._start_task.exception()):
            raise exception

    def _start_bot(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._start_task = self.loop.create_task(self.bot.start(self.token))
        self._start_task.add_done_callback(self._on_start_done)


        try:
            self.loop.run_forever()
        finally:
            self.loop.close()
    
    async def on_ready(self):
        logging.info(f'Logged in as user {self.bot.user}')
        self._ready.set()
    
    def _on_start_done(self, task: asyncio.Task):
        if task.cancelled():
            return
        if (exc := task.exception()) is not None:
            logging.error('Discord bot failed to start', exc_info=exc)
            self._ready.set()

    def stop(self):
        if self.loop is not None and not self.bot.is_closed():
            logging.info('Closing bot')
            asyncio.run_coroutine_threadsafe(self.bot.close(), self.loop).result()

            self.loop.call_soon_threadsafe(self.loop.stop)

        if self._thread is not None:
            logging.info('Joining thread')
            self._thread.join(timeout = 10)
    

    def _run_coroutine(self, routine, timeout: float | None = None):
        if self.loop is None:
            raise RuntimeError('Bot is not running')
        
        return asyncio.run_coroutine_threadsafe(routine, self.loop).result(timeout = timeout)
    
    def send_message(
        self,
        message: str,
        channels: int | list[int],
        files: list[str | Path] | None = None,
    ):
        channel_ids = [channels] if isinstance(channels, int) else channels
        return self._run_coroutine(
            self._send_message(message, channel_ids, files),
        )

    async def _send_message(
        self,
        message: str,
        channel_ids: list[int],
        file_paths: list[str | Path] | None,
    ):
        return await asyncio.gather(
            *(
                self._send_to_channel(channel_id, message, file_paths)
                for channel_id in channel_ids
            )
        )

    async def _send_to_channel(
        self,
        channel_id: int,
        message: str,
        file_paths: list[str | Path] | None,
    ):
        channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
        files = [discord.File(path) for path in file_paths] if file_paths else []
        return await channel.send(message, files=files)
    
    def ask_render_engine(
        self,
        preview: str | Path,
        channel: int,
        user: int,
        timeout: float = 30,
    ):
        return self._run_coroutine(
            self._ask_render_engine(preview, channel, user, timeout),
            timeout = timeout + 15,
        )

    async def _ask_render_engine(
        self,
        preview: str | Path,
        channel_id: int,
        user: int,
        timeout: float = 30,
    ) -> RenderEngine | None:
        if not self.loop:
            raise ValueError('Bot is not running')

        channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)

        result: asyncio.Future[RenderEngine] = self.loop.create_future()
        view = EngineChoiceView(
            result = result,
            user = user,
        )

        message = await channel.send(
            content = "Which engine to use?",
            file = discord.File(preview),
            view = view,
        )

        if not message:
            logging.error('Could not send render review message, defaulting to CYCLES')
            return 'CYCLES'

        engine: RenderEngine | None = None

        try:
            engine = await asyncio.wait_for(asyncio.shield(result), timeout = timeout)
        except asyncio.TimeoutError:
            logging.info('Messaged timed out')
            engine = 'CYCLES'
            view.disable()
            view.stop()
            try:
                await message.edit(
                    content = f"No response in time, choosing {engine}",
                    view = view,
                )

            except discord.HTTPException:
                logging.warning("Could not edit timed-out engine-choice message")
        
        return engine

        


        
