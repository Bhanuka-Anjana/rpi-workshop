# Native Picamera2 preview (QTGL) + YOLOv8 overlay
# Preview uses XBGR8888 (what QTGL supports). We convert to RGB for YOLO.

import os, platform, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO
import threading
import queue
from collections import deque

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
IMG_SIZE    = 416            # Reduced from 640 for faster inference
CONF_THRES  = 0.35
CAM_RES     = (1280, 720)
TARGET_FPS  = 30
OVERLAY_FPS = 15             # Increased for smoother display
BUFFER_SIZE = 3              # Size of frame buffers for threading
FRAME_SKIP  = 2              # Process every Nth frame for real-time performance
SMOOTHING_FACTOR = 0.8       # Temporal smoothing (0.0=none, 1.0=heavy)
# ====================

class FrameCapture(threading.Thread):
    """Dedicated thread for continuous frame capture"""
    def __init__(self, picam2, frame_queue, stop_event):
        super().__init__()
        self.picam2 = picam2
        self.frame_queue = frame_queue
        self.stop_event = stop_event
        self.daemon = True
        
    def run(self):
        while not self.stop_event.is_set():
            try:
                # Capture frame (XBGR8888) and convert to RGB
                xbgr = self.picam2.capture_array("main")
                rgb = xbgr[:, :, [3, 2, 1]].astype(np.uint8)
                rgb = np.ascontiguousarray(rgb)
                
                # Add frame to queue (non-blocking)
                if not self.frame_queue.full():
                    self.frame_queue.put(rgb, block=False)
                    
            except queue.Full:
                pass  # Skip frame if queue is full
            except Exception as e:
                if not self.stop_event.is_set():
                    print(f"Frame capture error: {e}")
                break

class YOLOProcessor(threading.Thread):
    """Dedicated thread for YOLO inference"""
    def __init__(self, model, frame_queue, result_queue, stop_event, img_size, conf_thres, frame_skip=1):
        super().__init__()
        self.model = model
        self.frame_queue = frame_queue
        self.result_queue = result_queue
        self.stop_event = stop_event
        self.img_size = img_size
        self.conf_thres = conf_thres
        self.frame_skip = frame_skip
        self.frame_count = 0
        self.daemon = True
        
    def run(self):
        while not self.stop_event.is_set():
            try:
                # Get frame from capture queue
                rgb = self.frame_queue.get(timeout=0.1)
                
                # Frame skipping for performance
                self.frame_count += 1
                if self.frame_count % self.frame_skip != 0:
                    continue  # Skip this frame
                
                # Run YOLO inference
                results = self.model(rgb)
                
                # Process results
                dets = []
                if results and len(results) > 0:
                    r = results[0]
                    names = r.names
                    for b in r.boxes:
                        x1, y1, x2, y2 = b.xyxy[0].tolist()
                        conf = float(b.conf[0])
                        cls = int(b.cls[0])
                        
                        if conf >= self.conf_thres:
                            dets.append((int(x1), int(y1), int(x2), int(y2), 
                                       f"{names[cls]} {conf:.2f}"))
                
                # Add results to result queue (non-blocking)
                if not self.result_queue.full():
                    self.result_queue.put((rgb, dets), block=False)
                    
            except queue.Empty:
                continue  # No frames to process
            except queue.Full:
                pass  # Skip if result queue is full
            except Exception as e:
                if not self.stop_event.is_set():
                    print(f"YOLO processing error: {e}")
                break

