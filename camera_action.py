import argparse
import cv2
import datetime
import os
import time
import threading
import json

import __support__ as support

ROOT_PATH = os.path.dirname(__file__)
BLOBS_DIR = os.path.join(ROOT_PATH, 'blobs')
os.makedirs(BLOBS_DIR, exist_ok=True)
DATA_FILE = os.path.join(BLOBS_DIR, 'raw_records.json')
open(DATA_FILE, 'a').close()
def write_file(metadata):
    # Here you would implement your logic to write metadata to a database or file
    with open(DATA_FILE, 'a') as f:
        f.write(json.dumps(metadata) + "\n")


class VideoRecorder:
    def __init__(self, dbms:str, data_dir:str=BLOBS_DIR, camera_id:int=0, width:float=640, height:float=480, wait_time:float=60):
        """
        Record video for user
        :args:
            camera_id:int - Camera ID
            width:float -  Image width size
            height:float - Image height size
            wait_time:float - how long each video will be
        :params:
            self.is_running:bool
            self.cap:cv2.VideoCapture - VideoCapture
            self.video_writer:cv2.VideoWriter
            self.start_time:float - epoch timestamp gets updated every time we create a new video
            self.camera_id:int - Camera ID
            self.width:float -  Image width size
            self.height:float - Image height size
            self.wait_time:float - how long each video will be
        """
        self.dbms = dbms
        self.data_dir = data_dir
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.is_running = False
        self.cap = self.__enable_video_capture()
        if not self.cap.isOpened() or self.cap is None:
            raise Exception(f"Error: Could not open video device for camera ID {camera_id}")
        self.video_writer = self.__create_video_writer()
        self.start_time = time.time()
        self.wait_time = wait_time

    def __enable_video_capture(self):
        cap = None
        try:
            cap = cv2.VideoCapture(self.camera_id)
        except Exception as error:
            raise Exception(f"Failed to start video capture with camera {self.camera_id} (Error: {error})")
        return cap

    def __set_cap_size(self, height=None, width=None):
        """
        Image capture size
        :args:
            width:int -  Image width size
            height:int - Image height size
        """
        if height is None:
            height = self.height
        if width is None:
            width = self.width

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def __create_video_writer(self):
        """
        Create video and store in file each time
        :params:
            self.filename - file to store video in
        """
        self.filename = os.path.join(BLOBS_DIR, f'{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_$f")}.mp4')
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(self.filename, fourcc, 20.0, (int(self.width), int(self.height)))
        return video_writer

    def start_recording(self, table_name:str=None, remote_conn:str=None):
        """
        Start recording
        """
        self.__set_cap_size()
        self.is_running = True
        threading.Thread(target=self.__record, args=(table_name, remote_conn)).start()

    def __record(self, table_name:str=None, remote_conn:str=None):
        """
        Actual recording process  - once recording is done, write video info into a JSON file
        """
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Could not read frame.")
                self.is_running = False
                break

            current_time = time.time()
            if current_time - self.start_time >= self.wait_time:
                self.video_writer.release()
                self.video_writer = self.__create_video_writer()
                metadata = {
                    "file_path": self.filename,
                    "start_time": datetime.datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S.%f'),
                    "end_time": datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f'),
                    "duration": round(current_time - self.start_time, 2)
                }
                if remote_conn is None:
                    support.write_file(data_dir=self.data_dir)
                else:
                    support.send_data(db_name=self.dbms, conn=remote_conn, table=table_name, metadata=metadata)
                self.start_time = current_time

            self.video_writer.write(frame)

    def stop_recording(self):
        """
        Stop recording
        """
        self.is_running = False
        self.cap.release()
        self.video_writer.release()



def video_reader(file_path:str):
    """
    Read video file from cv2
    """
    try:
        full_path = os.path.expandvars(os.path.expandvars(file_path))
    except Exception as error:
        print(f"Failed to locate file {file_path} (Error: {error})")
        exit(1)
    else:
        if not os.path.isfile(full_path):
            print(f"Failed to locate file {file_path}")
            exit(1)

    try:
        cap = cv2.VideoCapture(full_path)
    except Exception as error:
        print(f"Failed to open video file {file_path} (Error: {error})")
        exit(1)
    else:
        if not cap.isOpened():
            print(f"Failed to open video file {file_path}")
            exit(1)

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("Reached the end of the video or there was an error.")
                break

            # Display the current frame
            cv2.imshow('Video', frame)

            # Exit the loop when 'q' is pressed
            if cv2.waitKey(25) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        pass
    except Exception as error:
        print(f"None KeyboardInterrupt Error (Error: {error})")
    finally:
        # Release the VideoCapture object
        cap.release()
        # Close all OpenCV windows
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--camera-id', type=int, default=0, help='Camera ID')
    parser.add_argument('--width', type=float, default=640, help='Live feed screen ratio width')
    parser.add_argument('--height', type=float, default=480, help='Live feed screen ratio height')
    parser.add_argument('--cut-video', type=int, default=10, help='Video size (in seconds)')
    parser.add_argument('--db-name', type=str, default='live_data', help='logical database to store data in')
    parser.add_argument('--table', type=str, default='live_video', help='physical table name')
    parser.add_argument('--remote-conn', type=str, default=None, help='REST (POST) connection information (ex. [user]:[password]@[ip]:[port]')
    parser.add_argument('--data-dir', type=str, default=BLOBS_DIR, help='data directory for blobs')
    args = parser.parse_args()

    video_recorder = VideoRecorder(dbms=args.db_name, data_dir=args.data_dir, camera_id=args.camera_id, width=args.width,
                                   height=args.height, wait_time=args.cut_video)
    video_recorder.start_recording(table_name=args.table, remote_conn=args.remote_conn)

    try:
        while True:
            command = input("Command (q to quit): ").strip()
            if command == 'q':
                break
            else:
                print(f"Invalid option {command}")
    except KeyboardInterrupt:
        print("\nInterrupted by user. Stopping...")
    finally:
        video_recorder.stop_recording()


if __name__ == '__main__':
    main()
    # video_reader(file_path=os.path.join(BLOBS_DIR, '2024_05_28_08_36_27.mp4'))