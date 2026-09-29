from pathlib import Path

from pydantic import BaseModel, Field
import yaml

class ResolutionConfig(BaseModel):
    width: int = 720
    height: int = 540

class RenderConfig(BaseModel):
    output: str
    fps: float = 10
    frames: int = 100
    scrolling_texture_cycles: float = 2
    camera_margin: float = 0.5
    review_frame: int = 25
    resolution: ResolutionConfig = Field(default_factory = ResolutionConfig)
    transparent: bool = True

class DiscordConfig(BaseModel):
    token: str = ''
    review_channel: int | None = None
    approver_user: int | None = None
    output_channels: list[int] = Field(default_factory = list)

class WikiConfig(BaseModel):
    url: str = ''
    username: str = ''
    password: str = ''
    chunk_size: int = 0

class Config(BaseModel):
    render: RenderConfig
    discord: DiscordConfig = Field(default_factory = DiscordConfig)
    wiki: WikiConfig = Field(default_factory = WikiConfig)

def load_config(input_file: str | Path) -> Config:
    with open(input_file, 'r', encoding = 'utf-8') as file:
        data = yaml.safe_load(file)
    
    config = Config.model_validate(data)
    return config
