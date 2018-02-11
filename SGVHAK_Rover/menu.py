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
    return render_template("chassis_config.html",
      wheels = chassis.wheels)

  @app.route('/chassis_test')
  def chassis_test():
    flash("chassis_test placeholder","success")
    return render_template("index.html")