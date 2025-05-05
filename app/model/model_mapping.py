"""
This file is a place holder of function to get question data
"""
# Always set parent package, relative use case cause failure
import sys, os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from interfaces.db_connector import DB_Object

class GenQuizPool:
    @staticmethod
    def generate_p_quiz_pool():
        quiz_pool = [[],[],[]]
        db_obj = DB_Object("ADQ_DB")
        temp = db_obj.perform_sql("select cell_index, id as question_index from quiz_pool where pretest_quiz=1", True)

        for i in range(0, len(temp)):
            quiz_pool[1].append(temp[i][0])
            quiz_pool[2].append(temp[i][1])

        return quiz_pool

    @staticmethod
    def generate_quiz_df():
        db_obj = DB_Object("ADQ_DB")
        quiz_df = db_obj.perform_sql("select id as question_index, question_text, opt_1, opt_2, opt_3, opt_4, answer from quiz_pool", True)
        return quiz_df
    
    @staticmethod
    def generate_quiz_pool():
        quiz_pool = {}
        db_obj = DB_Object("ADQ_DB")
        temp = db_obj.perform_sql("select cell_index, id as question_index from quiz_pool where pretest_quiz=0", True)

        for i in range(0, len(temp)):
            cell_index = temp[i][0]
            question_index = temp[i][1]

            if cell_index not in quiz_pool:
                quiz_pool[cell_index] = []
            quiz_pool[cell_index].append(question_index)

        return quiz_pool
    
    @staticmethod
    def get_question_data(question_index:int):
        db_obj = DB_Object("ADQ_DB")
        question_data = db_obj.perform_sql("select question_text, opt_1, opt_2, opt_3, opt_4 from quiz_pool where id=" + str(question_index), True)
        question_data = question_data[0]
        return question_data  # Return the learner's response as an integer
    
    @staticmethod
    def get_explanation_data(question_index:int):
        db_obj = DB_Object("ADQ_DB")
        explanation_data = db_obj.perform_sql("select explanation from quiz_pool where id=" + str(question_index), True)
        explanation_data = explanation_data[0]

        return explanation_data
    
    @staticmethod
    def get_cell_index(question_index:int):
        db_obj = DB_Object("ADQ_DB")
        cell_index = db_obj.perform_sql("select cell_index from quiz_pool where id=" + str(question_index), True)
        cell_index = cell_index[0]

        return cell_index
    
    def get_learner_response(question_index:int,
                             question_answer:int):
        
        """ Answer checking """
        db_obj = DB_Object("ADQ_DB")
        response = db_obj.perform_sql("select id from quiz_pool where id="+str(question_index)+" and answer="+str(question_answer), True)

        if (len(response) > 0):
            response = 1
        else:
            response = 0

        return response
    
    def get_answer_index(question_index):
         """ Mapping answer index with shuffle ones .. retrieved from Database """
         db_obj = DB_Object("ADQ_DB")
         response = db_obj.perform_sql("select answer from quiz_pool where id="+str(question_index), True)
         extracted_value = response[0][0]
         return extracted_value
    
    def get_rationale(question_index):
         """ Mapping answer index with shuffle ones .. retrieved from Database """
         db_obj = DB_Object("ADQ_DB")
         response = db_obj.perform_sql("select explanation from quiz_pool where id="+str(question_index), True)
         rationale = response[0][0]
         return rationale
        
if __name__ == "__main__":
    pass