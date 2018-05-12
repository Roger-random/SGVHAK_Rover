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
import serial
from struct import *

import configuration

def bytetohex(bytearray):
  """
  Returns hexadecimal string representation of byte array
  Copied from StackOverflow
  https://stackoverflow.com/questions/19210414/byte-array-to-hex-string
  """
  return ''.join('{:02x}'.format(x) for x in bytearray)

class lewansoul_wrapper:
  """
  Class that implements the rover motor control methods for serial bus
  servo by LewanSoul. Specifically their model LX-16A.
  """
  def __init__(self):
    self.sp = None

  def check_sp(self):
    """ Raises error if we haven't opened serial port yet. """
    if self.sp == None:
      raise ValueError("LewanSoul serial communication is not available.")

  def connect(self):
    """
    Read serial port connection parameters from JSON configuration file
    and open the port.
    """

    # Read parameter file
    config = configuration.configuration("lewansoul")
    connectparams = config.load()['connect']

    # Open serial port with parameters
    s = serial.Serial()
    s.baudrate = connectparams['baudrate']
    s.port = connectparams['port']
    s.timeout = connectparams['timeout']
    s.open()

    if s.is_open:
      self.sp = s

  def close(self):
    """
    Closes down the serial port
    """
    if self.sp.is_open:
      self.sp.close()
      self.sp = None

  def send(self, servo_id, command, data=None):
    """
    Send a command to a LewanSoul servo, taking care of the header and
    checksum calculation for a command packet.
    """
    self.check_sp()
    packet = [0x55, 0x55]

    if servo_id < 0 or servo_id > 0xfe:
      raise ValueError("Servo ID {} is out of valid range".format(servo_id))
    packet.append(servo_id)

    length = 3
    if data:
      length = length + len(data)
    #TODO: check maximum length
    packet.append(length)

    #TODO: Check for valid command
    packet.append(command)

    if data:
      for d in data:
        packet.append(d)

    checksum = servo_id + length + command
    if data:
      for d in data:
        checksum = checksum + d
    checksum = (~checksum) & 0xff
    packet.append(checksum)

    packet_bytes = bytearray(packet)
    # print("Sending command byte stream of {}".format(bytetohex(packet_bytes)))
    self.sp.write(packet_bytes)

  def read_raw(self, length=100):
    """
    Reads a stream of bytes from serial device and returns it without any
    attempts at parsing or validation
    """
    self.check_sp()
    return bytearray(self.sp.read(length))

  def read_parsed(self, length=100, expectedid=None, expectedcmd=None, expectedparams=None):
    """
    Reads up to 'length' bytes and parse it according to pack format spec
    from "LewanSoul Bus servo Communication Protocol" PDF:

    0     1     2     3     4     [ ... ]
    0x55  0x55  ID    Len   Cmd   Param1... ParamN  Checksum

    Length of data is all bytes after ID, including length byte.
    Packet with no parameters has length of 3 bytes, plus header+ID = 6 bytes total.
    Checksum = (~(ID+Length+Cmd+Param1+...+ParamN)) & 0xFF

    - -

    Optional parameters:
      expectedid = if provided, will check message ID against expected ID.
      expectedcmd = if provided, will check message command against expected command.
      expectedparams = if provided, will check the number of bytes in parameter matches expected.

      If a mismatch is found, a ValueError is raised.
    """
    self.check_sp()
    r = bytearray(self.sp.read(length))

    # Check response length
    if len(r) < 6:
      raise ValueError("Need at least 6 bytes for a valid packet, received {}".format(len(r)))

    # Check header
    if r[0] != 0x55 or r[1] != 0x55:
      raise ValueError("Response header is {:02x} {:02x}, expected 0x55 0x55".format(r[0], r[1]))

    # Verify length
    rlen = r[3]
    if rlen+3 != len(r):
      raise ValueError("Packet claims to have {} bytes of data + 3 bytes of header, but we retrieved {} bytes.".format(rlen, len(r)))

    # Verify checksum
    checksum = 0
    for b in r[2:-1]:
      checksum = checksum + b
    checksum = (~checksum) & 0xFF

    if checksum != r[-1]:
      raise ValueError("Packet checksum {} does not match calculated checksum {}".format(r[-1], checksum))

    # If an expected ID is given, compare against ID in the message.
    rid = r[2]
    if expectedid != None and expectedid != rid:
      raise ValueError("Response stamped with ID {}, expected {}".format(rid, expectedid))

    # If an expected command is given, compare against command in the message.
    rcmd = r[4]
    if expectedcmd != None and expectedcmd != rcmd:
      raise ValueError("Response command {}, expected {}".format(rcmd, expectedcmd))

    # Examine parameters, if any.
    if rlen > 3:
      rparams = bytearray(r[5:-1])
      if expectedparams != None and expectedparams != len(rparams):
        raise ValueError("Received {} bytes of parameters, expected {}".format(len(rparams),expectedparams))
    else:
      rparams = None
      if expectedparams != None and expectedparams != 0:
        raise ValueError("Received {} bytes of parameters, expected none".format(len(rparams)))

    # Return results in a tuple
    return (rid, rcmd, rparams)

  def version(self, id):
    """ Identifier string for this motor controller """
    return "LewanSoul"

  @staticmethod
  def check_id(id):
    """ Verifies servo ID is within range and inverted status is boolean"""
    if not isinstance(id, (tuple,list)):
      raise ValueError("LewanSoul identifier must be a tuple")

    if not isinstance(id[0], int):
      raise ValueError("LewanSoul servo address must be an integer")

    if id[0] < 0 or id[0] > 253:
      raise ValueError("LewanSoul servo address {} outside of valid range 0-253".format(id[0]))

    if not isinstance(id[1], int):
      raise ValueError("LewanSoul servo center position must be an integer")

    if not isinstance(id[2], bool):
      raise ValueError("Inverted status must be a boolean")

    return tuple(id)

  def power_percent(self, id, percentage):
    """ Runs servo in motor mode at specified +/- percentage """
    sid, center, inverted = self.check_id(id)
    self.check_sp()

    pct = int(percentage)
    if abs(pct) > 100:
      raise ValueError("Motor power percentage {0} outside valid range from 0 to 100.".format(pct))

    # LewanSoul API wants power expressed between -1000 and 1000, so multiply by 10.
    power = percentage*10

    if inverted:
      power = power * -1

    self.send(sid, 29, bytearray(pack('hh',1,power)))

  def set_max_current(self, id, current):
    """ LewanSoul does not support overpower protection. """
    sid, center, inverted = self.check_id(id)
    self.check_sp()
    # Does nothing

  def init_velocity(self, id):
    """ Sets LewanSoul into motor mode and speed zero """
    sid, center, inverted = self.check_id(id)
    self.check_sp()

    self.send(sid, 29, bytearray(pack('hh',1,0)))

  def velocity(self,id,pct_velocity):
    """
    Runs the specified servo in motor mode at specified velocity
    In case of LewanSoul servos, it is the same as power_percent.
    """
    self.power_percent(id,pct_velocity)

  def init_angle(self, id):
    """
    Sets the LewanSoul into servo mode and move to center over 2 seconds
    """
    sid, center, inverted = self.check_id(id)
    self.check_sp()

    self.send(sid, 29, (0,0,0,0)) # Servo mode
    self.send(sid, 1, bytearray(pack('hh', center, 2000)))

  def maxangle(self, id):
    sid, center, inverted = self.check_id(id)
    self.check_sp()
    return 120

  def angle(self, id, angle):
    sid, center, inverted = self.check_id(id)
    self.check_sp()

    if abs(angle) > 95:
      raise ValueError("Steering angle {} exceeded expected maximum of 90".format(angle))

    delta = angle * (500.0/120.0) # 500 count/ 120 degrees = counts per degree.

    if inverted:
      delta = delta * -1

    self.send(sid, 29, (0,0,0,0)) # Servo mode
    self.send(sid, 1, bytearray(pack('hh', center+delta, 200)))

  def steer_setzero(self, id):
    sid, center, inverted = self.check_id(id)
    self.check_sp()
    # TODO: Support live adjustment

  def input_voltage(self, id):
    """
    Query LewanSoul servo's internal voltage monitor
    """
    sid, center, inverted = self.check_id(id)
    self.check_sp()

    self.send(sid, 27)
    (sid, cmd, params) = self.read_parsed(length=8, expectedcmd=27, expectedparams=2)
    millivolts = unpack('h', params)[0]

    return millivolts/1000.0

