import json
import io

class roverchassis:
  """ 
  Rover chassis class tracks the physical geometry of the chassis and uses
  that informaton to calculate Ackerman steering angles and relative
  velocity for wheel travel

  Geometry assumptions:
    Six wheels
    All wheels can be driven forward/back.
    All corner wheels can turn left-right.
    Mid wheels are fixed stright front-back.
  """

  # Constants used as keys to dictionaries holding geometry parameters.
  WHEEL_FRONT_RIGHT="WFR"
  WHEEL_FRONT_LEFT="WFL"
  WHEEL_MID_RIGHT="WMR"
  WHEEL_MID_LEFT="WML"
  WHEEL_REAR_RIGHT="WRR"
  WHEEL_REAR_LEFT="WRL"

  TURN_FRONT_RIGHT="TFR"
  TURN_FRONT_LEFT="TFL"
  TURN_REAR_RIGHT="TRR"
  TURN_REAR_LEFT="TRL"

  # Filename to store geometry parameters.
  paramFile = "roverchassis.distances"

  def __init__(self):
    # Dictionary of wheel controllers.
    # Keys =  WHEEL_* constants at the top of the file.
    self.wheelControl = dict()

    # Dictionary of turn controllers.
    # Keys = TURN_* constants at the top of the file.
    self.turnControl = dict()

    # Dictionary of lengthwise distance from rover's center
    # Keys =  WHEEL_* constants at the top of the file.
    # If WHEEL_MID_* are present, values will be ignored.
    self.lengthDist = dict()

    # Dictionary of widthwise distance from rover's center
    # Keys =  WHEEL_* constants at the top of the file.
    self.widthDist = dict()

  def loadDist(self):
    """
    Load distance parameters (self.lengthDist, self.widthDist) from file
    Any changes here will probably need corresponding changes in saveDist()
    """
    distFile = io.open(self.paramFile, "r")
    self.lengthDist = json.loads(distFile.readline())
    self.widthDist = json.loads(distFile.readline())
    distFile.close()

  def saveDist(self):
    """
    Read distance parameters (self.lengthDist, self.widthDist) from file
    Any changes here will probably need corresponding changes in loadDist()
    """
    distFile = io.open(self.paramFile,"w")
    distFile.write(unicode(json.dumps(self.lengthDist, sort_keys=True)))
    distFile.write(u'\n')
    distFile.write(unicode(json.dumps(self.widthDist, sort_keys=True)))
    distFile.close()
