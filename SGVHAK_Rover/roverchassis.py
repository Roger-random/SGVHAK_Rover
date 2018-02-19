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
import roboclaw_wrapper

# Python 2 does not have a constant for infinity. (Python 3 added math.inf.)
infinity = float("inf")

class chassis:
  """ 
  Rover chassis class tracks the physical geometry of the chassis and uses
  that informaton to calculate Ackerman steering angles and relative
  velocity for wheel travel
  """

  def __init__(self):
    # List of wheels
    # Each wheel is a dictionary with the following items:
    #   X,Y location relative to the center of the rover. Rover right is 
    #     positive X axis, rover forward is positive Y axis. So a wheel in
    #     front and to the right of rover center will have positive X and Y.
    self.wheels = list()

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

    # Dictionary of wheel angles calculated from currentMotion.
    #  Keys = the names of wheels
    #  Values = angle of wheel in degrees. Straight forward is zero degrees,
    #    positive angle indicates turning rover right.
    self.angles = dict()

    # Dictionary of wheel velocity calculated from currentMotion.
    #  Keys = the names of wheels
    #  Values = velocity of wheel in the same unit given in currentMotion.
    self.velocity = dict()

    # Each instance of this class represents one group of RoboClaw connected
    # together on the same packet serial network. Up to eight addressible
    # RoboClaws and two motors per controller = up to 16 motors. Since we
    # have less than 16 motors to control at the moment, a single instance is
    # sufficient.
    self.rclaw = roboclaw_wrapper.roboclaw_wrapper()

  def ensureready(self):
    """
    Makes sure this chassis class is ready for work by ensuring the required
    information is loaded and ready.
    """
    if len(self.wheels) > 0:
      return

    # Use a test stub RoboClaw instead of talking to a real RoboClaw.
    if not self.rclaw.connected():
      self.rclaw.connect(dict([('port','TEST')]))
    self.testchassis()
    self.move_velocity_radius(0)

  def testchassis(self):
    """
    Use a set of hard-coded values for chassis configuraton. In actual use,
    these values will be dictated by a configuration file read from disk.
    """

    # The order and the X,Y locations of wheels are taken from the reference 
    # chassis, dimensions are in inches.
    self.wheels.append(dict([
      ('name','front_left'),
      ('x',-7.254),
      ('y',10.5),
      ('rolling',(128,2,False)),
      ('steering',(131,2,False))]))
    self.wheels.append(dict([
      ('name','mid_left'),
      ('x',-10.073),
      ('y',0),
      ('rolling',(129,2,False)),
      ('steering',None)]))
    self.wheels.append(dict([
      ('name','rear_left'),
      ('x',-7.254),
      ('y',-10.5),
      ('rolling',(130,2,False)),
      ('steering',(132,2,False))]))
    self.wheels.append(dict([
      ('name','front_right'),
      ('x',7.254),
      ('y',10.5),
      ('rolling',(128,1,False)),
      ('steering',(131,1,False))]))
    self.wheels.append(dict([
      ('name','mid_right'),
      ('x',10.073),
      ('y',0),
      ('rolling',(129,1,False)),
      ('steering',None)]))
    self.wheels.append(dict([
      ('name','rear_right'),
      ('x',7.254),
      ('y',-10.5),
      ('rolling',(130,1,False)),
      ('steering',(132,1,False))]))

  def wheelDisplayTable(self):
    """
    Generate a table representing all the wheels for display in chassis 
    configuraton menu
    """
    rows = set()
    columns = set()

    # Count the unique X/Y coordinates into columns/rows
    for wheel in self.wheels:
      rows.add(wheel['y'])
      columns.add(wheel['x'])

    # Create a dictionary of dicationaries to hold entries.
    wheelTable = dict()
    for row in rows:
      wheelTable[row] = dict()
      for column in columns:
        wheelTable[row][column] = list()

    # Put each wheel into its matching location in the table.
    for wheel in self.wheels:
      wheelTable[wheel['y']][wheel['x']].append(wheel)

    return wheelTable

  def roboclaw_table(self):
    """
    Generate a dictionary of RoboClaw version strings for each wheel,
    keyed to the 'name' field for the wheel.
    """
    rctable = dict()
    for wheel in self.wheels:
      try:
        rollcontrol = wheel['rolling']
        rollclaw = self.rclaw.version(rollcontrol)
      except ValueError as ve:
        rollclaw = "(No Response)"

      steercontrol = wheel.get('steering', None)
      if steercontrol:
        try:
          steerclaw = self.rclaw.version(steercontrol)
        except ValueError as ve:
          steerclaw = "(No Response)"
      else:
        steerclaw = "N/A"

      rctable[wheel['name']] = (rollclaw, steerclaw)

    return rctable

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
    self.angles.clear()
    self.velocity.clear()

    if radius > self.maxRadius:
      # Straight line travel
      for wheel in self.wheels:
        name = wheel['name']
        self.angles[name] = 0
        self.velocity[name] = velocity
    else:
      # Calculate angle and velocity for each wheel
      for wheel in self.wheels:
        name = wheel['name']

        # Dimensions of triangle representing the wheel. Used for calculations
        # in form of opposite, adjacent, and hypotenuse
        opp = wheel['y']
        adj = radius-wheel['x']
        hyp = math.sqrt(pow(opp,2) + pow(adj,2))

        # Calculate wheel steering angle to execute the commanded motion.
        if adj == 0:
          self.angles[name] = 90
        else:
          self.angles[name] = math.degrees(math.atan(float(opp)/float(adj)))

        # Calculate wheel rolling velocity to execute the commanded motion.
        if radius == 0:
          self.velocity[name] = 0 # TODO: Velocity calculation for spin-in-place where radius is zero
        else:
          self.velocity[name] = velocity * hyp/abs(radius)

    # Go back and normalize al the wheel roll rate magnitude so they are at or
    # below target velocity while maintaining relative ratios between their rates.
    maxCalculated = 0

    for vel in self.velocity:
      if abs(self.velocity[vel]) > maxCalculated:
        maxCalculated = abs(self.velocity[vel])

    if maxCalculated > velocity:
      # At least one wheel exceeded specified maxVelocity, calculate
      # normalization ratio and apply to every wheel.
      reductionRatio = abs(velocity)/float(maxCalculated)
      for vel in self.velocity:
        self.velocity[vel] = self.velocity[vel] * reductionRatio

    # We're sending commands for a particular wheel - steering and rolling
    # velocity - before we move on to the next wheel. If this causes timing
    # issues (wheels start moving before they've finished pointing in the
    # right direction, etc.) we may have to send all steering commands first,
    # wait until we reach the angles, before sending velocity commands.

    for wheel in self.wheels:
      name = wheel['name']

      steering = wheel['steering']
      if steering:
        self.rclaw.angle(steering, self.angles[name])

      rolling = wheel['rolling']
      if rolling:
        self.rclaw.velocity(rolling, self.velocity[name])

  def radius_for(self, name, pct_angle):
    """
    Given the name of a wheel and the steering angle of that wheel, calculate
    the radius of the resulting rover path. This is useful when determining
    minimum turning radius.
    Angle is described in percentage range of the maximum steering angle, in
    range of -100 to 100, positive clockwise. (Angle 100 = full right turn.)
    """
    target = None
    for wheel in self.wheels:
      if wheel['name'] == name:
        target = wheel
        break

    if target == None:
      raise ValueError("Could not find wheel {} to calculate radius for steering at {} percent of maximum angle.".format(name, pct_angle))

    if abs(pct_angle) > 100:
      raise ValueError("Steering wheel angle percentage {} exceeds 100".format(pct_angle))

    angle = pct_angle * float(self.rclaw.maxangle()) / 100

    if abs(angle) < 1:
      # Rounding off to straight ahead
      return infinity

    if abs(angle) > 89:
      # Rounding off to right angle
      return wheel['x']

    return wheel['x'] + (wheel['y']/math.tan(math.radians(angle)))
