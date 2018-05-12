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

class dynamixel_wrapper:
  """
  Class that implements the rover motor control methods for Dynamixel serial
  bus servo by Robotis. Specifically the model AX-12A.
  """
  def __init__(self):
    self.sp = None

  def check_sp(self):
    """ Raises error if we haven't opened serial port yet. """
    if self.sp == None:
      raise ValueError("Dynamixel serial communication is not available.")

  def connect(self):
    """
    Read serial port connection parameters from JSON configuration file
    and open the port.
    """

    # Read parameter file
    config = configuration.configuration("dynamixel")
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
    Send a command to a Dynamixel servo, taking care of the header and
    checksum calculation for a command packet.
    """
    self.check_sp()
    packet = [0xFF, 0xFF]

    if servo_id < 0 or servo_id > 0xfe:
      raise ValueError("Servo ID {} is out of valid range".format(servo_id))
    packet.append(servo_id)

    length = 2
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

  def read_parsed(self, length=100, expectedid=None, expectederr=None, expectedparams=None):
    """
    Reads up to 'length' bytes and parse it according to pack format spec
    from Robotis e-Manual
    http://emanual.robotis.com/docs/en/dxl/protocol1/#status-packet
    http://support.robotis.com/en/techsupport_eng.htm#product/actuator/dynamixel/ax_series/dxl_ax_actuator.htm

    0     1     2     3     4     [ ... ]
    0xFF  0xFF  ID    Len   Err   Param1... ParamN  Checksum

    Length of data is number of parameters plus checksum.
    Packet with no parameters has length of 2 bytes, plus header+ID+Length = 6 bytes total.
    Checksum = (~(ID+Length+Err+Param1+...+ParamN)) & 0xFF

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
    if r[0] != 0xFF or r[1] != 0xFF:
      raise ValueError("Response header is {:02x} {:02x}, expected 0xFF 0xFF".format(r[0], r[1]))

    # Verify length
    rlen = r[3]
    if rlen+4 != len(r):
      raise ValueError("Packet claims to have {} bytes of data + 4 bytes of header, but we retrieved {} bytes.".format(rlen, len(r)))

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

    # If an expected error is given, compare against error in the message.
    rerr = r[4]
    if expectederr != None and expectederr != rerr:
      raise ValueError("Response error {}, expected {}".format(rerr, expectederr))

    # Examine parameters, if any.
    if rlen > 2:
      rparams = bytearray(r[5:-1])
      if expectedparams and expectedparams != len(rparams):
        raise ValueError("Received {} bytes of parameters, expected {}".format(len(rparams),expectedparams))
    else:
      rparams = None
      if expectedparams and expectedparams != 0:
        raise ValueError("Received {} bytes of parameters, expected none".format(len(rparams)))

    # Return results in a tuple
    return (rid, rerr, rparams)

  def version(self, id):
    """ Identifier string for this motor controller """
    return "Dynamixel"


