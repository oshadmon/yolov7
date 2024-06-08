import argparse
import os

import anylog_project.camera_commands as camera_commands

ROOT_PATH = os.path.dirname(__file__).split("anylog_project")[0]
BLOBS_DIR = os.path.join(ROOT_PATH, 'blobs')


def main():
    """
    Live video feed & store to file or AnyLog/EdgeLake
    :optional arguments:
        -h, --help              show this help message and exit
        --camera-id     CAMERA_ID   Camera ID
        --blobs-dir     BLOBS_DIR   directory to store videos in
        --db-name       DB_NAME     logical database name to store data in
        --table-name    TABLE_NAME  table name / if not set use mp4 file name (used in POST only)
        --rest-conn     REST_CONN   REST connection information
        --rest-topic    REST_TOPIC  REST topic header value
        --video-size    VIDEO_SIZE  how often to "wait" until saving / starting a new image
        --width         WIDTH       image size
        --height        HEIGHT      image size
    :params:
        command:str - User defined command
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--camera-id',  type=int,   default=camera_commands.get_default_camera_id(), help='Camera ID')
    parser.add_argument('--blobs-dir',  type=str,   default=BLOBS_DIR, help='directory to store videos in')
    parser.add_argument('--db-name',    type=str,   default='demo_blobs', help='logical database name to store data in')
    parser.add_argument('--table-name', type=str,   default=None, help='table name / if not set use mp4 file name (used in POST only)')
    # parser.add_argument('--rest-conn',  type=str,   default=None, help='REST connection information')
    # parser.add_argument('--rest-topic', type=str,   default='livefeed', help='REST topic header value')
    parser.add_argument('--video-size', type=float, default=60, help='how often to "wait" until saving / starting a new image')
    parser.add_argument('--width',      type=float, default=640, help='image size')
    parser.add_argument('--height',     type=float, default=480, help='image size')
    args = parser.parse_args()

    args.blobs_dir = os.path.expanduser(os.path.expandvars(args.blobs_dir))
    if not os.path.isdir(args.blobs_dir):
        try:
            os.makedirs(args.blobs_dir)
        except Exception as error:
            print(f"{args.blobs_dir} Failed to create / Does Not Exist, cannot continue. (Error: {error})")
            exit(1)

    video_recorder = camera_commands.VideoRecorder(blobs_dir=args.blobs_dir, db_name=args.db_name,
                                                   table_name=args.table_name, camera_id=args.camera_id,
                                                   width=args.width, height=args.height, wait_time=args.video_size)

    video_recorder.start_recording()


    try:
        while True:
            command = input("Command (o to open feed, q to quit, h to update height, w to update width): ").strip()
            if command.lower()[0] == 'o':
                video_recorder.display_feed(height=args.height, width=args.width)
            elif command.lower()[0] == 'q':
                break
            elif command.lower()[0] == 'h':
                args.height = float(input("Updated height: "))
            elif command.lower()[0] == 'w':
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

