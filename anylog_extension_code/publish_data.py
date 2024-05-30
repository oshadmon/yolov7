import argparse
import base64
import cv2
import json
import os
import requests

# Define the root and blobs directories
ROOT_PATH=os.path.dirname(__file__).split("anylog_extension_code")[0]
BLOBS_DIR=os.path.join(ROOT_PATH, 'blobs')
METADATA=os.path.join(BLOBS_DIR, 'metadata.json')

def read_metadata(metadata_file:str=METADATA):
    """Read metadata from a JSON file."""
    with open(metadata_file, 'r') as json_file:
        return [json.loads(line) for line in json_file.readlines()]

def read_video(video_path:str):
    """Read video file and extract frames and metadata."""
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"No such file:'{video_path}'")

    cap=cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception(f"Error:Could not open video file {video_path}")

    frames=[]
    frame_count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps=cap.get(cv2.CAP_PROP_FPS)
    duration=frame_count / fps

    while True:
        ret, frame=cap.read()
        if not ret:
            break
        frames.append(frame.tolist())

    cap.release()

    return {
        "frame_count":frame_count,
        "fps":fps,
        "duration":duration,
        "frames":frames
    }

def publish_data(conn:str, payload:dict, topic:str):
    """Publish data to a REST API."""
    try:
        requests.post(
            url=f'http://{conn}',
            headers={
                'command':'data',
                'topic':topic,
                'User-Agent':'AnyLog/1.23',
                'Content-Type':'application/json'
            },
            data=json.dumps(payload)
        )
    except requests.RequestException as error:
        print(f'Failed to publish data to {conn} (Error:{error})')


def main():
    parser=argparse.ArgumentParser(description="Publish video metadata to a REST API.")
    parser.add_argument('conn', type=str, help='REST POST IP and port to publish data')
    parser.add_argument('--metadata-file', type=str, default=METADATA, help='JSON file with metadata information')
    parser.add_argument('--topic', type=str, default="livefeed", help='REST POST topic')
    parser.add_argument('--db-name', type=str, default='livefeed', help='Logical database name')
    parser.add_argument('--table', type=str, help='Table name - if not set uses file name as table name')
    args=parser.parse_args()

    args.metadata_file=os.path.expanduser(os.path.expandvars(args.metadata_file))
    if not os.path.isfile(args.metadata_file):
        print(f"Failed to locate {args.metadata_file}, cannot continue...")
        exit(1)

    metadata_entries=read_metadata(metadata_file=args.metadata_file)

    for entry in metadata_entries:
        table_name=args.table or os.path.basename(entry['file_path']).replace('.', '_')
        metadata={
            "dbms":args.db_name,
            "table":table_name,
            "file_name":os.path.basename(entry['file_path']),
            "readings":{
                "start_time":entry['start_time'],
                "end_time":entry['end_time'],
                "duration":entry['duration']
            }
        }

        try:
            video_insight=read_video(video_path=entry['file_path'])
            metadata.update(video_insight)
            publish_data(conn=args.conn, payload=metadata, topic=args.topic)
        except Exception as error:
            print(f"Failed to process video file {entry['file_path']} (Error:{error})")

if __name__ == '__main__':
    main()
