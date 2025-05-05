"""
This file is responses throw back to requester
"""
# Non rendering template Route (controller), this is for getting GET/POST anything that is not displaying to client
from app import app
from ..model import *

from ..globalclass import crypto as Crypto

from flask import jsonify, request, session
import hashlib, time, os, pprint
from flask_caching import Cache


# Single quiz engine to optimize calling procedure
GLOBAL_QUIZ_ENGINE = model_enginev2.AdaptiveQuiz()
# Temporary memory, this memory shall be lived until the server is shutdown.
# Due to session is unable to store complex object and pickle is unusable, this is the way.
G_MEMORY = {}
P_MEMORY = {}
    
def generateSessionID():
    return Crypto.CryptoLib.generate_sha256(str(time.time()))

# Application start
@app.route("/access/", methods=["POST"])
def fn_login():
    if request.method == "POST":
        data = request.get_json()
        login_status = model_usercontrol.UserAuthentication(username=data['username'], password=data['password'])
        if ((session.get('user_id') is None)):
            if login_status.get_login_status() == True:
                session['session_id'], session['user_id'] = str(login_status.get_user_id()) + "_" + generateSessionID(), login_status.get_user_id()
                # Default settings
                session['m_duration'] = 10
                session['num_quiz'] = 3
                session['num_cell'] = 3
                session['max_limit_quiz'] = 10
                session['check_cell'] = []

                if (data['remember'] == True):
                    session.permanent = True
                else:
                    session.permanent = False
                response = {"result":"success"}
                
            else:
                response = {"result":"fail", "status": "Username/Password is incorrect"}
        else:
            if ((session.get('user_id') is None) or (session.get('user_id') == -1)):
                session.clear() # Force logout
                response = {"result":"fail", "status": "No record on loggin in"}
            else:
                response = {"result":"fail", "status": "Already logged in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}

    print("USERID", session)
    print(response)
    return jsonify(response)

@app.route("/req_save_settings", methods=["POST"])
def fn_req_save_settings():
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                ####################################################### Function start here
                data_json = request.get_json()
                allow_processing, num_cell, num_quiz, check_cell, m_duration, max_limit_quiz = sub_stq_check_data(data_json)
                if (allow_processing):
                    session['m_duration'] = m_duration
                    session['num_quiz'] = num_quiz
                    session['num_cell'] = num_cell
                    session['check_cell'] = check_cell
                    session['max_limit_quiz'] = max_limit_quiz
                    response = {"result":"success"}
                else:
                    response = {"result":"fail", "status": "Data input is invalid/incomplete"}
                ######################################################### Function end here
            else:
                session.clear() # Force logout
                response = {"result":"fail", "status": "Session info expired"}
        else:
            session.clear() # Force logout
            response = {"result":"fail", "status": "No record on loggin in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}

    return jsonify(response)

@app.route("/req_userinfo", methods=["POST"])
def fn_req_userinfo(): # Function goes two ways, either staying on dashboard or going to quiz
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                pretest_status = model_dbquery.UserDataQuery().get_user_pretest(session['user_id'])
                if (pretest_status == True):
                    if (G_MEMORY.get(session['user_id']) != None):
                        session['quiz_start'] = True
                    else:
                        session['quiz_start'] = False
                    full_name = login_status.get_user_info()
                    disclaimer_text = model_dbquery.GeneralDataQuery.get_disclaimer()
                    photo_string = model_dbquery.UserDataQuery.get_user_photo(session['user_id'])
                    session['n_attempt'] = model_dbquery.UserDataQuery.get_latest_attempt(session['user_id']) + 1
                    # ability
                    learner_ability, user_timestamp = model_dbquery.UserDataQuery.get_user_abilities(session['user_id'])
                    ability_list = {"Timestamp": user_timestamp, "Data Point": learner_ability}
                    # score
                    user_ans_number_list, user_quiz_number_list, user_score, n_attempt = model_dbquery.UserDataQuery.get_user_scores(session['user_id'])
                    score_list = {"Timestamp": user_timestamp, "Data Point": user_score, "Extrainfo": [user_ans_number_list, user_quiz_number_list]}
                    # mastery
                    mastery_list = model_dbquery.UserDataQuery.get_user_mastery(session['user_id'])
                    response = {"result":"success", 
                                "full_name": full_name, 
                                "user_id": session['user_id'], 
                                "session_active":session['quiz_start'],
                                "settings": [session['num_cell'], session['check_cell']],
                                "disclaimer": disclaimer_text,
                                "photo_string":photo_string,
                                "next_attempt": session['n_attempt'],
                                "pretest_done": pretest_status,
                                "learner_ability": ability_list,
                                "mastery_list": mastery_list,
                                "score_list": score_list}
                else:
                    session['quiz_start'] = False
                    try:
                        del(G_MEMORY[session['user_id']]) # Force remove
                    except:
                        pass

                    if (session.get('prequiz_start') is None):
                        pretest_start = False
                    else:
                        pretest_start = session.get('prequiz_start')

                    response = {"result":"success", 
                                "pretest_start":pretest_start,
                                "pretest_done": pretest_status}
            else:
                session.clear() # Force logout
                response = {"result":"fail", "status": "Session info expired"}
        else:
            session.clear() # Force logout
            response = {"result":"fail", "status": "No record on loggin in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}

    return jsonify(response)

@app.route("/req_fetch_report_score", methods=["POST"])
def fn_req_fetch_report_score():
    if request.method == "POST":
        if session.get('user_id') is not None:
            login_status = model_usercontrol.UserAuthentication(
                login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status():
                session['n_attempt'] = model_dbquery.UserDataQuery.get_latest_attempt(
                    session['user_id']) + 1
                textbox_data = model_dbquery.GeneralDataQuery.get_textboxdata()
                # print(session['n_attempt'])
                if session['n_attempt'] > 1:
                    learner_ability, user_timestamp = model_dbquery.UserDataQuery.get_user_abilities(
                        session['user_id'])
                    showing_ability = []
                    if len(learner_ability) > 0:
                        selected_quiz, response_list, choice_list, timestamp = model_dbquery.UserDataQuery.get_report_data(
                            session['user_id'], (session['n_attempt'] - 1))
                        if selected_quiz:
                            cell_index = []
                            for i in range(len(selected_quiz)):
                                cell_index.append(model_mapping.GenQuizPool.get_cell_index(
                                    selected_quiz[i]))
                            cell_index = set(cell_index)
                            cell_index = list(zip(*cell_index))
                            cell_index = cell_index[0]
                            if len(learner_ability) > 1:
                                showing_ability = [
                                    learner_ability[-2], learner_ability[-1]]
                                showing_timestamp = [
                                    user_timestamp[-2], user_timestamp[-1]]
                            else:
                                showing_ability = [learner_ability[-1]]
                                showing_timestamp = [user_timestamp[-1]]
                            total_second_used = max(timestamp) - min(timestamp)
                            total_quiz = len(selected_quiz)
                            total_correct_ans = sum(response_list)
                        else:
                            total_second_used = 0
                            total_quiz = 0
                            total_correct_ans = 0
                            cell_index = []
                            if len(learner_ability) > 1:
                                showing_ability = [
                                    learner_ability[-2], learner_ability[-1]]
                                showing_timestamp = [
                                    user_timestamp[-2], user_timestamp[-1]]
                            else:
                                showing_ability = [learner_ability[-1]]
                                showing_timestamp = [user_timestamp[-1]]
                            response_list = []
                    else:
                        total_second_used = 0
                        total_quiz = 0
                        total_correct_ans = 0
                        cell_index = []
                        showing_ability = []
                        showing_timestamp = []
                        response_list = []
                        choice_list = []
                else:
                    total_second_used = 0
                    total_quiz = 0
                    total_correct_ans = 0
                    cell_index = []
                    showing_ability = []
                    showing_timestamp = []
                    response_list = []
                    choice_list = []

                quiz_streak = []
                for i in range(len(response_list)):
                    if choice_list[i] == 0:
                        quiz_streak.append(-1)
                    else:
                        quiz_streak.append(response_list[i])

                chart_data = {"Data Point": showing_ability,
                              "Timestamp": showing_timestamp}
                
                # Score
                user_ans_number_list, user_quiz_number_list, user_score, n_attempt = model_dbquery.UserDataQuery.get_user_scores(session['user_id'])
                showing_score = user_score[-2:] if len(user_score) > 1 else user_score[-1:]
                score_list = {"Timestamp": user_timestamp[-2:] if len(user_timestamp) > 1 else user_timestamp[-1:], "Data Point": user_ans_number_list[-2:], "Extrainfo": [user_ans_number_list[-2:], user_quiz_number_list[-2:]]}
                
                response = {"result": "success",
                            "total_second_used": total_second_used,
                            "total_quiz": total_quiz,
                            "total_correct_ans": total_correct_ans,
                            "cell_index": cell_index,
                            "learner_ability": chart_data,
                            "n_attempt": session['n_attempt'],
                            "quiz_streak": quiz_streak,
                            "your_answer": choice_list,
                            "textboxdata": textbox_data,
                            "score_list": score_list}

            else:
                session.clear()
                response = {"result": "fail", "status": "Session info expired"}
        else:
            session.clear()
            response = {"result": "fail", "status": "No record on logging in"}
    else:
        response = {"result": "fail", "status": "Wrong method"}

    return jsonify(response)


@app.route("/req_fetch_report", methods=["POST"])
def fn_req_fetch_report(): # Function goes two ways, either staying on dashboard or going to quiz
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                # ability
                session['n_attempt'] = model_dbquery.UserDataQuery.get_latest_attempt(session['user_id']) + 1
                # For future using
                textbox_data = model_dbquery.GeneralDataQuery.get_textboxdata()
                if (session['n_attempt'] > 1):
                    learner_ability, user_timestamp = model_dbquery.UserDataQuery.get_user_abilities(session['user_id'])
                    showing_ability = []
                    if (len(learner_ability) > 0):
                        selected_quiz, response_list, choice_list, timestamp = model_dbquery.UserDataQuery.get_report_data(session['user_id'], (session['n_attempt'] - 1))
                        if (selected_quiz != []):
                            cell_index = []
                            for i in range(0, len(selected_quiz)):
                                cell_index.append(model_mapping.GenQuizPool.get_cell_index(selected_quiz[i]))
                            cell_index = set(cell_index) # remove duplication
                            cell_index = list(zip(*cell_index))
                            cell_index = cell_index[0]
                            if (len(learner_ability) > 1):
                                showing_ability = [learner_ability[-2], learner_ability[-1]]
                                showing_timestamp = [user_timestamp[-2], user_timestamp[-1]]
                            else:
                                showing_ability = [learner_ability[-1]]
                                showing_timestamp = [user_timestamp[-1]]
                            total_second_used = max(timestamp) - min(timestamp)
                            total_quiz = len(selected_quiz)
                            total_correct_ans = sum(response_list)
                        else:
                            total_second_used = 0
                            total_quiz = 0
                            total_correct_ans = 0
                            cell_index = []
                            if (len(learner_ability) > 1):
                                showing_ability = [learner_ability[-2], learner_ability[-1]]
                                showing_timestamp = [user_timestamp[-2], user_timestamp[-1]]
                            else:
                                showing_ability = [learner_ability[-1]]
                                showing_timestamp = [user_timestamp[-1]]
                            response_list = []
                    else:
                        total_second_used = 0
                        total_quiz = 0
                        total_correct_ans = 0
                        cell_index = []
                        showing_ability = []
                        showing_timestamp = []
                        response_list = []
                        choice_list = []
                else:
                    total_second_used = 0
                    total_quiz = 0
                    total_correct_ans = 0
                    cell_index = []
                    showing_ability = []
                    showing_timestamp = []
                    response_list = []
                    choice_list = []

                quiz_streak = []
                for i in range(0, len(response_list)):
                    if (choice_list[i] == 0):
                        quiz_streak.append(-1) 
                    else:
                        quiz_streak.append(response_list[i])

                chart_data = {"Data Point": showing_ability, "Timestamp": showing_timestamp}

                response = {"result":"success", 
                            "total_second_used": total_second_used,
                            "total_quiz": total_quiz,
                            "total_correct_ans": total_correct_ans,
                            "cell_index": cell_index,
                            "learner_ability": chart_data,
                            "n_attempt":session['n_attempt'],
                            "quiz_streak": quiz_streak,
                            "your_answer": choice_list,
                            "textboxdata": textbox_data}

            else:
                session.clear() # Force logout
                response = {"result":"fail", "status": "Session info expired"}
        else:
            session.clear() # Force logout
            response = {"result":"fail", "status": "No record on loggin in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}

    return jsonify(response)

@app.route("/req_get_explanation_history", methods=["POST"])
def fn_req_get_explanation_history():
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:

                selected_quiz, response_list, choice_list, timestamp = model_dbquery.UserDataQuery.get_report_data(session['user_id'], session['n_attempt'] - 1)
                data = request.get_json()
                quiz_index = int(data['answer_id']) - 1
                question_data = model_mapping.GenQuizPool.get_question_data(selected_quiz[quiz_index])
                explanation_data = model_mapping.GenQuizPool.get_explanation_data(selected_quiz[quiz_index])

                # I don't know case
                if (choice_list[quiz_index] == 0):
                    answer_text = "I don't know"
                else:
                    answer_text = question_data[choice_list[quiz_index]]

                response = {"result":"success", "question_text": question_data[0], "answer_text": answer_text, "explanation_text": explanation_data}

            else:
                session.clear() # Force logout
                response = {"result":"fail", "status": "Session info expired"}
        else:
            session.clear() # Force logout
            response = {"result":"fail", "status": "No record on loggin in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}

    return jsonify(response)

@app.route("/req_submit_finish_query", methods=["POST"])
def fn_req_submit_finish_query():
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                if (session['n_attempt'] > 1):
                    data = request.get_json()
                    model_dbquery.UserDataQuery.submit_user_query(session['user_id'], (session['n_attempt'] - 1), data['query'], int(time.time()))
                    response = {"result":"success", "status": "Query has been submitted."}
                else:
                    response = {"result": "fail", "status": "No permission to submit yet, please take an attempt at least once"}
            else:
                session.clear() # Force logout
                response = {"result":"fail", "status": "Session info expired"}
        else:
            session.clear() # Force logout
            response = {"result":"fail", "status": "No record on loggin in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}

    return jsonify(response)

@app.route("/req_start_pre_quiz", methods=["POST"])
def fn_req_start_pre_quiz():
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                model_dbquery.UserDataQuery.delete_residual_user_activity(session['user_id'], 1)
                session['prequiz_start'] = True
                session['quiz_response_list'] = model_mapping.GenQuizPool.generate_p_quiz_pool() # response_list, cell_index_list, question_list
                session['selecting_index'] = 0
                response = {"result": "success"}
            else:
                session.clear() # Force logout
                response = {"result":"fail", "status": "Session info expired"}
        else:
            session.clear() # Force logout
            response = {"result":"fail", "status": "No record on loggin in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}

    return jsonify(response)

@app.route("/req_fetch_pre_quiz", methods=["POST"])
def fn_req_fetch_pre_quiz():
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                if (len(session['quiz_response_list'][0]) < len(session['quiz_response_list'][1])):
                    question_id = session['quiz_response_list'][2][session['selecting_index']]
                    data = model_mapping.GenQuizPool().get_question_data(question_id)
                    P_MEMORY['question'] = data # store pretest data
                    response = {"result" : "success", \
                                    "question_no":(len(session['quiz_response_list'][0]) + 1), \
                                    "question":data[0], \
                                    "ans_1": data[1], \
                                    "ans_2": data[2], \
                                    "ans_3": data[3], \
                                    "ans_4": data[4],
                                    "timestart": 0,
                                    "current_ts": 0,
                                    "m_duration": 100,
                                    "quiz_streak":session['quiz_response_list'][0],
                                    "total_quiz":len(session['quiz_response_list'][2])}
                else:
                    pretest_status = model_dbquery.UserDataQuery().get_user_pretest(session['user_id'])
                    try:
                        del(session['prequiz_start'])
                        del(session['quiz_response_list'])
                        del(session['selecting_index'])
                    except:
                        pass
                    response = {"result":"success", 
                                "question": "",
                                "pretest_done": pretest_status}
                
            else:
                session.clear() # Force logout
                response = {"result":"fail", "status": "Session info expired"}
        else:
            session.clear() # Force logout
            response = {"result":"fail", "status": "No record on loggin in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}

    return jsonify(response)

@app.route("/req_submit_pre_quiz", methods=["POST"])
def fn_req_submit_pre_quiz():
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                if (len(session['quiz_response_list'][0]) <= len(session['quiz_response_list'][1])):
                    
                    if (request.json['selected_choice'] == 0):
                        idk = True
                        user_correct_ans = -1
                        answer_db = "I don't know"
                    else:
                        idk = False
                        user_correct_ans = model_mapping.GenQuizPool.get_learner_response(session['quiz_response_list'][2][session['selecting_index']],request.json['selected_choice'])
                        answer_db = P_MEMORY['question'][request.json['selected_choice']] # user answer
                    
                    question_id = session['quiz_response_list'][2][session['selecting_index']]
                    # print(session['quiz_response_list']) # link back to quiz_pool
                    answer_index = model_mapping.GenQuizPool.get_answer_index(question_id) # retrieved answer index from quiz_pool database
                    correct_ans = P_MEMORY['question'][answer_index]
                    rationale = model_mapping.GenQuizPool.get_rationale(question_id)
                    session['quiz_response_list'][0].append(user_correct_ans)
                    if user_correct_ans == -1:
                        user_correct_ans = 0
                    model_dbquery.UserDataQuery.log_user_activity(session['user_id'],model_dbquery.UserDataQuery.get_username(session['user_id']), 1, question_id, P_MEMORY['question'][0], request.json['selected_choice'], user_correct_ans, answer_db, correct_ans, rationale, int(time.time()))
                    explanation = model_mapping.GenQuizPool().get_explanation_data(session['quiz_response_list'][2][session['selecting_index']])

                    # Response will be returned either same question or new question.
                    
                    response = {"result":"success", "learner_feedback":"", "explanation":explanation}

                    if (user_correct_ans == 1):
                        response['learner_feedback'] = "pass"
                    else:
                        if (idk == False):
                            response['learner_feedback'] = "fail"
                        else:
                            response['learner_feedback'] = "idk"
                    session['selecting_index'] += 1
                    
                    if (session['selecting_index'] == len(session['quiz_response_list'][1])):
                        # Create pre-test table
                        # Normalize for prequiz IDK to be 0
                        normalize = []
                        for i in range(0, len(session['quiz_response_list'][0])):
                            if session['quiz_response_list'][0][i] == -1:
                                normalize.append(0)
                            else:
                                normalize.append(session['quiz_response_list'][0][i])
                        model_dbquery.UserDataQuery.submit_user_pretest(session['user_id'], normalize, session['quiz_response_list'][1])
                        # Create mastery table
                        model_dbquery.UserDataQuery.create_mastery_slot(session['user_id'])
                        # Update mastery table
                        cell_mastery = model_dbquery.UserDataQuery.update_mastery_slot_pretest(session['user_id'])
                        current_ability_cell = GLOBAL_QUIZ_ENGINE.pre_ability(cell_mastery)
                        # Create train table
                        model_dbquery.UserDataQuery.create_train_slot(session['user_id'])
                        # ability assign for pretest
                        model_dbquery.UserDataQuery.pre_ability_update(session['user_id'], 0 , current_ability_cell[0], 1)
                else:
                        # In case that question data unable to fetch due to learner already got all knowledges
                    response = {"result" : "success", "question":""}
            else:
                session.clear() # Force logout
                response = {"result":"fail", "status": "Session info expired"}
        else:
            session.clear() # Force logout
            response = {"result":"fail", "status": "No record on loggin in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}

    return jsonify(response)

@app.route("/req_start_quiz", methods=["POST"])
def fn_start_quiz():
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                ####################################################### Function start here
                if (G_MEMORY.get(session['user_id']) is None):
                    # model_dbquery.UserDataQuery.delete_residual_user_activity(session['user_id'], session['n_attempt'])
                    data = sub_create_dts(session['num_cell'], session['num_quiz'], session['check_cell'])
                    prev_learner_ab = model_dbquery.UserDataQuery.get_previous_ability(session['user_id'])
                    data = sub_mapping_activate_quiz(data, session['user_id'],prev_learner_ab)
                    quiz_engine_input = {"start_ts": int(time.time()), \
                                         "duration": session['m_duration'], \
                                         "num_cell": session['num_cell'], \
                                         "num_quiz": session['num_quiz'], \
                                         "check_cell": session['check_cell']} # Call assignment last to avoid timer starting, but acquisitioning is not yet completed.
                    session['quiz_start'] = True
                    G_MEMORY[session['user_id']] = {"sqe": data, "quiz_engine_input": quiz_engine_input}
                    response = {"result":"success"}
                else:
                    response = {"result":"fail", "status":"Session has been started, abort attempt first to start another"}
                    
                ######################################################### Function end here
            else:
                session.clear() # Force logout
                response = {"result":"fail", "status": "Session info expired"}
        else:
            session.clear() # Force logout
            response = {"result":"fail", "status": "No record on loggin in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}

    return jsonify(response)

@app.route("/req_abort_attempt", methods=["POST"])
def fn_abort_attempt():
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                # Delete any attempt that was in completed
                model_dbquery.UserDataQuery.delete_residual_user_activity(session['user_id'], session['n_attempt'])
                try:
                    del(G_MEMORY[session['user_id']])
                except KeyError:
                    pass # Clean in either way
                session['quiz_start'] = False
                response = {"result":"success", "status": "Attempt has been aborted."}
            else:
                session.clear() # Force logout
                response = {"result":"fail", "status": "Session info expired"}
        else:
            session.clear() # Force logout
            response = {"result":"fail", "status": "No record on loggin in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}

    return jsonify(response)

@app.route("/req_fetch_question", methods=["POST"])
def fn_fetch_question():
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                if (G_MEMORY.get(session['user_id']) is not None):
                    json_data = request.get_json()
                    client_timeout = json_data['timeout']
                    data = G_MEMORY[session['user_id']]['sqe']
                    if ((data['question_data'] == None) or # Case initiating from session creation
                        (len(data['append_select_quiz']) <= len(data['append_response_list']))):  # Case there is already data in G_MEMORY, do nothing
                        corrected_quiz = model_dbquery.UserDataQuery.fetch_solved_quiz(session['user_id'], session['n_attempt']-1) # new added
                        temp_quiz = model_dbquery.UserDataQuery.fetch_temp_quiz(session['user_id'], session['n_attempt'])
                        data = sub_mapping_fetch_quiz(data, session['max_limit_quiz'], client_timeout, corrected_quiz, temp_quiz)
                        # data = sub_mapping_fetch_quiz(data, session['max_limit_quiz'], client_timeout)
                        G_MEMORY[session['user_id']]['sqe'] = data # Save back to temp memory
                        # Response will be returned either same question or new question.
                        
                    else:
                        # some error encounter, extreme condition like timeout
                        if ((data['timeout'] == True) or (client_timeout == True)):
                            data = sub_mapping_fetch_quiz(data, session['max_limit_quiz'], client_timeout)

                        # Otherwise, do nothing
                    # # Shuffle the option: store the original options
                    # original_options = [
                    #     data['question_data'][1],
                    #     data['question_data'][2],
                    #     data['question_data'][3],
                    #     data['question_data'][4]
                    # ]

                    # # Shuffle the options
                    # shuffled_options = original_options[:]
                    # import random
                    # random.shuffle(shuffled_options)
                    # # Map the original answers to their new shuffled positions
                    # # shuffled_answer_mapping = {original_options[i]: shuffled_options[i] for i in range(4)}    #original_options: shuffled_options
                    # G_MEMORY['shuffle'] = shuffled_options

                    total_quiz = ((data['num_cell'] * data['num_quiz']) if session['max_limit_quiz'] > (data['num_cell'] * data['num_quiz']) else session['max_limit_quiz'])
                    response = {"result" : "success", \
                                    "question_no":len(data['append_select_quiz']), \
                                    "question":data['question_data'][0], \
                                    "ans_1":data['question_data'][1], \
                                    "ans_2":data['question_data'][2], \
                                    "ans_3":data['question_data'][3], \
                                    "ans_4":data['question_data'][4],
                                    "timestart": G_MEMORY[session['user_id']]['quiz_engine_input']['start_ts'],
                                    "current_ts": int(time.time()),
                                    "m_duration": G_MEMORY[session['user_id']]['quiz_engine_input']['duration'],
                                    "quiz_streak":data['append_response_list'],
                                    "total_quiz":total_quiz}
                    
                    
                        
                    # Overriding the data for special condition
                    if (data['session_complete'] == True):
                        mastery_data, learner_ab_cell = GLOBAL_QUIZ_ENGINE.finalize_mastery(data['initial_cell'], data['first_learner_ab_cell'])
                        model_dbquery.UserDataQuery.update_user_attempt(session['user_id'],data['first_learner_ab_cell'],learner_ab_cell, mastery_data)
                        
                        if (data['timeout'] == True):
                            response = {"result" : "success", "question":"", "reason":"timeout"}
                        else:
                            response = {"result" : "success", "question":"", "reason":"complete"}
                        
                        try:
                            del(G_MEMORY[session['user_id']])
                        except:
                            pass

                    if (data['no_quiz'] == True):
                        response = {"result" : "success", "question":"", "reason":"no_quiz"}
                else:
                    response = {"result":"fail", "status": "User's quiz attempting is not found on server."}
            else:
                session.clear() # Force logout
                response = {"result":"fail", "status": "Session info expired"}
        else:
            session.clear() # Force logout
            response = {"result":"fail", "status": "No record on loggin in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}

    return jsonify (response)

@app.route("/req_submit_answer", methods=["POST"])
def fn_submit_answer():
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                if (G_MEMORY.get(session['user_id']) is not None):
                    data = G_MEMORY[session['user_id']]['sqe']
                    time_data = G_MEMORY[session['user_id']]['quiz_engine_input']
                    # Response will be returned either same question or new question.
                    if (data['question_data'] != None):

                        if (request.json['selected_choice'] == 0):
                            idk = True
                            user_correct_ans = 0
                            answer_frontend = "I don't know"
                            answer_index = model_mapping.GenQuizPool.get_answer_index(data['append_select_quiz'][-1]) # retrieved answer index from quiz_pool database
                            answer_db = data['question_data'][answer_index]
                            rationale = model_mapping.GenQuizPool.get_rationale(data['append_select_quiz'][-1])
                        else:
                            idk = False
                            # # request.json['selected_choice] is retrieved from frontend (1,2,3,4)
                            # # assign variables
                            answer_frontend = data['question_data'][request.json['selected_choice']] # value of shuffled_answer_mapping from frontend --(1)
                            answer_index = model_mapping.GenQuizPool.get_answer_index(data['append_select_quiz'][-1]) # retrieved answer index from quiz_pool database
                            answer_db = data['question_data'][answer_index]
                            rationale = model_mapping.GenQuizPool.get_rationale(data['append_select_quiz'][-1])
                            # if answer_frontend == answer_db: # Correct: compare (1) with answer from DB
                            #     user_correct_ans = 1
                            #     request.json['selected_choice'] = answer_index
                            # else: # Incorrect
                            #     user_correct_ans = 0
                            #     request.json['selected_choice'] = data['question_data'].index(answer_frontend)
                            #     # try:
                            #     #     request.json['selected_choice'] = data['question_data'].index(answer_frontend)
                            #     # except ValueError:
                            #     #     request.json['selected_choice'] = -1


                            user_correct_ans = model_mapping.GenQuizPool.get_learner_response(data['append_select_quiz'][-1],request.json['selected_choice']) #question_index:int, question_answer:int

                        data = sub_mapping_answer(data, user_correct_ans, data['question_data'][0], time_data, request.json['selected_choice'], answer_frontend, answer_db, rationale) # To include
                        
                        G_MEMORY[session['user_id']]['sqe'] = data # Save back to temp memory
                        explanation = model_mapping.GenQuizPool().get_explanation_data(data['append_select_quiz'][-1])
                        response = {"result":"success", "learner_feedback":"", "explanation":explanation}

                        if (user_correct_ans == 1):
                            response['learner_feedback'] = "pass"
                        else:
                            if (idk == False):
                                response['learner_feedback'] = "fail"
                            else:
                                response['learner_feedback'] = "idk"
                    else:
                        # In case that question data unable to fetch due to learner already got all knowledges
                        response = {"result" : "success", "question":""}
                else:
                    response = {"result":"fail", "status": "User's quiz attempting is not found on server."}
            else:
                session.clear() # Force logout
                response = {"result":"fail", "status": "Session info expired"}
        else:
            session.clear() # Force logout
            response = {"result":"fail", "status": "No record on loggin in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}

    return jsonify (response)

@app.route("/req_get_total_cell", methods=["POST"])
def fn_get_total_cell():
    print("Requesting total cell")
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                cell_indices = model_dbquery.GeneralDataQuery.get_cell_indices()
                response = {"result":"success", "cell_list":cell_indices}
            else:
                session.clear() # Force logout
                response = {"result":"fail", "status": "Session info expired"}
        else:
            session.clear() # Force logout
            response = {"result":"fail", "status": "No record on loggin in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}
    return jsonify (response)

@app.route("/req_upload_profile_picture", methods=["POST"])
def fn_upload_profile_picture():
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                data = request.get_json()['file_content_string']
                model_dbquery.UserDataQuery().insert_user_photo(data, session['user_id'])
                response = {"result":"success", "message":"Profile picture successfully uploaded"}
            else:
                session.clear() # Force logout
                response = {"result":"fail", "status": "Session info expired"}
        else:
            session.clear() # Force logout
            response = {"result":"fail", "status": "No record on loggin in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}
        

    return jsonify(response)

@app.route("/req_get_profile_picture", methods=["POST"])
def fn_get_profile_picture():
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                photo_string = model_dbquery.UserDataQuery().get_user_photo(session['user_id'])
                response = {"result":"success", "photo_string": photo_string}
            else:
                session.clear() # Force logout
                response = {"result":"fail", "status": "Session info expired"}
        else:
            session.clear() # Force logout
            response = {"result":"fail", "status": "No record on loggin in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}
        

    return jsonify(response)

@app.route("/req_reset_password", methods=["POST"])
def fn_req_reset_password(): # Function goes two ways, either staying on dashboard or going to quiz
    if request.method == "POST":
        data = request.get_json()
        username = data['username']
        name_user = data['name']
        password = data['password']
        status = model_usercontrol.SystemAdminClass.reset_password(username=username, new_password=password, name_user=name_user)
        if (status == "Success"):
            response = {"result":"success", "status": "Password is successfully updated, you can login with new password now."}
        else:
            response = {"result":"fail", "status": status}
    else:
        response = {"result":"fail", "status": "Wrong method"}

    return jsonify(response)

def sub_stq_check_data(data):
# Data processor
    try:
        if (int(data['num_cell']) < 1):
            num_cell = 0
        elif (int(data['num_cell']) >= 30):
            num_cell = 30
        else:
            num_cell = int(data['num_cell'])
    except:
        # Value is not in form of integer
        num_cell = 0

    try:
        if (len(data['check_quiz']) < 1) and \
            (type(data['check_quiz']) == type([])):
            data_l = 0
            check_cell = []
        elif (len(data['check_quiz']) >= 30):
            data_l = 30
            check_cell = [i for i in range(1,(30 + 1))]
        else:
            data_l = len(data['check_quiz'])
            check_cell = [int(i) for i in data['check_quiz']]
    except:
        # Value is not in form of list
        data_l = 0
        check_cell = []
        
    try:
        num_quiz = int(data['num_quiz'])
    except:
        num_quiz = 0

    try:
        timer = int(data['timer'])
    except:
        timer = -1
        pass
    
    try:
        max_limit_quiz = int(data['max_quiz'])
    except:
        max_limit_quiz = 0
        pass

    if (((data_l == 0) and (num_cell == 0)) or
        (timer == -1) or
        (num_quiz == 0) or
        (max_limit_quiz == 0)):
        ret_val = False
    else:
        if (data_l > 0):
            num_cell = data_l
        else:
            check_cell = []
        ret_val = True

    return ret_val, num_cell, num_quiz, check_cell, timer, max_limit_quiz

def sub_create_dts(num_cell, num_quiz, user_cell):
    # Create data structure
    ret_val = {}
    ret_val['dsc_cell'] = None
    ret_val['dfc_cell'] = None
    ret_val['tagged_quiz_responses'] = None
    ret_val['initial_cell'] = None
    ret_val['total_selection_cell'] = None
    ret_val['total_selection_quiz'] = None
    ret_val['rps'] = None
    ret_val['cell_array'] = None
    ret_val['learner_ability_cell'] = None
    ret_val['first_learner_ab_cell'] = None
    ret_val['no_quiz'] = None
    ret_val['user_cell'] = (user_cell if len(user_cell) >= 1 else None)
    ret_val['available_questions'] = None
    ret_val['tagged_quiz_2'] = None
    ret_val['cell_var'] = None
    ret_val['selected_cell'] = None
    ret_val['question_data'] = None
    ret_val['quiz_var'] = None
    ret_val['selected_question'] = None
    ret_val['simulate_learner_response'] = None
    ret_val['count'] = 0
    ret_val['trigger'] = 0
    ret_val['dsc_quiz'] = None
    ret_val['dfc_quiz'] = None
    ret_val['num_cell'] = num_cell
    ret_val['num_quiz'] = num_quiz
    ret_val['imputed_train'] = None
    ret_val['remain_quiz_cell'] = 0
    ret_val['append_select_cell'] = []
    ret_val['append_select_quiz'] = []
    ret_val['append_response_list'] = []
    ret_val['input_i'] = 0
    ret_val['cell_available_questions'] = None
    ret_val['session_complete'] = False
    ret_val['timeout'] = False

    return ret_val

def sub_mapping_activate_quiz(in_sqe, user_id, prev_learner_ab): # sqe = session_quiz_engine
    sqe = in_sqe

    sqe['dsc_cell'], \
    sqe['dfc_cell'], \
    sqe['tagged_quiz_responses'], \
    sqe['initial_cell'], \
    sqe['total_selection_cell'], \
    sqe['total_selection_quiz'], \
    sqe['rps'], \
    sqe['cell_array'], \
    sqe['learner_ability_cell'], \
    sqe['no_quiz'], \
    sqe['imputed_train'] = GLOBAL_QUIZ_ENGINE.activate_quiz(user_id, prev_learner_ab)
    sqe['input_i'] = 0
    sqe['cell_var'] = sqe['total_selection_cell']

    sqe['first_learner_ab_cell'] = sqe['learner_ability_cell']

    return sqe

def sub_mapping_fetch_quiz(in_sqe, max_quiz_limit, timeout_case, corrected_quiz, temp_quiz): #sqe = session_quiz_engine
    sqe = in_sqe

    if (sqe['no_quiz'] == False):
        # Cell level
        if ((len(sqe['append_select_cell']) <= sqe['num_cell'])):
            if ((((sqe['remain_quiz_cell'] <= 0) or 
                (sqe['trigger'] == 1)) and 
                 (len(sqe['append_select_cell']) < sqe['num_cell']))):
                sqe['trigger'] = 0

                sqe['dsc_cell'], \
                sqe['dfc_cell'], \
                sqe['cell_array'], \
                sqe['total_selection_cell'], \
                sqe['user_cell'], \
                sqe['available_questions'], \
                sqe['cell_var'], \
                selected_cell, \
                sqe['dsc_quiz'], \
                sqe['dfc_quiz'], \
                sqe['count'] = GLOBAL_QUIZ_ENGINE.fetch_quiz_mastery(sqe['dsc_cell'],\
                                                                    sqe['dfc_cell'], \
                                                                    sqe['learner_ability_cell'], \
                                                                    sqe['cell_array'], \
                                                                    sqe['total_selection_cell'], \
                                                                    sqe['tagged_quiz_responses'],
                                                                    sqe['cell_var'],
                                                                    corrected_quiz,
                                                                    temp_quiz,
                                                                    sqe['user_cell'])
                
                sqe['cell_available_questions'] = sqe['available_questions']

                sqe['append_select_cell'].append(selected_cell)

                sqe['remain_quiz_cell'] = min(sqe['num_quiz'], len(sqe['available_questions']))
                
            # Quiz level, using while to simulate response as well
            while ((sqe['remain_quiz_cell'] > 0) and 
                   (sqe['trigger'] == 0)): # to prevent stucking in, avoid using True
                sqe['question_data'], \
                sqe['total_selection_quiz'], \
                selected_question, \
                simulate_response = GLOBAL_QUIZ_ENGINE.fetch_sub_quiz(sqe['dsc_quiz'], \
                                                                      sqe['dfc_quiz'], \
                                                                      sqe['total_selection_quiz'], \
                                                                      sqe['learner_ability_cell'], \
                                                                      sqe['available_questions'],
                                                                      sqe['cell_available_questions'])
                

                sqe['append_select_quiz'].append(selected_question)

                # For the case of available_question lower than 3
                if (sqe['question_data'] == None):
                    if (simulate_response == None):
                        simulate_response = 0
                    sqe = sub_mapping_answer(sqe, simulate_response)
                else:
                    break
    
    if (((sqe['timeout'] == True) or 
         ((len(sqe['append_response_list']) == max_quiz_limit)) or
         (timeout_case == True)) or
        ((len(sqe['append_select_cell']) == sqe['num_cell']) and
         ((sqe['remain_quiz_cell'] == 0) or (sqe['trigger'] == 1)))):
        sqe['session_complete'] = True

        if (timeout_case == True):
            sqe['timeout'] = True
        

    return sqe

def sub_mapping_answer(in_sqe, input_response, question, quiz_engine_input, answer_choice, answer_frontend, answer_db, rationale): #sqe = session_quiz_engine
    sqe = in_sqe
    qei = quiz_engine_input
    limit_time = qei['start_ts'] + (qei['duration'] * 60) # time format
    current_time = int(time.time())
    if (qei['duration'] == 0): # No timer
        limit_time = current_time + 1
        #current_time = limit_time - 1

    if (current_time <= limit_time):
        if (sqe['remain_quiz_cell'] > 0):
            sqe['rps'], \
            sqe['tagged_quiz_responses'], \
            sqe['available_questions'], \
            sqe['count'], \
            sqe['trigger'], \
            sqe['dsc_quiz'], \
            sqe['dfc_quiz'] = GLOBAL_QUIZ_ENGINE.record_submitted_answer(sqe['append_select_quiz'][-1],
                                                                        input_response,
                                                                        sqe['rps'],
                                                                        sqe['available_questions'],
                                                                        sqe['tagged_quiz_responses'],
                                                                        sqe['count'],
                                                                        sqe['num_quiz'],
                                                                        sqe['dsc_quiz'],
                                                                        sqe['dfc_quiz'],
                                                                        sqe['cell_available_questions'])
            if (answer_choice == 0):
                sqe['append_response_list'].append(-1)
            else:
                sqe['append_response_list'].append(input_response)
            sqe['remain_quiz_cell'] -= 1

        if (sqe['remain_quiz_cell'] <= 0):
            sqe['dsc_cell'],\
            sqe['dfc_cell'],\
            sqe['learner_ability_cell'],\
            sqe['total_selection_cell'], \
            sqe['cell_array'], \
            sqe['no_quiz'], \
            sqe['initial_cell'] = GLOBAL_QUIZ_ENGINE.update_profile(sqe['initial_cell'],
                                                                sqe['append_select_cell'][-1],
                                                                sqe['imputed_train'],
                                                                sqe['trigger'],
                                                                sqe['cell_var'],
                                                                sqe['cell_array'],
                                                                sqe['input_i'],
                                                                sqe['append_select_cell'])
        
            sqe['input_i'] += 1 # Mimicking for i in range(num_questions)
        username_log = model_dbquery.UserDataQuery.get_username(session['user_id'])
        model_dbquery.UserDataQuery.log_user_activity(session['user_id'], username_log, session['n_attempt'], sqe['append_select_quiz'][-1], question, answer_choice, input_response, answer_frontend, answer_db, rationale, current_time)
    else:
        sqe['timeout'] = True

    return sqe