import bpy

from .config import Config
from .utils import enable_addon_deps, blender_fps


def init_blend(config: Config):
    bpy.ops.wm.read_homefile(use_empty = True)
    failed = enable_addon_deps()
    if failed:
        raise ValueError(f'Missing addons: {", ".join(failed)}')
    setup_scene(config)

def setup_scene(config: Config):
    """
    Sets up the scene for rendering turnarounds.
    """
    
    cleanup_scene()
    scene: bpy.types.Scene = bpy.context.scene

    if scene.camera is None:
        camera = bpy.data.cameras.new('Camera')
        cam_obj = bpy.data.objects.new('Camera', camera)
        scene.collection.objects.link(cam_obj)
        scene.camera = cam_obj

    
    bpy.ops.rk.setup_renderer() # type: ignore
    scene.frame_start = 1
    scene.frame_end = config.render.frames
    scene.render.fps, scene.render.fps_base = blender_fps(config.render.fps)
    scene.render.resolution_x = config.render.resolution.width
    scene.render.resolution_y = config.render.resolution.height
    scene.render.film_transparent = config.render.transparent
    

def cleanup_scene():
    scene: bpy.types.Scene = bpy.context.scene
    to_remove = [obj for obj in scene.objects if obj.type != 'CAMERA']
    for obj in to_remove:
        bpy.data.objects.remove(obj, do_unlink = True)
    cleanup_blocks()
    
def cleanup_blocks():
    bpy.data.orphans_purge(
        do_local_ids = True,
        do_linked_ids = True,
        do_recursive = True,
    )
