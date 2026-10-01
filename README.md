# Auto Pony Turnarounds

This project is built to automatically render turnarounds of ponies from the My Little Pony Gameloft game.

## Setup

Clone the repo

```shell
git clone https://github.com/ego-lay-atman-bay/pony-turnarounds.git
cd pony-turnarounds
```

Copy `config.default.yaml` to `config.yaml` and make the necessary changes you want. You can see `config.example.yaml` to get more info about what the file should look like. You can leave the discord and wiki sections empty if you don't want to use those, it'll still render all the models and place them in the specified output folder, though reviews will happen on the device and don't have a timeout.

Make sure [uv](https://docs.astral.sh/uv/) is installed, and then run

```shell
uv sync
```

You also need to make sure [rk-blender](https://github.com/ego-lay-atman-bay/rk-blender) is installed in your system blender install.

Now you can run

```shell
uv run -- pony-turnarounds -h
```

## Usage

Set list of ponies

```shell
uv run -- pony-turnarounds -g "game/folder" -p Pony_Trenderhoof Pony_Mean_Princess_Luna Pony_Postshow_Sapphire_Shores
```

Range of ponies

```shell
uv run -- pony-turnarounds -g "game/folder" -r Pony_Grumpy_Manehattanite Pony_Alicorn_Cozy_Glow
```
