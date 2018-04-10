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
from subprocess import call
import socket
from SGVHAK_Rover import app
from flask import flash, json, redirect, render_template, request, url_for
import roverchassis

# Rover chassis geometry, including methods to calculate wheel angle and
# velocity based on chassis geometry.
chassis = roverchassis.chassis()

class main_menu:

  @app.route('/')
  def index():
    """
    Main menu, home of rover UI.
    """
    chassis.ensureready()
    return render_template("index.html",
      page_title = 'Main Menu')

  @app.route('/stop_motors')
  def stop_motors():
    """
    Stop motors immediately
    """
    chassis.ensureready()
    for wheel in chassis.wheels.values():
      wheel.poweroff()
    flash("Motors Stopped","success")
    return render_template("index.html")

  @app.route('/drive')
  def drive():
    """
    Drive by circular touchpad control for polar coordinates
    """
    chassis.ensureready()
    return render_template("drive.html",
      ui_angle=70,
      page_title = 'Polar Pad')

  @app.route('/drive_cartesian')
  def drive_cartesian():
    """
    Drive by rectangular touchpad control for cartesian coordinates
    """
    chassis.ensureready()
    return render_template("drive_cartesian.html",
      page_title = 'Cartesian Pad')

  @app.route('/drive_command', methods=['GET','POST'])
  def drive_command():
    """
    Allows user to send a single angle+velocity command to chassis.
    """
    chassis.ensureready()

    if request.method == 'GET':
      return render_template("drive_command.html",
        page_title = 'Velocity & Angle Commands')
    else:
      # TODO: Limit the frequency of updates to one every 50ms. If more
      # than one update arrive within the window, use the final one. This
      # reduces workload on RoboClaw serial network and the mechanical bits
      # can't respond super fast anyway.
      # EXCEPTION: If a stop command arrives, stop immediately.
      pct_angle = float(request.form['pct_angle'])
      magnitude = float(request.form['magnitude'])

      if pct_angle == 0:
        radius = float("inf")
      elif pct_angle>0:
        radius = chassis.minRadius + (chassis.maxRadius-chassis.minRadius) * (100-pct_angle)/100.0
      else:
        radius = -chassis.minRadius - (chassis.maxRadius-chassis.minRadius) * (100+pct_angle)/100.0

      chassis.move_velocity_radius(magnitude, radius)

      return json.jsonify({'Success':1})

  @app.route('/chassis_config')
  def chassis_config():
    """
    Returns HTML to display current chassis configuration, including status
    like desired angle and velocity of individual wheels.
    """
    chassis.ensureready()

    # Generate a table where unique wheel X/Y value gets a column/row so
    # we know where to place them relative to each other on screen.
    rows = set()
    columns = set()

    # Count the unique X/Y coordinates into columns/rows
    for wheel in chassis.wheels.values():
      rows.add(wheel.y)
      columns.add(wheel.x)

    # Sets enforced uniqueness, now we turn them into a list so we can sort.
    rowlist = list(rows)
    rowlist.sort(reverse=True)
    columnlist = list(columns)
    columnlist.sort()

    # Create a dictionary of dicationaries to hold entries.
    wheelTable = dict()
    for row in rowlist:
      wheelTable[row] = dict()
      for column in columnlist:
        wheelTable[row][column] = list()

    # Put each wheel into its matching location in the table.
    for wheel in chassis.wheels.values():
      wheelTable[wheel.y][wheel.x].append(wheel)

    # To help space out the above information properly, generate a table for
    # CSS grid layout column offsets.
    wheelOffset = dict()
    for row in wheelTable.values():
      # Every row starts with zero accumulated offset
      cumulative_offset = 0
      for column in row.values():
        if len(column) == 0:
          # Each column without information will add an offset of 2 for
          # the first following non-empty column
          cumulative_offset = cumulative_offset + 2
        else:
          for wheel in column:
            if cumulative_offset > 0:
              # Pick up the accumulated offset, reset accumulator to zero.
              wheelOffset[wheel.name] = "offset-m{}".format(cumulative_offset)
              cumulative_offset = 0
            else:
              wheelOffset[wheel.name] = ""

    # Get local IP address, copy/pasted from StackOverflow
    # https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    IP = 'unknown'
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = 'Exception encountered while retrieving IP address'
    finally:
        s.close()

    # Render table
    return render_template("chassis_config.html",
      wheelTable = wheelTable,
      wheelOffset = wheelOffset,
      local_ip = IP,
      page_title = 'Chassis Configuraton')

  @app.route('/request_wheel_status', methods=['POST'])
  def request_wheel_status():
    """
    Return a JSON representation of current chassis wheel status. Use POST
    instead of GET to clearify this data should not be cached.
    Polled regularly by chassis_config.js to update onscreen display of
    chassis_config.html.
    """
    chassis.ensureready()
    wheelInfo = dict()
    for name, wheel in chassis.wheels.iteritems():
      wheelInfo[name] = dict()
      wheelInfo[name]['velocity'] = wheel.velocity
      wheelInfo[name]['angle'] = wheel.angle
    return json.jsonify(wheelInfo)

  @app.route('/steering_trim', methods=['GET','POST'])
  def steering_trim():
    """
    Steering control motor can go off-center for various reasons. The steering
    trim function allows the user to adjust the wheel center position.
    """
    chassis.ensureready()

    if request.method == 'GET':
      # Find all the wheels that we can steer
      steered_wheels = list()
      for name, wheel in chassis.wheels.iteritems():
        if wheel.steeringcontrol:
          steered_wheels.append(name)
      steered_wheels.sort()

      # Pass the list of wheels along for display
      return render_template("steering_trim.html",
        steered_wheels=steered_wheels,
        page_title = 'Steering Trim')
    else:
      adjWheel = chassis.wheels[request.form['wheel']]

      if "move_to" in request.form:
        # Steer wheel to requested angle
        adjWheel.steerto(int(request.form['move_to']))

        return json.jsonify({'wheel':adjWheel.name, 'move_to':request.form['move_to']})
      elif "set_zero" in request.form:
        # Accept the current steering angle as new zero
        adjWheel.steersetzero()

        return json.jsonify({'wheel':adjWheel.name, 'set_zero':request.form['set_zero']})
      else:
        raise ValueError("Invalid POST parameters.")

  @app.route('/system_power', methods=['GET','POST'])
  def system_power():
    """
    Allows an user to either reboot or shut the system down. Depends on the
    ability to call out to system control ('systemctl') which may vary from
    system to system. (Known to work on Raspberry Pi running Raspbian OS)
    """
    if request.method == 'GET':
      return render_template("system_power.html",
        page_title = 'System Power')
    else:
      action = request.form.get('power_command',None)

      if action == "shutdown":
        r = call("systemctl poweroff", shell=True)
        if r == 0:
          flash("Shutting down...", "success")
        else:
          flash("Shutdown attempt failed with error {0}".format(r), "error")
      elif action == "reboot":
        r = call("systemctl reboot", shell=True)
        if r == 0:
          flash("Rebooting...", "success")
        else:
          flash("Reboot attempt failed with error {0}".format(r), "error")
      else:
        flash("Invalid Action {}".format(action), "error")

      return redirect(url_for('index'))

  @app.route('/input_voltage')
  def input_voltage():
    """
    Most motor controllers report their battery input voltage. Retrieve and
    display this information for the user.
    """
    chassis.ensureready()
    voltages = dict()

    for name,wheel in chassis.wheels.iteritems():
      voltages[name] = wheel.motor_voltage()

    return render_template("input_voltage.html",
      voltages = voltages,
      page_title = "Input Voltage")
