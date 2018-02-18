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
from roboclaw import Roboclaw
from roboclaw_stub import Roboclaw_stub

# For the 'buffered' parameter into RoboClaw API.
immediate_execution = 1

def apiget(resultTuple, errorMessage="RoboClaw API Getter"):
  """
  Every read operation from the Roboclaw API returns a tuple: index zero
  is 1 for success and 0 for failure. This helper looks for that zero and
  raises an exception if one is seen. If an optional error message was
  provided, it is sent into the ValueError constructor.

  In the normal case of success, if there was only one other element in
  the resultTuple, that element is returned by itself (not a single
  element tuple) If there are more than one, the result is a tuple.
  """
  if resultTuple[0] == 0:
    raise ValueError("{} {}".format(errorMessage, str(resultTuple)))

  if len(resultTuple) == 2:
    return resultTuple[1]
  else:
    return resultTuple[1:]

def apiset(result, errorMessage="RoboClaw API Setter"):
  """
  Every write operation returns true if successful. If it does not, a
  ValueError is raised with the optional error message parameter
  """
  if not result:
    raise ValueError(errorMessage)

class roboclaw_wrapper:
  """
  Class that wraps the roboclaw Python API released by Ion Motion Control.
  Includes some utility functions to help interface with the API, but mainly
  to keep the interface surface to the subset necessary to run a rover.

  Goal: Eventually have an abstract base class or interface ("motor_control"?)
  that defines the interface surface we need, and we have multiple derived
  classes, each corresponding to a motor controller. Rover builders can then
  swap out the appropriate software implementation to match different motor
  controller hardware: RoboClaw, ODrive Robotics, etc.

  Goal: Make this class safe to call from multiple threads.
    Option 1: Only allow commands from one thread, reject commands from others.
    Option 2: Allow commands from all threads, serialize them so only one is
              executed at a time. 
  """

  def __init__(self):
    self.roboclaw = None

    # Values taken from current SGVHAK prototype
    # TODO: Read these from a configuration file.
    self.rollingParams = dict([
      ('maxVelocity',6000),
      ('minVelocity',300),
      ('acceleration', 7500),
      ('velocity', dict([('p', 2500),
                         ('i', 100),
                         ('d', 500),
                         ('qpps',10000)]))])

    self.positionParams = dict([
      ('speed', 5000),
      ('accel', 7500),
      ('decel', 7500)])

    self.config = dict([
      ('velocity', dict([('p', 2500),
                         ('i', 100),
                         ('d', 500),
                         ('qpps',10000)])),
      ('position', dict([('p', 2400),
                         ('i', 0),
                         ('d', 500),
                         ('maxi', 0),
                         ('deadzone', 1),
                         ('minpos', -1362),    # -45 degrees
                         ('maxpos', 1362)]))]) #  45 degrees

  @staticmethod
  def check_id(id):
    """
    Verifies that a given perameter is correct formatted id tuple for this class.
    * Check that it is indeed a tuple with two elements.
    * Check that the first element is an integer in valid range of RoboClaw
      addresses. 128 <= X <= 135
      NOTE: Does not check if there's actually a RoboClaw at that address.
    * Check that the second element is an integer specifying a motor 1 or 2.
      NOTE: Does not check if there's actually a motor connected.

    Raises ValueError if check fails.
    """
    if not isinstance(id, tuple):
      raise ValueError("RoboClaw motor identifier must be a tuple")

    if len(id) != 2:
      raise ValueError("RoboClaw motor identifier must have two elements: address and motor number")

    if not isinstance(id[0], int):
      raise ValueError("RoboClaw address must be an integer")

    if id[0] < 128 or id[0] > 135:
      raise ValueError("RoboClaw address must be in the range of 128 to 135 (inclusive)")

    if not isinstance(id[1], int):
      raise ValueError("RoboClaw motor number must be an integer")

    if id[1] != 1 and id[1] != 2:
      raise ValueError("RoboClaw motor number must be 1 or 2")

    return id

  def check_roboclaw(self):
    """
    Check to make sure we've already connected to a RoboClaw. This should be
    called before every RoboClaw command.
    """
    if not self.connected():
      raise ValueError("RoboClaw not yet connected")

  def connect(self, parameters):
    """
    Connect to RoboClaw using provided dictionary of connection parameters
    """
    portname = parameters['port']
    if portname == 'TEST':
      self.roboclaw = Roboclaw_stub()
    else:
      baudrate = parameters.get('baudrate', 38400)
      timeout = parameters.get('timeout', 0.01) # Note this is actually interchar timeout
      retries = parameters.get('retries', 3)

      newrc = Roboclaw(portname, baudrate, timeout, retries)

      if newrc.Open():
        self.roboclaw = newrc
      else:
        raise ValueError("Could not connect to RoboClaw with provided parameters")

  def connected(self):
    """Returns True if we have connected Roboclaw API to a serial port"""
    return self.roboclaw != None

  def version(self, id):
    """Returns a version string for display"""
    address, motor = self.check_id(id)
    self.check_roboclaw()

    return apiget(self.roboclaw.ReadVersion(address), "RoboClaw ReadVersion @ {}".format(address))

  def velocity(self, id, pct_velocity):
    """
    Run the specified motor (address,motor#) at the specified percentage of
    maximum velocity.
    """
    address, motor = self.check_id(id)
    self.check_roboclaw()

    qpps = self.rollingParams['maxVelocity'] * pct_velocity / 100
    acceleration = self.rollingParams['acceleration']

    if motor==1:
      apiset(self.roboclaw.SpeedAccelM1(
        address, acceleration, qpps),
        "Velocity {} acceleration {} on RoboClaw M1@{}".format(qpps, acceleration, address))
    else:
      apiset(self.roboclaw.SpeedAccelM2(
        address, acceleration, qpps),
        "Velocity {} acceleration {} on RoboClaw M2@{}".format(qpps, acceleration, address))

  def position(self, id, position):
    """
    Immediately moves the specified motor (address,motor#) to the specified
    encoder count position.
    """
    address, motor = self.check_id(id)
    self.check_roboclaw()

    acceleration = self.positionParams['accel']
    speed = self.positionParams['speed']
    deceleration = self.positionParams['decel']

    if motor==1:
      apiset(self.roboclaw.SpeedAccelDeccelPositionM1(
        address, acceleration, speed, deceleration, position, immediate_execution),
        "Position {} via {}/{}/{} on RoboClaw M1@{}".format(position, acceleration, speed, deceleration, address))
    else:
      apiset(self.roboclaw.SpeedAccelDeccelPositionM2(
        address, acceleration, speed, deceleration, position, immediate_execution),
        "Position {} via {}/{}/{} on RoboClaw M2@{}".format(position, acceleration, speed, deceleration, address))
