import base64
import cv2
import datetime
import os
import time
import threading

import numpy
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

def frames_to_video(numpy_array, output_file, fps=30, codec='mp4v'):
    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*codec)

    # Get dimensions from the first frame
    height, width = numpy_array[0].shape[:2]

    # Create VideoWriter object
    out = cv2.VideoWriter(output_file, fourcc, fps, (width, height), isColor=True)

    for frame in numpy_array:
        # Ensure the frame is in the right format (convert if needed)
        if frame.shape[:2] != (height, width):
            frame = cv2.resize(frame, (width, height))
        out.write(frame)

    # Release the VideoWriter object
    out.release()

def read_video_to_frames(input_file):
    cap = cv2.VideoCapture(input_file)
    if not cap.isOpened():
        raise IOError("Error opening video file")

    frames = []
    fps = cap.get(cv2.CAP_PROP_FPS)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)

    cap.release()
    return np.array(frames), fps


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

    frames, fps = read_video_to_frames(input_file=full_path)

    # Check if frames are extracted
    if frames.size > 0:
        # Calculate the delay between frames in milliseconds
        delay = int(1000 / fps)

        for frame in frames:
            cv2.imshow('Video', frame)
            if cv2.waitKey(delay) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()
    else:
        print("No frames extracted from the video.")

def write_image(image_path:str, img:numpy.ndarray):
    image_path = os.path.expanduser(os.path.expandvars(image_path))
    dir_path = os.path.dirname(image_path)
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    try:
        cv2.imwrite(image_path, img)
    except Exception as error:
        print(f"Failed to write image into {image_path} (Error: {error})")

def display_image_with_bbox(image_path:str, bbox:list=[]):
    img = cv2.imread(image_path)
    if img is not None and bbox != []:
        # Draw the bounding box
        x1, y1, x2, y2 = bbox
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green box with thickness 2

    if img is not None:
        # Display the image
        cv2.imshow('Image', img)
        cv2.waitKey(0)  # Wait for a key press to close the image window
        cv2.destroyAllWindows()



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

        self.is_running = threading.Event()
        self.cap = self.__enable_video_capture()
        # self.cap.setExceptionMode(enable=True) # enable exception messages for cap
        self.video_writer = None
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

    def start_recording(self):
        """
        Start recording video
        """
        self.__set_cap_size()
        self.is_running.set()
        threading.Thread(target=self.__record).start()

    def __record(self):
        self.video_writer = None
        frames = []
        start_time = time.time()
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
            if current_time - start_time >= self.wait_time:
                self.__save_video(frames)
                self.__send_metadata(frames, start_time, current_time)
                frames = []
                start_time = current_time

    def __save_video(self, frames):
        """
        Save frames to video file
        """
        if not frames:
            return
        if self.video_writer is None:
            filename = os.path.join(self.blobs_dir, f'{self.db_name}.{self.rest_topic}_{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")}.mp4')
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (int(self.width), int(self.height)))
        for frame in frames:
            self.video_writer.write(frame)

    def __send_metadata(self, frames, start_time, end_time):
        """
        Send metadata to service
        """
        if not frames:
            return
        metadata = {
            "dbms": self.db_name,
            "table": self.table_name if self.table_name is not None else os.path.basename(self.video_writer.getBackendName()).split(".")[0],
            "file_name": os.path.basename(self.video_writer.getBackendName()),
            "readings": {
                "start_time": datetime.datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S.%f'),
                "end_time": datetime.datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S.%f'),
                "duration": round(end_time - start_time, 2)
            },
            "frame_count": len(frames),
            'frames': frames,
            "fps": self.cap.get(cv2.CAP_PROP_FPS),
            "width": self.width,
            "height": self.height
        }
        # if self.rest_conn is not None:
        #     support.send_data(rest_conn=self.rest_conn, topic=self.rest_topic, metadata=metadata)
        # else:
        support.write_metadata(blobs_dir=self.blobs_dir, metadata=metadata)

    def stop_recording(self):
        """
        Stop recording
        """
        self.is_running.clear()
        if self.video_writer is not None:
            self.video_writer.release()
        self.cap.release()

