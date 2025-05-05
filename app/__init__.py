"""
This file is Master Server initiate file and configuration

Canvas Integration via LTI1.3 Modification --> Merge routes.py and responses.py

# Adaptive Quiz App for Introduction to Project Management Course

header_template.html
model_enginev2.py
model_usercontrol.py

"""

from http.client import responses
import os
import warnings
import threading

'LLM'
import pandas as pd
""" Canvas API """
import requests

'''======================= Added (LTI) ==============================='''
import datetime
from datetime import timedelta
from os import urandom
import pprint


from tempfile import mkdtemp
from flask import Flask, jsonify, request, render_template, url_for, session
from flask_caching import Cache
from werkzeug.exceptions import Forbidden
from werkzeug.utils import redirect
from pylti1p3.contrib.flask import FlaskOIDCLogin, FlaskMessageLaunch, FlaskRequest, FlaskCacheDataStorage
from pylti1p3.deep_link_resource import DeepLinkResource
from pylti1p3.tool_config import ToolConfJsonFile

from .model import *

from .globalclass import crypto as Crypto

import hashlib, time
from flask_caching import Cache
from flask_session import Session
from cachelib.file import FileSystemCache
from pylti1p3.contrib.flask import FlaskRequest, FlaskCacheDataStorage, FlaskMessageLaunch
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.registration import Registration

from cachelib import MemcachedCache
from cachelib.memcached import MemcachedCache
from flask_cors import CORS,cross_origin

from .model.canvas_overrides_delete_specific import cleanup_overrides
from .model.canvas_overrides_create_update import create_assignment_overrides
from .model.canvas_did_student_complete_all_paths import check_all_assignments_completed, check_to_unlock_all_modules
from .model.canvas_overrides_create_given_assignment_list import create_assignment_given_assignment_list
#from .canvas_overrides_app import *
''' CANVAS API Process '''
from dotenv import load_dotenv

'''======================= LTI CONFIGURATION ==============================='''

class ReverseProxied:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        scheme = environ.get('HTTP_X_FORWARDED_PROTO')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)

def configure():
    load_dotenv()

# 'New' Application creation
app = Flask(__name__, template_folder='templates', static_folder='static')
app.wsgi_app = ReverseProxied(app.wsgi_app)
app.secret_key = urandom(24)
# print(app.secret_key)
configure()

# # Assign 'session' as session
# global session
# session = session

config = {
    "DEBUG": True,
    "ENV": "development",
    "DEBUG_HOST": "0.0.0.0",
    "DEBUG_PORT": 15236,
    "SESSION_PERMANENT": True,
    "CACHE_TYPE": "simple",  # Use Memcached for caching
    "CACHE_DEFAULT_TIMEOUT": 600,
    "SECRET_KEY": app.secret_key,
    "SESSION_TYPE": "memcached",  # Use Memcached for session storage
    "SESSION_MEMCACHED": MemcachedCache(['127.0.0.1:15236'], default_timeout=7200),  # Memcached server address
    "SESSION_COOKIE_NAME": 'session',
    "SESSION_COOKIE_HTTPONLY": True,  # To allow JavaScript to access cookies, if necessary
    "SESSION_COOKIE_SECURE": True,     # If your environment is HTTPS, cookies should be marked as Secure
    "SESSION_COOKIE_SAMESITE": 'None', # Due to LTI, which often embeds content in iframes, set it to 'None' to allow cross-site requests
    "SESSION_USE_SIGNER": True,
    "PERMANENT_SESSION_LIFETIME": timedelta(hours=1),
    "DEBUG_TB_INTERCEPT_REDIRECTS": False,
    "SESSION_REFRESH_EACH_REQUEST": True,
    'PREFERRED_URL_SCHEME': 'https',
    "SERVER_NAME": 'adaptivequiz-cpfm.app'
}

# # # PROD Configuration
# config = {
#     "DEBUG": False,  # Disable debug mode in production to prevent information disclosure
#     "ENV": "production",  # Set the environment to production
#     "DEBUG_HOST": "0.0.0.0",  # Keep it to listen on all available IPs, but consider a firewall to protect access
#     "DEBUG_PORT": 15236,  # Ensure port is properly configured and protected by firewall

#     "SESSION_PERMANENT": True,  # Keep session persistence enabled for better user experience
#     "CACHE_TYPE": "memcached",  # Use Memcached (avoid "simple" in prod for scalability)
#     "CACHE_DEFAULT_TIMEOUT": 600,  # Timeout for cache items; adjust as per application needs

#     "SECRET_KEY": app.secret_key,  # Move the secret key to an environment variable for security
#     "SESSION_TYPE": "memcached",  # Use Memcached for session storage
#     "SESSION_MEMCACHED": MemcachedCache(['127.0.0.1:15236'], default_timeout=7200),
#     "SESSION_COOKIE_NAME": 'session',
#     "SESSION_COOKIE_HTTPONLY": True,  # Ensure JavaScript cannot access cookies to reduce XSS risk
#     "SESSION_COOKIE_SECURE": True,  # Keep it True since HTTPS is required in production for security
#     "SESSION_COOKIE_SAMESITE": 'None',  # Required if your app is embedded in an iframe
#     "SESSION_USE_SIGNER": True,  # Sign session cookies for added security
#     "PERMANENT_SESSION_LIFETIME": timedelta(hours=1),  # Consider extending this if needed for your user experience
#     "DEBUG_TB_INTERCEPT_REDIRECTS": False,  # Ensure no debug toolbar intercept in production
#     "SESSION_REFRESH_EACH_REQUEST": True,  # Refresh session lifetime on each request for active users
#     "PREFERRED_URL_SCHEME": 'https',  # Keep HTTPS as preferred for security
#     "SERVER_NAME": 'adaptivequiz-cpfm.app'
# }

app.config.from_mapping(config)
warnings.simplefilter("ignore")
cache = Cache(app)

# Initialize the cross origin resource sharing
CORS(app, supports_credentials=True)


PAGE_TITLE = 'Adaptive Quiz App'

# Assign the canvas API key from the environment variables (access_token)
canvas_api_key = os.getenv('CANVAS_API_KEY')
openai_api_key = os.getenv('OPENAI_API_KEY')
pinecone_api_key = os.getenv('PINECONE_API_KEY')
canvas_prod_key = os.getenv('CANVAS_PROD_KEY')
access_token_for_overrides = os.getenv('CANVAS_API_KEY')
# Debugging prints
# print(f"Canvas API Key: {canvas_api_key}")
# print(f"OpenAI API Key: {openai_api_key}")
# print(f"Pinecone API Key: {pinecone_api_key}")
# print(f"Canvas PROD Key: {canvas_prod_key}")
if not canvas_api_key or not openai_api_key or not pinecone_api_key or not canvas_prod_key:
    raise ValueError("One or more API keys are missing.")

