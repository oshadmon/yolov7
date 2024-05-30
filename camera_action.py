import argparse
import cv2
import datetime
import os
import time
import threading
import json

ROOT_PATH = os.path.dirname(__file__)
BLOBS_DIR = os.path.join(ROOT_PATH, 'blobs')

def get_default_camera_id():
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cap.release()
            return i
    raise Exception("Error: Could not find an available camera.")

class VideoRecorder:
    def __init__(self, blobs_dir:str, metadata_file:str, camera_id:int=0, width:float=640, height:float=480, wait_time:int=60):
        self.blobs_dir = blobs_dir
        self.metadata_file = metadata_file
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

    def __record(self):
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
                metadata = {
                    "file_path": self.filename,
                    "start_time": datetime.datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S.%f'),
                    "end_time": datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f'),
                    "duration": round(current_time - self.start_time, 2)
                }
                with open(self.metadata_file, 'a') as f:
                    f.write(f"{json.dumps(metadata)}\n")
                self.start_time = current_time
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
    parse.add_argument('--height', type=float, default 480, help='Live feed screen ratio height')
    parse.add_argument('--cut-video', type=int, default=10, help='Video size (in seconds)')
    parse.add_argument('--blobs-dir', type=str, default=BLOBS_DIR, help='Directory to store videos cuts and insight')
    args = parse.parse_args()

    args.blobs_dir = os.path.expanduser(os.path.expandvars(args.blobs_dir))
    os.makedirs(args.blobs_dir, exist_ok=True)
    metadata_file = os.path.join(args.blobs_dir, 'metadata.json')
    if not os.path.isfile(metadata_file):
        open(metadata_file, 'w').close()

    video_recorder = VideoRecorder(blobs_dir=args.blobs_dir, metadata_file=metadata_file, camera_id=args.camera_id,
                                   width=args.width, height=args.height, wait_time=args.cut_video)
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
