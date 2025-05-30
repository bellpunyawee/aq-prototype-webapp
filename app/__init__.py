"""
This file is Master Server initiate file and configuration

# Adaptive Quiz App for Introduction to Project Management Course
Adaptive Quiz app version 0.1 
- Prototype version
- Standalone from KU Recommender
- Minor Changes for Input Handling and UI (still in-progress)
- Requirement Modification for UAT1a
- KLI-based UCB Implementing, not yet tested
- Adjusting Quiz Pool for UAT1a

header_template.html
model_enginev2.py
model_usercontrol.py

"""
import os
import json
import warnings

from flask import Flask, session

# Application creation
app = Flask(__name__, instance_relative_config=False)
app.secret_key = b'2\xa7\x8e\xc0\x95\xa1O)\xb3oY\xb58\x16\x00\x10'

# Configuration
app.config.from_file("conf/flask_conf.json", load=json.load)
warnings.simplefilter("ignore")

# Definition of routes
# Route with rendering templates
from app.controller import routes
# Route for requesting responses
from app.controller import responses