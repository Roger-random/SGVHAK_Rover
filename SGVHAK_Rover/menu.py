from SGVHAK_Rover import app
from flask import flash, render_template

@app.route('/')
def index():
	return render_template("index.html")

@app.route('/stop_motors')
def stop_motors():
  flash("Stop Motor Placeholder","success")
  return render_template("index.html")