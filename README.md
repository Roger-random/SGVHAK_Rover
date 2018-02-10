# SGVHAK Rover
Main UI server and associated software for SGVHAK rover project.
---
Written under `python 3.6.3` with associated `pip 9.0.1`

### `virtualenv` recommended to help keep Python libraries separate.
- Install virtualenv `pip3 install virtualenv`
- Switch to SGVHAK_Rover directory
- Create new virtual environment `python3 -m virtualenv venv`
- Activate virtual environment `. venv/bin/activate`. Prompt should now be prepended with `(venv)`
  
### Install dependencies
- `pip3 install -e .`

### Start Flask
- `export FLASK_APP=SGVHAK_Rover`
- To enable debugging (warning: development only) `export FLASK_DEBUG=1`
- `python3 -m flask run`
- Open UI by pointing web browser to `http://localhost:5000`