# Canvas URL endpoint
# base_url = 'https://nus-dev.instructure.com' # development
base_url = 'https://canvas.nus.edu.sg' # production
course_id = '72396' # PM5101 course
# course_id = '55450' # sandbox course


# Check if the API key is retrieved
if canvas_api_key:
    print("Canvas API Key Loaded Successfully")
else:
    print("Canvas API Key Not Found")

'''_________ Canvas API _________'''
def get_canvas_user_id(base_url, course_id, access_token):
    """
    Retrieves the user_id for a specific course.

    Args:
        base_url (str): The base URL of the Canvas instance (e.g., 'https://canvas.instructure.com').
        course_id (str or int): The ID of the course.
        access_token (str): The access token for authentication.

    Returns:
        int: The user_id associated with the course.
    """
    endpoint = f"{base_url}/api/v1/courses/{course_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        course_info = response.json()
        # print('Course Info: ',course_info)
        user_id = course_info.get('enrollments')[0].get('user_id')
        return user_id
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Status Code: {response.status_code}")
        print(f"Response content: {response.text}")
    except requests.exceptions.RequestException as err:
        print(f"An error occurred: {err}")
    return None

def submit_prequiz_assignment(base_url, course_id, assignment_id, user_id, grade, access_token):
        # base_url = 'https://nus-dev.instructure.com'
        base_url = 'https://canvas.nus.edu.sg' # actual environment
        url =  f"{base_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    
        headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
        }

        # Submission Body
        data = {
            "submission": {
                "posted_grade": str(grade)
            }
        }
        
        response = requests.put(url, json=data, headers=headers)
    
        if response.status_code == 200:
            print(f"Grade {grade} successfully updated for user {user_id}")
        else:
            print(f"Failed to update grade. Status Code: {response.status_code}, Response: {response.text}")

