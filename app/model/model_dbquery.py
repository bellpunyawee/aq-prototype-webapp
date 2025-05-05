"""
This file is a place holder of function to perform general inqueries that is not related to confidential/credential data
"""
# Always set parent package, relative use case cause failure
import sys, os
import pandas as pd
from datetime import datetime
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import random as rd
from interfaces.db_connector import DB_Object
from globalclass.osbasic import Fundamental as OSBASIC
from model.model_usercontrol import SystemAdminClass



class GeneralDataQuery():
    @staticmethod
    # def get_cell_indices():
    #     db_obj = DB_Object("ADQ_DB")
    #     sql_command = "select cell, topics from KU_table_data"
    #     result = db_obj.perform_sql(sql_command, True)
    #     return result
    def get_cell_indices():
        db_obj = DB_Object("ADQ_DB")
        sql_command = "select cell, short_description, topics, duration_min from KU_table_data"
        result = db_obj.perform_sql(sql_command, True)
        return result
    
    @staticmethod
    def get_cell_time():
        db_obj = DB_Object("ADQ_DB")
        sql_command = "select cell, duration_min from KU_table_data"
        result = db_obj.perform_sql(sql_command, True)
        return result
    
    @staticmethod
    def get_disclaimer():
        disclaimer_file_path = OSBASIC.loadConfiguration("/conf/db_conf.json")
        disclaimer_string = ""
        with open(disclaimer_file_path['DISCLAIMER_TEXT'], "r") as fp:
            disclaimer_string = fp.read()

        return disclaimer_string
    
    @staticmethod
    def get_textboxdata(user_id, n_attempt):
        db_obj = DB_Object("TEXTBOXAREA_DB")
        sql_command = "select feedback from textboxdata where user_id = " + str(user_id)+ " and n_attempt = " + str(n_attempt)
        result = db_obj.perform_sql(sql_command, True)

        if (result != []):
            result = result[0][0]
        else:
            result = ""    
        return result

