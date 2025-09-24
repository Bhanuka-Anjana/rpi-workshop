# Vision Module - Camera & Object Detection Guide

This guide will help beginners set up camera functionality and YOLO object detection on Raspberry Pi.

## 📷 Camera Connection Methods

### 1. CSI Camera Interface (Recommended)
- **What we're using**: CSI (Camera Serial Interface) connection
- **Advantages**: 
  - Higher performance and lower latency
  - Direct hardware integration with Raspberry Pi
  - Better frame rates and image quality
  - Lower CPU usage compared to USB cameras

### 2. Alternative: USB Web Camera
- Connect any USB webcam to Raspberry Pi USB ports
- Generally slower than CSI but more flexible
- Plug-and-play compatibility with most USB cameras

---

## 🐍 Python Virtual Environment Setup

### Step 1: Create Virtual Environment
```bash
# Navigate to the vision directory
cd /home/bhanu/Desktop/test/vision

# Create a new virtual environment
python3 -m venv venv_vision

# Alternative method using virtualenv
# sudo apt install python3-virtualenv
# virtualenv venv_vision
```

### Step 2: Activate Virtual Environment
```bash
# Activate the environment
source venv_vision/bin/activate

# You should see (venv_vision) in your terminal prompt
```

### Step 3: Deactivate Virtual Environment
```bash
# When you're done working
deactivate
```

---

## 📦 Required Packages Installation

### Essential Packages
```bash
# Make sure virtual environment is activated
source venv_vision/bin/activate

# Update pip first
pip install --upgrade pip

# Core packages for camera and vision
pip install picamera2
pip install opencv-python
pip install numpy
pip install pillow

# YOLO and AI packages
pip install ultralytics
pip install torch torchvision

# Additional utilities
pip install threading-utils
```

### System Dependencies (if needed)
```bash
# Install system packages (outside virtual environment)
sudo apt update
sudo apt install python3-dev python3-pip
sudo apt install libcamera-apps
sudo apt install python3-opencv
```

---

## 🚀 Step-by-Step Testing Guide

### Step 1: Test Camera Connection
```bash
# Activate virtual environment
source venv_vision/bin/activate

# Test basic camera preview
python3 cam_preview.py
```

**Expected Result**: You should see a live camera preview window. Press `Ctrl+C` to exit.

**Troubleshooting**:
- If camera not detected: Check CSI cable connection
- If permission error: Add user to video group: `sudo usermod -a -G video $USER`
- Reboot if needed: `sudo reboot`

### Step 2: Run Basic YOLO Detection
```bash
# Run standard YOLO detection
python3 yolo_prediction.py
```

**What it does**:
- Loads YOLOv11 model
- Processes camera frames
- Displays bounding boxes around detected objects
- Shows confidence scores and class names

### Step 3: Run High-Performance Detection
```bash
# Run optimized fast detection
python3 yolo_prediction_fast.py
```

---

## ⚡ Performance Optimizations in Fast Version

### Key Improvements for Higher FPS:

#### 1. **Multi-threading Architecture**
- **Dedicated Capture Thread**: Continuous frame capture without blocking
- **Dedicated Processing Thread**: YOLO inference runs separately
- **Non-blocking Queues**: Prevents bottlenecks between threads

#### 2. **NCNN Model Optimization**
- **Compressed Model**: Uses NCNN format optimized for ARM processors
- **Smaller Input Size**: 416x416 instead of 640x640 pixels
- **Faster Inference**: 2-3x speed improvement on Raspberry Pi

#### 3. **Frame Management**
- **Frame Skipping**: Processes every 2nd frame (configurable)
- **Buffer Management**: Smart queue handling prevents memory overflow
- **Adaptive Performance**: Automatically adjusts settings based on FPS

#### 4. **Display Optimizations**
- **Selective Rendering**: Only shows high-confidence detections
- **Reduced Overlay Updates**: Updates display at 15 FPS while processing at 30 FPS
- **Optimized Drawing**: Thinner lines and selective labeling

#### 5. **Temporal Smoothing**
- **Detection Smoothing**: Reduces bounding box jitter
- **Historical Averaging**: Uses previous detections for stability

### Performance Comparison:
- **Standard Version**: ~8-12 FPS
- **Fast Version**: ~15-25 FPS
- **Improvement**: 2-3x faster processing

---

## 📋 File Structure

```
vision/
├── README.md                    # This guide
├── cam_preview.py              # Basic camera test
├── yolo_prediction.py          # Standard YOLO detection
├── yolo_prediction_fast.py     # Optimized high-FPS detection
├── yolo11n.pt                  # YOLO model file
├── yolo11n.torchscript         # TorchScript version
├── yolo11n_ncnn_model/         # Optimized NCNN model
└── yolov8n_ncnn_model/         # Alternative NCNN model
```

---

## 🔧 Configuration Options

### Adjustable Parameters in Fast Version:
```python
IMG_SIZE = 416          # Input image size (lower = faster)
CONF_THRES = 0.35      # Confidence threshold
TARGET_FPS = 30        # Target frame rate
OVERLAY_FPS = 15       # Display update rate
FRAME_SKIP = 2         # Process every Nth frame
SMOOTHING_FACTOR = 0.8 # Detection smoothing (0-1)
```

---

## 🐛 Common Issues & Solutions

### Camera Issues:
```bash
# Check camera status
vcgencmd get_camera

# Enable camera interface
sudo raspi-config
# Navigate to Interface Options > Camera > Enable
```

### Performance Issues:
- **Low FPS**: Increase `FRAME_SKIP` or reduce `IMG_SIZE`
- **High CPU Usage**: Enable GPU memory split: `sudo raspi-config` > Advanced > Memory Split > 128
- **Memory Errors**: Reduce `BUFFER_SIZE` in fast version

### Package Issues:
```bash
# If ultralytics installation fails
pip install --upgrade setuptools wheel
pip install ultralytics --no-deps
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

---

## 📚 Additional Resources

- **Ultralytics Raspberry Pi Guide**: https://docs.ultralytics.com/guides/raspberry-pi/#set-up-ultralytics
- **Picamera2 Documentation**: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
- **YOLO Model Zoo**: https://github.com/ultralytics/ultralytics

---

## 🎯 Quick Start Summary

1. **Setup Environment**:
   ```bash
   python3 -m venv venv_vision
   source venv_vision/bin/activate
   pip install picamera2 ultralytics opencv-python
   ```

2. **Test Camera**:
   ```bash
   python3 cam_preview.py
   ```

3. **Run Detection**:
   ```bash
   # Standard version
   python3 yolo_prediction.py
   
   # Fast optimized version
   python3 yolo_prediction_fast.py
   ```

4. **For Best Performance**: Use `yolo_prediction_fast.py` with NCNN optimization

---

*Happy coding! 🚀 For questions or issues, refer to the troubleshooting section above.*
