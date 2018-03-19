"""
MIT License

Copyright (c) 2018 Roger Cheng

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import configuration
import Adafruit_PCA9685

class adafruit_servo_wrapper:
  """
  Class that wraps the Adafruit PCA9685 servo control HAT with the motor
  interface expected by roverchassis class.

  Goal: Eventually have an abstract base class or interface shared with the
  other motor control classes. For more details see roboclaw_wrapper.py
  """

  def __init__(self):
    # Reference to the PWM controller object
    self.pwm = None

    # List mapping servo number (0 <= X <= 15) to a tuple
    # * first element of touple is the zero position pulse count
    # * second element of touple is the maximum angle.
    # * third element of touple is the pulse count for maximum angle.
    self.servoparams = list()

  @staticmethod
  def check_id(id):
    """
    Verifies that a given parameter is correctly formatted id for this motor
    controller class. For the servo HAT, it's a single number - the servo
    location 0 <= X <= 15
    """

    if not isinstance(id, int):
      raise ValueError("Adafruit Servo identifier must be an integer")

    if id < 0 or id > 15:
      raise ValueError("Adafruit Servo identifier {} out of accepted range 0 <= X <= 15".format(id[0]))

    return id

  def check_pwmhat(self):
    """
    Check to make sure we have an instance of the HAT controller. This should
    be called before every command.
    """
    if self.pwm == None:
      raise ValueError("Adafruit Servo HAT not yet connected")

  def connect(self):
    """
    Read configuration parameters and use them to create an instance of the
    Adafruit PWM control class.
    """

    # Load configuration file
    config = configuration.configuration("adafruit_servo")
    allparams = config.load()

    self.servoparams = allparams['servos']
    if len(self.servoparams) != 16:
      raise ValueError("Expected 16 servo parameters in configuration file, found {}".format(len(self.servoparams)))

    i2cbus = allparams['bus']
    i2caddr = allparams['address']
    self.pwm = Adafruit_PCA9685.PCA9685(address=i2caddr, busnum=i2cbus)

    self.pwm.set_pwm_freq(allparams['pwm_freq'])

  def version(self, id):
    """
    Returns a version string for display - the servo HAT doesn't really have
    anything unique to return so we're just going to display a fixed string
    """
    return "Adafruit Servo HAT"

  def power_percent(self, id, percentage):
    """
    Instructs the specified motor to the specified percentage of max power.
    100 is full forward, -100 is full reverse, 0 cuts power.
    """
    address = self.check_id(id)
    self.check_pwmhat()

    pct = int(percentage)
    if abs(pct) > 100:
      raise ValueError("Motor power percentage {0} outside valid range from 0 to 100.".format(pct))

    if pct == 0:
      # PWM zero cuts power instead of holding zero position
      pulse = 0
    else:
      pulsezero = self.servoparams[address][0]
      pulsemax = self.servoparams[address][2]
      pulse = int(pulsezero + (pct*(pulsemax-pulsezero))/100)

    self.pwm.set_pwm(address, 0, pulse)

  def init_velocity(self, id):
    """ Initializes controller for velocity - no-op in case of servo HAT. """
    return True

  def velocity(self, id, pct_velocity):
    """
    Very similar to power_percent for this servo HAT, except zero percent will
    try to hold at zero instead of cutting power.
    """
    address = self.check_id(id)
    self.check_pwmhat()

    pct = int(percentage)
    if abs(pct) > 100:
      raise ValueError("Motor power percentage {0} outside valid range from 0 to 100.".format(pct))

    pulsezero = self.servoparams[address][0]
    pulsemax = self.servoparams[address][2]
    pulse = int(pulsezero + (pct*(pulsemax-pulsezero))/100)

    self.pwm.set_pwm(address, 0, pulse)

  def init_angle(self, id):
    """ Initializes controller for angle - no-op in case of servo HAT. """
    return True

  def maxangle(self, id):
    """
    Returns the maximum steering angle. Callers should subtract a small margin
    for use in their calculation.
    """
    address = self.check_id(id)

    return self.servoparams[address][1]

  def angle(self, id, angle):
    """
    Moves the identified servo to the specified angle expressed in number of
    degrees off zero center, positive clockwise.
    """
    address = self.check_id(id)
    self.check_pwmhat()

    pulsezero, anglemax, pulsemax = self.servoparams[address]

    if abs(angle) > anglemax:
      raise ValueError("Angle {} exceeds maximum allowable up to {} degrees off center".format(angle,anglemax))

    fraction = float(angle)/anglemax
    pulse = int(pulsezero + fraction*(pulsemax-pulsezero))

    self.pwm.set_pwm(address, 0, pulse)

  def steer_setzero(self, id):
    """
    Sets the current servo angle to the new zero.
    """
    raise NotImplementedError("Steering servo trim not implemented yet")

  def input_voltage(self, id):
    """
    Read the input voltage available to drive specified motor.
    """
    return "Not Available"
