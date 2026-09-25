import bpy

from .utils import enable_addon_deps

def init_blend():
    bpy.ops.wm.read_homefile(use_empty = True)
    failed = enable_addon_deps()
    if failed:
        raise ValueError(f'Missing addons: {", ".join(failed)}')
    setup_scene()

def setup_scene():
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
    scene.frame_end = 100
    scene.render.fps = 10
    scene.render.resolution_x = 720
    scene.render.resolution_y = 540
    scene.render.film_transparent = True
    

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