if __name__ == "__main__":
  """
  Command line interface to work with LewanSoul serial bus servos.
  Implements a subset of the servo's functionality
  * Move to position over time. (Servo mode)
  * Spin at a specified speed. (Motor mode)
  * Broadcast query for servo ID
  * Rename servo to another ID
  * Unload and power down motors
  """
  import argparse

  parser = argparse.ArgumentParser(description="LewanSoul Serial Servo Command Line Utility")

  parser.add_argument("-id", "--id", help="Servo identifier integer 0-253. 254 is broadcast ID.", type=int, default=1)
  parser.add_argument("-t", "--time", help="Time duration for action", type=int, default=0)
  group = parser.add_mutually_exclusive_group()
  group.add_argument("-m", "--move", help="Move servo to specified position 0-1000", type=int)
  group.add_argument("-q", "--queryid", help="Query for servo ID", action="store_true")
  group.add_argument("-r", "--rename", help="Rename servo identifier", type=int)
  group.add_argument("-s", "--spin", help="Spin the motor at a specified speed from -1000 to 1000", type=int)
  group.add_argument("-u", "--unload", help="Power down servo motor", action="store_true")
  group.add_argument("-v", "--voltage", help="Read current input voltage", action="store_true")
  args = parser.parse_args()

  c = lewansoul_wrapper()
  c.connect()

  if args.move != None: # Explicit check against None because zero is a valid value
    if args.move < 0 or args.move > 1000:
      print("Servo move destination {} is outside valid range of 0 to 1000 (1000 = 240 degrees)".format(args.move))
    elif args.time < 0 or args.time > 30000:
      print("Servo move time duration {} is outside valid range of 0 to 30000 milliseconds".format(args.time))
    else:
      print("Moving servo {} to position {}".format(args.id, args.move))
      c.send(args.id, 29, (0,0,0,0)) # Turn on servo mode (in case it was previously in motor mode)
      c.send(args.id, 1, bytearray(pack('hh', args.move, args.time)))
  elif args.queryid:
    print("Broadcasting servo ID query")
    c.send(0xfe, 14) # Broadcast and ask to report ID
    (sid, cmd, params) = c.read_parsed(length=7, expectedcmd=14, expectedparams=1)
    if sid != params[0]:
      raise ValueError("ID response stamped with {} but payload says {}".format(sid, params[0]))
    print("Servo ID {} responded to query".format(sid))
  elif args.rename:
    print("Checking the specified servo ID {} is on the serial network.".format(args.id))
    c.send(args.id, 14) # Ask for current servo ID
    (sid, cmd, params) = c.read_parsed(length=7, expectedcmd=14, expectedparams=1)
    if sid != args.id or params[0] != args.id:
      print("Unexpected answer from servo {} when verifying servo {} is on the network.".format(sid, args.id))
    else:
      print("Checking the specified destination servo ID {} is not already taken.".format(args.rename))
      c.send(args.rename, 14)
      expectempty=c.read_raw()
      if len(expectempty) > 0:
        raise ValueError("Someone answers to servo ID {} on the network, rename aborted.".format(args.rename))
      else:
        print("Renaming servo ID {} to {}".format(args.id, args.rename))
        c.send(args.id, 13, (args.rename,))
        print("Verifying the servo now answers to new ID")
        c.send(args.rename, 14)
        (sid, cmd, params) = c.read_parsed(length=7, expectedcmd=14, expectedparams=1)
        if sid != args.rename or sid != params[0]:
          print("Querying for response from ID {} failed, we got answer from ID {}/{} instead.".format(args.rename, sid, params[0]))
        else:
          print("Servo successfully renamed to ID {}".format(args.rename))
  elif args.spin != None: # Zero is a valid parameter.
    if args.spin < -1000 or args.spin > 1000:
      print("Servo spin speed {} is outside valid range of -1000 to 1000".format(args.spin))
    else:
      print("Spinning motor of servo {} at rate of {}".format(args.id, args.spin))
      c.send(args.id, 29, bytearray(pack('hh', 1, args.spin)))
  elif args.unload:
    c.send(args.id, 31, (0,))
  elif args.voltage:
    c.send(args.id, 27)
    (sid, cmd, params) = c.read_parsed(length=8, expectedcmd=27, expectedparams=2)
    voltage = unpack('h', params)[0]
    print("Servo {} reports input voltage of {}".format(sid, voltage/1000.0))
  else:
    # None of the actions were specified? Show help screen.
    parser.print_help()

  c.close()
