import RPi.GPIO as GPIO
import time

BUTTON_PIN = 14

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN)

def is_button_pressed():
    return GPIO.input(BUTTON_PIN) == GPIO.HIGH

def loop():
    try:
        while True:
            if is_button_pressed():
                print("Button Pressed!")
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    setup()
    loop()