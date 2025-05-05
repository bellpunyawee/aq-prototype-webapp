"""
This file is a place holder of function to perform any credential data and user normal inquery
"""
# Always set parent package, relative use case cause failure
import sys, os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from interfaces.db_connector import DB_Object
from globalclass.crypto import CryptoLib

class SystemAdminClass():
    @staticmethod
    def registration(username, password, name, canvas_id):
        db_obj = DB_Object("USERINFO_DB")
        get_info = db_obj.perform_sql("select id from user_table where username=\""+username + "\"", True)
        print(get_info)
        if (len(get_info) == 0):
            # user not found
            encode_password = username + CryptoLib.encode_base64(password) # Salt + password
            encode_password = CryptoLib.generate_sha256(encode_password)
            db_obj.perform_sql("insert into user_table(username, password) values(\"" + username + "\", \"" + encode_password + "\")")
            db_obj.commit_update()
            get_info = db_obj.perform_sql("select id from user_table where username=\""+username + "\"", True)
            if (len(get_info) == 0):
                ret_val = False # Registration incomplete
            else:
                ret_val = True # Registration complete but only name
                this_id = get_info[0][0]
                
                sql_string = "insert into user_info(user_id, name, canvas_id) values("
                sql_string += str(this_id) + ",\"" + name + "\"," + str(canvas_id) + ")"
                db_obj.perform_sql(sql_string)
                db_obj.commit_update()
                get_info = db_obj.perform_sql("select name from user_info where name = \"" +name + "\"", True)
                if (len(get_info) == 0):
                    db_obj.perform_sql("delete from  user_table where id="+str(this_id))
                    db_obj.commit_update()
                    ret_val = False # Registration incomplete
                else:
                    ret_val = True# Registration fully completed
        else:
            ret_val = False

        return ret_val
    
    @staticmethod 
    def reset_password(username, new_password, admin_request=False, name_user=""):
        db_obj = DB_Object("USERINFO_DB")
        get_info = db_obj.perform_sql("select id from user_table where username=\""+username + "\"", True)
        if (len(get_info) == 0):
            # user not found
            ret_val = "User not found"
        else:
            if (admin_request):
                encode_new_password = username + CryptoLib.encode_base64(new_password) # Salt + plain password to base64
                ret_val = "Success"
            else:
                get_info = db_obj.perform_sql("select name from user_table inner join user_info on user_table.id = user_info.user_id where user_table.username=\""+username + "\"", True)
                if (len(get_info) != 0):
                    name = get_info[0][0]
                    input_name = name_user
                    # Trim and lower to make case insensitive and avoiding unknow space from database dumping
                    name = name.strip(" ")
                    name = name.lower()
                    input_name = input_name.strip(" ")
                    input_name = input_name.lower()
                    
                    if (name == input_name):
                        encode_new_password = username + new_password # Salt + prebase64 password
                        ret_val = "Success"
                    else:
                        ret_val = "Provided name does not match with registered name"
                else:
                    ret_val = "Username is not found in system"

            if (ret_val == "Success"):
                encode_new_password = CryptoLib.generate_sha256(encode_new_password)
                db_obj.perform_sql("update user_table set password = \"" + encode_new_password + "\" where username=\""+username + "\"")
                db_obj.commit_update()
                get_info = db_obj.perform_sql("select password from user_table where username=\""+username + "\"", True)
                if (get_info[0][0] == encode_new_password):
                    ret_val = "Success"
                else:
                    ret_val = "Fail, unable to update new password" # Update not completed

        return ret_val

class UserAuthentication():
    __login_successful = False
    __user_id = -1
    
    def __init__(self, login_state:int =0, user_id:int =0, session_id:str ="" ,username:str ="" ,password:str =""):
        if (login_state == 0):
            self.__login(username, password)
        else:
            session_id_exp = session_id.split("_")
            user_id_session = int(session_id_exp[0])
            if (user_id == user_id_session):
                self.__login_successful = True
                self.__user_id = user_id
            else:
                self.__login_successful = False

    def __login(self, username:str, password:str):
        db_obj = DB_Object("USERINFO_DB")
        get_user = db_obj.perform_sql("select username, password, id from user_table where username=\"" + username + "\"", True)
        pw_idx = 1

        encode_password = username + password
        encode_password = CryptoLib.generate_sha256(encode_password)

        if (len(get_user) != 0) and \
            ((get_user[0][pw_idx] == encode_password)):
            self.__login_successful = True
            self.__user_id = get_user[0][2]

    def get_user_info(self):
        db_obj = DB_Object("USERINFO_DB")
        get_info = db_obj.perform_sql("select name from user_info where user_id="+str(self.__user_id), True)
        return get_info[0][0]
    
    def get_canvas_id(self):
        db_obj = DB_Object("USERINFO_DB")
        get_info = db_obj.perform_sql("select canvas_id from user_info where user_id="+str(self.__user_id), True)
        return get_info[0][0]

    def get_user_id(self):
        return self.__user_id

    """ Get Authentication status, to be used with session"""
    def get_login_status(self):
        return self.__login_successful


"""
New user will be registered only from backend side, not having frontend section.
Example, Add this python code:
SystemAdminClass.registration("username", "password", "Full name")

v

Run

"""

if __name__ == "__main__":
    for i in range(1, 41):
        student_id = f"s{i:03d}" # username can be an 'email'
        password = "1234"  # Assuming the password is the same for all students
        fullname = f"Student #{i}" # LTI assigns 'given_name' and 'family_name'
        SystemAdminClass.registration(student_id, password, fullname)

    pass