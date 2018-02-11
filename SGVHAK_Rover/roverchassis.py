import json
import io

class roverchassis:
  """ 
  Rover chassis class tracks the physical geometry of the chassis and uses
  that informaton to calculate Ackerman steering angles and relative
  velocity for wheel travel
  """

  # Filename to store geometry parameters.
  paramFile = "roverchassis.parameters"

  def __init__(self):
    # List of wheels
    # Each wheel is a dictionary with the following items:
    #   X,Y location relative to the center of the rover. Rover right is 
    #     positive X axis, rover forward is positive Y axis. So a wheel in
    #     front and to the right of rover center will have positive X and Y.
    self.wheels = list()

  def defaultWheels(self):
    """
    Use a set of hard-coded values for wheels.
    The order and the X,Y locations are taken from the reference chassis.
      Dimensions are in inches.
    """
    self.wheels.append(dict([('x',-7.254), ('y',10.5)]))
    self.wheels.append(dict([('x',-10.073), ('y',0)]))
    self.wheels.append(dict([('x',-7.254), ('y',-10.5)]))
    self.wheels.append(dict([('x',7.254), ('y',10.5)]))
    self.wheels.append(dict([('x',10.073), ('y',0)]))
    self.wheels.append(dict([('x',7.254), ('y',-10.5)]))

  def loadDist(self):
    """
    Load distance parameters (self.lengthDist, self.widthDist) from file
    Any changes here will probably need corresponding changes in saveDist()
    """
    distFile = io.open(self.paramFile, "r")
    self.wheels = json.loads(distFile.readline())
    distFile.close()

  def saveDist(self):
    """
    Read distance parameters (self.lengthDist, self.widthDist) from file
    Any changes here will probably need corresponding changes in loadDist()
    """
    distFile = io.open(self.paramFile,"w")
    distFile.write(unicode(json.dumps(self.wheels)))
    distFile.close()
