# GPIO LED Control - Raspberry Pi Workshop

This project demonstrates basic GPIO control on Raspberry Pi using Python to toggle an LED and configure it to auto-start on boot.


### Circuit Connection:
```
Raspberry Pi GPIO18 → 220Ω Resistor → LED (+) → LED (-) → Ground
```

**Pin Configuration:**
- GPIO Pin: BCM 18 (Physical pin 12)
- Ground: Any ground pin

## 🚀 Running the Script

### Manual Execution:
```bash
cd /path/to/gpio/
python3 led_blink_rpigpio.py
```

### Stop the script:
Press `Ctrl+C` to stop the program safely.

## ⚡ Auto-Start on Boot Setup

### 1. systemd Service Configuration

The project includes a systemd service file (`ledblink.service`) to automatically start the LED blinking when the Raspberry Pi boots up.

**Service Configuration:**
- **Service Name:** `ledblink.service`
- **User:** {user123} (update to your username)
- **Working Directory:** `/home/{user123}/your_working directory...` (update to your path)
- **Auto-restart:** On failure

### 2. Installation Commands

Execute these commands to set up auto-start:

```bash
# Enable + start now:
sudo systemctl daemon-reload
sudo systemctl enable --now ledblink.service

# Check status / logs:
systemctl --no-pager status ledblink.service
journalctl -u ledblink.service -e

# Stop / disable later:
sudo systemctl stop ledblink.service
sudo systemctl disable ledblink.service
```