def submit_status(base_url, course_id, assignment_id, user_id, access_token):
        # base_url = 'https://nus-dev.instructure.com'
        base_url = 'https://canvas.nus.edu.sg' # actual environment
        url =  f"{base_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions"
    
        headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
        }

        # Submission Body
        data = {
            "submission": {
                "url": base_url,
                "submission_type": 'basic_lti_launch',
                "user_id": user_id
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
    
        if response.status_code == 201:
            print(f"Submission successfully updated for user {user_id}")
        else:
            print(f"Failed to update grade. Status Code: {response.status_code}, Response: {response.text}")            

def get_assignments(base_url, course_id, access_token):
    """
    Function to retrieve assignment names and IDs for a given course in Canvas, handling pagination.

    :param base_url: The base URL for the Canvas instance.
    :param course_id: The ID of the course.
    :param access_token: Your Canvas API token.
    :return: A list of dictionaries containing assignment names and IDs.
    """
    # Set up headers with the authorization token
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # API endpoint to list assignments for a specific course
    url = f'{base_url}/api/v1/courses/{course_id}/assignments'
    assignment_list = []

    while url:
        # Make the request
        response = requests.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            try:
                assignments = response.json()

                # Extract assignment details
                assignment_list.extend([
                    {'name': assignment['name'], 'id': assignment['id']}
                    for assignment in assignments
                ])

                # Check if there is a "next" page in the "Link" header
                if 'Link' in response.headers:
                    links = response.headers['Link']
                    next_link = None

                    # Extract the "next" URL from the link header if available
                    for link in links.split(','):
                        if 'rel="next"' in link:
                            next_link = link.split(';')[0].strip('<>')

                    # If there is a next page, set the URL to it, else exit the loop
                    if next_link:
                        url = next_link
                    else:
                        url = None

            except requests.exceptions.JSONDecodeError:
                print("Error decoding JSON response")
                return None

        else:
            print(f"Failed to retrieve assignments: {response.status_code} - {response.text}")
            return None

    return assignment_list

# list of assignment_ids to be mapped with the cell_ids
assignment_ids_list = get_assignments(base_url, course_id, canvas_api_key) # ex.
# {'name': '[Quiz] Initiating integration management', 'id': 149669}, {'name': '[Quiz] Initiating stakeholder management', 'id': 149683}, {'name': '[Quiz] Planning integration management', 'id': 149670}
# cell_ids_map = [{'149669': 1}, {'149670': 2}, {'149674':3},{'149682':5}
#                 ,{'149671':18}, {'149675':19}, {'149679':20}, {'149673':24}, {'149677':25}
#                 ,{'149680':26}, {'149683':27}, {'149672':28}, {'149678':29}, {'149681':30}] # quiz tagged to cell

# PM5101 course ID = 72396 : Assignment Lists (Assignment ID: cell ID)
cell_ids_map = [
    {"159526": [0]},
    {"159527": [1, 27]},
    {"159528": [2, 6]},
    {"159529": [8, 10]},
    {"159530": [12, 15, 18, 28]},
    {"159531": [21, 24]},
    {"159532": [3, 13, 22, 25]},
    {"159533": [16, 19, 29]},
    {"159534": [4, 7, 9, 11]},
    {"159535": [14, 17, 20, 23, 26, 30]},
    {"159536": [5]},
]

# Canvas Sandbox course ID = 55450 : Assignment Lists (Assignment ID: cell ID)
# cell_ids_map = []

def mod_to_cell(mod_title, module_list, id_map):
    """
    Function to find the corresponding value in id_map for a given module title.

    :param mod_title: The title of the module to search for.
    :param module_list: A list of dictionaries containing 'name' and 'id' for each module.
    :param id_map: A list of dictionaries mapping 'id' to a specific value.
    :return: The corresponding value in id_map or None if not found.
    """
    # Step 1: Find the id for the given mod_title in the module_list
    module_id = next((module['id'] for module in module_list if module['name'] == mod_title), None)

    # Step 2: Find the corresponding value in id_map using the module_id
    if module_id:
        module_id_str = str(module_id)  # Convert to string for comparison
        output_value = next((mapping[module_id_str] for mapping in id_map if module_id_str in mapping), None)
        return output_value
    return None

# def mod_to_cell(mod_title, module_list, id_map):
#     """
#     Function to find the corresponding value in id_map for a given module title,
#     and return the values as a concatenated string.

#     :param mod_title: The title of the module to search for.
#     :param module_list: A list of dictionaries containing 'name' and 'id' for each module.
#     :param id_map: A list of dictionaries mapping 'id' to a specific value.
#     :return: The corresponding values in id_map as a comma-separated string, or None if not found.
#     """
#     # Step 1: Find the id for the given mod_title in the module_list
#     module_id = next((module['id'] for module in module_list if module['name'] == mod_title), None)

#     # Step 2: Find the corresponding value in id_map using the module_id
#     if module_id:
#         module_id_str = str(module_id)  # Convert to string for comparison
#         output_value = next((mapping[module_id_str] for mapping in id_map if module_id_str in mapping), None)
#         print("Output Value: ", output_value)
#         if output_value:
#             # Convert the list of values to a comma-separated string
#             out = ",".join(map(str, output_value))
#             print("Output: ", out)
#             return ",".join(map(str, output_value))
#     return None

def map_mod_to_cell_id(mod, cell_ids_map):
    for item in cell_ids_map:
        for key, value in item.items():
            if value == mod:
                return key  # Return the key that matches the given mod value
    return None  # Return None if the mod value is not found

def extend_string_and_list(initial_string, sample_list):
    """
    Extend an initial comma-separated string with unique items from a list (excluding None values) 
    and return both the updated list of integers and the updated comma-separated string.
    
    :param initial_string: Comma-separated string of numbers (can be empty or None). Fetching directly from Students DB
    :param sample_list: List of items to add, None values will be ignored. Fetching over the Flask session
    :return: Tuple containing (extended list of integers, updated comma-separated string). ex. (session['check_cell'], cell_history)
    """
    # Handle the case where initial_string is empty or None
    if not initial_string or initial_string == 'None':
        initial_list = []
    else:
        initial_list = list(map(int, initial_string.split(',')))

    # Handle the case where sample_list is None
    if sample_list is None:
        sample_list = []

    # Extend the list with unique items from sample_list, ignoring None values
    for item in sample_list:
        if item is not None and item not in initial_list:
            initial_list.append(item)
    
    # Convert the list back to a comma-separated string
    updated_string = ','.join(map(str, initial_list))
    
    return initial_list, updated_string

def update_user_cell_history(user_id, session, assignment_id):
    """
    Function to retrieve, update, and save cell history for a user.
    
    :param user_id: The ID of the user whose cell history needs to be updated.
    :param session: The session object containing user's session data.
    :return: None
    """
    # Step 1: Get the cell history from the database
    check_cell_str = model_dbquery.UserDataQuery.get_cell_history(user_id)
    
    # Step 2: Update the cell history string and list using extend_string_and_list
    updated_check_cell, updated_string = extend_string_and_list(check_cell_str, session['check_cell'])
    
    # Step 3: Update the cell history in the database
    model_dbquery.UserDataQuery.update_cell_history(user_id, updated_string)
    print("Updated Cell History: ", updated_string)
    model_dbquery.UserDataQuery.update_student_score(user_id, assignment_id)

    # Step 4: Update session data with the updated cell list
    session['check_cell'] = updated_check_cell
    # session['assignment_id'] = int(assignment_id)
    session['assignment_id'] = int(assignment_id) if assignment_id is not None else 0  # or some other default value

def replace_user_cell_history(user_id, session, assignment_id):
    """
    Function to retrieve, replace, and save cell history for a user.
    
    :param user_id: The ID of the user whose cell history needs to be replaced.
    :param session: The session object containing user's session data.
    :param assignment_id: The ID of the assignment.
    :return: None
    """
    try:
        # Step 1: Get the new cell history from the session
        new_check_cell = session.get('check_cell', [])
        
        # Ensure new_check_cell is a list even if None or other invalid type is returned
        if not isinstance(new_check_cell, list):
            new_check_cell = []

        # Step 2: Convert the new list to a comma-separated string
        new_string = ','.join(map(str, new_check_cell))

        # Step 3: Replace the cell history in the database
        model_dbquery.UserDataQuery.update_cell_history(user_id, new_string)
        model_dbquery.UserDataQuery.update_student_score(user_id, assignment_id)

        # Step 4: Update session data with the new cell list
        session['check_cell'] = new_check_cell

        # Handle assignment_id in session
        session['assignment_id'] = int(assignment_id) if assignment_id is not None else 0  # or some default value
    
    except Exception as e:
        # Log the error and raise it for debugging
        print(f"Error in replace_user_cell_history: {e}")
        raise ValueError(f"Failed to replace cell history for user {user_id}. Error: {str(e)}")



'''____________________________________________________________________________________________________________'''

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

def get_launch_data_storage():
    return FlaskCacheDataStorage(cache)

def get_jwk_from_public_key(key_name):
    key_path = os.path.join(app.root_path, 'conf', key_name)
    f = open(key_path, 'r')
    key_content = f.read()
    jwk = Registration.get_jwk(key_content)
    f.close()
    return jwk

''' ======================== '''

""" ERROR HANDLING SECTION"""

# Custom error handler for 403 Forbidden
@app.errorhandler(403)
def forbidden_error_handler(error):
    return "<h1>403 Forbidden - Access is forbidden</h1>", 403

# Custom error handler for accessing undefined page
@app.errorhandler(404)
def page_not_found(error):
    return "<h1>404 Not Found</h1>", 404

''' ======================== '''

# LTI login OIDC
@app.route("/login/", methods=['GET','POST'])
@cross_origin(supports_credentials=True)
def login():
    # LTI 1.3
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    launch_data_storage = get_launch_data_storage()

    flask_request = FlaskRequest()
    target_link_uri = flask_request.get_param('target_link_uri')
    print("Target: ", target_link_uri, flush=True)
    if not target_link_uri:
        raise Exception('Missing "target_link_uri" param')

    oidc_login = FlaskOIDCLogin(flask_request, tool_conf, launch_data_storage=launch_data_storage)

    return oidc_login\
        .enable_check_cookies()\
        .redirect(target_link_uri)

# LTI message launch
@app.route("/launch/", methods=['GET','POST'])
@cross_origin(supports_credentials=True)
def display_homepage():
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    flask_request = FlaskRequest()
    launch_data_storage = get_launch_data_storage()
    message_launch = ExtendedFlaskMessageLaunch(flask_request, tool_conf, launch_data_storage=launch_data_storage)
    message_launch_data = message_launch.get_launch_data()
    # pprint.pprint(message_launch_data)
    # message_launch_data['https://purl.imsglobal.org/spec/lti/claim/lti1p1']['user_id']
    mod_title = message_launch_data['https://purl.imsglobal.org/spec/lti/claim/resource_link']['title']

    'Fetch LTI message to frontend'
    username = message_launch_data['email'] # email registered in Canvas
    curr_user_name = message_launch_data.get('name', '') # fullname registered in Canvas
    # df = pd.read_csv(r'C:\Users\punyawee\Downloads\AQ_Prototype\docs\canvas_mapping.csv')
    canvas_map_path = os.path.join(os.curdir, 'docs', 'canvas_mapping.csv')
    df = pd.read_csv(canvas_map_path)
    # df = pd.read_csv(r'~/Documents/GitHub/AQ_Prototype/docs/canvas_mapping.csv')
    result= df[df['username'] == username]['canvas_id']
    
    if not result.empty:
        canvas_id = result.values[0]
        print('Canvas ID: ', canvas_id)  # Return the canvas_id
    else:
        pass  # If username not found, return None

    model_dbquery.UserDataQuery.check_username_LTI(username, curr_user_name, canvas_id) # To check if the LTI username already exists in the database

    # login_status = model_usercontrol.UserAuthentication(username=username, password=12345)

    if session.get('user_id') is not None:
        print("user_id: Found")
        session_start = True
        timer_select = session['m_duration']
        quiz_number = session['num_quiz']
        max_limit = session['max_limit_quiz']
        session['n_attempt'] = model_dbquery.UserDataQuery.get_latest_attempt(session['user_id']) + 1
    else:
        print("user_id: Not Found")
        session_start = False
        timer_select = 10
        quiz_number = 3
        max_limit = 10
        path = []
        path_text = ""

    tpl_kwargs = {
        'session_start': session_start,
        'session_cookie': session,
        'timer_select': timer_select,
        'quiz_number': quiz_number,
        'max_limit': max_limit,
        'page_title': 'Dashboard',
        'is_deep_link_launch': message_launch.is_deep_link_launch(),
        'launch_data': message_launch.get_launch_data(),
        'launch_id': message_launch.get_launch_id(),
        'curr_user_name': message_launch_data.get('name', ''),
        'username': message_launch_data['email']
    }
    
    # Check if "Post" is in the module title
    if 'Post' in mod_title:
        # Check if completed post-quiz assignment or not?
        if not (check_to_unlock_all_modules(course_id,[159913],canvas_id)):
            return redirect("/posttest_start/" + message_launch.get_launch_id() + "/") # Redirect to the posttest start page with the launch ID
        else:
            return render_template('dashboard.html', **tpl_kwargs)
    else:
        # Render the dashboard template if no redirect is needed
        return render_template('dashboard.html', **tpl_kwargs)

@app.route('/jwks/', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_jwks():
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    return jsonify({'keys': tool_conf.get_jwks()})

""" ROUTING ENDPOINT """
# temporary testing for pretest page redirecting
@app.route("/launch_2/<launch_id>/", methods=['GET','POST'])
@cross_origin(supports_credentials=True)
def display_homepage_2(launch_id):
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    flask_request = FlaskRequest()
    launch_data_storage = get_launch_data_storage()
    message_launch = ExtendedFlaskMessageLaunch.from_cache(launch_id, flask_request, tool_conf, launch_data_storage=launch_data_storage)
    message_launch_data = message_launch.get_launch_data()
    

    if session.get('user_id') is not None:
        print("user_id: Found")
        session_start = True
        timer_select = session['m_duration']
        quiz_number = session['num_quiz']
        max_limit = session['max_limit_quiz']
        #main_exp_group.main() # move override it to here
        # Run `main_exp_group.main()` as a background thread
        # background_thread = threading.Thread(target=main_exp_group.main)
        # background_thread.start()
    else:
        print("user_id: None")
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
    ret_val = render_template('redirect.html', **tpl_kwargs)
    # bad practice

    return ret_val

# temporary testing for posttest page redirecting
@app.route("/launch_3/<launch_id>/", methods=['GET','POST'])
@cross_origin(supports_credentials=True)
def display_homepage_3(launch_id):
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    flask_request = FlaskRequest()
    launch_data_storage = get_launch_data_storage()
    message_launch = ExtendedFlaskMessageLaunch.from_cache(launch_id, flask_request, tool_conf, launch_data_storage=launch_data_storage)
    message_launch_data = message_launch.get_launch_data()
    

    if session.get('user_id') is not None:
        print("user_id: Found")
        session_start = True
        timer_select = session['m_duration']
        quiz_number = session['num_quiz']
        max_limit = session['max_limit_quiz']
    else:
        print("user_id: None")
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
    ret_val = render_template('redirect2.html', **tpl_kwargs)

    return ret_val


# pretest for new users
@app.route("/pretest_start/<launch_id>/", methods=['GET','POST'])
@cross_origin(supports_credentials=True)
def display_pretest(launch_id):
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    flask_request = FlaskRequest()
    launch_data_storage = get_launch_data_storage()
    message_launch = ExtendedFlaskMessageLaunch.from_cache(launch_id, flask_request, tool_conf, launch_data_storage=launch_data_storage)
    message_launch_data = message_launch.get_launch_data()
    # pprint.pprint(message_launch_data)
    
    if (session.get('user_id') is not None):
        session_start = True
    else:
        session_start = False

    tpl_kwargs = {
        'session_start': session_start,
        'session_cookie': session,
        'page_title': 'Dashboard',
        'is_deep_link_launch': message_launch.is_deep_link_launch(),
        'launch_data': message_launch.get_launch_data(),
        'launch_id': message_launch.get_launch_id(),
        'curr_user_name': message_launch_data.get('name', '')
    }
    ret_val = render_template('pretest_page.html', **tpl_kwargs)

    return ret_val

# ! In-progress
# post-test for QE2
@app.route("/posttest_start/<launch_id>/", methods=['GET','POST'])
@cross_origin(supports_credentials=True)
def display_posttest(launch_id):
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    flask_request = FlaskRequest()
    launch_data_storage = get_launch_data_storage()
    message_launch = ExtendedFlaskMessageLaunch.from_cache(launch_id, flask_request, tool_conf, launch_data_storage=launch_data_storage)
    message_launch_data = message_launch.get_launch_data()

    # Fetch LTI message to frontend
    username = message_launch_data['email'] # email registered in Canvas
    curr_user_name = message_launch_data.get('name', '') # fullname registered in Canvas
    canvas_map_path = os.path.join(os.curdir, 'docs', 'canvas_mapping.csv')
    df = pd.read_csv(canvas_map_path)
    result= df[df['username'] == username]['canvas_id']
    # session['n_attempt'] = model_dbquery.UserDataQuery.get_latest_attempt(session['user_id'])
    
    if not result.empty:
        canvas_id = result.values[0]
        print('Canvas ID: ', canvas_id)  # Return the canvas_id
    else:
        pass  # If username not found, return None

    model_dbquery.UserDataQuery.check_username_LTI(username, curr_user_name, canvas_id)
    
    if (session.get('user_id') is not None):
        session_start = True
        session['n_attempt'] = model_dbquery.UserDataQuery.get_latest_attempt(session['user_id']) + 1
    else:
        session_start = False

    tpl_kwargs = {
        'session_start': session_start,
        'session_cookie': session,
        'page_title': 'Dashboard',
        'is_deep_link_launch': message_launch.is_deep_link_launch(),
        'launch_data': message_launch.get_launch_data(),
        'launch_id': message_launch.get_launch_id(),
        'curr_user_name': message_launch_data.get('name', '')
    }
    ret_val = render_template('posttest_page.html', **tpl_kwargs)

    return ret_val    

# logout
@app.route("/logout/<launch_id>/", methods=["GET", "POST"])
@cross_origin(supports_credentials=True)
def fn_logout(launch_id):
    ''' No need when using LTI Integration'''
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    flask_request = FlaskRequest()
    launch_data_storage = get_launch_data_storage()
    message_launch = ExtendedFlaskMessageLaunch.from_cache(launch_id, flask_request, tool_conf, launch_data_storage=launch_data_storage)
    # message_launch_data = message_launch.get_launch_data()
    session.clear()
    return redirect("/launch_2/"+launch_id+"/")

'=====================Temporary memory========================'
# Single quiz engine to optimize calling procedure
GLOBAL_QUIZ_ENGINE = model_enginev2.AdaptiveQuiz()
# Temporary memory, this memory shall be lived until the server is shutdown.
# Due to session is unable to store complex object and pickle is unusable, this is the way.
G_MEMORY = {}
P_MEMORY = {}
'=============================================================='
    
def generateSessionID():
    return Crypto.CryptoLib.generate_sha256(str(time.time()))

# Application start
@app.route("/access/<launch_id>/", methods=["POST"])
@cross_origin(supports_credentials=True)
def fn_login(launch_id):
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    flask_request = FlaskRequest()
    launch_data_storage = get_launch_data_storage()
    message_launch = ExtendedFlaskMessageLaunch.from_cache(launch_id, flask_request, tool_conf, launch_data_storage=launch_data_storage)
    message_launch_data = message_launch.get_launch_data()
    # pprint.pprint(message_launch_data)

    # mod_title = message_launch_data['https://purl.imsglobal.org/spec/lti/claim/resource_link']['title']
    # mod = mod_to_cell(mod_title, assignment_ids_list, cell_ids_map) # map module title with the cell_id

    if request.method == "POST":
        data = request.get_json()
        # login_status = model_usercontrol.UserAuthentication(username=message_launch_data['email'], password='12345') 
        login_status = model_usercontrol.UserAuthentication(username=message_launch_data['email'], password=data['password'])
        if ((session.get('user_id') is None)):
            if login_status.get_login_status() == True:
                # session['session_id'], session['user_id'] = str(login_status.get_user_id()) + "_" + generateSessionID(), login_status.get_user_id()
                session['session_id'], session['user_id'] = str(login_status.get_user_id()) + "_" + generateSessionID(), login_status.get_user_id()
                # Default settings
                session['canvas_id'] = login_status.get_canvas_id()
                session['num_update'] = 0
                session['m_duration'] = 10000
                session['num_quiz'] = 3 # minimum number of quiz items of each cell
                session['num_cell'] = 3 # minimum number of num_cell
                session['max_limit_quiz'] = 10 # maximum number of quiz to be asked
                session['check_cell'] = mod_to_cell(message_launch_data['https://purl.imsglobal.org/spec/lti/claim/resource_link']['title'], assignment_ids_list, cell_ids_map) # initial assign for new function
                session['assignment_id'] = map_mod_to_cell_id(mod_to_cell(message_launch_data['https://purl.imsglobal.org/spec/lti/claim/resource_link']['title'], assignment_ids_list, cell_ids_map), cell_ids_map)
                replace_user_cell_history(session['user_id'], session, session['assignment_id'])

                if (data['remember'] == True):
                    session.permanent = True
                else:
                    session.permanent = False
                response = {"result":"success", "session": session, "posttest_start": 'false'}
                session.permanent = True

            else:
                response = {"result":"fail", "status": "Username/Password is incorrect"}
        else:
            if ((session.get('user_id') is None) or (session.get('user_id') == -1)):
                session.clear() # Force logout
                response = {"result":"fail", "status": "No record on loggin in"}
            else:
                # this condition is when the session is running and logging in has been completed
                session['check_cell'] = mod_to_cell(message_launch_data['https://purl.imsglobal.org/spec/lti/claim/resource_link']['title'], assignment_ids_list, cell_ids_map) # need to assign from Canvas and store for the subsequent module: QE2
                session['assignment_id'] = map_mod_to_cell_id(mod_to_cell(message_launch_data['https://purl.imsglobal.org/spec/lti/claim/resource_link']['title'], assignment_ids_list, cell_ids_map), cell_ids_map)
                replace_user_cell_history(session['user_id'], session, session['assignment_id'])
                # Ex. matching module title and assignment_id --> [output] 
                response = {"result":"fail", "status": "Already logged in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}
    return jsonify(response)

' --- Session Debugger --- '
# @app.before_request
# def check_session():
#     print("Session Cookies data before request:",session)

@app.after_request
def after_request_func(response):
    ''' This endpoint is to monitor session session '''
    print("Session Cookies data after request:", session, flush=True)
    # session.permanent = True
    # print("Check secret_key" , app.secret_key)
    return response

@app.route("/req_save_settings", methods=["POST"])
def fn_req_save_settings():
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                ####################################################### Function start here
                data_json = request.get_json()
                allow_processing, num_cell, num_quiz, check_cell, m_duration, max_limit_quiz = sub_stq_check_data(data_json)
                print("Data save: ", data_json)
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
                pretest_status = model_dbquery.UserDataQuery().get_user_pretest(session['user_id']) # check there is any records in pretest_table
                if (pretest_status == True):
                    if (G_MEMORY.get(session['user_id']) != None):
                        session['quiz_start'] = True
                    else:
                        session['quiz_start'] = False
                    full_name = login_status.get_user_info()
                    disclaimer_text = model_dbquery.GeneralDataQuery.get_disclaimer()
                    photo_string = model_dbquery.UserDataQuery.get_user_photo(session['user_id'])
                    # ------- Recall Info from DB --------
                    session['n_attempt'] = model_dbquery.UserDataQuery.get_latest_attempt(session['user_id']) + 1
                    session['num_update'] = model_dbquery.UserDataQuery.get_latest_update(session['user_id']) + 1
                    
                    # ! ------- Update Cell History (PM Course) --------
                    check_cell_str = model_dbquery.UserDataQuery.get_cell_history(session['user_id']) # new cell_history
                    # print("Check Cell Str Before: ", check_cell_str, flush=True)
                    # model_dbquery.UserDataQuery.clear_cell_history(session['user_id']) # clear all cell_history
                    # check_cell_str = model_dbquery.UserDataQuery.get_cell_history(session['user_id']) # to store cell_history 
                    # print("Check Cell Str After: ", check_cell_str, flush=True)
                    # print("Session Check Cell: ", session['check_cell'], flush=True)
                    updated_check_cell, updated_string = extend_string_and_list(check_cell_str, [])
                    model_dbquery.UserDataQuery.update_cell_history(session['user_id'], updated_string) # update one by one cell with str
                    # print("Updated_check_cell: ", updated_check_cell, flush=True)
                    session['check_cell'] = updated_check_cell
                    
                    # Handle both NoneType and the string 'None'
                    if model_dbquery.UserDataQuery.get_student_score(session['user_id']) is None or model_dbquery.UserDataQuery.get_student_score(session['user_id']) == 'None':
                        session['assignment_id'] = 0  # Assign default value
                    else:
                        session['assignment_id'] = int(model_dbquery.UserDataQuery.get_student_score(session['user_id']))
                    
                    latest_time = model_dbquery.UserDataQuery.get_latest_time(session['user_id'], session['num_update']-1)
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
                                "score_list": score_list,
                                "latest_time": latest_time}
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

@app.route("/req_fetch_report_score", methods=["POST"]) # for putting LLM PF
def fn_req_fetch_report_score():
    if request.method == "POST":
        if session.get('user_id') is not None:
            login_status = model_usercontrol.UserAuthentication(
                login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status():
                session['n_attempt'] = model_dbquery.UserDataQuery.get_latest_attempt(
                    session['user_id']) + 1

                textbox_data = model_dbquery.GeneralDataQuery.get_textboxdata(session['user_id'], session['n_attempt']-1) # fetch feedback in db to variable

                if session['n_attempt'] > 1:
                    learner_ability, user_timestamp = model_dbquery.UserDataQuery.get_user_abilities(
                        session['user_id'])
                    showing_ability = []
                    if len(learner_ability) > 0:
                        # selected_quiz, response_list, choice_list, timestamp = model_dbquery.UserDataQuery.get_report_data(
                            # session['user_id'], (session['n_attempt'] - 1))
                        selected_quiz, response_list, choice_list, timestamp = model_dbquery.UserDataQuery.get_report_data(
                            session['user_id'], (session['n_attempt']-1))
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

@app.route("/req_get_quiz_streak", methods=["POST"])
def fn_req_get_quiz_streak():
    quiz_streak = []
    response = {}
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                if (session['n_attempt'] > 1):
                    learner_ability, user_timestamp = model_dbquery.UserDataQuery.get_user_abilities(session['user_id'])
                    if (len(learner_ability) > 0):
                        data = request.get_json()
                        selected_quiz, response_list, choice_list, timestamp = model_dbquery.UserDataQuery.get_report_data(session['user_id'], (data['attempt_num']))
                        for i in range(0, len(response_list)):
                            if (choice_list[i] == 0):
                                quiz_streak.append(-1)
                            else:
                                quiz_streak.append(response_list[i])
                        response["result"] = "success"
        else:
            response["result"] = "failure"
    response["quiz_streak"] = quiz_streak
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

                # selected_quiz, response_list, choice_list, timestamp = model_dbquery.UserDataQuery.get_report_data(session['user_id'], session['n_attempt'] - 1)
                data = request.get_json()
                selected_quiz, response_list, choice_list, timestamp = model_dbquery.UserDataQuery.get_report_data(session['user_id'], data['attempt_num'])
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
                # model_dbquery.UserDataQuery.insert_students_table(session['user_id'])
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
                    # _____________________________ may put LLM function here!! pre-quiz = baseline <-> n_attempt = 1
                    
                    # ! _____________________________ QE2 pre-quiz = baseline <-> n_attempt = 0
                    # QE2 needs PF for pre quiz?
                    # userLog_excel = model_dbquery.UserDataQuery.log_to_excel(session['user_id'], 1)
                    # # canvas_map_path = os.curdir + r'\docs\canvas_mapping.csv' # Mapping canvas user_id
                    # canvas_map_path = os.path.join(os.curdir, 'docs', 'canvas_mapping.csv')
                    # gpt_feedback_txt = aq_pf_prompt.main(userLog_excel, canvas_map_path, name='Baseline quiz')
                    # file_path = os.path.join('gpt_feedback_log', gpt_feedback_txt)
                    # with open(file_path, 'r', encoding='utf-8') as feedback:
                    #     feedback_string = feedback.read()
                    # model_dbquery.UserDataQuery.import_txt_to_db(session['user_id'], 1, feedback_string)
                    # ______________________________
                
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
                    # model_dbquery.UserDataQuery.log_user_activity(session['user_id'],model_dbquery.UserDataQuery.get_username(session['user_id']), 1, question_id, P_MEMORY['question'][0], request.json['selected_choice'], user_correct_ans, answer_db, correct_ans, rationale, int(time.time()))
                    # ! QE2
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

                        # ______________________________________________________________________________________________________
                        # Canvas instance and all necessary parameters for submission API .. Not yet stress test
                        pre_quiz_score = sum(normalize) # Pre-quiz score
                        # course_id = '55450'   # Sandbox Course: Fill your own course_id <str>
                        course_id = '72396'
                        # assignment_id = 3894  # assignment_id: Fill specific assignment_id <int>
                        assignment_id = 159905 # Prequiz Assignment ID for PM5101
                        canvas_user_id = session['canvas_id']
                        # user_id = get_canvas_user_id(base_url, course_id, canvas_api_key)
                        # user_id = 104993 # User ID: Assign user_id <int>
                        submit_prequiz_assignment(base_url, course_id, assignment_id, canvas_user_id, pre_quiz_score, canvas_api_key)
                        submit_status(base_url, course_id, assignment_id, canvas_user_id, canvas_api_key)
                        # ______________________________________________________________________________________________________

                        # Create mastery table
                        model_dbquery.UserDataQuery.create_mastery_slot(session['user_id'])
                        # Update mastery table
                        cell_mastery = model_dbquery.UserDataQuery.update_mastery_slot_pretest(session['user_id'])
                        current_ability_cell = GLOBAL_QUIZ_ENGINE.pre_ability(cell_mastery)
                        # Create train table
                        model_dbquery.UserDataQuery.create_train_slot(session['user_id'])
                        # ability assign for pretest
                        model_dbquery.UserDataQuery.pre_ability_update(session['user_id'], 0 , current_ability_cell[0], 1)
                        # added new code
                        model_dbquery.UserDataQuery.migrate_student_data(session['canvas_id'], session['user_id'])
                        model_dbquery.UserDataQuery.update_pre_quiz_status(session['canvas_id'])
                        # main_exp_group.main() # move override it to here
                        
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
                    # data = sub_create_dts(session['num_cell'], session['num_quiz'], session['check_cell'])
                    # Check if 'check_cell' exists in session, is a list, and has elements
                    try:
                        if 'check_cell' in session and isinstance(session['check_cell'], list) and len(session['check_cell']) > 0:
                            session['num_cell'] = len(session['check_cell'])
                        else:
                            # If 'check_cell' is missing, empty, or not a list, assign default value
                            session['num_cell'] = 4
                    except KeyError as ke:
                        # Handle case where session keys are not accessible properly
                        print(f"KeyError: Missing key in session: {ke}")
                        # You can assign default values or handle it as required here
                    except Exception as e:
                        # General fallback for any unexpected error
                        print(f"Unexpected error: {e}")
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
                        corrected_quiz = model_dbquery.UserDataQuery.fetch_solved_quiz(session['user_id']) # new added
                        temp_quiz = model_dbquery.UserDataQuery.fetch_temp_quiz(session['user_id'], session['n_attempt'])
                        data = sub_mapping_fetch_quiz(data, session['max_limit_quiz'], client_timeout, corrected_quiz, temp_quiz)
                        # data = sub_mapping_fetch_quiz(data, session['max_limit_quiz'], client_timeout)
                        G_MEMORY[session['user_id']]['sqe'] = data # Save back to temp memory
                        # Response will be returned either same question or new question.
                        
                    else:
                        # some error encounter, extreme condition like timeout
                        if ((data['timeout'] == True) or (client_timeout == True)):
                            data = sub_mapping_fetch_quiz(data, session['max_limit_quiz'], client_timeout, None, None)
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
                        # _____________________________ may put LLM function here!!
                        # userLog_excel = model_dbquery.UserDataQuery.log_to_excel(session['user_id'], session['n_attempt'])
                        # # canvas_map_path = os.curdir + r'\docs\canvas_mapping.csv' # Mapping canvas user_id
                        # canvas_map_path = os.path.join(os.curdir, 'docs', 'canvas_mapping.csv')
                        # gpt_feedback_txt = aq_pf_prompt.main(userLog_excel, canvas_map_path, name='')
                        # file_path = os.path.join('gpt_feedback_log', gpt_feedback_txt)
                        # with open(file_path, 'r', encoding='utf-8') as feedback:
                        #     feedback_string = feedback.read()
                        # model_dbquery.UserDataQuery.import_txt_to_db(session['user_id'], session['n_attempt'], feedback_string)
                        print("Sum", sum(data['append_response_list']), flush=True)
                        print("Session", session['assignment_id'], flush=True)
                        print("Canvas", session['canvas_id'], flush=True)
                        print(canvas_api_key, flush=True)
                        submit_prequiz_assignment(base_url, course_id, session['assignment_id'], session['canvas_id'], sum(data['append_response_list']), canvas_api_key)
                        submit_status(base_url, course_id, session['assignment_id'], session['canvas_id'], canvas_api_key)
                        # ! Suggest to remove this part since we are not using it in PM5101 course
                        # ______________________________
                        # QE2 workflow
                        # THIS SECTION IS TO
                        # 1. Pull initial_student_path from Students in adq.db. This can get messy if user changes path in the future iterations but for the final product there is no need to open all paths as the user can select their own paths
                        # student_path = model_dbquery.UserDataQuery.get_current_path(session['user_id'])
                        # if student_path is None:
                        #     student_path = model_dbquery.UserDataQuery.get_initial_path(session['user_id'])
                        # student_canvas_id__path = model_dbquery.UserDataQuery.get_quizcourseIDs_from_db_given_cell_list(student_path)
                        # 2. Somehow get all the user's latest attempt data or pull the videos that have been marked as done in Canvas
                        # 3. From 2, get the user's completed cells
                        # 4. Compare the completed cells with the initial_student_path
                        # if initial_student_path == user_completed_cells:
                            # 5. If both matches, then the user has completed the path and can move on to post quiz
                        #! This check_all_assignments function causes massive delay due to canvas API :( 
                        #! Should relocate to only when final question is submitted
                        # if session['assignment_id'] != 0:
                        #     if(check_all_assignments_completed(course_id,student_canvas_id__path,str(session['canvas_id']))):
                        #         print("All assignments are completed")
                        #         #! Just for QE2 so its hardcoded
                        #         post_test_id=[149917]
                        #         create_assignment_given_assignment_list(course_id,post_test_id,[session['canvas_id']])
                        #         print("Post test assignment created")
                            # ______________________________


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

@app.route("/req_get_cell_time", methods=["POST"])
def fn_get_cell_time():
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                cell_indices = model_dbquery.GeneralDataQuery.get_cell_time()
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

@app.route("/req_get_user_path", methods=["POST"])
def get_user_path():
    if request.method == "POST":
        ini_path = model_dbquery.UserDataQuery.get_initial_path(session['user_id'])
        cur_path = model_dbquery.UserDataQuery.get_current_path(session['user_id'])
        # if ini_path is None:
        #     path = []
        #     cpath = []
        #     path_text = ""
        # else:
        #     path = ini_path.split(",")
        #     cpath = cur_path.split(",")
        #     path_text = ini_path.replace(",", "->")
        #     cpath_text = cur_path.replace(",", "->")
        path = [] if ini_path is None or ini_path == "" else ini_path.split(",")
        cpath = [] if cur_path is None or cur_path == "" else cur_path.split(",")
        # response = {"result": "success", "path": path, "path_text": path_text, "cpath": cpath, "cpath_text": cpath_text}
        response = {"result": "success", "path": path,"cpath": cpath, }
    else:
        response = {"result": "fail", "status": "Wrong method"}
    return jsonify(response)

@app.route("/update_path", methods=["POST"])
def update_path():
    courseID='73869'
    if session.get('user_id') is not None:
        ini_path = model_dbquery.UserDataQuery.get_initial_path(session['user_id'])
        canvas_id_list = model_dbquery.UserDataQuery.get_canvas_id(session['user_id'])
        model_dbquery.UserDataQuery.update_path(session['user_id'], ini_path, request.form['path'], session['num_update'] ,int(time.time())) # Still have no pre_quiz complete
        session['num_update'] += 1
        # ! This is masked during QE2 testing. Will be implemented in the future
        # Deletes existing overrides
        # cleanup_overrides(courseID,canvas_id_list)
        # # Adds new overrides
        # path_list = request.form['path'].split(',')
        # path_list = list(map(int, path_list))
        # KU_courseIDs = model_dbquery.UserDataQuery.get_courseIDs_from_db()
        # canvas_id = canvas_id_list[0]
        # print("canvas_id",canvas_id)
        # create_override_input_format = {
        #     str(canvas_id): path_list  # Ensure canvas_id is used as a string key
        # }
        # print("create_override_input_format",create_override_input_format)
        # create_assignment_overrides(courseID,create_override_input_format,KU_courseIDs)
    return "updated"

@app.route("/req_userinfo_post", methods=["POST"])
def fn_req_userinfo_post(): # Function goes two ways, either staying on dashboard or going to quiz
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                pretest_status = model_dbquery.UserDataQuery().get_user_pretest(session['user_id']) # check there is any records in pretest_table
                if (pretest_status == False): # check if pretest were done
                    if (G_MEMORY.get(session['user_id']) != None):
                        session['quiz_start'] = True
                    else:
                        session['quiz_start'] = False
                    full_name = login_status.get_user_info()
                    disclaimer_text = model_dbquery.GeneralDataQuery.get_disclaimer()
                    photo_string = model_dbquery.UserDataQuery.get_user_photo(session['user_id'])
                    # ------- Recall Info from DB --------
                    session['n_attempt'] = model_dbquery.UserDataQuery.get_latest_attempt(session['user_id']) + 1
                    session['num_update'] = model_dbquery.UserDataQuery.get_latest_update(session['user_id']) + 1
                    
                    check_cell_str = model_dbquery.UserDataQuery.get_cell_history(session['user_id']) # to store cell_history 
                    updated_check_cell, updated_string = extend_string_and_list(check_cell_str, session['check_cell'])
                    model_dbquery.UserDataQuery.update_cell_history(session['user_id'], updated_string) # update one by one cell with str
                    session['check_cell'] = updated_check_cell
                    
                    latest_time = model_dbquery.UserDataQuery.get_latest_time(session['user_id'], session['num_update']-1)
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
                                "score_list": score_list,
                                "latest_time": latest_time}
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


@app.route("/req_start_post_quiz", methods=["POST"])
def fn_req_start_post_quiz():
    if request.method == "POST":
        if ((session.get('user_id') is not None)):
            login_status = model_usercontrol.UserAuthentication(login_state=1, session_id=session['session_id'], user_id=session['user_id'])
            if login_status.get_login_status() == True:
                # model_dbquery.UserDataQuery.delete_residual_user_activity(session['user_id'], 1) # remove this one causing overwrite
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

@app.route("/req_fetch_post_quiz", methods=["POST"])
def fn_req_fetch_post_quiz():
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
                    # _____________________________ may put LLM function here!! post-quiz
                    # userLog_excel = model_dbquery.UserDataQuery.log_to_excel(session['user_id'], session['n_attempt'])
                    # canvas_map_path = os.path.join(os.curdir, 'docs', 'canvas_mapping.csv')
                    # gpt_feedback_txt = aq_pf_prompt.main(userLog_excel, canvas_map_path, name='Post-quiz')
                    # file_path = os.path.join('gpt_feedback_log', gpt_feedback_txt)
                    # with open(file_path, 'r', encoding='utf-8') as feedback:
                    #     feedback_string = feedback.read()
                    # model_dbquery.UserDataQuery.import_txt_to_db(session['user_id'], session['n_attempt'], feedback_string)
                    # ______________________________
                
            else:
                session.clear() # Force logout
                response = {"result":"fail", "status": "Session info expired"}
        else:
            session.clear() # Force logout
            response = {"result":"fail", "status": "No record on loggin in"}
    else:
        response = {"result":"fail", "status": "Wrong method"}

    return jsonify(response)

@app.route("/req_submit_post_quiz", methods=["POST"])
def fn_req_submit_post_quiz():
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
                    model_dbquery.UserDataQuery.log_user_activity(session['user_id'],model_dbquery.UserDataQuery.get_username(session['user_id']), session['n_attempt'], question_id, P_MEMORY['question'][0], request.json['selected_choice'], user_correct_ans, answer_db, correct_ans, rationale, int(time.time()))
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

                        # ______________________________________________________________________________________________________
                        # Canvas instance and all necessary parameters for submission API .. Not yet stress test
                        post_quiz_score = sum(normalize) # Pre-quiz score
                        course_id = '72396'
                        assignment_id = 159913 # Post-quiz Assignment ID
                        canvas_user_id = session['canvas_id']
                        submit_prequiz_assignment(base_url, course_id, assignment_id, canvas_user_id, post_quiz_score, canvas_api_key)
                        submit_status(base_url, course_id, assignment_id, canvas_user_id, canvas_api_key)
                        
                        # Once post quiz is completed, create override for all paths. 
                        # Could just whack all the cells and just ignore the errors from Canvas OR filter out the cells that are not in the initial_student_path and 
                        # ! This is suggested to comment out during PM5101
                        # To check post test completion list
                        # all_assignment_list = model_dbquery.UserDataQuery.get_just_courseIDs_from_db()
                        # print("all_assignment_list",all_assignment_list)
                        # if(check_to_unlock_all_modules(course_id,[assignment_id],session['canvas_id'])):
                        #     create_assignment_given_assignment_list(course_id,all_assignment_list,[session['canvas_id']])
                        #     print("Remaining assignments created")
                        # ______________________________________________________________________________________________________

                        # No Need to Create mastery table
                        # model_dbquery.UserDataQuery.create_mastery_slot(session['user_id'])
                        # Update mastery table
                        cell_mastery = model_dbquery.UserDataQuery.update_mastery_slot_pretest(session['user_id'])
                        current_ability_cell = GLOBAL_QUIZ_ENGINE.pre_ability(cell_mastery)
                        # No need to Create train table
                        # model_dbquery.UserDataQuery.create_train_slot(session['user_id'])
                        # Ability assign for post-test
                        prev_learner_ab = model_dbquery.UserDataQuery.get_previous_ability(session['user_id'])
                        model_dbquery.UserDataQuery.pre_ability_update(session['user_id'], prev_learner_ab , current_ability_cell[0], session['n_attempt'])
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
        print("===LOGGED USER RESPONSE===", flush=True)
    else:
        sqe['timeout'] = True

    return sqe

#Previous Code

# # Application creation
# app = Flask(__name__, instance_relative_config=False)
# app.secret_key = b'2\xa7\x8e\xc0\x95\xa1O)\xb3oY\xb58\x16\x00\x10'

# # Configuration
# app.config.from_file("conf/flask_conf.json", load=json.load)
# warnings.simplefilter("ignore")

# print("Run")
# # from app.controller import run

# # Definition of routes
# # Route with rendering templates
# # app --> controller --> routes.py
# from app.controller import routes
# # Route for requesting responses
# # app --> controller --> responses.py
# from app.controller import responses
# print("Success")