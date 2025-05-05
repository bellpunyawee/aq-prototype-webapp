#!/bin/sh
set -e

# Run the user generation script
python3.12 app/model/model_usercontrol.py

# Start the Flask application
exec python3.12 server_frontend.py 0