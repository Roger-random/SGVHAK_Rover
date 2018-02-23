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

import random
import serial
import struct
import time

class Roboclaw_stub:
  """
  This class implements a subset of the full RoboClaw API released by
  Ion Motion Control.

  This subset was created for testing purposes. it allows running our app in
  the absence of an actual RoboClaw attached to the computer.

  The functional fidelity of this class is poor since it only needs to be
  enough to exercise features of the control application.
  """
  'Stub of Roboclaw Interface Class'

  def __init__(self):
    self.name = "TEST API"

  def SetEncM1(self,address,cnt):
    return True

  def SetEncM2(self,address,cnt):
    return True

  def SetM1VelocityPID(self,address,p,i,d,qpps):
    return True

  def SetM2VelocityPID(self,address,p,i,d,qpps):
    return True

  def SpeedAccelM1(self,address,accel,speed):
    return True

  def SpeedAccelM2(self,address,accel,speed):
    return True

  def SetM1PositionPID(self,address,kp,ki,kd,kimax,deadzone,min,max):
    return True

  def SetM2PositionPID(self,address,kp,ki,kd,kimax,deadzone,min,max):
    return True

  def SpeedAccelDeccelPositionM1(self,address,accel,speed,deccel,position,buffer):
    return True

  def SpeedAccelDeccelPositionM2(self,address,accel,speed,deccel,position,buffer):
    return True

  def ReadVersion(self,address):
    return (1, self.name)

  def Open(self):
    return 1
