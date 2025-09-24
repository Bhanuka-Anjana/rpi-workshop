#!/usr/bin/env python3
import time
import serial

# /dev/serial0 points to the 40-pin header UART (stable alias)
ser = serial.Serial('/dev/serial0', baudrate=115200, timeout=1)

# Small delay lets the port settle after open
time.sleep(0.1)

while True:
    ser.write(bytes([0xff, 0x00, 0x00])) # "r,g,b"
    ser.flush()
    time.sleep(1)
    ser.write(bytes([0x00, 0xff, 0x00])) # "r,g,b"
    ser.flush()
    time.sleep(1)
    ser.write(bytes([0x00, 0x00, 0xff])) # "r,g,b"
    ser.flush()
    time.sleep(1)

ser.close()
