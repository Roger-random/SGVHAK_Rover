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
import configuration
import roboclaw_wrapper

# Python 2 does not have a constant for infinity. (Python 3 added math.inf.)
infinity = float("inf")

class roverwheel:
  """
  Rover wheel class tracks information specific to a particular wheel on
  the chassis.
  """
  def __init__(self, name, x=0, y=0, rollingcontrol=None,rollingparam=None,
    steeringcontrol=None, steeringparam=None):

    self.name = name
    self.x = x
    self.y = y
    self.rollingcontrol = rollingcontrol
    self.rollingparam = rollingparam
    self.steeringcontrol = steeringcontrol
    self.steeringparam = steeringparam

    self.angle = 0
    self.velocity = 0

    if self.rollingcontrol:
      self.rollingcontrol.init_velocity(self.rollingparam)
      try:
        self.rollinglabel = self.rollingcontrol.version(self.rollingparam)
      except ValueError as ve:
        self.rollinglabel = "(No Response)"

    if self.steeringcontrol:
      self.steeringcontrol.init_angle(self.steeringparam)
      try:
        self.steeringlabel = self.steeringcontrol.version(self.steeringparam)
      except ValueError as ve:
        self.steeringlabel = "(No Response)"

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

  def setzero(self):
    """
    Set the current steering angle of this wheel as the new zero. Caller is
    responsible for validation of all parameters
    """
    self.steeringcontrol.steer_setzero(self.steeringparam)

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

  def ensureready(self):
    """
    Makes sure this chassis class is ready for work by ensuring the required
    information is loaded and ready.
    """
    if len(self.wheels) > 0:
      return

    # Each instance of this class represents one group of RoboClaw connected
    # together on the same packet serial network. Up to eight addressible
    # RoboClaws and two motors per controller = up to 16 motors. Since we
    # have less than 16 motors to control at the moment, a single instance is
    # sufficient.
    rclaw = roboclaw_wrapper.roboclaw_wrapper()
    rclaw.connect()

    config = configuration.configuration("roverchassis")
    wheeljson = config.load()

    for wheel in wheeljson:
      # Using the data in configuration JSON file, create a wheel object.
      name = wheel['name']
      steeringcontrol = None
      steeringparam = None
      rollingcontrol = None
      rollingparam = None

      rolling = wheel['rolling']
      if rolling:
        rollingtype = rolling[0]
        rollingparam = rolling[1:]
        if rollingtype == 'roboclaw':
          rollingcontrol = rclaw
        else:
          raise ValueError("Unknown motor control type")

      steering = wheel['steering']
      if steering:
        steeringtype = steering[0]
        steeringparam = steering[1:]
        if steeringtype == 'roboclaw':
          steeringcontrol = rclaw
        else:
          raise ValueError("Unknown motor control type")

      self.wheels[name] = roverwheel(name, wheel['x'], wheel['y'],
        rollingcontrol, rollingparam, steeringcontrol, steeringparam)

    # Wheels are initialized, set everything to zero.
    self.move_velocity_radius(0)

  def wheelDisplayTable(self):
    """
    Generate a table representing all the wheels for display in chassis 
    configuraton menu
    """
    rows = set()
    columns = set()

    # Count the unique X/Y coordinates into columns/rows
    for wheel in self.wheels.values():
      rows.add(wheel.y)
      columns.add(wheel.x)

    # Sets enforced uniqueness, now we turn them into a list so we can sort.
    rowlist = list(rows)
    rowlist.sort(reverse=True)
    columnlist = list(columns)
    columnlist.sort()

    # Create a dictionary of dicationaries to hold entries.
    wheelTable = dict()
    for row in rowlist:
      wheelTable[row] = dict()
      for column in columnlist:
        wheelTable[row][column] = list()

    # Put each wheel into its matching location in the table.
    for wheel in self.wheels.values():
      wheelTable[wheel.y][wheel.x].append(wheel)

    return wheelTable

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

    angle = pct_angle * float(wheel.rollingcontrol.maxangle()) / 100

    if abs(angle) < 1:
      # Rounding off to straight ahead
      return infinity

    if abs(angle) > 89:
      # Rounding off to right angle
      return wheel.x

    return wheel.x + (wheel.y/math.tan(math.radians(angle)))

  def steering_by_name(self, wheel_name):
    """
    Find a steerable wheel by the given name. Returns wheel reference if
    found. If wheel is not found, or wheel is not steerable, will raise
    ValueError.
    """
    if wheel_name not in self.wheels:
      raise ValueError("Invalid wheel name")

    namedWheel = self.wheels[wheel_name]

    if namedWheel.steeringcontrol == None:
      raise ValueError("Specified wheel may not be steered")

    return namedWheel

  def steer_wheel(self, wheel_name, angle):
    """
    Steer the named wheel to the specified angle
    """
    self.steering_by_name(wheel_name).steerto(angle)

  def steer_setzero(self, wheel_name):
    """
    The named wheel's current steering angle is set as new zero position
    """
    self.steering_by_name(wheel_name).setzero()
