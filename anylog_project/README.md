# Camera demo 

The following demonstrates using YOLOv7 with AnyLog/EdgeLake to process and store video insight.  

Given the following, merge into a working product that's able to analyze video(s) and send everything in AnyLog/EdgeLake
* videos
* images 
* insight

* **Step 1**: Create video and store to file 
  * **Code**: [video_creation.py](video_creation.py)
  * **Issue**: `Error: Could not read frame.`* 
```shell
python3 yolov7/anylog_project/video_creation.py  
```
  
* **Step 2**: Read video file
  * **Code**: [read_video.py](read_video.py)
```shell
python3 yolov7/anylog_project/read_video.py
```

* **Step 3**: Analyze video
  * **Code**: [detect.py](../detect.py)
  * **Issue**: image quality is horrible
```shell
python3 yolov7/detect.py --weights yolov7.pt --conf 0.1 --img-size 640 --source ~/yolov7/blobs/video2B.mp4 
```

* **Step 4**: Publish to AnyLog/EdgeLake
  * **Code**: In [__support__.py](__support__.py) method named `publish_data`
  * **Issue**: Once playloads (json to publish into AnyLog) will be ready need to create mapping policy 
  * **Example**:
    * [Mapping Policy](https://github.com/EdgeLake/deployment-scripts/blob/main/demo-scripts/blobs_car_videos.al) - note we'll b using OpenCV instead of Base64
    * Sample JSON to be published:
```json
# image
{
  "dbms": "demo_blobs", 
  "table": "video2B", 
  "img_info": {
      "bbox": [551, 333, 587, 360], 
    "img_size": [720, 1280]
  }, 
  "readings": {
    "person": 3, 
    "vehicle": 5
  }, 
  "cropped_img_path": "/Users/orishadmon/yolov7/blobs/video2B_1.jpg",
  "image_blob": [
    [
      [ 90  78  24],  [ 62  60  19],  [ 56  58  22],  [ 56  56  20],  [ 59  58  20],  [ 63  57  22],  [ 63  57  22],  
      [ 64  57  24],  [ 62  57  24],  [ 60  57  26],  [ 61  56  25],  [ 67  58  25],  [ 71  58  26],  [ 76  59  26],  
      [ 78  59  26],  [ 79  58  27],  [ 80  56  26],  [ 79  55  25],  [ 92  59  13],  [130  83   1],  [191 136  37]
    ], 
    ...
    [
      [ 81  73  33],  [ 50  51  25],  [ 40  45  24],  [ 38  43  22],  [ 38  39  19],  [ 43  37  18],  [ 45  38  19],  
      [ 44  37  20],  [ 40  36  18],  [ 56  53  38],  [ 53  53  37],  [ 58  56  38],  [ 68  61  44],  [ 72  62  44],  
      [ 73  59  41],  [ 65  49  32],  [ 57  39  22],  [ 51  35  18],  [ 63  37   1],  [107  63   0],  [184 132  42]
    ]
  ], 
}
        
{
  "dbms": "demo_blobs", 
  "table": "livefeed", 
  "file_name": "demo_blobs.livefeed_2024_06_07_17_22_27_273661.mp4", 
  "readings": {
    "start_time": "2024-06-07 17:22:17.271190", 
    "end_time": "2024-06-07 17:22:27.273594", 
    "duration": 10.0
  }, 
  "frame_count": 301, 
  "fps": 1.0, 
  "width": 640.0, 
  "height": 480.0, 
  "video_blob": [
    [
      [
        [109 113 122],   [109 113 122],   [109 113 122],   ...,   [ 83  90 101],   [ 83  90 101],   [ 83  90 101]
      ],,  
      [
        [109 113 122],   [109 113 122],   [109 113 122],   ...,   [ 83  90 101],   [ 83  90 101],   [ 83  90 101]
      ],,  
        [[109 113 122],   [109 113 122],   [109 113 122],   ...,   [ 83  90 101],   [ 83  90 101],   [ 83  90 101]
      ],
      ...
  ]]
}
```

