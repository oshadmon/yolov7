# Camera demo 

The following demonstrates using YOLOv7 with AnyLog/EdgeLake to process and store video insight.  

Given the following, merge into a working product that's able to analyze video(s) and send everything in AnyLog/EdgeLake
* videos
* images 
* insight

## Process
* **Step 1**: Create video and store to file 
  * **Code**: [video_creation.py](video_creation.py)
  * **Issue**: `Error: Could not read frame.`
* **Step 2**: Read video file
  * **Code**: [read_video.py](read_video.py)
* **Step 3**: Analyze video
  * 

## File Struct (Tree)

* [camera commands](camera_commands.py) - camera related methods and functions
  * generate video
  * show video 
  * read / write video file
* [__support__.py](__support__.py) - support functions
  * write to file 
  * send to EdgeLake / AnyLog via _POST_ 