# SGVHAK Rover
Main UI server and associated software for SGVHAK rover project.
---
Written under `python 2.7.14` with associated `pip 9.0.1`
- Python version dictated by Ion Motion Control's RoboClaw Python API, which is written for 2.7. See http://forums.ionmc.com/viewtopic.php?f=2&t=542

### `virtualenv` recommended to help keep Python libraries separate.
- Install virtualenv `pip install virtualenv`
- Switch to SGVHAK_Rover directory
- Create new virtual environment `python -m virtualenv venv`
- Activate virtual environment `. venv/bin/activate`. Prompt should now be prepended with `(venv)`
  
### Install dependencies
- `pip install -e .`

### Start Flask
- `export FLASK_APP=SGVHAK_Rover`
- To enable debugging (warning: development only) `export FLASK_DEBUG=1`
- `python -m flask run`
- Open UI by pointing web browser to `http://localhost:5000`
