"""
This file is route / page as display to user a real webpage
"""
# Route with template (also controller) / display rendering
from app import app
from flask import session

# Only the routes.py will need this rendering template
from flask import render_template, jsonify

# Error handling for page renderer
from flask import abort

''' ====== Added LTI ====== '''
import os
import pprint
from werkzeug.utils import redirect

from flask_caching import Cache
from werkzeug.exceptions import Forbidden
from pylti1p3.contrib.flask import FlaskOIDCLogin, FlaskMessageLaunch, FlaskRequest, FlaskCacheDataStorage
from pylti1p3.tool_config import ToolConfJsonFile

class ExtendedFlaskMessageLaunch(FlaskMessageLaunch):

    def validate_nonce(self):
        iss = self.get_iss()
        deep_link_launch = self.is_deep_link_launch()
        if iss == "http://imsglobal.org" and deep_link_launch:
            return self
        return super().validate_nonce()

# fetch LTI config ('aq.json')
def get_lti_config_path():
    return os.path.join(app.root_path,'conf', 'aq.json')

cache = Cache(app)
def get_launch_data_storage():
    return FlaskCacheDataStorage(cache)

''' ======================== '''

# Custom error handler for 403 Forbidden
@app.errorhandler(403)
def forbidden_error_handler(error):
    return "<h1>403 Forbidden - Access is forbidden</h1>", 403

# Custom error handler for accessing undefined page
@app.errorhandler(404)
def page_not_found(error):
    return "<h1>404 Not Found</h1>", 404

# LTI login OIDC
@app.route("/login/", methods=['GET','POST'])
def login():
    # LTI 1.3
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    launch_data_storage = get_launch_data_storage()

    flask_request = FlaskRequest()
    target_link_uri = flask_request.get_param('target_link_uri')
    if not target_link_uri:
        raise Exception('Missing "target_link_uri" param')

    oidc_login = FlaskOIDCLogin(flask_request, tool_conf, launch_data_storage=launch_data_storage)
    return oidc_login\
        .enable_check_cookies()\
        .redirect(target_link_uri)

# default page
# @app.route("/")
# def display_homepage():
#     if (session.get('user_id') is not None):
#         session_start = True
#         timer_select = session['m_duration']
#         quiz_number = session['num_quiz']
#         max_limit = session['max_limit_quiz']
#     else:
#         session_start = False
#         timer_select = 10
#         quiz_number = 3
#         max_limit = 10

#     ret_val = render_template('dashboard.html', session_start=session_start, timer_select=timer_select, quiz_number=quiz_number, max_limit=max_limit)
    
#     return ret_val

#  launch message for LTI
@app.route("/launch/", methods=['GET','POST'])
def display_homepage():
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    flask_request = FlaskRequest()
    launch_data_storage = get_launch_data_storage()
    message_launch = ExtendedFlaskMessageLaunch(flask_request, tool_conf, launch_data_storage=launch_data_storage)
    message_launch_data = message_launch.get_launch_data()

    # pprint.pprint(message_launch_data)
    # message_launch_data['https://purl.imsglobal.org/spec/lti/claim/lti1p1']['user_id']
    if session.get('user_id') is not None:
        print("not None")
        session_start = True
        timer_select = 10
        quiz_number = 3
        max_limit = 10
    else:
        print("None")
        session_start = False
        timer_select = 10
        quiz_number = 3
        max_limit = 10

    tpl_kwargs = {
        'session_start': session_start,
        'timer_select': timer_select,
        'quiz_number': quiz_number,
        'max_limit': max_limit,
        'page_title': 'Dashboard',
        'is_deep_link_launch': message_launch.is_deep_link_launch(),
        'launch_data': message_launch.get_launch_data(),
        'launch_id': message_launch.get_launch_id(),
        'curr_user_name': message_launch_data.get('name', '')
    }
    ret_val = render_template('dashboard.html', **tpl_kwargs)

    return ret_val

@app.route('/jwks/', methods=['GET'])
def get_jwks():
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    return jsonify({'keys': tool_conf.get_jwks()})

@app.route("/pretest_start/", methods=['POST'])
def display_pretest():
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    flask_request = FlaskRequest()
    launch_data_storage = get_launch_data_storage()
    message_launch = ExtendedFlaskMessageLaunch(flask_request, tool_conf, launch_data_storage=launch_data_storage)
    message_launch_data = message_launch.get_launch_data()
    pprint.pprint(message_launch_data)
    
    if (session.get('user_id') is not None):
        session_start = True
    else:
        session_start = False

    ret_val = render_template('pretest_page.html', session_start=session_start)
    return ret_val

@app.route("/logout/", methods=["GET", "POST"])
def fn_logout():
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    flask_request = FlaskRequest()
    launch_data_storage = get_launch_data_storage()
    message_launch = ExtendedFlaskMessageLaunch(flask_request, tool_conf, launch_data_storage=launch_data_storage)
    message_launch_data = message_launch.get_launch_data()

    pprint.pprint(message_launch_data)
    session.clear()
    return redirect("/")