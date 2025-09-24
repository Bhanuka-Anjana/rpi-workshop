# file: cam_preview.py
# Shows a live camera preview with FPS. Press 'q' to quit.

import time
import cv2
from picamera2 import Picamera2

def main():
    picam2 = Picamera2()

    # 1280x720 @ ~30 fps is a good, light test
    video_config = picam2.create_video_configuration(
        main={"size": (1280, 720)},
        controls={"FrameRate": 30.0},
    )
    picam2.configure(video_config)
    picam2.start()

    last_time = time.time()
    frames = 0
    fps = 0.0

    try:
        while True:
            frame = picam2.capture_array()  # numpy array (RGB)
            frames += 1

            now = time.time()
            if now - last_time >= 1.0:
                fps = frames / (now - last_time)
                frames = 0
                last_time = now

            # Put FPS text on the frame
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            cv2.imshow("Pi Camera Preview (press 'q' to quit)", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cv2.destroyAllWindows()
        picam2.stop()

if __name__ == "__main__":
    main()
