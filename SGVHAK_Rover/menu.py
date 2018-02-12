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
from flask import flash, render_template
from roverchassis import roverchassis

chassis = roverchassis()

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
    flash("Drive placeholder","success")
    return render_template("index.html")

  @app.route('/chassis_config')
  def chassis_config():
    chassis.loadDist()
    rows = set()
    columns = set()
    # Count the unique X/Y coordinates into columns/rows
    for wheel in chassis.wheels:
      rows.add(wheel['y'])
      columns.add(wheel['x'])
    # Create a dictionary of dicationaries to hold entries.
    wheelTable = dict()
    for row in rows:
      wheelTable[row] = dict()
      for column in columns:
        wheelTable[row][column] = list()
    # Put each wheel into its matching location in the table.
    for wheel in chassis.wheels:
      wheelTable[wheel['y']][wheel['x']].append(wheel)

    # Render table
    return render_template("chassis_config.html",
      wheelTable = wheelTable)

  @app.route('/chassis_test')
  def chassis_test():
    flash("chassis_test placeholder","success")
    return render_template("index.html")
