import argparse, os
import sys, subprocess
from typing import List, Optional
from dataclasses import dataclass

VIDEO_FILTER = [".mkv", ".mp4"] # only files in this extension set will be processed

BINARY_NAME = "ffmpeg"
BINARY_PREFIXES = ["-hwaccel", "auto"]

VIDEO_TOOLBOX_ARGS = ["-c:v", "hevc_videotoolbox", "-q:v"]

BINARY_SUFFIXES = ["-c:a", "libopus", "-vbr", "1", "-b:a", "128k"]

@dataclass
class QualityConfig:
    cq: int
    scale: Optional[str]

    def __repr__(self):
        return "[cq{}scale{}]".format(self.cq, self.scale.replace(":", "by") if self.scale is not None else "O")


QUALITY_PRESETS = {
    0: QualityConfig(cq=50, scale=None),
    1: QualityConfig(cq=40, scale=None),
    2: QualityConfig(cq=30, scale=None),
    3: QualityConfig(cq=25, scale=None),
    4: QualityConfig(cq=20, scale=None),
    10: QualityConfig(cq=50, scale="1280:720"),
    11: QualityConfig(cq=40, scale="1280:720"),
    12: QualityConfig(cq=30, scale="1280:720"),
    13: QualityConfig(cq=25, scale="1280:720"),
    14: QualityConfig(cq=20, scale="1280:720"),
    20: QualityConfig(cq=50, scale="848:480"),
    21: QualityConfig(cq=40, scale="848:480"),
    22: QualityConfig(cq=30, scale="848:480"),
    23: QualityConfig(cq=25, scale="848:480"),
    24: QualityConfig(cq=20, scale="848:480"),
}

def extract_files(input_dir: str) -> List[str]:
    filenames = os.listdir(input_dir)
    videos = []
    for f in filenames:
        if not any([ext in f for ext in VIDEO_FILTER]):
            continue
        videos.append(f)
    return videos

def sanitize_output_video(f: str) -> str:
    # recursively delete matching []
    new = f
    while ("[" in new):
        l = new.find("[")
        r = new.find("]")
        new = new.replace(new[l:r+1], "")
    while (" " in new or "-" in new):
        new = new.replace(" ", "")
        new = new.replace("-", "")
    return new

def process_videos(filenames: List[str], input_dir: str, output_dir: str, quality: int, clear_queue: bool, clear_output: bool) -> None:
    if clear_output:
        # subprocess.run(["rm", "-r", output_dir + "*"], shell=True)
        print("[debug] Cleared output directory")
    if quality not in QUALITY_PRESETS:
        print("Must provide a valid quality preset")
        sys.exit(1)
    quality_config = QUALITY_PRESETS[quality]
    for f in filenames:
        input_path = input_dir + f
        output_path = output_dir + str(quality_config) + sanitize_output_video(f)
        output_path = output_path[:-3] + "mkv"
        process_video(input_path=input_path, output_path=output_path, quality_config=quality_config)
        print("[debug] Finished processing: ", f)
        if clear_queue:
            print('[debug] Clearning the original file in the queue... ')
            # subprocess.run(["rm", input_path], shell=True)



def process_video(input_path: str, output_path: str, quality_config: QualityConfig) -> None:
    args = [BINARY_NAME] + BINARY_PREFIXES + ["-i", input_path] + VIDEO_TOOLBOX_ARGS + [str(quality_config.cq)]
    if quality_config.scale:
        args += ["-vf", "scale={}".format(quality_config.scale)]
    args += BINARY_SUFFIXES + [output_path]
    # argument building
    print("[debug]", args)
    subprocess.run(args=args, stdout=sys.stdout, stderr=sys.stderr)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = 'ffmpeg-videotoolkit',
        description = 'Invokes ffmpeg to convert all video files in a directory and output to another dir')

    parser.add_argument('-i', '--inputdir', required=True)
    parser.add_argument('-o', '--outputdir', required=True)
    parser.add_argument('-q', '--quality', default=11, type=int)
    parser.add_argument('-cq', '--clearqueue', default=False, type=bool)
    parser.add_argument('-co', '--clearoutput', default=False, type=bool)
    args = parser.parse_args()

    videos = extract_files(input_dir=args.inputdir)
    process_videos(videos, input_dir=args.inputdir, output_dir=args.outputdir,
                   quality=args.quality, clear_queue=args.clearqueue, clear_output=args.clearoutput)
