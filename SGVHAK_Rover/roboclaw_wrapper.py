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
from roboclaw import Roboclaw
from roboclaw_stub import Roboclaw_stub

# For the 'buffered' parameter into RoboClaw API.
immediate_execution = 1

def apiget(result_tuple, errormessage="RoboClaw API Getter"):
  """
  Every read operation from the Roboclaw API returns a tuple: index zero
  is 1 for success and 0 for failure. This helper looks for that zero and
  raises an exception if one is seen. If an optional error message was
  provided, it is sent into the ValueError constructor.

  In the normal case of success, if there was only one other element in
  the result_tuple, that element is returned by itself (not a single
  element tuple) If there are more than one, the result is a tuple.
  """
  if result_tuple[0] == 0:
    raise ValueError("{} {}".format(errormessage, str(result_tuple)))

  if len(result_tuple) == 2:
    return result_tuple[1]
  else:
    return result_tuple[1:]

def apiset(result, errormessage="RoboClaw API Setter"):
  """
  Every write operation returns true if successful. If it does not, a
  ValueError is raised with the optional error message parameter
  """
  if not result:
    raise ValueError(errormessage)

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

  @staticmethod
  def check_id(id):
    """
    Verifies that a given perameter is correct formatted id tuple for this class.
    * Check that it is indeed a tuple with three elements.
    * Check that the first element is an integer in valid range of RoboClaw
      addresses. 128 <= X <= 135
      NOTE: Does not check if there's actually a RoboClaw at that address.
    * Check that the second element is an integer specifying a motor 1 or 2.
      NOTE: Does not check if there's actually a motor connected.
    * Check that the third element is True or False, specifying whether the
      motor is inverted.

    Raises ValueError if check fails.
    """
    if not isinstance(id, (tuple,list)):
      raise ValueError("RoboClaw motor identifier must be a tuple")

    if len(id) != 3:
      raise ValueError("RoboClaw motor identifier must have three elements: address, motor number, and whether it is inverted")

    if not isinstance(id[0], int):
      raise ValueError("RoboClaw address must be an integer")

    if id[0] < 128 or id[0] > 135:
      raise ValueError("RoboClaw address must be in the range of 128 to 135 (inclusive)")

    if not isinstance(id[1], int):
      raise ValueError("RoboClaw motor number must be an integer")

    if id[1] != 1 and id[1] != 2:
      raise ValueError("RoboClaw motor number must be 1 or 2")

    if not isinstance(id[2], bool):
      raise ValueError("Inverted status must be a boolean")

    return tuple(id)

  def check_roboclaw(self):
    """
    Check to make sure we've already connected to a RoboClaw. This should be
    called before every RoboClaw command.
    """
    if not self.connected():
      raise ValueError("RoboClaw not yet connected")

  def connect(self):
    """
    Read all configuration parameters (not just connect) and use the connect
    parameters to create new RoboClaw API handle.
    """

    # First load configuration file
    config = configuration.configuration("roboclaw")
    allparams = config.load()

    self.velocityparams = allparams['velocity']
    self.angleparams = allparams['angle']

    # Use connect configuration to create a RoboClaw API handle
    portname = allparams['connect']['port']
    if portname == 'TEST':
      self.roboclaw = Roboclaw_stub()
    else:
      baudrate = allparams['connect']['baudrate']
      timeout = allparams['connect']['timeout']
      retries = allparams['connect']['retries']
      newrc = Roboclaw(portname, baudrate, timeout, retries)

      if newrc.Open():
        self.roboclaw = newrc
      else:
        raise ValueError("Could not connect to RoboClaw. {} @ {}".format(portname, baudrate))

  def connected(self):
    """Returns True if we have connected Roboclaw API to a serial port"""
    return self.roboclaw != None

  def version(self, id):
    """Returns a version string for display"""
    address, motor, inverted = self.check_id(id)
    self.check_roboclaw()

    return apiget(self.roboclaw.ReadVersion(address), "RoboClaw ReadVersion @ {}".format(address))

  def set_velocity_pid(self, id, params):
    address, motor, inverted = self.check_id(id)
    self.check_roboclaw()

    p = params['p']
    i = params['i']
    d = params['d']
    qpps = params['qpps']
    args = (address, p, i, d, qpps)
    error = "RoboClaw M{}@{} Velocity P{} I{} D{} QPPS{}".format(motor, address, p, i, d, qpps)

    if motor==1:
      apiset(self.roboclaw.SetM1VelocityPID(*args), error)
    else:
      apiset(self.roboclaw.SetM2VelocityPID(*args), error)

  def init_velocity(self, id):
    """
    Initializes the identified motor for wheel rolling control
    """
    self.set_velocity_pid(id, self.velocityparams['velocity'])

  def velocity(self, id, pct_velocity):
    """
    Run the specified motor (address,motor#) at the specified percentage of
    maximum velocity.
    """
    address, motor, inverted = self.check_id(id)
    self.check_roboclaw()

    if abs(pct_velocity) > 100.1:
      raise ValueError("Velocity percentage {} exceeds maximum of 100".format(pct_velocity))

    qpps = self.velocityparams['maxVelocity'] * pct_velocity / 100

    if inverted:
      qpps = -qpps

    acceleration = self.velocityparams['acceleration']

    if motor==1:
      apiset(self.roboclaw.SpeedAccelM1(
        address, acceleration, qpps),
        "Velocity {} acceleration {} on RoboClaw M1@{}".format(qpps, acceleration, address))
    else:
      apiset(self.roboclaw.SpeedAccelM2(
        address, acceleration, qpps),
        "Velocity {} acceleration {} on RoboClaw M2@{}".format(qpps, acceleration, address))

  def set_position_pid(self, id, params, limit):
    address, motor, inverted = self.check_id(id)
    self.check_roboclaw()

    p = params['p']
    i = params['i']
    d = params['d']
    maxi = params['maxi']
    deadzone = params['deadzone']
    args = (address, p, i, d, maxi, deadzone, -limit, limit)
    error = "RoboClaw M{}@{} Position P{} I{} D{} MaxI{} Deadzone{} from {} to {}".format(
      motor, address, p, i, d, maxi, deadzone, -limit, limit)

    if motor==1:
      apiset(self.roboclaw.SetM1PositionPID(*args), error)
    else:
      apiset(self.roboclaw.SetM2PositionPID(*args), error)

  def init_angle(self, id):
    """
    Initializes the identified motor for wheel steering control
    """
    p = self.angleparams
    self.set_velocity_pid(id, p['velocity'])
    self.set_position_pid(id, p['position'], p['hardstop']['count'])

  def maxangle(self):
    """
    Returns the maximum angle callers should use for their calculation.
    Take the absolute end stop and subtract a little bit of margin.
    """
    return self.angleparams['hardstop']['angle']-1.5

  def angle(self, id, angle):
    """
    Immediately moves the specified motor (address,motor#) to the specified
    angle expressed in number of degrees off zero center, positive clockwise.
    """
    address, motor, inverted = self.check_id(id)
    self.check_roboclaw()

    hardstopangle = self.angleparams['hardstop']['angle']
    hardstopcount = self.angleparams['hardstop']['count']

    if abs(angle) > hardstopangle:
      raise ValueError("Steering angle {} exceeds maximum of {} degrees off center".format(angle, hardstopangle))

    # Translate angle to position
    position = hardstopcount * angle / hardstopangle

    if inverted:
      position = -position

    acceleration = self.angleparams['accel']
    speed = self.angleparams['speed']
    deceleration = self.angleparams['decel']

    if motor==1:
      apiset(self.roboclaw.SpeedAccelDeccelPositionM1(
        address, acceleration, speed, deceleration, position, immediate_execution),
        "Position {} via {}/{}/{} on RoboClaw M1@{}".format(position, acceleration, speed, deceleration, address))
    else:
      apiset(self.roboclaw.SpeedAccelDeccelPositionM2(
        address, acceleration, speed, deceleration, position, immediate_execution),
        "Position {} via {}/{}/{} on RoboClaw M2@{}".format(position, acceleration, speed, deceleration, address))
