from flask import render_template, session, redirect, url_for
from app import app # Assuming 'app' is the Flask app instance, imported from the app package

# Note: If 'app' is not available directly, this might need adjustment
# depending on how Flask app is structured (e.g., using a Blueprint)
# For now, assuming 'app' can be imported as shown.

# Custom error handler for 403 Forbidden
@app.errorhandler(403)
def forbidden_error_handler(error):
    return "<h1>403 Forbidden - Access is forbidden</h1>", 403

# Custom error handler for accessing undefined page
@app.errorhandler(404)
def page_not_found(error):
    return "<h1>404 Not Found</h1>", 404

@app.route("/overview_new") # Added _new to avoid potential conflict if old /overview is still somehow active
def overview(): # Function name is overview, not overview_new to match url_for in template
    session_start = session.get('user_id') is not None
    curr_user_name = session.get('user_name', 'Guest')
    
    return render_template('overview_page.html', 
                           session_start=session_start,
                           curr_user_name=curr_user_name)

@app.route("/post-pre-quiz-summary_new") # Added _new
def post_prequiz_summary(): # Function name is post_prequiz_summary
    if session.get('user_id') is None:
        return redirect(url_for('display_homepage')) # Assuming display_homepage is a valid fallback

    session_start = True 
    curr_user_name = session.get('user_name', 'User')

    prequiz_score = 0
    prequiz_total_answered = 0
    prequiz_total_questions = 0
    quiz_responses_summary = []

    if 'quiz_response_list' in session and session['quiz_response_list'] and \
       isinstance(session['quiz_response_list'], list) and len(session['quiz_response_list']) >= 2:
        responses = session['quiz_response_list'][0]
        all_questions_in_prequiz = session['quiz_response_list'][1]

        if isinstance(responses, list) and isinstance(all_questions_in_prequiz, list):
            prequiz_total_answered = len(responses)
            prequiz_total_questions = len(all_questions_in_prequiz)
            prequiz_score = sum(1 for r in responses if r == 1)
            quiz_responses_summary = responses
    
    return render_template('post_prequiz_summary_page.html',
                           session_start=session_start,
                           curr_user_name=curr_user_name,
                           prequiz_score=prequiz_score,
                           prequiz_total_answered=prequiz_total_answered,
                           prequiz_total_questions=prequiz_total_questions,
                           quiz_responses=quiz_responses_summary)

@app.route("/report-history_new") # Added _new
def report_history(): # Function name is report_history
    session_start = session.get('user_id') is not None
    curr_user_name = session.get('user_name', 'Guest')
    
    if not session_start:
        return redirect(url_for('display_homepage'))

    return render_template('report_history_page.html',
                           session_start=session_start,
                           curr_user_name=curr_user_name)

@app.route("/settings_new") # Added _new
def application_settings(): # Function name is application_settings
    session_start = session.get('user_id') is not None
    curr_user_name = session.get('user_name', 'Guest')
    max_limit = session.get('max_limit_quiz', 10) 
    
    if not session_start:
        return redirect(url_for('display_homepage'))

    return render_template('settings_page.html',
                           session_start=session_start,
                           curr_user_name=curr_user_name,
                           max_limit=max_limit)
