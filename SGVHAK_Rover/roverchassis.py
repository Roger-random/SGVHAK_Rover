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
import math
import logging
import configuration
import roboclaw_wrapper
import adafruit_servo_wrapper

# Python 2 does not have a constant for infinity. (Python 3 added math.inf.)
infinity = float("inf")

class roverwheel:
  """
  Rover wheel class tracks information specific to a particular wheel on
  the chassis.
  """
  def __init__(self, name, x=0, y=0, rollingcontrol=None,rollingparam=None,
    steeringcontrol=None, steeringparam=None):

    # String is used to identify this wheel in various operations. Bonus if
    # the words make sense to a human reader ('front_left') but not required.
    self.name = name

    # X,Y coordinate of this wheel on the rover chassis, relative to center.
    self.x = x
    self.y = y

    # Rolling velocity motor (optional): a reference to the control object and
    # the parameters to identify this wheel to the control.
    self.rollingcontrol = rollingcontrol
    self.rollingparam = rollingparam

    # Steering angle motor (optiona): similar to the above, but for steering.
    self.steeringcontrol = steeringcontrol
    self.steeringparam = steeringparam

    # The most recently commanded steering angle and rolling velocity
    self.angle = 0
    self.velocity = 0

    # If we were given a rolling velocity control, run any initialization we
    # need and obtain its label string to show to user.
    if self.rollingcontrol:
      self.rollingcontrol.init_velocity(self.rollingparam)
      try:
        self.rollinglabel = self.rollingcontrol.version(self.rollingparam)
      except ValueError as ve:
        self.rollinglabel = "(No Response)"

    # Repeat the above, this time for steering angle control.
    if self.steeringcontrol:
      self.steeringcontrol.init_angle(self.steeringparam)
      try:
        self.steeringlabel = self.steeringcontrol.version(self.steeringparam)
      except ValueError as ve:
        self.steeringlabel = "(No Response)"

  def poweroff(self):
    """
    Instructs the motor controller to stop rolling, stop holding position,
    whatever is the least-effort situation. (If applicable)
    """
    self.velocity = 0
    if self.rollingcontrol:
      self.rollingcontrol.power_percent(self.rollingparam, 0)

    # Killing the power leaves the angle wherever it was last (except as
    # moved by external forces) so leave self.angle alone.
    if self.steeringcontrol:
      self.steeringcontrol.power_percent(self.steeringparam, 0)

  def anglevelocity(self):
    """
    Send the dictated angle and velocity to their respective controls
    """
    if self.rollingcontrol:
      self.rollingcontrol.velocity(self.rollingparam, self.velocity)

    if self.steeringcontrol:
      self.steeringcontrol.angle(self.steeringparam, self.angle)

  def steerto(self, angle):
    """
    Steer this wheel to the specified angle. Caller is responsible for
    validation of all parameters.
    """
    self.steeringcontrol.angle(self.steeringparam, angle)

  def steersetzero(self):
    """
    Set the current steering angle of this wheel as the new zero. Caller is
    responsible for validation of all parameters
    """
    self.steeringcontrol.steer_setzero(self.steeringparam)

  def motor_voltage(self):
    """
    Query the rolling and steering motor controllers for their current input
    voltage levels
    """
    voltages = dict()

    if self.rollingcontrol:
      voltages["Rolling"] = self.rollingcontrol.input_voltage(self.rollingparam)
    else:
      voltages["Rolling"] = "Not Applicable"

    if self.steeringcontrol:
      voltages["Steering"] = self.steeringcontrol.input_voltage(self.steeringparam)
    else:
      voltages["Steering"] = "Not Applicable"

    return voltages

