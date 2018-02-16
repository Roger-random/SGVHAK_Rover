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
import roboclaw_wrapper

# Each instance of this class represents one group of RoboClaw connected
# together on the same packet serial network. Up to eight addressible
# RoboClaws and two motors per controller = up to 16 motors.
rclaw = roboclaw_wrapper.roboclaw_wrapper()

# Rover chassis geometry, including methods to calculate wheel angle and
# velocity based on chassis geometry.
chassis = roverchassis.chassis()

class main_menu:

  @app.route('/')
  def index():
    return render_template("index.html")

  @app.route('/stop_motors')
  def stop_motors():
    flash("Stop Motor Placeholder","success")
    return render_template("index.html")

  @app.route('/drive')
  def drive():
    return render_template("drive.html",
      ui_angle=70)

  @app.route('/drive_command', methods=['POST'])
  def drive_command():
    angle = float(request.form['angle'])*45/100
    magnitude = float(request.form['magnitude'])

    if angle >= 0:
      radius = chassis.radius_for('front_right', angle)
    else:
      radius = chassis.radius_for('front_left', angle)

    chassis.updateMotion(magnitude, radius)

    return json.jsonify({'Success':1})

  @app.route('/chassis_config')
  def chassis_config():
    if len(chassis.wheels)==0:
      chassis.testWheels()
      chassis.updateMotion(0)
    if not rclaw.connected():
      rclaw.connect(dict([('port','TEST')]))

    # Render table
    return render_template("chassis_config.html",
      wheelTable = chassis.wheelDisplayTable(),
      velocity = chassis.velocity,
      angles = chassis.angles,
      roboclaw_table = chassis.roboclaw_table(rclaw))

  @app.route('/chassis_test')
  def chassis_test():
    flash("chassis_test placeholder","success")
    return render_template("index.html")
