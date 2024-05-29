import os
import time
from detect import detect


if __name__ == '__main__':
    source = os.path.expanduser(os.path.expandvars('~/yolov7/blobs/2024_05_28_08_36_37.mp4'))
    # source = os.path.expandvars(os.path.expanduser('~/Sample-Data-Generator/blobs/car_video/video67A.mp4'))
    readings = detect(db_name='test', weights="yolov7.pt", conf_thres=0.25, imgsz=640, source=source)
    print(readings)