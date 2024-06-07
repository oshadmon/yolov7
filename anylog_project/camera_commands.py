import cv2
import datetime
import os
import time
import threading
import numpy as np
import __support__ as support

ROOT_PATH = os.path.dirname(__file__).split("anylog_project")[0]
BLOBS_DIR = os.path.join(ROOT_PATH, 'blobs')


def get_default_camera_id():
    """
    Get default camera ID
    """
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cap.release()
            return i
    raise Exception("Error: Could not find an available camera.")

def frames_to_video_base64(frames, fps, output_file):
    """
    Convert video frames into a base64 encoded string
    :args:
        frames:list - frames to write
        fps:float - frame rates
    :return:
        base64_str:str - base64 encoded video string
    """
    frames = [np.array(frame, dtype=np.uint8) for frame in frames]
    height, width, layers = frames[0].shape
    size = (width, height)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    # Create a VideoWriter object with an in-memory buffer
    video_writer = cv2.VideoWriter(output_file, fourcc, fps, size)

    for frame in frames:
        video_writer.write(frame)

    video_writer.release()

    # # Read the video file into a buffer
    # try:
    #     with open('output.mp4', 'rb') as video_file:
    #         video_buffer = video_file.read()
    # except Exception as error:
    #     return None
    #
    # # Convert the buffer to base64
    # base64_str = base64.b64encode(video_buffer).decode('utf-8')
    #
    # # Clean up the temporary file
    # os.remove('output.mp4')
    #
    # return base64_str

def frames_to_video(frames, output_file, fps):
    """
    Write video frames into mp4 file using H.264 codec
    :args:
        frames:list - frames to write
        output_file:str - file to store frames into
        fps:float - frame rates
    """
    frames = [np.array(frame, dtype=np.uint8) for frame in frames]

    # Check if the first frame is grayscale
    if len(frames[0].shape) == 2:
        height, width = frames[0].shape
        layers = 1  # Grayscale image has only one layer
    else:
        height, width, layers = frames[0].shape

    size = (width, height)
    fourcc = cv2.VideoWriter_fourcc(*'avc1')  # Use H.264 codec
    out = cv2.VideoWriter(output_file, fourcc, fps, size)
    for frame in frames:
        out.write(frame)
    out.release()



def video_to_frames(video_file):
    """
    Read video file and extract frames.
    :args:
        video_file:str - path to the video file
    :return:
        frames:list - list of frames extracted from the video
        fps:float - frames per second of the video
    """
    # Check if the file exists
    if not os.path.exists(video_file):
        raise Exception(f"Error: Video file {video_file} does not exist")

    # Print the file path for debugging
    print(f"Trying to open video file: {video_file}")

    cap = cv2.VideoCapture(video_file)
    cv2.VideoCapture.set(cv2.CAP_PROP_VERBOSE, 1)
    if not cap.isOpened():
        raise Exception(f"Error: Could not open video file {video_file}")

    frames = []
    fps = cap.get(cv2.CAP_PROP_FPS)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)

    cap.release()
    return frames, fps

def show_video(video_file):
    """
    Show content in video file - calls video_to_frames
    :args:
        video_file:str - path to the video file
    :return:
        frames:list - list of frames extracted from the video
        fps:float - frames per second of the video
    """
    full_path = os.path.expanduser(os.path.expandvars(video_file))
    if not os.path.isfile(full_path):
        print(f"Failed to locate file {video_file}")
        return

    frames, fps = video_to_frames(full_path)

    # Display the first frame
    if frames:
        cv2.imshow('First Frame', frames[0])
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("No frames extracted from the video.")


class VideoRecorder:
    def __init__(self, blobs_dir, db_name, table_name=None, rest_conn=None, rest_topic='livefeed',
                 camera_id=0, width=640, height=480, wait_time=60):
        """
        Initialize VideoRecorder.
        :params:
            blobs_dir - directory to store video
            db_name:str - logical database name (used in POST + mp4 file name)
            table_name:str - table name / if not set use mp4 file name (used in POST only)
            rest_conn:str - REST connection information
            rest_topic:str - REST topic header value
            camera_id:id - camera ID
            width:float / height:float - image size
            wait_time:float - how often to "wait" until saving / starting a new image
        """
        self.blobs_dir = blobs_dir
        self.db_name = db_name
        self.table_name = table_name
        self.rest_conn = rest_conn
        self.rest_topic = rest_topic
        self.camera_id = int(camera_id)
        self.width = float(width)
        self.height = float(height)
        self.wait_time = wait_time
        self.start_time = time.time()

        self.is_running = threading.Event()
        self.cap = self.__enable_video_capture()
        self.cap.setExceptionMode(enable=True) # enable exception messages for cap
        self.video_writer = self.__create_video_writer()
        if not self.cap.isOpened():
            raise Exception(f"Error: Could not open video device for camera ID {camera_id}")

    def __enable_video_capture(self):
        """
        Enable video capture
        """
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            raise Exception(f"Failed to start video capture with camera {self.camera_id}")
        return cap

    def __set_cap_size(self, height=None, width=None):
        """
        Set capture size
        """
        if height is None:
            height = self.height
        if width is None:
            width = self.width
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def __create_video_writer(self):
        """
        Create video writer
        :return: VideoWriter object
        """
        self.filename = os.path.join(self.blobs_dir, f'{self.db_name}.{self.rest_topic}_{datetime.datetime.fromtimestamp(self.start_time).strftime("%Y_%m_%d_%H_%M_%S_%f")}.mp4')
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        return cv2.VideoWriter(self.filename, fourcc, 20.0, (int(self.width), int(self.height)))

    def start_recording(self):
        """
        Start recording video
        """
        self.__set_cap_size()
        self.is_running.set()
        threading.Thread(target=self.__record).start()

    def __record(self):
        frames = []
        while self.is_running.is_set():
            try:
                ret, frame = self.cap.read()
            except Exception as error:
                print(f"Failed to read video (Error: {error})")
                self.is_running.clear()
                self.stop_recording()
                break

            if not ret:
                print(f"Record Error: Could not read frame.")
                # Attempt to reinitialize the capture device
                self.cap.release()
                self.cap = self.__enable_video_capture()
                if not self.cap.isOpened():
                    print("Error: Could not reopen video capture device.")
                    self.is_running.clear()
                    self.stop_recording()
                    break
                continue  # Skip processing this frame and try reading the next one

            current_time = time.time()
            frames.append(frame)
            if current_time - self.start_time >= self.wait_time:
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
                    'frames': frame,
                    "fps": self.cap.get(cv2.CAP_PROP_FPS),
                }

                if self.table_name is None:
                    metadata['table'] = os.path.basename(self.filename).split(".")[0]
                if self.rest_conn is not None:
                    support.send_data(rest_conn=self.rest_conn, topic=self.rest_topic, metadata=metadata)
                else:
                    support.write_metadata(blobs_dir=self.blobs_dir, metadata=metadata)
                frames_to_video(frames, self.filename, self.cap.get(cv2.CAP_PROP_FPS))  # Adjust codec
                self.start_time = current_time
                frames = []

    def stop_recording(self):
        """
        Stop recording
        """
        self.is_running.clear()
        self.cap.release()
        self.video_writer.release()

    def display_feed(self, height=None, width=None):
        """
        Open a window to show camera feed
        """
        self.__set_cap_size(height=height, width=width)
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Display Feed Error: Could not read frame.")
                self.stop_recording()
                continue
            cv2.imshow('Video Feed', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()