class UserDataQuery():
    @staticmethod
    def import_txt_to_db(user_id, n_attempt,feedback):
        db_obj = DB_Object("TEXTBOXAREA_DB")

        # check if a record exists with the same user_id and n_attempt
        sql_check = "select count(*) from textboxdata where user_id =" + str(user_id) + " "
        sql_check += "and n_attempt =" + str(n_attempt)
        result = db_obj.perform_sql(sql_check,True)
        count = result[0][0]
        feedback = feedback.replace("'", "").replace('"', "")

        if count > 0:
            sql_update = "update textboxdata set feedback =\" " + feedback + " \"where user_id ="
            sql_update += str(user_id) + " " + " and n_attempt =" + str(n_attempt)
            db_obj.perform_sql(sql_update)
            db_obj.commit_update()
            # print("Updated")

        else:
            sql_insert = "insert into textboxdata(user_id, n_attempt, feedback) values("
            sql_insert += str(user_id) + "," + str(n_attempt) + ",\" " + feedback + " \")"
            db_obj.perform_sql(sql_insert)
            db_obj.commit_update()
            # print("Inserted")

    @staticmethod
    def submit_user_query(user_id, n_attempt, query_detail, timestamp):
        db_obj = DB_Object("USER_QUERY_DB")
        sql_command = "insert into user_query(user_id, n_attempt, query_detail, log_timestamp) values("
        sql_command += str(user_id) + "," + str(n_attempt) + ",\"" + query_detail + "\","  + str(timestamp) + ")"

        db_obj.perform_sql(sql_command)
        db_obj.commit_update()

    @staticmethod
    def fetch_solved_quiz(user_id):
        """
        Fetch quizzes that have been solved correctly for the given user, considering up to the latest 3 attempts.

        :param user_id: The ID of the user.
        :return: A list of quiz IDs that have been answered correctly.
        """
        db_obj = DB_Object("USER_ACTIVITY_LOG_DB")

        # ! SQL command to get all distinct attempts by the user from n_attempt 2
        sql_command_attempts = "select distinct n_attempt from activity_log where user_id = {} and answer_correct = 1 and n_attempt > 1 order by n_attempt desc".format(user_id)

        # Execute query to get all attempts for the user
        try:
            attempts_result = db_obj.perform_sql(sql_command_attempts, True)
            recent_attempts = [row[0] for row in attempts_result] if attempts_result else []
        except Exception as e:
            print(f"Database query failed: {e}")
            return []

        # If fewer than 3 attempts exist, use all available attempts
        limited_attempts = recent_attempts[:3]

        # SQL command to get quizzes for the selected attempts
        if limited_attempts:
            sql_command_quizzes = "select quiz_id from activity_log where user_id = {} and n_attempt in ({}) and answer_correct = 1".format(user_id, ",".join(map(str, limited_attempts)))
        else:
            return []
        # Execute query with the selected attempts as parameters
        try:
            get_info = db_obj.perform_sql(sql_command_quizzes, True)
        except Exception as e:
            print(f"Database query failed: {e}")
            return []

        # Extract the quiz IDs
        already_corrected_quiz = [row[0] for row in get_info] if get_info else []
        print("Already Correct List: ", already_corrected_quiz)

        return already_corrected_quiz

    # @staticmethod # New one
    # def fetch_solved_quiz(user_id, attempt_no):
    #     """
    #     Fetch quizzes that have been solved correctly for a given user and attempt number.
        
    #     :param user_id: The ID of the user.
    #     :param attempt_no: The attempt number to filter the records.
    #     :return: A list of quiz IDs that have been answered correctly.
    #     """
    #     # cover all history records
    #     db_obj = DB_Object("USER_ACTIVITY_LOG_DB")
    #     sql_command = "select quiz_id from activity_log where user_id = " + str(user_id) + " and answer_correct = 1"
    #     # Execute query with parameters
    #     try:
    #         get_info = db_obj.perform_sql(sql_command, True)
    #     except Exception as e:
    #         print(f"Database query failed: {e}")
    #         return []

    #     already_corrected_quiz = [row[0] for row in get_info] if get_info else []
    #     # print("Already Correct List: ", already_corrected_quiz)
    #            # from previous record
    #     # sql_command = "select quiz_id, answer_correct from activity_log where n_attempt=" +str(attempt_no) + " "
    #     # sql_command += " and user_id=" + str(user_id)
    #     # get_info = db_obj.perform_sql(sql_command, True)
    #     # item = list(zip(*get_info))

    #     # if (item != []):
    #     #     selected_quiz = item[0]
    #     #     response_list = item[1]
    #     # else:
    #     #     selected_quiz = []
    #     #     response_list = []

    #     # mapped_list = list(zip(selected_quiz, response_list))
    #     # already_corrected_quiz = list(set([quiz for quiz, response in mapped_list if response == 1]))

    #     return already_corrected_quiz
    
    # temp_quiz = model_dbquery.UserDataQuery.fetch_temp_quiz(session['user_id'], session['n_attempt'])
    @staticmethod # New one
    def fetch_temp_quiz(user_id, attempt_no):
        """
        Fetch quizzes that have been attempted for a given user and attempt number.
        
        :param user_id: The ID of the user.
        :param attempt_no: The attempt number to filter the records.
        :return: A list of quiz IDs that have been attempted.
        """
        db_obj = DB_Object("USER_ACTIVITY_LOG_DB")
        sql_command = "select quiz_id from activity_log where n_attempt=" +str(attempt_no) + " "
        sql_command += " and user_id=" + str(user_id)

        # Execute query with parameters
        try:
            get_info = db_obj.perform_sql(sql_command, (attempt_no, user_id), True)
        except Exception as e:
            print(f"Database query failed: {e}")
            return []

        # get_info = db_obj.perform_sql(sql_command, True)
        # flat_list = [item for sublist in get_info for item in sublist]
        quiz_id_list = [row[0] for row in get_info] if get_info else []
        # print("Temp List List: ", quiz_id_list)

        return quiz_id_list

    @staticmethod
    def get_report_data(user_id, attempt_no):
        db_obj = DB_Object("USER_ACTIVITY_LOG_DB")
        sql_command = "select quiz_id, answer_correct, quiz_answer, timecode from activity_log where n_attempt=" +str(attempt_no) + " "
        sql_command += " and user_id=" + str(user_id)

        get_info = db_obj.perform_sql(sql_command, True)
        item = list(zip(*get_info))

        if (item != []):
            selected_quiz = item[0]
            response_list = item[1]
            choice_list = item[2]
            timestamp = item[3]
        else:
            selected_quiz = []
            response_list = []
            choice_list = []
            timestamp = []
        
        return [selected_quiz, response_list, choice_list, timestamp]

    @staticmethod
    def log_to_excel(user_id, n_attempt):
        db_obj = DB_Object("USER_ACTIVITY_LOG_DB")
        # timestamp = datetime.fromtimestamp(timecode).strftime('%Y-%m-%d %H:%M:%S')
        sql_command = "select * from activity_log where user_id = " + str(user_id) + " "
        sql_command += " and n_attempt = " +  str(n_attempt)
        
        try:
            # Execute the query using db_obj and get the cursor
            cursor = db_obj.perform_sql(sql_command, True)
            
            # Get column names from cursor description
            columns = ['id', 'user_id', 'username', 'n_attempt', 'quiz_id',
                       'question_text','answer_correct', 'quiz_answer',
                       'answer_text','correct_answer', 'explanation', 
                       'timestamp', 'timecode']

            # Create DataFrame from rows and columns
            df = pd.DataFrame(cursor, columns=columns)
            
            # Generate a filename for the Excel file
            excel_filename = os.path.join('_cache', f'export.xlsx')
            
            # Export the DataFrame to an Excel file
            df.to_excel(excel_filename, index=False)
            
            # print(f'Data successfully exported to {excel_filename}')
            return excel_filename
        
        except Exception as e:
            print(f"An error occurred: {e}")

    @staticmethod
    def log_user_activity(user_id, username, n_attempt, quiz_id, question_text, quiz_answer, correctness, answer_text, correct_ans, explanation, timecode):
        db_obj = DB_Object("USER_ACTIVITY_LOG_DB")
        # Convert to human-readable date and time
        timestamp = datetime.fromtimestamp(timecode).strftime('%Y-%m-%d %H:%M:%S')
        sql_command = "insert into activity_log(user_id, username, n_attempt, quiz_id, question_text, answer_correct ,quiz_answer, answer_text, correct_answer, explanation, timestamp, timecode) values("

        # Need to add --> answer_text + answer_rationale & generate this one in real-time
        # sql_command += str(user_id) + "," + str(n_attempt) + "," + str(quiz_id) + "," + str(correctness) +"," + str(quiz_answer) + "," +str(timestamp) + ")"
        # sql_command += str(user_id) + "," + str(n_attempt) + "," + str(quiz_id) + ",\"" + question_text + "\"," + str(correctness) +"," + str(quiz_answer) + ",\"" +timestamp + "\")"
        sql_command += str(user_id) + ",\"" + username + "\"," + str(n_attempt) + "," + str(quiz_id) + ",\"" + question_text + "\"," + str(correctness) +"," + str(quiz_answer) + ",\"" + answer_text + "\",\"" + correct_ans + "\",\"" + (explanation if explanation is not None else '') + "\",\"" +timestamp + "\"," + str(timecode) + ")"

        db_obj.perform_sql(sql_command)
        db_obj.commit_update()

    @staticmethod
    def delete_residual_user_activity(user_id, n_attempt):
        db_obj = DB_Object("USER_ACTIVITY_LOG_DB")
        sql_command = "delete from activity_log where user_id = "+ str(user_id)+ " and n_attempt = " + str(n_attempt)

        db_obj.perform_sql(sql_command)
        db_obj.commit_update()

    @staticmethod
    def update_user_attempt(user_id, prev_ability_cell, current_ability_cell, mastery_list):
        db_obj = DB_Object("ADQ_DB")
        # Mastery updating
        sql_command = "update mastery_table set topic_"
        for i in range(0, len(mastery_list)):
            if (mastery_list[i] == 1):
                string_value = str(i + 1) + " ="  + str(mastery_list[i]) + " where user_id=" + str(user_id)
                db_obj.perform_sql(sql_command + string_value)

        get_info = db_obj.perform_sql("select distinct n_attempt from learner_ability where user_id=" + str(user_id), True)
        if (get_info != []):
            get_info = max(get_info)
            last_attempt = get_info[0]
        else:
            last_attempt = 0
        
        # Ability updating
        sql_command = "insert into learner_ability (user_id, previouse_ability, current_ability, n_attempt, timestamp) values("
        sql_command += str(user_id) + "," + str(prev_ability_cell) + "," + str(current_ability_cell) + "," + str(last_attempt + 1) + "," + str(int(OSBASIC.getCurrentTimestamp())) + ")"

        db_obj.perform_sql(sql_command)
        db_obj.commit_update()
    
    @staticmethod
    def pre_ability_update(user_id, prev_ability_cell, current_ability_cell, attempt):
        db_obj = DB_Object("ADQ_DB")
        # assign ability for pretest 
        sql_command = "insert into learner_ability (user_id, previouse_ability, current_ability, n_attempt, timestamp) values("
        sql_command += str(user_id) + "," + str(prev_ability_cell) + "," + str(current_ability_cell) + "," + str(attempt) + "," + str(int(OSBASIC.getCurrentTimestamp())) + ")"

        db_obj.perform_sql(sql_command)
        db_obj.commit_update()

    
    @staticmethod
    def create_mastery_slot(user_id):
        db_obj = DB_Object("ADQ_DB")
        sql_command = "insert into mastery_table (user_id) values (" 
        sql_command += str(user_id) + ")"
        db_obj.perform_sql(sql_command)
        db_obj.commit_update()

    @staticmethod
    def update_mastery_slot_pretest(user_id):
        db_obj = DB_Object("ADQ_DB")
        # res_list, cell_list --> normalize, session['quiz_response_list][1], respectively.
        data_list = db_obj.perform_sql("select learner_response, cell_index from pretest_table where user_id = " + str(user_id), True) 
        import pandas as pd
        df = pd.DataFrame(data_list, columns=['learner_response', 'cell_index'])

        # Group by cell_index and calculate the average learner_response for each cell
        cell_avg = df.groupby('cell_index')['learner_response'].mean()

        # Use MinMaxScaler to normalize the values between 0 and 1
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler()
        normalized_values = scaler.fit_transform(cell_avg.values.reshape(-1, 1))

        # Apply threshold (greater than 0.5 becomes 1, otherwise 0)
        learner_mastery_cell = (normalized_values > 0.5).astype(int)

        # Convert dichotomous values to 2D array
        cell_mastery = learner_mastery_cell.reshape(-1, 1)
        # Mastery updating
        sql_command = "update mastery_table set topic_"
        for i in range(0, len(cell_mastery)):
            if (cell_mastery[i][0] == 1):
                string_value = str(i + 1) + " ="  + str(cell_mastery[i][0]) + " where user_id=" + str(user_id)
                db_obj.perform_sql(sql_command + string_value)
        
        db_obj.commit_update()
        return cell_mastery
        

    @staticmethod
    def create_train_slot(user_id):
        db_obj = DB_Object("ADQ_DB")
        get_info = db_obj.perform_sql("select id from quiz_pool where pretest_quiz = 0", True)
        # user_possibility = db_obj.perform_sql("select CAST(SUM(learner_response) AS FLOAT) / "+
        #                                       "CAST(COUNT(id) as FLOAT) from pretest_table " +
        #                                       "where (cell_index=4 OR cell_index=7 OR cell_index=9 OR cell_index=11)" +
        #                                      " AND user_id=" + str(user_id),True)
        # for QE2
        # user_possibility = db_obj.perform_sql("select CAST(SUM(learner_response) AS FLOAT) / "+
        #                                       "CAST(COUNT(id) as FLOAT) from pretest_table " +
        #                                       "where (cell_index=1 OR cell_index=2 OR cell_index=3 OR cell_index=5 OR cell_index=18 OR cell_index=19 OR cell_index=20 OR cell_index=24 OR cell_index=25 OR cell_index=26 OR cell_index=27 OR cell_index=28 OR cell_index=29 OR cell_index=30)" +
        #                                      " AND user_id=" + str(user_id),True)
        
        # for PM5101: all cells
        user_possibility = db_obj.perform_sql("select CAST(SUM(learner_response) AS FLOAT) / "+
                                              "CAST(COUNT(id) as FLOAT) from pretest_table " +
                                              "where (cell_index=1 OR cell_index=2 OR cell_index=3 OR cell_index=4 OR cell_index=5 OR cell_index=6 OR cell_index=7 OR cell_index=8 OR cell_index=9 OR cell_index=10 OR cell_index=11 OR cell_index=12 OR cell_index=13 OR cell_index=14 OR cell_index=15 OR cell_index=16 OR cell_index=17 OR cell_index=18 OR cell_index=19 OR cell_index=20 OR cell_index=21 OR cell_index=22 OR cell_index=23 OR cell_index=24 OR cell_index=25 OR cell_index=26 OR cell_index=27 OR cell_index=28 OR cell_index=29 OR cell_index=30)" +
                                             " AND user_id=" + str(user_id),True)
        
        user_possibility = user_possibility[0][0]

        sql_command = "insert into train_table (user_id, quiz_id, quiz_correct_ans) values("
        for i in range(0, len(get_info)):
            quiz_id = get_info[i][0]
            string_value = str(user_id ) + ", " + str(quiz_id) + "," + str(1 if rd.random() < user_possibility else 0) + ")"
            db_obj.perform_sql(sql_command + string_value)
        
        db_obj.commit_update()

    @staticmethod
    def submit_user_pretest(user_id, res_list, cell_list):
        db_obj = DB_Object("ADQ_DB")
        sql_command = "insert into pretest_table(user_id, cell_index,learner_response) values("
        for i in range(0, len(res_list)):
            string_value = str(user_id) + "," + str(cell_list[i]) + "," + str(res_list[i]) + ")"
            db_obj.perform_sql(sql_command + string_value)

        # padding to have all cells, otherwise it will be troubled due to pre-made with 30 cells assumption
        for i in range(1, (30 + 1)):
            if (i not in cell_list):
                string_value = str(user_id) + "," + str(i) + ",0)"
                db_obj.perform_sql(sql_command + string_value)

        db_obj.commit_update()

    @staticmethod
    def get_user_pretest(user_id):
        db_obj = DB_Object("ADQ_DB")
        sql_command = "select learner_response, cell_index from pretest_table where user_id="+str(user_id)
        result = db_obj.perform_sql(sql_command, True)
        if (result != []):
            ret_val = True
        else:
            ret_val = False
        
        return ret_val

    @staticmethod
    def get_latest_attempt(user_id):
        " Retrieve Latest no. of quiz attempts from learner_ability Database "
        db_obj = DB_Object("ADQ_DB")
        get_info = db_obj.perform_sql("select distinct n_attempt from learner_ability where user_id=" + str(user_id), True)
        if (get_info != []):
            get_info = max(get_info)
            last_attempt = get_info[0]
        else:
            last_attempt = 0

        return last_attempt
    
    @staticmethod
    def get_latest_update(user_id):
        " Retrieve Latest no. of updated attempts from Students Database "
        db_obj = DB_Object("ADQ_DB")
        get_info = db_obj.perform_sql("select distinct num_update from Students where student_id=" + str(user_id), True)
        if (get_info != []):
            get_info = max(get_info)
            last_attempt = get_info[0]
        else:
            last_attempt = 0

        return last_attempt
    
    @staticmethod
    def get_latest_time(user_id, num_update):
        " Retrieve Latest Updated Time from Students Database "
        db_obj = DB_Object("ADQ_DB")
        get_info = db_obj.perform_sql("select timestamp from Students where student_id=" + str(user_id) + " and num_update=" + str(num_update), True)
        if (get_info != []):
            get_info = max(get_info)
            last_attempt = get_info[0]
        else:
            last_attempt = 0
        return last_attempt
    
    @staticmethod
    def get_previous_ability(user_id):
        db_obj = DB_Object("ADQ_DB")
        sql_command = "select current_ability from learner_ability where n_attempt=(select MAX(n_attempt) from learner_ability where user_id=" + str(user_id)
        sql_command += ") and user_id=" + str(user_id)
        get_info = db_obj.perform_sql(sql_command, True)
        if (get_info != []):
            previous_ability = get_info[0][0]
        else:
            previous_ability = None
        
        return previous_ability
    
    @staticmethod
    def get_user_photo(user_id):
        db_obj = DB_Object("USERPHOTO_DB")

        get_info = db_obj.perform_sql("select profile_photo from user_photo where user_id=" + str(user_id), True)
        if (len(get_info) == 0):
            ret_val = ""
        else:
            ret_val = get_info[0][0]
            ret_val = "data:image/png;base64,"+ret_val
            
        return ret_val

    @staticmethod
    def insert_user_photo(base64_string, user_id):
        file_path = OSBASIC.convertB64ToFile(base64_string)
        file_path = OSBASIC.convertPictoSmallerFile(file_path=file_path, size=250) # Standardize 250 pixels (with ratio of original file)
        mod_image_string = OSBASIC.convertImageToBase64(file_path,True) # Convert and give base 64 only

        db_obj = DB_Object("USERPHOTO_DB")
        sql_command = "select user_id from user_photo where user_id=" + str(user_id)
        get_info = db_obj.perform_sql(sql_command, True)
        

        if (len(get_info) == 0): # No image has been uploaded before
            sql_command = "insert into user_photo(user_id, profile_photo) values(" + str(user_id) + ", \"" + mod_image_string + "\")"
            db_obj.perform_sql(sql_command)
            db_obj.commit_update()
        else: # Image already has been uploaded, needs update
            sql_command = "update user_photo set profile_photo=\"" + mod_image_string + "\" where user_id=" + str(user_id)
            db_obj.perform_sql(sql_command)
            db_obj.commit_update()

        # Check image is correct
        get_info = db_obj.perform_sql("select profile_photo from user_photo where user_id=" + str(user_id), True)
        if (get_info[0][0] == mod_image_string):
            ret_val = True
        else:
            ret_val = False

        return ret_val
    
    @staticmethod
    def get_user_scores(user_id):
        db_obj = DB_Object("USER_ACTIVITY_LOG_DB")
        sql_command = "SELECT SUM(answer_correct) , COUNT(answer_correct), (SUM(answer_correct) * 100 / COUNT(answer_correct)),n_attempt "
        sql_command += " FROM activity_log WHERE user_id = " + str(user_id) +" GROUP BY n_attempt ORDER BY n_attempt"
        
        get_info = db_obj.perform_sql(sql_command, True)
        user_ans_number_list = []
        user_quiz_number_list = []
        user_score_percentage_list = []
        user_timestamp = []

        for i in range(0, len(get_info)):
            user_ans_number_list.append(get_info[i][0])
            user_quiz_number_list.append(get_info[i][1])
            user_score_percentage_list.append(get_info[i][2])
            user_timestamp.append(get_info[i][3])
        
        return user_ans_number_list, user_quiz_number_list, user_score_percentage_list, user_timestamp
    
    @staticmethod
    def get_latest_user_scores(user_id, attempt):
        db_obj = DB_Object("USER_ACTIVITY_LOG_DB")
        sql_command = "SELECT SUM(answer_correct) , COUNT(answer_correct), (SUM(answer_correct) * 100 / COUNT(answer_correct)),n_attempt "
        sql_command += " FROM activity_log WHERE user_id = " + str(user_id) + " and n_attempt = " + str(attempt)
        
        get_info = db_obj.perform_sql(sql_command, True)
        user_ans_number_list = []
        user_quiz_number_list = []
        user_score_percentage_list = []
        user_timestamp = []

        for i in range(0, len(get_info)):
            user_ans_number_list.append(get_info[i][0])
            user_quiz_number_list.append(get_info[i][1])
            user_score_percentage_list.append(get_info[i][2])
            user_timestamp.append(get_info[i][3])
        
        return user_ans_number_list, user_quiz_number_list, user_score_percentage_list, user_timestamp
    
    @staticmethod
    def get_user_abilities(user_id):
        db_obj = DB_Object("ADQ_DB")
        sql_command = "select timestamp, current_ability from learner_ability where user_id=" + str(user_id) + " order by n_attempt asc"
        get_info = db_obj.perform_sql(sql_command, True)
        user_ab_list = []
        user_timestamp = []

        for i in range(0, len(get_info)):
            user_timestamp.append(get_info[i][0])
            user_ab_list.append(get_info[i][1])
            
        
        return user_ab_list, user_timestamp
    
    @staticmethod
    def get_user_mastery(user_id):
        db_obj = DB_Object("ADQ_DB")
        sql_command = "select * from mastery_table where user_id=" + str(user_id)
        get_info = db_obj.perform_sql(sql_command, True)

        item = list(zip(*get_info))
        item.pop(0) # Pop id
        item.pop(0) # Pop user id
        mastery_list = []
        for i in range(0, len(item)):
            mastery_list.append(True if item[i][0] >= 1.0 else False)
            
        return mastery_list
    
    @staticmethod
    def get_username(user_id):
        db_obj = DB_Object("USERINFO_DB")
        sql_command = "select * from user_table where id=" + str(user_id)
        get_info = db_obj.perform_sql(sql_command, True)
        username = get_info[0][1]
        return username
    
    @staticmethod
    def check_username_LTI(username,fullname,canvas_id):
        '''
        To check if the LTI username already exists in the database
        '''
        print(f"Checking if user '{username}' exists in the database ...")
        db_obj = DB_Object("USERINFO_DB")
        sql_command = "select * from user_table where username='" + username + "'"
        get_info = db_obj.perform_sql(sql_command, True)
    
        if get_info:
            # Safely access the result and check if the user exists
            curr = get_info[0][1]
            print(f"User '{username}' already exists. Skipping registration.")
            return True
        else:
            print(f"User '{username}' does not exist. Proceeding with registration.")
            # Registration ...
            print("Registration ...")
            SystemAdminClass.registration(username, password="12345", name=fullname, canvas_id=canvas_id) # Register new user
            return False
        
    # @staticmethod
    # def get_initial_path(user_id):
    #     db_obj = DB_Object("ADQ_DB")
    #     sql_command = "select initial_student_path from Students where student_id=" + str(user_id)
    #     get_info = db_obj.perform_sql(sql_command, True)
    #     path = get_info[0][0]
    #     return path

    @staticmethod
    def get_initial_path(user_id):
        try:
            db_obj = DB_Object("ADQ_DB")
            sql_command = "select initial_student_path from Students where student_id=" + str(user_id)
            get_info = db_obj.perform_sql(sql_command, True)

            # Check if the result is empty or None
            if not get_info or get_info[0][0] is None:
                # logging.warning(f"No initial path found for user_id {user_id}. Returning default value.")
                return None  # You can return None or a default value if needed

            path = get_info[0][0]
            return path

        except Exception as e:
            # logging.error(f"Error occurred while getting initial path for user_id {user_id}: {e}")
            return None  # Return None or raise an exception if appropriate
    
    # @staticmethod
    # def get_current_path(user_id):
    #     db_obj = DB_Object("ADQ_DB")
    #     sql_command = "select current_student_path from Students where student_id=" + str(user_id)
    #     get_info = db_obj.perform_sql(sql_command, True)
    #     path = get_info[-1][0]
    #     return path
    
    @staticmethod
    def get_current_path(user_id):
        try:
            db_obj = DB_Object("ADQ_DB")
            sql_command = "select current_student_path from Students where student_id=" + str(user_id)
            get_info = db_obj.perform_sql(sql_command, True)

            # Check if the result is empty or None
            if not get_info or get_info[0][0] is None:
                return None  # You can return None or a default value if needed

            path = get_info[0][0]
            return path

        except Exception as e:
            # logging.error(f"Error occurred while getting initial path for user_id {user_id}: {e}")
            return None  # Return None or raise an exception if appropriate
    
    # # To return accumulated cell history
    # @staticmethod
    # def get_cell_history(user_id):
    #     db_obj = DB_Object("ADQ_DB")
    #     sql_command = "select cell_history from Students where student_id=" + str(user_id)
    #     get_info = db_obj.perform_sql(sql_command, True)
    #     cell = get_info[0][0]
    #     return cell
    @staticmethod
    def get_cell_history(user_id):
        db_obj = DB_Object("ADQ_DB")
        sql_command = "select cell_history from Students where student_id=" + str(user_id)
        get_info = db_obj.perform_sql(sql_command, True)
        cell = get_info[0][0] if get_info and get_info[0][0] is not None else ""
        return cell
    
    @staticmethod
    def get_student_score(user_id):
        # ! ''' It is a placeholder to retrieve assignment id'''
        db_obj = DB_Object("ADQ_DB")
        sql_command = "select student_score from Students where student_id=" + str(user_id)
        get_info = db_obj.perform_sql(sql_command, True)
        assignment_id = get_info[0][0] if get_info and get_info[0][0] is not None else ""
        return assignment_id
        
    @staticmethod
    def update_cell_history(user_id, cell_history):
        db_obj = DB_Object("ADQ_DB")
        sql_command = "update Students set cell_history = '{}' where student_id = '{}'".format(cell_history, user_id)
        db_obj.perform_sql(sql_command, True)
        db_obj.commit_update()

    @staticmethod
    def clear_cell_history(user_id):
        db_obj = DB_Object("ADQ_DB")
        # Set cell_history to an empty string
        sql_command = "UPDATE Students SET cell_history = '' WHERE student_id = '{}'".format(user_id)
        db_obj.perform_sql(sql_command, True)
        db_obj.commit_update()

    @staticmethod
    def update_student_score(user_id, student_score):
        db_obj = DB_Object("ADQ_DB")
        ''' Temporary to store assignment id'''
        sql_command = "update Students set student_score = '{}' where student_id = '{}'".format(student_score, user_id)
        db_obj.perform_sql(sql_command, True)
        db_obj.commit_update()    
    
    # @staticmethod
    # def update_path(user_id, init, path, num_update, timecode,cell_history=None):
    #     db_obj = DB_Object("ADQ_DB")
    #     timestamp = datetime.fromtimestamp(timecode).strftime('%Y-%m-%d %H:%M:%S')
    #     # sql_command = "insert into Students(student_id, student_score, initial_student_path, current_student_path, num_update, timestamp) values('{}','{}','{}','{}','{}','{}')".format(user_id,0,init,path,num_update,timestamp)
    #     sql_command = "UPDATE Students SET student_score = '{}', current_student_path = '{}', num_update = '{}', pre_quiz_completed = '{}', cell_history = '{}', timestamp = '{}' WHERE student_id = '{}'".format(0, path, num_update, 1, cell_history, timestamp, user_id)
    #     db_obj.perform_sql(sql_command, True)
    #     db_obj.commit_update()
        
    @staticmethod
    def get_canvas_id(user_id):
        db_obj = DB_Object("USERINFO_DB")
        sql_command = "select canvas_id from user_info where user_id=" + str(user_id)
        canvas_id = db_obj.perform_sql(sql_command, True)
        canvas_id = [item[0] for item in canvas_id]
        return canvas_id
    
    @staticmethod
    def get_courseIDs_from_db():
        db_obj = DB_Object("ADQ_DB")
        sql_command = "SELECT cell, ku_values FROM KU_courseID_link"
        get_info = db_obj.perform_sql(sql_command, True)
        KU_dict = {}
        for item in get_info:
            ku_id = str(item[0])  # First element is the 'id'
            ku_values = list(map(int, item[1].split(',')))  # Second element is the 'ku_values', split and convert to list of integers
            # Populate the KU_dict with the id as the key and ku_values as the list of integers
            KU_dict[ku_id] = ku_values
        return KU_dict

    # @staticmethod
    # def insert_students_table(user_id):
    #     db_obj_2 = DB_Object("ADQ_DB")
    #     sql_command_2 = "INSERT OR REPLACE INTO Students(student_id, pre_quiz_completed) VALUES ('{}','{}')".format(user_id, 0)
    #     db_obj_2.perform_sql(sql_command_2, True)
    #     db_obj_2.commit_update()

    @staticmethod
    def update_pre_quiz_status(canvas_id):
        db_obj_1 = DB_Object("USERINFO_DB")
        sql_command_1 = "SELECT user_id FROM user_info WHERE canvas_id=" + str(canvas_id)
        get_info = db_obj_1.perform_sql(sql_command_1, True)
        student_id = get_info[0][0]

        db_obj_2 = DB_Object("ADQ_DB")
        sql_command_2 = "UPDATE Students SET pre_quiz_completed = 1 WHERE student_id = '{}'".format(student_id)
        db_obj_2.perform_sql(sql_command_2, True)
        db_obj_2.commit_update()
        
    @staticmethod
    def get_just_courseIDs_from_db():
        db_obj = DB_Object("ADQ_DB")
        sql_command = "SELECT ku_values FROM KU_courseID_link"
        get_info = db_obj.perform_sql(sql_command, True)
        ku_values_list = []
        for item in get_info:
            ku_values = list(map(int, item[0].split(','))) 
            ku_values_list.extend(ku_values)  
        return ku_values_list
    
    @staticmethod
    def get_quizcourseIDs_from_db_given_cell_list(cell_list_string):
        print("Original cell list string:", cell_list_string)
        cells = [int(cell.strip()) for cell in cell_list_string.split(',')]
        cell_input = ', '.join(map(str, cells))
        sql_command = f"SELECT ku_values FROM KU_courseID_link WHERE cell IN ({cell_input})"
        print("sql_command =", sql_command)
        db_obj = DB_Object("ADQ_DB")
        get_info = db_obj.perform_sql(sql_command, True)
        ku_values_list = []
        for item in get_info:
            ku_values = list(map(int, item[0].split(','))) 
            ku_values_list.extend(ku_values) 
        return ku_values_list

    @staticmethod
    def migrate_student_data(canvas_id, student_id):
        # ! This is for QE2 testing. Will be optimised later
        try:
            # Fetch data from original tables
            db_obj = DB_Object("ADQ_DB") 
            # student_data_query = "SELECT student_score, initial_student_path, current_student_path, num_update, pre_quiz_completed, cell_history, timestamp FROM qualtrics_manual_insert_Students WHERE canvas_id = '{}'".format(canvas_id)
            # student_data = db_obj.perform_sql(student_data_query, True)

            # pg_preferences_query = "SELECT Initiating, Planning, Executing, Monitoring_Controlling, Closing FROM qualtrics_manual_insert_PG_preferences WHERE canvas_id = '{}'".format(canvas_id)
            # pg_preferences = db_obj.perform_sql(pg_preferences_query, True)
            # ka_preferences_query = "SELECT Integration, Communication, Procurement, Stakeholder FROM qualtrics_manual_insert_KA_preferences WHERE canvas_id = '{}'".format(canvas_id)
            # ka_preferences = db_obj.perform_sql(ka_preferences_query, True)
            # background_info_query = "SELECT gender, role, company, experience_years, projects, qualification, major FROM qualtrics_manual_insert_background_info WHERE canvas_id = '{}'".format(canvas_id)
            # background_info = db_obj.perform_sql(background_info_query, True)

            # Insert data into new tables using provided student_id
            student_insert_query = "INSERT OR REPLACE INTO Students(student_id) VALUES('{}')".format(student_id)
            db_obj.perform_sql(student_insert_query)
            db_obj.commit_update()
            # update_query = '''
            #     UPDATE Students
            #     SET initial_student_path = NULL
            #     WHERE initial_student_path = 'None'
            # '''
            # # Execute the query using the db_obj
            # db_obj.perform_sql(update_query)
            # db_obj.commit_update()
            
            # if pg_preferences:
            #     pg_insert_query = "INSERT OR REPLACE INTO PG_preferences (student_id, Initiating, Planning, Executing, Monitoring_Controlling, Closing) VALUES ('{}', '{}', '{}', '{}', '{}', '{}')".format(student_id, pg_preferences[0][0],pg_preferences[0][1], pg_preferences[0][2], pg_preferences[0][3], pg_preferences[0][4])
            #     db_obj.perform_sql(pg_insert_query)
            #     db_obj.commit_update()
                
            # if ka_preferences:
            #     ka_insert_query = "INSERT OR REPLACE INTO KA_preferences (student_id, Integration, Communication, Procurement, Stakeholder) VALUES ('{}', '{}', '{}', '{}', '{}')".format(student_id, ka_preferences[0][0],ka_preferences[0][1], ka_preferences[0][2], ka_preferences[0][3])
            #     db_obj.perform_sql(ka_insert_query)
            #     db_obj.commit_update()
            # # Insert into Background_info table if data exists
            # if background_info:
            #     background_insert_query = "INSERT OR REPLACE INTO Background_info(student_id, gender, role, company, experience_years, projects, qualification, major) VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(student_id, background_info[0][0], background_info[0][1], background_info[0][2], background_info[0][3], background_info[0][4], background_info[0][5], background_info[0][6])
            #     db_obj.perform_sql(background_insert_query)
            #     db_obj.commit_update()
        except Exception as e:
            print("An error occurred during migration:", e)

    def dump_Students_data(csv_file_name):
        """
        Function to map canvas_id from CSV file into qualtrics_manual_insert_Students table.
        """
        # Load data from CSV
        csv_path = f'docs/{csv_file_name}'
        try:
            # Load the CSV file into a DataFrame
            df = pd.read_csv(csv_path)

            # Initialize database connection
            db_obj = DB_Object("ADQ_DB")

            # Iterate over each row in the DataFrame to perform the mapping
            for _, row in df.iterrows():
                canvas_id = row['canvas_id']

                # SQL query to update or insert student data in the database table based on 'canvas_id'
                sql_command = '''
                    INSERT OR REPLACE INTO qualtrics_manual_insert_Students (canvas_id)
                    VALUES ({})
                '''.format(canvas_id)

                try:
                    # Execute the SQL command
                    db_obj.perform_sql(sql_command, (canvas_id,))
                except Exception as e:
                    print(f"Error occurred while updating database: {e}")

            db_obj.commit_update()

            print(f"Mapping canvas_id from '{csv_file_name}' to database completed successfully.")

        except FileNotFoundError:
            print(f"CSV file '{csv_file_name}' not found.")
        except pd.errors.EmptyDataError:
            print(f"CSV file '{csv_file_name}' is empty.")
        except Exception as e:
            print(f"An error occurred while processing the CSV file: {e}")

    @staticmethod
    def dump_background_info_from_excel():
        try:
            # Load the Excel file
            file_path = 'docs/QE2 Sign Up List.xlsx'
            df = pd.read_excel(file_path, sheet_name='Sheet1')

            # Map the columns from Excel to the database table
            data_to_insert = df[['Canvas ID', 'Gender', 'Role', 'Job title', 'Years of experience',
                                 'How many projects have you managed or been heavily involved in?',
                                 'Highest qualification', 'Discipline/ major of highest qualification']]

            # Renaming columns to match database table fields
            data_to_insert.columns = ['canvas_id', 'gender', 'role', 'company', 'experience_years',
                                      'projects', 'qualification', 'major']

            # Connect to the database
            db_obj = DB_Object("ADQ_2")

            # Insert data into qualtrics_manual_insert_background_info
            for _, row in data_to_insert.iterrows():
                print(_)
                print(row)
                insert_query = f'''
                    INSERT OR REPLACE INTO qualtrics_manual_insert_background_info (
                        canvas_id, gender, role, company, experience_years, projects, qualification, major
                    ) VALUES ('{row['canvas_id']}', '{row['gender']}', '{row['role']}', '{row['company']}',
                              '{row['experience_years']}', '{row['projects']}', '{row['qualification']}', '{row['major']}')
                '''
                db_obj.perform_sql(insert_query)

            db_obj.commit_update()
            print("Background information successfully dumped to the database.")

            # Insert KA_preferences data
            ka_data_to_insert = df[['Canvas ID', 'Integration management', 'Communication management',
                                    'Procurement management', 'Stakeholder management']]
            ka_data_to_insert.columns = ['canvas_id', 'Integration', 'Communication', 'Procurement', 'Stakeholder']

            for _, row in ka_data_to_insert.iterrows():
                insert_query_ka = f'''
                    INSERT OR REPLACE INTO qualtrics_manual_insert_KA_preferences (
                        canvas_id, Integration, Communication, Procurement, Stakeholder
                    ) VALUES ('{row['canvas_id']}', '{row['Integration']}', '{row['Communication']}',
                              '{row['Procurement']}', '{row['Stakeholder']}')
                '''
                db_obj.perform_sql(insert_query_ka)

            # Insert PG_preferences data
            pg_data_to_insert = df[['Canvas ID', 'Initiating process group', 'Planning process group',
                                    'Executing process group', 'Monitoring and controlling process group',
                                    'Closing process group']]
            pg_data_to_insert.columns = ['canvas_id', 'Initiating', 'Planning', 'Executing', 'Monitoring_Controlling', 'Closing']

            for _, row in pg_data_to_insert.iterrows():
                insert_query_pg = f'''
                    INSERT OR REPLACE INTO qualtrics_manual_insert_PG_preferences (
                        canvas_id, Initiating, Planning, Executing, Monitoring_Controlling, Closing
                    ) VALUES ('{row['canvas_id']}', '{row['Initiating']}', '{row['Planning']}',
                              '{row['Executing']}', '{row['Monitoring_Controlling']}', '{row['Closing']}')
                '''
                db_obj.perform_sql(insert_query_pg)

            db_obj.commit_update()
            print("KA and PG preferences successfully dumped to the database.")

        except Exception as e:
            print(f"An error occurred: {e}")

# Usage for dumbp registration
# UserDataQuery.dump_Students_data('canvas_mapping2.csv')
# UserDataQuery.dump_background_info_from_excel()
# UserDataQuery.migrate_student_data(194276,248)

if __name__ == "__main__":
    print(UserDataQuery.get_user_scores(3))
    pass

