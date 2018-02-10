#!/usr/bin/python3
import os
from flask import Flask
app = Flask(__name__)

# Randomly generated key means session cookies will not be usable across
# instances. This is acceptable for now but may need changing later.
app.secret_key = os.urandom(24)

import SGVHAK_Rover.menu