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
import json
import io

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

  def testWheels(self):
    """
    Use a set of hard-coded values for wheels.
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
