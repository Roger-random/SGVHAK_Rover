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

  def connect(self):
    # TODO: Read config

    s = serial.Serial()
    s.baudrate = 115200
    s.port = "/dev/ttyUSB0"
    s.timeout = 0.5
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

if __name__ == "__main__":
  c = lewansoul_wrapper()
  c.connect()

  c.send(0xfe, 14) # Broadcast and ask to report ID
  # c.send(0x01, 29, (1, 0, 0x0, 0x00)) # Turn using motor mode. 0x3E8 (0xE8 0x03) for full speed
  # c.send(0x01, 29, (0, 0, 0, 0)) # Return to servo mode
  # c.send(0x01, 1, (0xF4, 0x01, 0, 4)) # Move to position over time. 0=0, 30=0x7D, 120=0x1F4, 210=0x36b, 240 = 0x3E8

  # c.send(0x01, 13, (2,)) # Change servo #1 to #2
  c.read_raw()

  c.close()
