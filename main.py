import RPi.GPIO as GPIO
import time

BUTTON_PIN = 14
MOTOR_L_PIN = 12
MOTOR_R_PIN = 13

# ESC expects 50Hz PWM (standard servo frequency)
PWM_FREQUENCY = 50

# PWM duty cycle ranges for ESC control
# These values may need adjustment based on your specific ESC calibration
MIN_THROTTLE = 5.0   # ~1ms pulse width (stop/neutral)
MAX_THROTTLE = 10.0  # ~2ms pulse width (full throttle)

class ESCController:
    def __init__(self, pin, frequency=PWM_FREQUENCY):
        self.pin = pin
        self.frequency = frequency
        self.pwm = None
        self.current_speed = 0
        
    def initialize(self):
        """Initialize PWM and set to neutral position"""
        self.pwm = GPIO.PWM(self.pin, self.frequency)
        self.pwm.start(MIN_THROTTLE)  # Start at neutral/stop position
        time.sleep(0.1)  # Allow ESC to recognize signal
        
    def set_speed(self, speed_percent):
        """Set motor speed (0-100%)"""
        if self.pwm is None:
            return
            
        # Clamp speed to valid range
        speed_percent = max(0, min(100, speed_percent))
        
        # Convert percentage to duty cycle
        duty_cycle = MIN_THROTTLE + (speed_percent / 100.0) * (MAX_THROTTLE - MIN_THROTTLE)
        
        self.pwm.ChangeDutyCycle(duty_cycle)
        self.current_speed = speed_percent
        
    def stop(self):
        """Stop the motor and cleanup PWM"""
        if self.pwm:
            self.pwm.ChangeDutyCycle(MIN_THROTTLE)
            time.sleep(0.1)
            self.pwm.stop()
            self.pwm = None

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Added pull-down resistor
    GPIO.setup(MOTOR_L_PIN, GPIO.OUT)
    GPIO.setup(MOTOR_R_PIN, GPIO.OUT)
    
    # Initialize pins to LOW
    GPIO.output(MOTOR_L_PIN, GPIO.LOW)
    GPIO.output(MOTOR_R_PIN, GPIO.LOW)

def is_button_pressed():
    return GPIO.input(BUTTON_PIN) == GPIO.HIGH

def debounce_button():
    """Simple button debouncing"""
    if is_button_pressed():
        time.sleep(0.05)  # 50ms debounce
        return is_button_pressed()
    return False

def main():
    setup()
    
    # Initialize ESC controllers
    motor_l = ESCController(MOTOR_L_PIN)
    motor_r = ESCController(MOTOR_R_PIN)
    
    try:
        print("Initializing ESCs...")
        motor_l.initialize()
        motor_r.initialize()
        
        # ESC calibration/arming sequence
        print("ESC arming sequence...")
        time.sleep(2)  # Wait for ESC to arm
        
        motor_speed = 0
        last_button_time = 0
        button_pressed = False
        
        print("ESC ready. Press button to increase speed.")
        print("Current speed: 0%")
        
        while True:
            current_time = time.time()
            
            # Check for button press with debouncing and rate limiting
            if debounce_button() and not button_pressed and (current_time - last_button_time > 0.5):
                button_pressed = True
                last_button_time = current_time
                
                # Increment speed in 20% steps
                motor_speed = (motor_speed + 20) % 101  # 0, 20, 40, 60, 80, 100, 0...
                
                print(f"Motor speed set to: {motor_speed}%")
                motor_l.set_speed(motor_speed)
                motor_r.set_speed(motor_speed)
                
            elif not is_button_pressed():
                button_pressed = False
                
            time.sleep(0.01)  # 10ms loop delay
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Proper cleanup
        print("Stopping motors...")
        motor_l.stop()
        motor_r.stop()
        GPIO.cleanup()
        print("Cleanup complete.")

if __name__ == "__main__":
    main()