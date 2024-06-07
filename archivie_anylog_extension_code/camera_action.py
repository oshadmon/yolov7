import argparse



def main():
    """
    Generate live camera feeds (broken every N seconds) and either store them to file or publish them directly into
    AnyLog / EdgeLake via REST
    :positional arguments:
        db_name               database name
    :optional arguments:
        -h, --help                      show this help message and exit
        --table-name    TABLE_NAME      table to store live feed name - if no table then each file will be
        --camera-id     CAMERA_ID       Camera ID
        --width         WIDTH           Live feed screen ratio width
        --height        HEIGHT          Live feed screen ratio height
        --cut-video     CUT_VIDEO       Video size (in seconds)
        --blobs-dir     BLOBS_DIR       Directory to store videos cuts and insight
        --rest-conn     REST_CONN       REST connection info
        --rest-topic    REST_TOPIC      Topic associated with REST command
    :params:
        video_recorder:VideoRecorder - process to record video(s)
        command:str - user defined command to execute in parallel to live images
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('db_name', type=str, default='new_company', help='database name')
    parser.add_argument('--table-name', type=str, default=None, help='table to store live feed name - if no table then each file will be ')
    parser.add_argument('--camera-id', type=int, default=get_default_camera_id(), help='Camera ID')
    parser.add_argument('--width', type=float, default=640, help='Live feed screen ratio width')
    parser.add_argument('--height', type=float, default=480, help='Live feed screen ratio height')
    parser.add_argument('--cut-video', type=int, default=10, help='Video size (in seconds)')
    parser.add_argument('--blobs-dir', type=str, default=BLOBS_DIR, help='Directory to store videos cuts and insight')
    parser.add_argument('--rest-conn', type=str, default=None, help='REST connection info')
    parser.add_argument('--rest-topic', default='livefeed', help='Topic associated with REST command')
    args = parser.parse_args()

    args.blobs_dir = os.path.expanduser(os.path.expandvars(args.blobs_dir))
    os.makedirs(args.blobs_dir, exist_ok=True)

    video_recorder = VideoRecorder(blobs_dir=args.blobs_dir, db_name=args.db_name, table_name=args.table_name,
                                   rest_conn=args.rest_conn, rest_topic=args.rest_topic, camera_id=args.camera_id,
                                   width=args.width, height=args.height, wait_time=args.cut_video)

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
