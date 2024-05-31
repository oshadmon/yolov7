import argparse
import cv2
import datetime
import json
import numpy
import os
import requests
import time
import threading

ROOT_PATH = os.path.dirname(__file__).split("anylog_extension_code")[0]
BLOBS_DIR = os.path.join(ROOT_PATH, 'blobs')

def get_default_camera_id():
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cap.release()
            return i
    raise Exception("Error: Could not find an available camera.")

def frames_to_video(frames, output_file, fps):
    """
    Convert a list of frames to a video file.
    :args:
        frames (list): List of frames (each frame is a list of lists).
        output_file (str): Output video file path.
        fps (float): Frames per second.
    """
    # Convert frames from lists back to numpy arrays
    frames = [numpy.array(frame, dtype=numpy.uint8) for frame in frames]

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4')  # Codec for mp4
    out = cv2.VideoWriter(output_file, fourcc, fps)

    for frame in frames:
        out.write(frame)

    out.release()
def write_metadata(blobs_dir:str=BLOBS_DIR, metadata:dict={}):
    """
    Write metadata to file
    :args:
        blobs_dir:str - dir to store file
        metadata:dict - content to store in file
    :paraams:
        metadata_file:sr - JSON file to store data in
    """
    metadata_file = os.path.join(blobs_dir, 'metadata.json')

    if not os.path.isfile(metadata_file):
        open(metadata_file, 'w').close()

    frames_to_video(frams=metadata['frames'],
                    output_file=os.path.join(blobs_dir, metadata['file_name']),
                    fps=metadata['fps'])

    try:
        with open(metadata_file, 'a') as f:
            f.write(f"{json.dumps(metadata)}\n")
    except Exception as error:
        print(f"Failed to write metadata into file {metadata_file} (Error: {error})")

def send_data(rest_conn:str, topic:str='livefeed', metadata:dict={}):
    """
    Send data into AnyLog / EdgeLake
    :args:
        rest_conn:str - REST connection information
        topic:str - REST POST topic
        metadata:dict - conteent to send into AnyLog/EdgeLake
    :params:
        auth:tuple - REST authentication
        headers:dict - REST headers
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

    try:
        response = requests.post(url=f"http://{conn}", headers=headers, json=metadata, auth=auth, timeout=30)
        response.raise_for_status()
    except Exception as error:
        print(f"Failed to send metadata to {conn} (Error: {error})")


class VideoRecorder:
    def __init__(self, blobs_dir:str, db_name:str, table_name:str=None, rest_conn:str=None, rest_topic:str='livefeed',
                 camera_id:int=0, width:float=640, height:float=480, wait_time:int=60):
        self.blobs_dir = blobs_dir
        self.db_name = db_name
        self.table_name = table_name
        self.rest_conn = rest_conn
        self.rest_topic = rest_topic
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.wait_time = wait_time
        self.is_running = threading.Event()
        self.cap = self.__enable_video_capture()
        self.video_writer = self.__create_video_writer()
        self.start_time = time.time()

        if not self.cap.isOpened():
            raise Exception(f"Error: Could not open video device for camera ID {camera_id}")

    def __enable_video_capture(self):
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            raise Exception(f"Failed to start video capture with camera {self.camera_id}")
        return cap

    def __set_cap_size(self, height:float=None, width:float=None):
        if height is None:
            height = self.height
        if width is None:
            width = self.width
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def __create_video_writer(self):
        self.filename = os.path.join(self.blobs_dir, f'{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")}.mp4')
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        return cv2.VideoWriter(self.filename, fourcc, 20.0, (int(self.width), int(self.height)))

    def start_recording(self):
        self.__set_cap_size()
        self.is_running.set()
        threading.Thread(target=self.__record).start()

    def __record_old(self):
        while self.is_running.is_set():
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Could not read frame.")
                self.is_running.clear()
                break
            current_time = time.time()
            if current_time - self.start_time >= self.wait_time:
                self.video_writer.release()
                self.video_writer = self.__create_video_writer()

                self.start_time = current_time
            self.video_writer.write(frame)

    def __record(self):
        frames = []
        while self.is_running.is_set():
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Could not read frame.")
                self.is_running.clear()
                break
            current_time = time.time()
            frames.append(frame.tolist())
            if current_time - self.start_time >= self.wait_time:
                self.video_writer.release()
                self.video_writer = self.__create_video_writer()
                metadata = {
                    "dbms": self.db_name,
                    "table": self.table_name,
                    "file_name": os.path.basename(self.filename),
                    "readings": {
                        "start_time": datetime.datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S.%f'),
                        "end_time": datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f'),
                        "duration": round(current_time - self.start_time, 2)
                    },
                    "frame_count": len(frames),
                    "fps": self.cap.get(cv2.CAP_PROP_FPS),
                    "frames": frames
                }

                if self.table_name is None:
                    metadata['table'] = os.path.basename(self.filename).split(".")[0]

                if self.rest_conn:
                    send_data(rest_conn=self.rest_conn, topic=self.rest_topic, metadata=metadata)
                else:
                    write_metadata(blobs_dir=self.blobs_dir, metadata=metadata)

                self.start_time = current_time
                frames = []
            self.video_writer.write(frame)

    def stop_recording(self):
        self.is_running.clear()
        self.cap.release()
        self.video_writer.release()

    def display_feed(self, height:float=None, width:float=None):
        self.__set_cap_size(height=height, width=width)
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Could not read frame.")
                continue
            cv2.imshow('Video Feed', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()

def main():
    parse = argparse.ArgumentParser()
    parse.add_argument('--camera-id', type=int, default=get_default_camera_id(), help='Camera ID')
    parse.add_argument('--width', type=float, default=640, help='Live feed screen ratio width')
    parse.add_argument('--height', type=float, default=480, help='Live feed screen ratio height')
    parse.add_argument('--cut-video', type=int, default=10, help='Video size (in seconds)')
    parse.add_argument('--blobs-dir', type=str, default=BLOBS_DIR, help='Directory to store videos cuts and insight')
    args = parse.parse_args()

    args.blobs_dir = os.path.expanduser(os.path.expandvars(args.blobs_dir))
    os.makedirs(args.blobs_dir, exist_ok=True)
    # metadata_file = os.path.join(args.blobs_dir,

    video_recorder = VideoRecorder(blobs_dir=args.blobs_dir, db_name='test', camera_id=args.camera_id, width=args.width, height=args.height, wait_time=args.cut_video)
    video_recorder.start_recording()

    try:
        while True:
            command = input("Command (o to open feed, q to quit, h to update height, w to update width): ").strip()
            if command == 'o':
                video_recorder.display_feed(height=args.height, width=args.width)
            elif command == 'q':
                break
            elif command == 'h':
                args.height = float(input("Updated height: "))
            elif command == 'w':
                args.width = float(input("Updated width: "))
            else:
                print(f"Invalid option {command}")
    except KeyboardInterrupt:
        print("\nInterrupted by user. Stopping...")
    except Exception as error:
        print(f"\nError: {error}")
    finally:
        video_recorder.stop_recording()


if __name__ == "__main__":
    main()
