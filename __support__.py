import base64
import json
import os

ROOT_PATH = os.path.dirname(__file__)
BLOBS_DIR = os.path.join(ROOT_PATH, 'blobs')

def file_processing(file_name:str):
    """
    read content from file and convert to base64 - used for both images and blobs
    :steps:
        1. read file
        2. base64 encode file
        3. base64 decode ASCII
    :args:
        file_name:str - file to process
        exception:bool - whether to print exceptions
    :params:

        file_content - content from file
        full_file_path:str - full path of file_name
    """
    file_content = None
    base64_bytes = None
    full_file_path = os.path.expanduser(os.path.expandvars(file_name))

    try:
        with open(full_file_path, 'rb') as f:
            try:
                content  = f.read()
            except Exception as error:
                print(f"Failed to read content from file {file_name} (Error: {error})")
    except Exception as error:
        print(f"Failed to open file {file_name} to be read (Error: {error})")
    else:
        try:
            base64_bytes = base64.b64encode(content)
        except Exception as error:
            print(f'Failed to encode file data (Error: {error})')
        else:
            try:
                file_content = base64_bytes.decode('ascii')
            except Exception as error:
                print(f'Failed to convert encoded message to ASCII based value (Error: {error})')

        return file_content


def write_file(metadata:dict, data_dir:str=BLOBS_DIR):
    data_file = os.path.join(data_dir, 'raw_records.json')
    # Here you would implement your logic to write metadata to a database or file
    with open(data_file, 'a') as f:
        f.write(json.dumps(metadata) + "\n")


def send_data(db_name:str, table:str=None, conn:str=None, metadata:dict={}):
    """
    send data into EdgeLake/AnyLog via REST
    :process:
        1. read cv2 file
        2. build payload
        3. publish data
    :args:
        conn:str - REST connection information ([user]:[password]@[ip]:[port])
        metadata:dict - video metadata (includes video path)
    """
    payload = {
        "dbms":  db_name,
        "table": table,
        "file_name": os.path.basename(metadata['file_path']),
        "readings": {
            "start_time": metadata['start_time'],
            "end_time": metadata['end_time'],
            "duration": metadata['duration']
        }
    }
    if not table:
        payload['table'] = payload['file_name'].replace(".", "_")

    payload["raw_video"] = file_processing(file_name=metadata['file_path'])
    print(payload)



