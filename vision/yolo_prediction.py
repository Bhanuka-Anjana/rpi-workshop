# Native Picamera2 preview (QTGL) + YOLOv8 overlay
# Preview uses XBGR8888 (what QTGL supports). We convert to RGB for YOLO.

import os, platform, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

# --- Ensure Qt uses system plugins (avoid cv2 plugin clash) ---
os.environ.pop("QT_PLUGIN_PATH", None)
arch = platform.machine().lower()
if "aarch64" in arch:
    os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", "/usr/lib/aarch64-linux-gnu/qt5/plugins")
else:
    os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", "/usr/lib/arm-linux-gnueabihf/qt5/plugins")

from picamera2 import Picamera2, Preview

# ===== Settings =====
MODEL_PATH  = "yolo11n.pt"
IMG_SIZE    = 640            # try 416 or 320 for more FPS
CONF_THRES  = 0.35
CAM_RES     = (1280, 720)
TARGET_FPS  = 30
OVERLAY_FPS = 10
# ====================

def make_overlay(size_wh, dets, fps=None):
    w, h = size_wh
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    try: font = ImageFont.load_default()
    except: font = None

    for (x1, y1, x2, y2, label) in dets:
        d.rectangle([x1, y1, x2, y2], outline=(0,255,0,255), width=3)
        tw, th = d.textbbox((0,0), label, font=font)[2:]
        ylab = max(0, y1 - th - 6)
        d.rectangle([x1, ylab, x1 + tw + 6, ylab + th + 4], fill=(0,255,0,200))
        d.text((x1 + 3, ylab + 2), label, fill=(0,0,0,255), font=font)

    if fps is not None:
        s = f"FPS: {fps:.1f}"
        tw, th = d.textbbox((0,0), s, font=font)[2:]
        d.rectangle([8, 8, 8 + tw + 8, 8 + th + 8], fill=(0,0,0,120))
        d.text((12, 12), s, fill=(255,255,255,255), font=font)
    return np.array(img)  # RGBA8888

def main():
    # Camera: use XBGR8888 for QTGL preview
    picam2 = Picamera2()
    cfg = picam2.create_video_configuration(
        main={"format": "XBGR8888", "size": CAM_RES},
        controls={"FrameRate": TARGET_FPS},
        buffer_count=4
    )
    picam2.configure(cfg)

    # Start native preview (QTGL → QT → DRM fallback)
    try:
        picam2.start_preview(Preview.QTGL)
    except Exception as e1:
        print("QTGL failed, falling back to QT:", e1)
        try:
            picam2.start_preview(Preview.QT)
        except Exception as e2:
            print("QT failed, falling back to DRM (local console required):", e2)
            picam2.start_preview(Preview.DRM)

    picam2.start()
    time.sleep(0.2)

    model = YOLO(MODEL_PATH)

    W, H = CAM_RES
    t_prev, frames, shown_fps, last_overlay = time.time(), 0, 0.0, 0.0

    try:
        while True:
            # Grab preview frame (XBGR8888). Convert to RGB for YOLO.
            xbgr = picam2.capture_array("main")                # H x W x 4 (X,B,G,R)
            rgb  = xbgr[:, :, [3, 2, 1]].astype(np.uint8)      # -> H x W x 3 (R,G,B)
            rgb  = np.ascontiguousarray(rgb)

            results = model.predict(
                rgb, imgsz=IMG_SIZE, conf=CONF_THRES, device="cpu", verbose=False
            )

            dets = []
            if results and len(results) > 0:
                r = results[0]; names = r.names
                for b in r.boxes:
                    x1, y1, x2, y2 = b.xyxy[0].tolist()
                    conf = float(b.conf[0]); cls = int(b.cls[0])
                    x1 = max(0, min(int(x1), W-1)); y1 = max(0, min(int(y1), H-1))
                    x2 = max(0, min(int(x2), W-1)); y2 = max(0, min(int(y2), H-1))
                    dets.append((x1, y1, x2, y2, f"{names[cls]} {conf:.2f}"))

            # FPS
            frames += 1
            now = time.time()
            if now - t_prev >= 1.0:
                shown_fps = frames / (now - t_prev)
                frames = 0
                t_prev = now

            # Overlay throttled to save CPU
            if now - last_overlay >= (1.0 / OVERLAY_FPS):
                overlay = make_overlay((W, H), dets, fps=shown_fps)
                picam2.set_overlay(overlay)
                last_overlay = now

            time.sleep(0.001)

    except KeyboardInterrupt:
        pass
    finally:
        picam2.set_overlay(None)
        picam2.stop()
        picam2.stop_preview()

if __name__ == "__main__":
    main()