class chassis:
  """
  Rover chassis class tracks the physical geometry of the chassis and uses
  that informaton to calculate Ackerman steering angles and relative
  velocity for wheel travel
  """

  def __init__(self):
    # List of wheels
    # Each wheel is a dictionary mapping name of a wheel to its specific info.
    self.wheels = dict()

    # When turning radius grows beyond this point, the wheel angles are so
    #   miniscule it is indistinguishable from straight line travel.
    self.maxRadius = 250 # TODO: calculate based on chassis configuration.

    # Radius representing the tightest turn this chassis can make. Minimum
    #   value of zero indicates chassis is capable of turning in place.
    self.minRadius = 17.75 # TODO: calculate based on chassis configuration.

    # The current (velocity, radius) that dictated wheel angle and velocity.
    #   Velocity unit is up to the caller, math works regardless of units
    #     inches, metric, quadrature pulses, etc.
    #   Radius unit must match those used to specify wheel coordinates.
    self.currentMotion = (0, infinity)

    # A dictionary mapping a name string identifying a motor controller type
    #   to an instance of the motor controller.
    self.motorcontrollers = dict()

  def init_motorcontrollers(self):
    """
    Creates the dictionary where a name in the configuration file can be
    matched with its corresponding motor controller.
    """
    try:
      # Each instance of this class represents one group of RoboClaw connected
      # together on the same packet serial network. Up to eight addressible
      # RoboClaws and two motors per controller = up to 16 motors.
      rclaw = roboclaw_wrapper.roboclaw_wrapper()
      rclaw.connect()
      self.motorcontrollers['roboclaw'] = rclaw
    except ValueError as ve:
      logging.getLogger(__name__).error("Unable to initialize roboclaw: %s",str(ve))

    try:
      asw = adafruit_servo_wrapper.adafruit_servo_wrapper()
      asw.connect()
      self.motorcontrollers['adafruit_servo'] = asw
    except StandardError as se:
      logging.getLogger(__name__).error("Unable to initialize Adafruit Servo HAT library: %s",str(se))

  def ensureready(self):
    """
    Makes sure this chassis class is ready for work by ensuring the required
    information is loaded and ready.
    """
    if len(self.wheels) > 0:
      return

    # Initialize motor controller dictionary.
    self.init_motorcontrollers()

    # Load configuration from JSON.
    config = configuration.configuration("roverchassis")
    wheeljson = config.load()

    # Using the data in configuration JSON file, create a wheel object.
    for wheel in wheeljson:
      # Retrieve name and verify uniqueness.
      name = wheel['name']
      if name in self.wheels:
        raise ValueError("Duplicate wheel name {} encountered.".format(name))

      # Initialize all optional motor control values to None
      steeringcontrol = None
      steeringparam = None
      rollingcontrol = None
      rollingparam = None

      # Fill in any rolling velocity motor control and associated parameters
      rolling = wheel['rolling']
      if rolling:
        rollingtype = rolling[0]
        if len(rolling) == 2:
          rollingparam = rolling[1]
        else:
          rollingparam = rolling[1:]
        if rollingtype in self.motorcontrollers:
          rollingcontrol = self.motorcontrollers[rollingtype]
        else:
          raise ValueError("Unknown motor control type")

      # Fill in any steering angle motor control and associated parameters
      steering = wheel['steering']
      if steering:
        steeringtype = steering[0]
        if len(steering) == 2:
          steeringparam = steering[1]
        else:
          steeringparam = steering[1:]
        if steeringtype in self.motorcontrollers:
          steeringcontrol = self.motorcontrollers[steeringtype]
        else:
          raise ValueError("Unknown motor control type")

      # Add the newly created roverwheel object to wheels dictionary.
      self.wheels[name] = roverwheel(name, wheel['x'], wheel['y'],
        rollingcontrol, rollingparam, steeringcontrol, steeringparam)

    # Wheels are initialized, set everything to zero.
    self.move_velocity_radius(0)

  def move_velocity_radius(self, velocity, radius=infinity):
    """
    Given the desired velocity and turning radius, update the angle and
    velocity required for each wheel to perform the desired motion.

    Velocity and radius is given relative to rover center.

    Radius of zero indicates a turn-in-place movement. (Not yet implemented)
    Radius of infinity indicates movement in a straight line.
    """
    if abs(radius) < self.minRadius:
      # This chassis configuration could not make that tight of a turn.
      raise ValueError("Radius below minimum")

    if abs(velocity) > 100:
      raise ValueError("Velocity percentage may not exceed 100")

    self.currentMotion = (velocity, radius)

    if radius > self.maxRadius:
      # Straight line travel
      for wheel in self.wheels.values():
        wheel.angle = 0
        wheel.velocity = velocity
    else:
      # Calculate angle and velocity for each wheel
      for wheel in self.wheels.values():
        # Dimensions of triangle representing the wheel. Used for calculations
        # in form of opposite, adjacent, and hypotenuse
        opp = wheel.y
        adj = radius-wheel.x
        hyp = math.sqrt(pow(opp,2) + pow(adj,2))

        # Calculate wheel steering angle to execute the commanded motion.
        if adj == 0:
          wheel.angle = 90
        else:
          wheel.angle = math.degrees(math.atan(float(opp)/float(adj)))

        # Calculate wheel rolling velocity to execute the commanded motion.
        if radius == 0:
          wheel.velocity = 0 # TODO: Velocity calculation for spin-in-place where radius is zero
        else:
          wheel.velocity = velocity * hyp/abs(radius)

    # Go back and normalize al the wheel roll rate magnitude so they are at or
    # below target velocity while maintaining relative ratios between their rates.
    maxCalculated = 0

    for wheel in self.wheels.values():
      if abs(wheel.velocity) > maxCalculated:
        maxCalculated = abs(wheel.velocity)

    if maxCalculated > velocity:
      # At least one wheel exceeded specified maxVelocity, calculate
      # normalization ratio and apply to every wheel.
      reductionRatio = abs(velocity)/float(maxCalculated)
      for wheel in self.wheels.values():
        wheel.velocity = wheel.velocity * reductionRatio

    # We're sending commands for a particular wheel - steering and rolling
    # velocity - before we move on to the next wheel. If this causes timing
    # issues (wheels start moving before they've finished pointing in the
    # right direction, etc.) we may have to send all steering commands first,
    # wait until we reach the angles, before sending velocity commands.
    for wheel in self.wheels.values():
      wheel.anglevelocity()

  def radius_for(self, name, pct_angle):
    """
    Given the name of a wheel and the steering angle of that wheel, calculate
    the radius of the resulting rover path. This is useful when determining
    minimum turning radius.
    Angle is described in percentage range of the maximum steering angle, in
    range of -100 to 100, positive clockwise. (Angle 100 = full right turn.)
    """

    if name not in self.wheels:
      raise ValueError("Could not find wheel {} to calculate radius for steering at {} percent of maximum angle.".format(name, pct_angle))

    if abs(pct_angle) > 100:
      raise ValueError("Steering wheel angle percentage {} exceeds 100".format(pct_angle))

    wheel = self.wheels[name]

    # Maximum angle pulled from the control class is subtracted by 1.5 degree
    # for a bit of margin against the hard end stop.
    angle = pct_angle * float(wheel.rollingcontrol.maxangle(wheel.rollingparam)-1.5) / 100

    if abs(angle) < 1:
      # Rounding off to straight ahead
      return infinity

    if abs(angle) > 89:
      # Rounding off to right angle
      return wheel.x

    return wheel.x + (wheel.y/math.tan(math.radians(angle)))
