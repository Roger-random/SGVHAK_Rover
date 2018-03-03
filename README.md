# SGVHAK Rover
Main UI server and associated software for SGVHAK rover project.

Setup for development & testing
---
Written under `python 2.7.14` with associated `pip 9.0.1`
- Python version dictated by Ion Motion Control's RoboClaw Python API, which is written for 2.7. See http://forums.ionmc.com/viewtopic.php?f=2&t=542

### `virtualenv` recommended to help keep Python libraries separate.
- Install virtualenv `pip install virtualenv`
- Switch to SGVHAK_Rover directory
- Create new virtual environment `python -m virtualenv venv`
- Activate virtual environment `. venv/bin/activate`. Prompt should now be prepended with `(venv)`
  
### Install dependencies
- All dependencies are described in setup.py and can be installed with `pip install -e .`

### Start Flask
- `export FLASK_APP=SGVHAK_Rover`
- To enable debugging (warning: development only) `export FLASK_DEBUG=1`
- `flask run`
- Open UI by pointing web browser to `http://localhost:5000`

Setup for Rover Raspberry Pi
---

- Clone this repository and set up python, pip, and virtualenv as described above. Manually launch Flask and a web browser to verify the web app launched successfully.
- Configure flask for launch on startup by editing `/etc/rc.local` and add the following just above `exit 0` at the end of that file.
```
cd /home/pi/SGVHAK_Rover
export FLASK_APP=SGVHAK_Rover
. venv/bin/activate
flask run --host=0.0.0.0 &
```
- Configure Pi to be a wireless access point by following instructions at https://www.raspberrypi.org/documentation/configuration/wireless/access-point.md
- Once complete, connect to the new Pi-hosted wireless access point and open a web browser (default URL is `http://192.168.4.1:5000`) to use rover UI.
