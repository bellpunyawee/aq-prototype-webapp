"""
This file is Server front running for Report Webpage application.
"""
import ctypes, sys, os
from app import app
from app.globalclass import osbasic as OSBASIC
from flask import session

def debug_mode_running(config):
    if sys.platform == "win32":
        ctypes.windll.kernel32.SetConsoleTitleW("Adaptive Quiz server - Debug mode")
    app.run(debug=True, host=config["DEBUG_HOST"], port=config["DEBUG_PORT"])

def production_mode_running(config):
    if sys.platform == "win32":
        ctypes.windll.kernel32.SetConsoleTitleW("Adaptive Quiz server")
    from waitress import serve # pip install waitress
    from paste.translogger import TransLogger # pip install paste
    port = int(os.environ.get('PORT', config["PORT"]))
    serve(TransLogger(app, setup_console_handler=False), host=config["HOST"], port=port)

def print_exit():
    print("Default (debugging mode): python server_frontend.py")
    print("Debugging mode: python server_frontend.py 0")
    print("Production mode: python server_frontend.py 1")
    exit(-1)

# Default debug running mode
load_config = OSBASIC.Fundamental.loadConfiguration("/conf/flask_conf.json")
if (load_config == {}):
    print("Configuration is not found in \"conf\" folder")
    exit(-1)

if len(sys.argv) < 2:
    debug_mode_running(load_config)
elif len(sys.argv) == 2:
    if (sys.argv[1] == "0"):
        debug_mode_running(load_config)
    elif (sys.argv[1] == "1"):
        production_mode_running(load_config)
    else:
        print_exit()
else:
    print_exit()