if __name__ == "__main__":
  """
  Command line interface to work with serial bus servos.
  Implements a subset of the servo's functionality
  * Move to position over time. (Servo mode)
  * Spin at a specified speed. (Motor mode)
  * Broadcast query for servo ID
  * Rename servo to another ID
  * Unload and power down motors
  """
  import argparse

  parser = argparse.ArgumentParser(description="Dynamixel Serial Servo Command Line Utility")

  parser.add_argument("-id", "--id", help="Servo identifier integer 0-253. 254 is broadcast ID.", type=int, default=1)
  parser.add_argument("-p", "--speed", help="Speed for move (0-1023) 0=max uncontrolled 1=slowest controlled 1023=fastest controlled", type=int, default=0)
  group = parser.add_mutually_exclusive_group()
  group.add_argument("-m", "--move", help="Move servo to specified position 0-1023", type=int)
  group.add_argument("-q", "--queryid", help="Query for servo ID", action="store_true")
  group.add_argument("-r", "--rename", help="Rename servo identifier", type=int)
  group.add_argument("-s", "--spin", help="Spin the motor at a specified speed from 0 to 2047", type=int)
  group.add_argument("-u", "--unload", help="Power down servo motor", action="store_true")
  group.add_argument("-v", "--voltage", help="Read current input voltage", action="store_true")
  group.add_argument("-l", "--location", help="Read current locaton.", action="store_true")
  group.add_argument("-e", "--reset", help="Reset to factory defaults.", action="store_true")
  args = parser.parse_args()

  c = dynamixel_wrapper()
  c.connect()

  if args.move != None: # Explicit check against None because zero is a valid value
    if args.move < 0 or args.move > 1023:
      print("Servo move destination {} is outside valid range of 0 to 1023 (1023 = 300 degrees)".format(args.move))
    elif args.speed < 0 or args.speed > 1023:
      print("Servo move speed {} is outside valid range of 0 to 1023".format(args.speed))
    else:
      if args.speed == 0:
        speedarg = "max uncontrolled speed"
      else:
        speedarg = "controlled speed {}".format(args.speed)
      print("Moving servo {} to position {} at {}".format(args.id, args.move, speedarg))
      c.send(args.id, 3, bytearray(pack('=Bhh',6, 0, 1023))) # Make sure we're in joint mode
      c.read_parsed(expectedid=args.id, expectederr=0, expectedparams=0)
      c.send(args.id, 3, bytearray(pack('=Bhh',30, args.move, args.speed)))
      c.read_parsed(expectedid=args.id, expectederr=0, expectedparams=0)
  elif args.queryid:
    print("Broadcasting servo ID query")
    c.send(0xfe, 1) # Broadcast and ask to report ID
    (sid, err, params) = c.read_parsed(length=6, expectederr=0, expectedparams=0)
    print("Servo ID {} responded to query".format(sid))
  elif args.rename:
    print("Checking the specified servo ID {} is on the serial network.".format(args.id))
    c.send(args.id, 1) # Ask for current servo ID
    (sid, err, params) = c.read_parsed(length=6, expectederr=0, expectedparams=0)
    if sid != args.id:
      print("Unexpected answer from servo {} when verifying servo {} is on the network.".format(sid, args.id))
    else:
      print("Checking the specified destination servo ID {} is not already taken.".format(args.rename))
      c.send(args.rename, 1)
      expectempty=c.read_raw()
      if len(expectempty) > 0:
        raise ValueError("Someone answers to servo ID {} on the network, rename aborted.".format(args.rename))
      else:
        print("Renaming servo ID {} to {}".format(args.id, args.rename))
        c.send(args.id, 3, bytearray(pack('=BB', 3,args.rename)))
        c.read_parsed(expectedid=args.id, expectederr=0, expectedparams=0)
        print("Verifying the servo now answers to new ID")
        c.send(args.rename, 1)
        (sid, cmd, params) = c.read_parsed(length=6, expectederr=0, expectedparams=0)
        if sid != args.rename:
          print("Querying for response from ID {} failed, we got answer from ID {}/{} instead.".format(args.rename, sid))
        else:
          print("Servo successfully renamed to ID {}".format(args.rename))
  elif args.spin != None: # Zero is a valid parameter
    if args.spin < 0 or args.spin > 2047:
      print("Servo spin speed {} is outside valid range of 0 to 2047".format(args.spin))
    else:
      print("Spinning motor of servo {} at speed {}".format(args.id, args.spin))
      c.send(args.id, 3, bytearray(pack('=Bhh',6, 0, 0))) # Make sure we're in wheel mode
      c.read_parsed(expectedid=args.id, expectederr=0, expectedparams=0)
      c.send(args.id, 3, bytearray(pack('=Bh',32, args.spin)))
      c.read_parsed(expectedid=args.id, expectederr=0, expectedparams=0)
  elif args.unload:
    print("Unloading servo ID {}".format(args.id))
    c.send(args.id, 3, (24,0))
    c.read_parsed(expectedid=args.id, expectederr=0, expectedparams=0)
  elif args.reset:
    print("Reset servo ID {} to factory defaults".format(args.id))
    c.send(args.id, 6, None)
    print(bytetohex(c.read_raw()))
  elif args.voltage:
    c.send(args.id, 2, (42,1))
    (sid, err, params) = c.read_parsed(expectedid=args.id, expectederr=0, expectedparams=1)
    voltage = params[0]
    print("Servo {} reports input voltage of {}".format(sid, voltage/10.0))
  elif args.location:
    c.send(args.id, 2, (36,2))
    (sid, err, params) = c.read_parsed(expectedid=args.id)
    position=unpack('h',params)[0]
    print("Servo current locaton {} with err {}".format(position, err))
  else:
    # None of the actions were specified? Show help screen.
    parser.print_help()

  c.close()
