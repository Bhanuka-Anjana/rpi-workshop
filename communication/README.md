# UART Communication - Raspberry Pi Workshop

This project demonstrates UART (Universal Asynchronous Receiver-Transmitter) serial communication on Raspberry Pi using Python to send data and control RGB LEDs.

## 🔧 Hardware Setup

### UART Pins on Raspberry Pi:
- **GPIO14 (Pin 8)**: UART TX (Transmit)
- **GPIO15 (Pin 10)**: UART RX (Receive)
- **Ground (Pin 6)**: Common ground

### Connection Example:
```
Raspberry Pi → External Device/Arduino/ESP32
GPIO14 (TX)  → RX of external device
GPIO15 (RX)  → TX of external device
Ground       → Ground
```

## ⚙️ System Setup

### 1. Enable UART Interface

Configure the Raspberry Pi to enable UART communication:

```bash
# Open Raspberry Pi configuration
sudo raspi-config

# Navigate to:
# Interface Options → Serial
#  - "Login shell over serial?" → No
#  - "Enable serial port hardware?" → Yes

# Reboot to apply changes
sudo reboot
```

### 2. Install Python Serial Library

Install the required Python serial library:

```bash
# Update package list
sudo apt update

# Install python3-serial
sudo apt install -y python3-serial
```

### 3. Verify UART Setup

Check if UART is properly enabled:

```bash
# Check if serial port exists
ls -l /dev/serial*

# Should show:
# /dev/serial0 -> ttyAMA0  (or similar)

# Test UART functionality
dmesg | grep tty
```

## 💻 Software Implementation

### Script 1: RGB LED Control (`uart_control_rgb.py`)

Controls RGB LEDs by sending color values via UART:

**Features:**
- Sends RGB color bytes (Red, Green, Blue)
- Cycles through primary colors
- Uses `/dev/serial0` for stable UART access
- 115200 baud rate for reliable communication

**Color Sequence:**
1. Red: `[0xFF, 0x00, 0x00]`
2. Green: `[0x00, 0xFF, 0x00]`  
3. Blue: `[0x00, 0x00, 0xFF]`

### Script 2: Basic UART Send (`uart_send.py`)

Demonstrates basic UART data transmission:

**Features:**
- Sends binary data via UART
- Continuous transmission loop
- Serial port management with proper cleanup

## 🚀 Running the Scripts

### RGB LED Control:
```bash
cd /path/to/communication/
python3 uart_control_rgb.py
```

### Basic UART Send:
```bash
python3 uart_send.py
```

### Stop Scripts:
Press `Ctrl+C` to stop any running script safely.

## 📊 UART Configuration Details

### Serial Port Settings:
```python
serial.Serial(
    '/dev/serial0',    # UART device (stable alias)
    baudrate=115200,   # Communication speed
    timeout=1          # Read timeout in seconds
)
```

### 3. Check Serial Port Status

```bash
# List all serial devices
ls -l /dev/tty*

# Check UART-specific devices
ls -l /dev/serial*

# View serial port information
dmesg | grep -i uart
```

## 🛠️ Troubleshooting

### Common Issues:

1. **Permission Denied:**
   ```bash
   # Add user to dialout group
   sudo usermod -a -G dialout $USER
   # Logout and login again
   ```

2. **Serial Port Not Found:**
   ```bash
   # Check if UART is enabled in config
   cat /boot/config.txt | grep enable_uart
   # Should show: enable_uart=1
   ```

3. **Port Already in Use:**
   ```bash
   # Check what's using the port
   sudo lsof /dev/serial0
   
   # Kill conflicting processes
   sudo pkill -f "process_name"
   ```

4. **No Data Transmission:**
   ```bash
   # Verify wiring connections
   # Check baud rate matching on both devices
   # Ensure common ground connection
   ```

## 📝 Code Examples

### Basic UART Write:
```python
import serial
import time

ser = serial.Serial('/dev/serial0', 115200, timeout=1)
time.sleep(0.1)  # Port settle time

# Send string data
ser.write("Hello World\r\n".encode())
ser.flush()

ser.close()
```

### UART Read/Write:
```python
import serial

ser = serial.Serial('/dev/serial0', 115200, timeout=1)

# Send command
ser.write("GET_STATUS\r\n".encode())
ser.flush()

# Read response
response = ser.readline().decode().strip()
print(f"Received: {response}")

ser.close()
```

### Binary Data Transmission:
```python
import serial

ser = serial.Serial('/dev/serial0', 115200, timeout=1)

# Send binary data (bytes)
data = bytes([0x01, 0x02, 0x03, 0xFF])
ser.write(data)
ser.flush()

ser.close()
```


