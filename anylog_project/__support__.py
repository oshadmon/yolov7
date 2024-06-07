import json
import os
import requests

from camera_commands import frames_to_video_base64

ROOT_PATH = os.path.dirname(__file__).split("anylog_extension_code")[0]
BLOBS_DIR = os.path.join(ROOT_PATH, 'blobs')


def write_metadata(blobs_dir=BLOBS_DIR, metadata:dict={}):
    """
    write conteent into file
    :args:
        blobs_dir:str - directory file
        metadata:dict - content to store
    :params:
        metadata_file:str - file path (blobs_dir + metadata.json)
    """
    metadata_file = os.path.join(blobs_dir, 'metadata.json')
    if not os.path.isfile(metadata_file):
        open(metadata_file, 'w').close()

    # write frames to mp4 file
    frames_to_video_base64(numpy_array=metadata['frames'], output_file=os.path.join(blobs_dir, metadata['file_name']),
                           codec='mp4v', fps=metadata['fps'])

    # frames_to_video_base64(frames=metadata['frames'], fps=metadata['fps'], width=metadata['width'],
    #                        height=metadata['height'], output_file=os.path.join(blobs_dir, metadata['file_name']))
    del metadata['frames']

    # write metadata to file
    try:
        with open(metadata_file, 'a') as f:
            f.write(f"{json.dumps(metadata)}\n")
    except Exception as error:
        print(f"Failed to write metadata into file {metadata_file} (Error: {error})")

def publish_data(rest_conn:str, topic:str='livefeed', metadata={}):
    """
    Send data to file
    :args:
        rest_conn:str - REST connection information
        topic:str - REST topic
        metadata:dict - content to store
    :params:
        conn:str - REST conn IP:PORT
        auth:tuple - REST authentication
        headers:dict - REST header information
    """
    auth = ()
    conn = rest_conn
    if '@' in rest_conn:
        auth, conn = rest_conn.split('@')
        auth = tuple(auth.split(':'))
    headers = {
        'command': 'data',
        'topic': topic,
        'User-Agent': 'AnyLog/1.23',
        'Content-Type': 'application/json'
    }

    metadata['frames'] = frames_to_video_base64(frames=metadata['frames'], fps=metadata['fps'])

    try:
        response = requests.post(url=f"http://{conn}", headers=headers, data=json.dumps(metadata),
                                 auth=auth, timeout=30)
        response.raise_for_status()
    except Exception as error:
        print(f"Failed to send metadata to {conn} (Error: {error})")
