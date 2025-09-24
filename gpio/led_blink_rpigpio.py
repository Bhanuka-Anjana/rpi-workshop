import RPi.GPIO as GPIO
import time

try:
    GPIO.setmode(GPIO.BCM)
    led_pin = 18
    GPIO.setup(led_pin, GPIO.OUT)

    while True:
        GPIO.output(led_pin, GPIO.HIGH) # Turn LED on
        time.sleep(1)
        GPIO.output(led_pin, GPIO.LOW)  # Turn LED off
        time.sleep(1)

except KeyboardInterrupt:
    print("Exiting program.")

finally:
    GPIO.cleanup() # Clean up GPIO settings on exit