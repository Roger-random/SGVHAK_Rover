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

class dmfe_wrapper:
  """
  Class that implements the rover motor control methods for David M Flynn
  Enterprises motor control boards.
  """
  def __init__(self):
    self.sp = None

  def check_sp(self):
    """ Raises error if we haven't opened serial port yet. """
    if self.sp == None:
      raise ValueError("DMFE serial communication is not available.")

  def connect(self):
    """
    Read serial port connection parameters from JSON configuration file
    and open the port.
    """

    # Read parameter file
    config = configuration.configuration("dmfe")
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

  def send(self, device_id, command, data=b'\x00\x00\x00'):
    """
    Send a command to a DMFE bus device, taking care of the header and
    checksum calculation for a command packet.
    """
    self.check_sp()
    packet = bytearray([0xDD, 0xDD])

    # Sender is master with ID of 1
    packet.append(1)

    # Append receiver ID
    if device_id < 2 or device_id > 0xFE:
      raise ValueError("Device ID {} is out of valid range 0x02 to 0xFE".format(servo_id))
    packet.append(servo_id)

    # Append command
    packet.append(command) # TBD: need to validate command?

    # Append data
    packet = packet + data # TBD: need to validate data is bytearray of size 3?

    # Calculate & append checksum
    checksum = 0
    for i in range (2,8):
      checksum = checksum ^ packet[i]
    packet.append(checksum)

    print(packet)
    # Hold off until we get back to hardware. self.sp.write(packet)

  def read_raw(self, length=100):
    """
    Reads a stream of bytes from serial device and returns it without any
    attempts at parsing or validation
    """
    self.check_sp()
    return bytearray(self.sp.read(length))

  def read_ack(self):
    """
    We expect to receive a single byte 0xFF as acknowledgement
    """
    self.check_sp()
    r = bytearray(self.sp.read(1))

    if len(r) == 0:
      raise ValueError("Expected single byte 0xFF in response but received no data.")

    if r[0] != b'\xFF':
      raise ValueError("Expected 0xFF in response but got {}".format(r[0]))

  def read_dmfeserialservo(self):
    """
    We expect a device identifier string
    """
    self.check_sp()
    r = self.sp.read(18).decode('utf-8')

    if len(r) == 0:
      raise ValueError("Expected 'DMFE Serial Servo' but received no data.")

    if r != 'DMFE Serial Servo\n':
      raise ValueError("Expected 'DMFE Serial Servo' but received {}".format(r))

  def read_datapacket(self, expectedid):
    """
    We expect a data packet originating from device ID 'expectedid'

    Returns the 4-byte data array
    """
    self.check_sp()
    r = self.sp.read(7)

    if len(r) != 7:
      raise ValueError("Expected data packet of 7 bytes but received only {}".format(len(r)))
    
    if r[0] != expectedid:
      raise ValueError("Expected data packet from device {} but received from {}".format(expectedid, r[0]))
    
    if r[1] != 1:
      raise ValueError("Expected data packet for master id 1 but received ID {}".format(r[1]))

    checksum = 0
    for i in range (0,6):
      checksum = checksum ^ r[i]

    if checksum != r[6]:
      raise ValueError("Calculated checksum of {} does not match transmitted checksum {}".format(checksum,r[6]))

    return r[2:6]

  def version(self, id):
    """ Identifier string for this motor controller """
    return "DMFE"
  



