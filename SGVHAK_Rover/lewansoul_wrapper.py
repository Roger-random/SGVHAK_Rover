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

  def connect(self, port="/dev/ttyUSB0", baudrate=115200, timeout=0.5):
    s = serial.Serial()
    s.baudrate = baudrate
    s.port = port
    s.timeout = timeout
    s.open()

    if s.is_open:
      self.sp = s

  def close(self):
    if self.sp.is_open:
      self.sp.close()
      self.sp = None

  def send(self, servo_id, command, data=None):
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
    print "Sending command byte stream of {}".format(bytetohex(packet_bytes))
    self.sp.write(packet_bytes)

  def read_raw(self):
    response = bytearray(self.sp.read(100))
    print "Raw response = {}".format(bytetohex(response))

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
    if expectedid and expectedid != rid:
      raise ValueError("Response stamped with ID {}, expected {}".format(rid, expectedid))

    # If an expected command is given, compare against command in the message.
    rcmd = r[4]
    if expectedcmd and expectedcmd != rcmd:
      raise ValueError("Response command {}, expected {}".format(rcmd, expectedcmd))

    # Examine parameters, if any.
    if rlen > 3:
      rparams = bytearray(r[5:-1])
      if expectedparams and expectedparams != len(rparams):
        raise ValueError("Received {} bytes of parameters, expected {}".format(len(rparams),expectedparams))
    else:
      rparams = None
      if expectedparams and expectedparams != 0:
        raise ValueError("Received {} bytes of parameters, expected none".format(len(rparams)))

    # Return results in a tuple
    return (rid, rcmd, rparams)

if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser(description="LewanSoul Serial Servo Command Line Utility")

  parser.add_argument("-id", "--id", help="Servo identifier integer 0-253. 254 is broadcast ID.", type=int, default=1)
  group = parser.add_mutually_exclusive_group()
  group.add_argument("-q", "--queryid", help="Query for servo ID", action="store_true")
  group.add_argument("-r", "--rename", help="Rename servo identifier", type=int)
  args = parser.parse_args()

  c = lewansoul_wrapper()
  c.connect()

  if args.queryid:
    print "Broadcasting servo ID query"
    c.send(0xfe, 14) # Broadcast and ask to report ID
    (sid, cmd, params) = c.read_parsed(length=7, expectedcmd=14, expectedparams=1)
    if sid != params[0]:
      raise ValueError("ID response stamped with {} but payload says {}".format(sid, params[0]))
    print "Servo ID {} responded to query".format(sid)

  #elif args.renameid:
  # c.send(0x01, 13, (2,)) # Change servo #1 to #2

  # c.send(0x01, 29, (1, 0, 0x0, 0x00)) # Turn using motor mode. 0x3E8 (0xE8 0x03) for full speed
  # c.send(0x01, 29, (0, 0, 0, 0)) # Return to servo mode
  # c.send(0x01, 1, (0xF4, 0x01, 0, 4)) # Move to position over time. 0=0, 30=0x7D, 120=0x1F4, 210=0x36b, 240 = 0x3E8

  c.close()
