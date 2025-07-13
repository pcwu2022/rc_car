from flask import Flask, render_template_string, jsonify, request
import RPi.GPIO as GPIO
import time
import threading
import os

app = Flask(__name__)

# Motor control pins
MOTOR_L_PIN = 12
MOTOR_R_PIN = 13

# ESC settings
PWM_FREQUENCY = 50
MIN_THROTTLE = 5.0
MAX_THROTTLE = 10.0

class ESCController:
    def __init__(self, pin, frequency=PWM_FREQUENCY):
        self.pin = pin
        self.frequency = frequency
        self.pwm = None
        self.current_speed = 0
        self.lock = threading.Lock()
        
    def initialize(self):
        """Initialize PWM and set to neutral position"""
        self.pwm = GPIO.PWM(self.pin, self.frequency)
        self.pwm.start(MIN_THROTTLE)
        time.sleep(0.1)
        
    def set_speed(self, speed_percent):
        """Set motor speed (0-100%) - thread safe"""
        with self.lock:
            if self.pwm is None:
                return False
                
            # Clamp speed to valid range
            speed_percent = max(0, min(100, speed_percent))
            
            # Convert percentage to duty cycle
            duty_cycle = MIN_THROTTLE + (speed_percent / 100.0) * (MAX_THROTTLE - MIN_THROTTLE)
            
            self.pwm.ChangeDutyCycle(duty_cycle)
            self.current_speed = speed_percent
            return True
            
    def get_speed(self):
        """Get current speed - thread safe"""
        with self.lock:
            return self.current_speed
        
    def stop(self):
        """Stop the motor and cleanup PWM"""
        with self.lock:
            if self.pwm:
                self.pwm.ChangeDutyCycle(MIN_THROTTLE)
                time.sleep(0.1)
                self.pwm.stop()
                self.pwm = None

# Global motor controllers
motor_l = None
motor_r = None

def setup_gpio():
    """Initialize GPIO and motor controllers"""
    global motor_l, motor_r
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(MOTOR_L_PIN, GPIO.OUT)
    GPIO.setup(MOTOR_R_PIN, GPIO.OUT)
    
    # Initialize pins to LOW
    GPIO.output(MOTOR_L_PIN, GPIO.LOW)
    GPIO.output(MOTOR_R_PIN, GPIO.LOW)
    
    # Initialize motor controllers
    motor_l = ESCController(MOTOR_L_PIN)
    motor_r = ESCController(MOTOR_R_PIN)
    
    print("Initializing ESCs...")
    motor_l.initialize()
    motor_r.initialize()
    
    print("ESC arming sequence...")
    time.sleep(2)  # Wait for ESC to arm
    
    print("Motors ready!")

@app.route('/')
def index():
    """Serve the main control interface from an HTML file"""
    try:
        with open('./html/rc.html', 'r') as file:
            html_content = file.read()
        return render_template_string(html_content)
    except FileNotFoundError:
        return "Error: HTML template file not found. Please create the file at ./html/rc.html", 404
    except Exception as e:
        return f"Error loading template: {str(e)}", 500

@app.route('/adjust_speed', methods=['POST'])
def adjust_speed():
    """Adjust motor speed by a given amount"""
    try:
        data = request.json
        motor = data.get('motor')
        change = data.get('change', 0)
        
        if motor == 'left':
            current_speed = motor_l.get_speed()
            new_speed = max(0, min(100, current_speed + change))
            success = motor_l.set_speed(new_speed)
        elif motor == 'right':
            current_speed = motor_r.get_speed()
            new_speed = max(0, min(100, current_speed + change))
            success = motor_r.set_speed(new_speed)
        else:
            return jsonify({'success': False, 'message': 'Invalid motor specified'})
        
        if success:
            return jsonify({'success': True, 'speed': new_speed})
        else:
            return jsonify({'success': False, 'message': 'Failed to set motor speed'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/stop_all', methods=['POST'])
def stop_all():
    """Stop both motors"""
    try:
        motor_l.set_speed(0)
        motor_r.set_speed(0)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/max_speed', methods=['POST'])
def max_speed():
    """Set both motors to maximum speed"""
    try:
        motor_l.set_speed(100)
        motor_r.set_speed(100)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/status')
def get_status():
    """Get current motor speeds"""
    try:
        return jsonify({
            'left_speed': motor_l.get_speed(),
            'right_speed': motor_r.get_speed(),
            'success': True
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def cleanup():
    """Clean up GPIO on exit"""
    if motor_l:
        motor_l.stop()
    if motor_r:
        motor_r.stop()
    GPIO.cleanup()

if __name__ == '__main__':
    try:
        setup_gpio()
        print("Starting web server...")
        print("Access the control interface at: http://[your-pi-ip]:5000")
        print("Press Ctrl+C to stop")
        
        # Run Flask app
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cleanup()
        print("Cleanup complete.")