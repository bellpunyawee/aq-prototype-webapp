"""
This file is route / page as display to user a real webpage
"""
# Route with template (also controller) / display rendering
from app import app
from flask import session

# Only the routes.py will need this rendering template
from flask import render_template,redirect

# Error handling for page renderer
from flask import abort

from flask import request

# Custom error handler for 403 Forbidden
@app.errorhandler(403)
def forbidden_error_handler(error):
    return "<h1>403 Forbidden - Access is forbidden</h1>", 403

# Custom error handler for accessing undefined page
@app.errorhandler(404)
def page_not_found(error):
    return "<h1>404 Not Found</h1>", 404

# default page
@app.route("/")
def display_homepage():
    if (session.get('user_id') is not None):
        session_start = True
        timer_select = session['m_duration']
        quiz_number = session['num_quiz']
        max_limit = session['max_limit_quiz']
    else:
        session_start = False
        timer_select = 10
        quiz_number = 3
        max_limit = 10

    ret_val = render_template('dashboard.html', session_start=session_start, timer_select=timer_select, quiz_number=quiz_number, max_limit=max_limit)
    
    return ret_val


@app.route("/pretest_start")
def display_pretest():
    if (session.get('user_id') is not None):
        session_start = True
    else:
        session_start = False

    ret_val = render_template('pretest_page.html', session_start=session_start)
    
    return ret_val

@app.route("/logout", methods=["GET", "POST"])
def fn_logout():
    session.clear()
    return redirect("/")