class DetectionSmoother:
    """Temporal smoothing for object detections to reduce jitter"""
    def __init__(self, smoothing_factor=0.8, max_history=5):
        self.smoothing_factor = smoothing_factor
        self.max_history = max_history
        self.detection_history = deque(maxlen=max_history)
        
    def smooth_detections(self, current_dets):
        """Apply temporal smoothing to detections"""
        self.detection_history.append(current_dets)
        
        if len(self.detection_history) < 2:
            return current_dets
            
        # Simple averaging across recent detections
        smoothed_dets = []
        for det in current_dets:
            x1, y1, x2, y2, label = det
            
            # Find similar detections in history
            similar_dets = []
            for hist_dets in self.detection_history:
                for hist_det in hist_dets:
                    hx1, hy1, hx2, hy2, hlabel = hist_det
                    # Check if detections are similar (same class, nearby position)
                    if (label.split()[0] == hlabel.split()[0] and
                        abs(x1 - hx1) < 50 and abs(y1 - hy1) < 50):
                        similar_dets.append(hist_det)
            
            if similar_dets:
                # Smooth coordinates
                avg_x1 = sum(d[0] for d in similar_dets) / len(similar_dets)
                avg_y1 = sum(d[1] for d in similar_dets) / len(similar_dets)
                avg_x2 = sum(d[2] for d in similar_dets) / len(similar_dets)
                avg_y2 = sum(d[3] for d in similar_dets) / len(similar_dets)
                
                # Apply smoothing
                smooth_x1 = int(x1 * (1 - self.smoothing_factor) + avg_x1 * self.smoothing_factor)
                smooth_y1 = int(y1 * (1 - self.smoothing_factor) + avg_y1 * self.smoothing_factor)
                smooth_x2 = int(x2 * (1 - self.smoothing_factor) + avg_x2 * self.smoothing_factor)
                smooth_y2 = int(y2 * (1 - self.smoothing_factor) + avg_y2 * self.smoothing_factor)
                
                smoothed_dets.append((smooth_x1, smooth_y1, smooth_x2, smooth_y2, label))
            else:
                smoothed_dets.append(det)
                
        return smoothed_dets

class PerformanceAdaptor:
    """Dynamically adjust settings based on performance"""
    def __init__(self, target_fps=15, adjustment_interval=3.0):
        self.target_fps = target_fps
        self.adjustment_interval = adjustment_interval
        self.last_adjustment = time.time()
        self.fps_history = deque(maxlen=8)
        self.current_skip = FRAME_SKIP
        self.current_img_size = IMG_SIZE
        
    def update_performance(self, fps):
        self.fps_history.append(fps)
        
        now = time.time()
        if now - self.last_adjustment >= self.adjustment_interval and len(self.fps_history) >= 5:
            avg_fps = sum(self.fps_history) / len(self.fps_history)
            
            # Adaptive adjustments
            if avg_fps < self.target_fps * 0.8:  # Performance too low
                if self.current_skip < 4:
                    self.current_skip += 1
                    print(f"Performance low ({avg_fps:.1f} FPS), increasing frame skip to {self.current_skip}")
                elif self.current_img_size > 320:
                    self.current_img_size = max(320, self.current_img_size - 96)
                    print(f"Reducing image size to {self.current_img_size}")
                    
            elif avg_fps > self.target_fps * 1.3:  # Can improve quality
                if self.current_skip > 1:
                    self.current_skip -= 1
                    print(f"Performance good ({avg_fps:.1f} FPS), reducing frame skip to {self.current_skip}")
                elif self.current_img_size < IMG_SIZE:
                    self.current_img_size = min(IMG_SIZE, self.current_img_size + 96)
                    print(f"Increasing image size to {self.current_img_size}")
                    
            self.last_adjustment = now
            
        return self.current_skip, self.current_img_size

def make_overlay(size_wh, dets, fps=None):
    w, h = size_wh
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    try: font = ImageFont.load_default()
    except: font = None

    # Optimized drawing - only show high confidence detections
    for (x1, y1, x2, y2, label) in dets:
        # Extract confidence from label
        parts = label.split()
        if len(parts) > 1:
            try:
                conf = float(parts[-1])
                if conf < 0.5:  # Skip low confidence detections
                    continue
            except ValueError:
                pass
        
        # Draw thinner rectangle for performance
        d.rectangle([x1, y1, x2, y2], outline=(0,255,0,255), width=2)
        
        # Only draw labels for larger boxes to reduce clutter
        box_area = (x2 - x1) * (y2 - y1)
        if box_area > 2000:  # Only label larger detections
            tw, th = d.textbbox((0,0), label, font=font)[2:]
            ylab = max(0, y1 - th - 4)
            d.rectangle([x1, ylab, x1 + tw + 4, ylab + th + 2], fill=(0,255,0,180))
            d.text((x1 + 2, ylab), label, fill=(0,0,0,255), font=font)

    # Simplified FPS display
    if fps is not None:
        s = f"FPS: {fps:.1f}"
        tw, th = d.textbbox((0,0), s, font=font)[2:]
        d.rectangle([8, 8, 8 + tw + 6, 8 + th + 4], fill=(0,0,0,140))
        d.text((10, 10), s, fill=(255,255,255,255), font=font)
    return np.array(img)  # RGBA8888

