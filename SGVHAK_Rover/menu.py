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
from SGVHAK_Rover import app
from flask import flash, json, render_template, request
import roverchassis

# Rover chassis geometry, including methods to calculate wheel angle and
# velocity based on chassis geometry.
chassis = roverchassis.chassis()

class main_menu:

  @app.route('/')
  def index():
    chassis.ensureready()
    return render_template("index.html")

  @app.route('/stop_motors')
  def stop_motors():
    chassis.ensureready()
    chassis.move_velocity_radius(0)
    flash("Motors Stopped","success")
    return render_template("index.html")

  @app.route('/drive')
  def drive():
    chassis.ensureready()
    return render_template("drive.html", ui_angle=70)

  @app.route('/drive_command', methods=['POST'])
  def drive_command():
    chassis.ensureready()

    # TODO: Limit the frequency of updates to one every 100(?) ms. If more
    # than one update arrive within the window, use the final one. This
    # reduces workload on RoboClaw serial network and the mechanical bits
    # can't respond super fast anyway.
    # EXCEPTION: If a stop command arrives, stop immediately.
    pct_angle = float(request.form['pct_angle'])
    magnitude = float(request.form['magnitude'])

    # TODO: Find a more general way to do this math rather than hard-coding
    # wheel names.
    if pct_angle >= 0:
      radius = chassis.radius_for('front_right', pct_angle)
    else:
      radius = chassis.radius_for('front_left', pct_angle)

    chassis.move_velocity_radius(magnitude, radius)

    return json.jsonify({'Success':1})

  @app.route('/chassis_config')
  def chassis_config():
    chassis.ensureready()

    # Render table
    return render_template("chassis_config.html",
      wheelTable = chassis.wheelDisplayTable(),
      velocity = chassis.velocity,
      angles = chassis.angles,
      roboclaw_table = chassis.roboclaw_table())

  @app.route('/request_wheel_status', methods=['POST'])
  def request_wheel_status():
    chassis.ensureready()
    wheelInfo = dict()
    for wheel in chassis.wheels:
      name = wheel['name']
      velocity = chassis.velocity[name]
      angle = chassis.angles[name]
      wheelInfo[name] = dict()
      wheelInfo[name]['velocity'] = velocity
      wheelInfo[name]['angle'] = angle
    return json.jsonify(wheelInfo)

  @app.route('/steering_trim', methods=['GET','POST'])
  def steering_trim():
    chassis.ensureready()

    # Find all the wheels that we can steer
    steered_wheels = list()
    for wheel in chassis.wheels:
      name = wheel['name']
      if wheel['steering']:
        steered_wheels.append(name)

    if request.method == 'GET':
      return render_template("steering_trim.html",
        steered_wheels=steered_wheels)
    else:
      adjWheel = request.form['wheel']

      if "move_to" in request.form:
        chassis.steer_wheel(adjWheel, int(request.form['move_to']))

        return json.jsonify({'wheel':adjWheel, 'move_to':request.form['move_to']})
      elif "set_zero" in request.form:
        chassis.steer_setzero(adjWheel)

        return json.jsonify({'wheel':adjWheel, 'set_zero':request.form['set_zero']})
      else:
        raise ValueError("Invalid POST parameters.")
