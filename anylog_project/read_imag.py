import argparse
import os
import json
from anylog_project.camera_commands import display_image_with_bbox

ROOT_PATH = os.path.dirname(__file__).split("anylog_project")[0]
BLOBS_DIR = os.path.join(ROOT_PATH, 'blobs', 'demo_blobs.video2B.0.json')


def main():
    parse = argparse.ArgumentParser()
    parse.add_argument('--metadata-file', type=str, default=BLOBS_DIR, help='Metadata file')
    args = parse.parse_args()

    full_path = os.path.expandvars(os.path.expanduser(args.metadata_file))
    if not os.path.isfile(full_path):
        print(f"Unable to locate {args.mtadata_file}. Cannot contine...")
        exit(1)

    with open(full_path, 'r') as f:
        for line in f.readlines():
            output = json.loads(line)
    if 'cropped_img_path' in output:
        file_name = os.path.expanduser(os.path.expandvars(output['cropped_img_path']))
    bbox =[]
    try:
        if 'img_info' in output and 'bbox' in output['img_info']:
            bbox =  output['img_info']['bbox']
    except:
        pass

    display_image_with_bbox(image_path=file_name, bbox=bbox)



if __name__ == '__main__':
    main()