def main():
    # Camera: use XBGR8888 for QTGL preview
    picam2 = Picamera2()
    cfg = picam2.create_video_configuration(
        main={"format": "XBGR8888", "size": CAM_RES},
        controls={"FrameRate": TARGET_FPS},
        buffer_count=6  # Increased buffer for threading
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

    # Load models
    model = YOLO(MODEL_PATH)
    model.export(format="ncnn") 
    ncnn_model = YOLO("yolo11n_ncnn_model")

    W, H = CAM_RES
    
    # Threading setup
    stop_event = threading.Event()
    frame_queue = queue.Queue(maxsize=BUFFER_SIZE)
    result_queue = queue.Queue(maxsize=BUFFER_SIZE)
    
    # Start capture and processing threads
    capture_thread = FrameCapture(picam2, frame_queue, stop_event)
    processor_thread = YOLOProcessor(ncnn_model, frame_queue, result_queue, 
                                   stop_event, IMG_SIZE, CONF_THRES, FRAME_SKIP)
    
    capture_thread.start()
    processor_thread.start()
    
    # FPS tracking and overlay management
    t_prev, frames, shown_fps, last_overlay = time.time(), 0, 0.0, 0.0
    latest_dets = []  # Store latest detections
    
    # Initialize detection smoother
    smoother = DetectionSmoother(smoothing_factor=SMOOTHING_FACTOR)
    
    # Initialize performance adaptor
    adaptor = PerformanceAdaptor(target_fps=12)
    
    print(f"Optimized YOLO processing started. Press Ctrl+C to exit.")
    print(f"Settings: IMG_SIZE={IMG_SIZE}, FRAME_SKIP={FRAME_SKIP}, OVERLAY_FPS={OVERLAY_FPS}")
    
    try:
        while True:
            # Check for new detection results (non-blocking)
            try:
                rgb, dets = result_queue.get(block=False)
                # Apply temporal smoothing to reduce jitter
                latest_dets = smoother.smooth_detections(dets)
                result_queue.task_done()
            except queue.Empty:
                pass  # No new results, keep using latest_dets
            
            # FPS calculation and performance adaptation
            frames += 1
            now = time.time()
            if now - t_prev >= 1.0:
                shown_fps = frames / (now - t_prev)
                
                # Update performance adaptor
                current_skip, current_img_size = adaptor.update_performance(shown_fps)
                
                frames = 0
                t_prev = now
                print(f"Display FPS: {shown_fps:.1f}, "
                      f"Capture queue: {frame_queue.qsize()}, "
                      f"Result queue: {result_queue.qsize()}, "
                      f"Detections: {len(latest_dets)}")

            # Update overlay at higher rate for smoother display
            if now - last_overlay >= (1.0 / OVERLAY_FPS):
                overlay = make_overlay((W, H), latest_dets, fps=shown_fps)
                picam2.set_overlay(overlay)
                last_overlay = now

            # Reduced sleep for more responsive display
            time.sleep(0.003)

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Clean shutdown
        stop_event.set()
        
        # Wait for threads to finish
        capture_thread.join(timeout=2.0)
        processor_thread.join(timeout=2.0)
        
        # Cleanup
        picam2.set_overlay(None)
        picam2.stop()
        picam2.stop_preview()
        
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
