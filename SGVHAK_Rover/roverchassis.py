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

  def testWheels(self):
    """
    Use a set of hard-coded values for wheels. Will eventually be replaced
    by a configuration file read from disk.
    The order and the X,Y locations are taken from the reference chassis.
      Dimensions are in inches.
    """
    self.wheels.append(dict([
      ('name','front_left'),
      ('x',-7.254),
      ('y',10.5),
      ('rolling', dict([('address',128),
                        ('motor',1),
                        ('inverted',True)])),
      ('steering', None)]))
    self.wheels.append(dict([
      ('name','mid_left'),
      ('x',-10.073),
      ('y',0),
      ('rolling', dict([('address',128),
                        ('motor',2),
                        ('inverted',True)])),
      ('steering', None)]))
    self.wheels.append(dict([
      ('name','rear_left'),
      ('x',-7.254),
      ('y',-10.5),
      ('rolling', dict([('address',129),
                        ('motor',1),
                        ('inverted',True)])),
      ('steering', None)]))
    self.wheels.append(dict([
      ('name','front_right'),
      ('x',7.254),
      ('y',10.5),
      ('rolling', dict([('address',129),
                        ('motor',2),
                        ('inverted',False)])),
      ('steering', None)]))
    self.wheels.append(dict([
      ('name','mid_right'),
      ('x',10.073),
      ('y',0),
      ('rolling', dict([('address',130),
                        ('motor',1),
                        ('inverted',False)])),
      ('steering', None)]))
    self.wheels.append(dict([
      ('name','rear_right'),
      ('x',7.254),
      ('y',-10.5),
      ('rolling', dict([('address',130),
                        ('motor',2),
                        ('inverted',False)])),
      ('steering', None)]))

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

  def roboclaw_table(self, rclaw):
    """
    Generate a dictionary of RoboClaw version strings for each wheel,
    keyed to the 'name' field for the wheel.
    """
    rctable = dict()
    for wheel in self.wheels:
      try:
        rollcontrol = wheel['rolling']
        rcver = rclaw.version((rollcontrol['address'],rollcontrol['motor']))
      except ValueError as ve:
        rcver = "(No Response)"
      rctable[wheel['name']] = rcver

    return rctable

  def updateMotion(self, velocity, radius=infinity):
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
    currentMax = 0

    for vel in self.velocity:
      if abs(self.velocity[vel]) > currentMax:
        currentMax = abs(self.velocity[vel])

    if currentMax > velocity:
      # At least one wheel exceeded specified maxVelocity, calculate
      # normalization ratio and apply to every wheel.
      reductionRatio = abs(velocity)/float(currentMax)
      for vel in self.velocity:
        self.velocity[vel] = self.velocity[vel] * reductionRatio

  def radius_for(self, name, angle):
    """
    Given the name of a wheel and the steering angle of that wheel, calculate
    calculate the radius of the resulting rover path. This is used when
    dictating turns by wheel behavior instead of rover behavior.
    """
    target = None
    for wheel in self.wheels:
      if wheel['name'] == name:
        target = wheel
        break

    if target == None:
      raise ValueError("Could not find wheel {} to calculate radius for angle {}.".format(name, angle))

    if abs(angle) < 1:
      # Rounding off to straight ahead
      return infinity

    if abs(angle) > 90:
      raise ValueError("Steering wheel > 90 degrees not supported.")

    if abs(angle) > 89:
      # Rounding off to right angle
      return wheel['x']

    return wheel['x'] + (wheel['y']/math.tan(math.radians(angle)))
