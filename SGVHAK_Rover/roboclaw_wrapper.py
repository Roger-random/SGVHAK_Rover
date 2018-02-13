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
import roboclaw

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

    if isinstance(id[0], int):
      raise ValueError("RoboClaw address must be an integer")

    if id[0] < 128 or id[0] > 135:
      raise ValueError("RoboClaw address must be in the range of 128 to 135 (inclusive)")

    if isinstance(id[1], int):
      raise ValueError("RoboClaw motor number must be an integer")

    if id[1] != 1 and id[1] != 2:
      raise ValueError("RoboClaw motor number must be 1 or 2")


  def connect(self, parameters):
    """
    Connect to RoboClaw using provided dictionary of connection parameters
    """
    portname = parameters['port']
    baudrate = parameters.get('baudrate', 115200)
    timeout = parameters.get('timeout', 0.01) # Note this is actually interchar timeout
    retries = parameters.get('retries', 3)

    newrc = Roboclaw(portname, baudrate, timeout, retries)

    if newrc.Open():
      self.roboclaw = newrc
    else:
      raise ValueError("Could not connect to RoboClaw with provided parameters")

  def check_roboclaw(self):
    """
    Check to make sure we've already connected to a RoboClaw. This should be
    called before every RoboClaw command.
    """
    if self.roboclaw == None:
      raise ValueError("RoboClaw not yet connected")

  def velocity(self, velocity, id):
    """
    Run the specified motor (address,motor#) at the specified velocity.
    (quadrature pulses per second)
    """
    address, motor = check_id(id)

    check_roboclaw()

    if motor==1:
      self.roboclaw.SpeedM1(address, velocity)
    else:
      self.roboclaw.SpeedM2(address, velocity)
