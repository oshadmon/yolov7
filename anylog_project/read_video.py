import argparse
import os

# import camera_commands
from anylog_project.camera_commands import show_video

ROOT_PATH = os.path.dirname(__file__).split("anylog_project")[0]
BLOBS_DIR = os.path.join(ROOT_PATH, 'blobs')


def main():
    parse = argparse.ArgumentParser()
    parse.add_argument('--file-path', type=str, default=BLOBS_DIR, help='directory or file to read')
    args = parse.parse_args()

    full_path = os.path.expandvars(os.path.expanduser(args.file_path))
    if not os.path.isfile(full_path) and not os.path.isdir(full_path):
        print(f"Unable to locate {args.file_path}. Cannot contine...")
        exit(1)

    if os.path.isfile(full_path):
        show_video(full_path)
        exit(1)
    for fname in os.listdir(full_path):
        if not fname.endswith('mp4'):
            continue
        else:
            file_path = os.path.join(full_path, fname)
            show_video(file_path)

if __name__ == '__main__':
    main()
