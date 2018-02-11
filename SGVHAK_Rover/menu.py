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
