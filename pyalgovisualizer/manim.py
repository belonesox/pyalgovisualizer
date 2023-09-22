"""Main module."""

import sys
try:
    import manimlib 
    import manimlib.config
    import manimlib.constants
    import manimlib.extract_scene
    from manimlib.imports import *
except:
    pass    

original_set_suspend = None
import argparse

def _get_camera_configuration(args):
    camera_config = {}
    if args.low_quality:
        camera_config.update(manimlib.constants.LOW_QUALITY_CAMERA_CONFIG)
    elif args.medium_quality:
        camera_config.update(manimlib.constants.MEDIUM_QUALITY_CAMERA_CONFIG)
    elif args.high_quality:
        camera_config.update(manimlib.constants.HIGH_QUALITY_CAMERA_CONFIG)
    else:
        camera_config.update(manimlib.constants.PRODUCTION_QUALITY_CAMERA_CONFIG)

    # If the resolution was passed in via -r
    if args.resolution:
        if "," in args.resolution:
            height_str, width_str = args.resolution.split(",")
            height = int(height_str)
            width = int(width_str)
        else:
            height = int(args.resolution)
            width = int(16 * height / 9)
        camera_config.update({
            "pixel_height": height,
            "pixel_width": width,
        })

    if args.color:
        try:
            camera_config["background_color"] = colour.Color(args.color)
        except AttributeError as err:
            print("Please use a valid color")
            print(err)
            sys.exit(2)

    # If rendering a transparent image/move, make sure the
    # scene has a background opacity of 0
    if args.transparent:
        camera_config["background_opacity"] = 0

    return camera_config


def _get_configuration(args):
    # module = get_module(args.file)
    file_writer_config = {
        # By default, write to file
        "write_to_movie": args.write_to_movie or not args.save_last_frame,
        "save_last_frame": args.save_last_frame,
        "save_pngs": args.save_pngs,
        "save_as_gif": args.save_as_gif,
        # If -t is passed in (for transparent), this will be RGBA
        "png_mode": "RGBA" if args.transparent else "RGB",
        "movie_file_extension": ".mov" if args.transparent else ".mp4",
        "file_name": args.file_name,
        # "input_file_path": args.file,
    }
    file_writer_config["output_directory"] = '/tmp'
    # if hasattr(module, "OUTPUT_DIRECTORY"):
    #     file_writer_config["output_directory"] = module.OUTPUT_DIRECTORY
    config = {
        # "module": module,
        # "scene_names": args.scene_names,
        "open_video_upon_completion": False, #args.preview,
        "show_file_in_finder": False, #args.show_file_in_finder,
        "file_writer_config": file_writer_config,
        "quiet": args.quiet or args.write_all,
        "ignore_waits": False, #args.preview,
        "write_all": args.write_all,
        "start_at_animation_number": args.start_at_animation_number,
        "end_at_animation_number": None,
        "sound": False, #args.sound,
        "leave_progress_bars": args.leave_progress_bars,
        "media_dir": args.media_dir,
        "video_dir": args.video_dir,
        "video_output_dir": args.video_output_dir,
        "tex_dir": args.tex_dir,
    }

    # Camera configuration
    config["camera_config"] = _get_camera_configuration(args)

    # Arguments related to skipping
    stan = config["start_at_animation_number"]
    if stan is not None:
        if "," in stan:
            start, end = stan.split(",")
            config["start_at_animation_number"] = int(start)
            config["end_at_animation_number"] = int(end)
        else:
            config["start_at_animation_number"] = int(stan)

    config["skip_animations"] = any([
        file_writer_config["save_last_frame"],
        config["start_at_animation_number"],
    ])
    return config


def get_scene_kwargs():
    args = argparse.Namespace(
                            write_to_movie=False, 
                            save_last_frame=False, 
                            low_quality=False, 
                            medium_quality=True, 
                            high_quality=False, 
                            save_pngs=False, 
                            save_as_gif=False, 
                            show_file_in_finder=False, 
                            transparent=False, 
                            quiet=False, 
                            write_all=False, 
                            file_name=None, 
                            start_at_animation_number=None, 
                            resolution='360,640', 
                            color=None, 
                            sound=False, 
                            leave_progress_bars=False, 
                            media_dir=None, 
                            video_dir=None, 
                            video_output_dir=None, 
                            tex_dir=None)

    config = _get_configuration(args)
    manimlib.constants.initialize_directories(config)

    scene_kwargs = dict([
        (key, config[key])
        for key in [
            "camera_config",
            "file_writer_config",
            "skip_animations",
            "start_at_animation_number",
            "end_at_animation_number",
            "leave_progress_bars",
        ]
    ])

    return scene_kwargs




# for setup only
# def yellow_frame_annotation(framew, frameh):
#     d1 = DoubleArrow(framew * LEFT / 2, framew * RIGHT / 2, buff=0).to_edge(DOWN)
#     t1 = Text(str(framew)[:6]).next_to(d1, UP)
#     d2 = DoubleArrow(frameh * UP / 2, frameh * DOWN / 2, buff=0).to_edge(LEFT)
#     t2= Text(str(frameh)).next_to(d2, RIGHT)
#     x=Group(d1,d2,t1,t2).set_color(YELLOW)
#     return x

# def blue_pixel_annotation(framew, frameh,pixelw, pixelh):
#     d1 = DoubleArrow(framew * LEFT / 2, framew * RIGHT / 2, buff=0).to_edge(UP)
#     t1 = Text(str(pixelw) + " pixel").next_to(d1, DOWN)
#     d2 = DoubleArrow(frameh * UP / 2, frameh * DOWN / 2, buff=0).to_edge(RIGHT)
#     t2= Text(str(pixelh) + " pixel").next_to(d2, LEFT)
#     x=Group(d1,d2,t1,t2).set_color(BLUE)
#     return x

# annulus = Annulus(inner_radius =1,outer_radius=2,color=WHITE,  stroke_width=10)
