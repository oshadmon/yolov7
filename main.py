import os
from detect import detect



# class DetectParams:
#     weights = ['yolov7.pt']
#     source = 'inference/images'
#     img_size = 640
#     conf_thres = 0.25
#     iou_thres = 0.45
#     device = ''
#     view_img = False
#     save_txt = False
#     save_conf = False
#     nosave = False
#     classes = None
#     agnostic_nms = False
#     augment = False
#     update = False
#     project = 'runs/detect'
#     name = 'exp'
#     exist_ok = False
#     no_trace = False
#
# opt = DetectParams()
#
#
# print(opt.no_trace)

if __name__ == '__main__':
    # source = os.path.expanduser(os.path.expandvars('~/yolov7/blobs/2024_05_28_08_36_37.mp4'))
    source = os.path.expandvars(os.path.expanduser('~/Sample-Data-Generator/blobs/car_video/video67A.mp4'))
    readings = detect(weights="yolov7.pt", conf_thres=0.25, imgsz=640, source=source)
    print(readings)