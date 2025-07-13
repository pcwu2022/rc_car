import RPi.GPIO as GPIO
import time

BUTTON_PIN = 14
MOTOR_L_PIN = 12
MOTOR_R_PIN = 13

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN)
    GPIO.setup(MOTOR_L_PIN, GPIO.OUT)
    GPIO.setup(MOTOR_R_PIN, GPIO.OUT)
    GPIO.output(MOTOR_L_PIN, GPIO.LOW)
    GPIO.output(MOTOR_R_PIN, GPIO.LOW)

def is_button_pressed():
    return GPIO.input(BUTTON_PIN) == GPIO.HIGH

def pwm_motor(speed):
    pwm_l = GPIO.PWM(MOTOR_L_PIN, 40)
    pwm_r = GPIO.PWM(MOTOR_R_PIN, 40)
    pwm_l.start(speed)
    pwm_r.start(speed)
    time.sleep(1)  # Run for 1 second
    pwm_l.stop()
    pwm_r.stop()

def loop():
    motor_speed = 0
    if is_button_pressed():
        motor_speed = (motor_speed + 20) % 80
        print(f"Motor speed set to: {motor_speed}")
        pwm_motor(motor_speed)

if __name__ == "__main__":
    setup()
    try:
        while True:
            loop()
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()