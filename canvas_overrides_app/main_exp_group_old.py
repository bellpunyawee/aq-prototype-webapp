"""
Automated Assignment Override Script for Canvas LMS

This script automates the creation of assignment overrides for specific students in the Canvas Learning Management System (LMS). It is designed to run indefinitely on a server, executing at regular intervals (default is every 5 minutes), to apply updated due dates for assignments based on predefined configurations.

**Main Functionality:**

- **Parameter Import**: Imports necessary parameters such as `due_date`, `course_id`, and `student_ids` from the `main_params` module.
- **Canvas API Interaction**: Authenticates with the Canvas API using an access token stored in environment variables and retrieves course data to ensure connectivity.
- **Student-Cell Mapping**: Defines a mapping (`student_cells`) of student IDs to their respective cell numbers (groups of assignments).
- **Assignment Overrides**:
  - Collects all relevant assignments for each student based on their assigned cells from the `KU_dict` dictionary (imported from `UAT1b_KU_dict`).
  - Creates an assignment override for each assignment, setting a new due date that increments by one minute for each subsequent assignment.
  - Overrides are created via POST requests to the Canvas API's overrides endpoint.
- **Error Handling**: Includes try-except blocks to catch and log exceptions without terminating the script.
- **Execution Loop**: Runs the `main()` function in an infinite loop, waiting for a specified `period` between executions.
"""
import sqlite3
import time
import traceback
import json

# period = 5 * 60  # 5 minutes
period = 10  # Uncomment this line for testing with a 10-second interval

# Database paths
db_path = ".//db/adq.db"
student_id_db_path = ".//db/user_info.db"

def fetch_all_user_ids():
    """
    Fetch all user_ids from the Students table in adq.db.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT student_id FROM Students")
    rows = cursor.fetchall()
    conn.close()
    user_ids = [row[0] for row in rows]
    return user_ids

def fetch_user_id_canvas_id_mapping():
    """
    Fetch user_id and canvas_id mapping from user_info.db.
    Returns two dictionaries:
    - user_id_to_canvas_id
    - canvas_id_to_user_id
    """
    conn = sqlite3.connect(student_id_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, canvas_id FROM user_info")  
    rows = cursor.fetchall()
    conn.close()
    user_id_to_canvas_id = {}
    canvas_id_to_user_id = {}
    for user_id, canvas_id in rows:
        user_id_to_canvas_id[user_id] = canvas_id
        canvas_id_to_user_id[canvas_id] = user_id
    return user_id_to_canvas_id, canvas_id_to_user_id

def load_student_preferences_from_db():
    """
    Load student preferences and background information from the SQLite database.
    Returns a dictionary with user_id as keys and their preferences and background info as values.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch all student_ids to ensure we have a base for the preferences
    cursor.execute("SELECT student_id FROM Students")
    students = cursor.fetchall()
    student_preferences = {}

    for (user_id,) in students:
        # Initialize the dictionary for each student
        student_preferences[user_id] = {
            "PG_preferences": {},
            "KA_preferences": {},
            "background_info": {}
        }

        # Fetch PG_preferences
        cursor.execute("""
            SELECT Planning, Executing, Monitoring_Controlling
            FROM PG_preferences
            WHERE student_id = ?
        """, (user_id,))
        pg_prefs = cursor.fetchone()
        if pg_prefs:
            student_preferences[user_id]["PG_preferences"] = {
                "Planning": pg_prefs[0],
                "Executing": pg_prefs[1],
                "Monitoring & Controlling": pg_prefs[2]
            }

        # Fetch KA_preferences
        cursor.execute("""
            SELECT Resource, Risk
            FROM KA_preferences
            WHERE student_id = ?
        """, (user_id,))
        ka_prefs = cursor.fetchone()
        if ka_prefs:
            student_preferences[user_id]["KA_preferences"] = {
                "Resource": ka_prefs[0],
                "Risk": ka_prefs[1]
            }

        # Fetch Background_info
        cursor.execute("""
            SELECT gender, role, company, experience_years, projects, qualification, major
            FROM Background_info
            WHERE student_id = ?
        """, (user_id,))
        bg_info = cursor.fetchone()
        if bg_info:
            student_preferences[user_id]["background_info"] = {
                "gender": bg_info[0],
                "role": bg_info[1],
                "company": bg_info[2],
                "experience_years": bg_info[3],
                "projects": bg_info[4],
                "qualification": bg_info[5],
                "major": bg_info[6]
            }

    conn.close()
    return student_preferences

def load_ku_dict_from_db():
    ku_dict = {}
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query the KU_courseID_link table
    cursor.execute("SELECT id, ku_values FROM KU_courseID_link")
    rows = cursor.fetchall()
    
    # Populate KU_dict with database data
    for row in rows:
        ku_id = row[0]
        ku_values = list(map(int, row[1].split(',')))  # Convert ku_values to a list of integers
        ku_dict[str(ku_id)] = ku_values
    
    conn.close()
    return ku_dict

def load_ka_table_data_from_db():
    """
    Load KATableData data from the SQLite database and format it to match the original KATableData structure.
    """
    ku_table_data = {"columns": [], "rows": [], "data": {}}

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT PG FROM KU_table_data")
    ku_table_data["columns"] = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT KA FROM KU_table_data")
    ku_table_data["rows"] = [row[0] for row in cursor.fetchall()]

    # Query all data from KU_table_data to populate the 'data' field
    cursor.execute("SELECT KA, PG, cell, topics, duration_min FROM KU_table_data")
    rows = cursor.fetchall()

    # Organize data into the specified structure
    for KA, PG, cell, topics, duration_min in rows:
        if KA not in ku_table_data["data"]:
            ku_table_data["data"][KA] = {}
        
        ku_table_data["data"][KA][PG] = {
            "Cell": cell,
            "Topics": topics.split('; '),  # Split topics into a list
            "Duration_min": duration_min
        }

    # Close the database connection
    conn.close()
    return ku_table_data

def main():
    ### Main code to be run on server indefinitely
    ### This code will run every 5 min to check for new submissions

    # Import params (excluding student_ids)
    from main_parameters import due_date, course_id, time_constraint
    import requests
    import os
    import json
    from dotenv import load_dotenv
    from datetime import datetime, timedelta
    from UAT1b_llm_ensemble_voting_system import llm_ensemble

    # Fetch all user_ids from the database
    user_ids = fetch_all_user_ids()  # These are user_ids from adq.db

    # Fetch mapping between user_id and canvas_id
    user_id_to_canvas_id, canvas_id_to_user_id = fetch_user_id_canvas_id_mapping()

    # Fetch all student preferences from the database
    student_preferences = load_student_preferences_from_db()
    print("student_preferences", student_preferences)

    load_dotenv()
    access_token = os.getenv('canvas_api_key')

    # The base URL for the Canvas instance
    base_url = 'https://canvas.nus.edu.sg'

    # Headers to include the access token
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    initial_due_date = datetime.strptime(due_date, "%Y-%m-%dT%H:%M:%S%z")

    # Make the GET request to the API
    url = f'{base_url}/api/v1/courses/{course_id}'

    response = requests.get(url, headers=headers)

    # Check the response status and print the course information
    if response.status_code == 200:
        course_data = response.json()
        # print("course_data", course_data)
    else:
        print(f"Failed to retrieve course data: {response.status_code}")
        print(response.text)

    # Load data from the database
    KU_dict = load_ku_dict_from_db()
    KATableData = load_ka_table_data_from_db()
    
    # Initialize a dictionary to store detailed question results and scores for each student
    student_question_details = {}

    # Fetch and process quiz data, calculate familiarity, and create overrides
    def get_submission_questions(course_id, quiz_id, submission_id):
        question_url = f'{base_url}/api/v1/quiz_submissions/{submission_id}/questions'
        response = requests.get(question_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f'Error: Unable to fetch questions for submission {submission_id} (Status Code: {response.status_code})')
            return None

    # Function to fetch quiz submissions and detailed question data for each student with pagination
    def fetch_quiz_submission_details():
        quiz_id = '44598'  # Replace with your quiz ID
        url = f'{base_url}/api/v1/courses/{course_id}/quizzes/{quiz_id}/submissions'
        page = 1
        per_page = 100 

        while True:
            params = {'page': page, 'per_page': per_page}
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                submissions_data = response.json()

                for submission in submissions_data['quiz_submissions']:
                    canvas_user_id = submission['user_id']
                    if canvas_user_id in canvas_id_to_user_id:
                        user_id = canvas_id_to_user_id[canvas_user_id]
                        if user_id in user_ids:
                            submission_id = submission['id']
                            score = submission['score']  # Extract the overall score
                            finished_at = submission['finished_at']  # Check if the quiz is completed

                            # Skip incomplete quizzes
                            if finished_at is None:
                                print(f"Student ID {user_id} has not completed the quiz. Skipping...")
                                continue

                            # Get detailed question data for each submission
                            questions_data = get_submission_questions(course_id, quiz_id, submission_id)

                            if questions_data:
                                student_question_details[user_id] = {
                                    "questions": questions_data,
                                    "score": score  # Store the score along with question details
                                }

                # Check if there's another page
                if 'next' in response.links:
                    page += 1  # Go to the next page
                else:
                    break  # No more pages, exit the loop
            else:
                print(f'Error: Unable to fetch quiz submissions (Status Code: {response.status_code})')
                print(response.text)  # Print error message if any
                break

    # Fetch quiz submission details
    fetch_quiz_submission_details()

    # Define the quiz cell categories
    quiz_cell_category = {
        1: 15, 2: 15, 3: 15, 4: 15,
        5: 21, 6: 21, 7: 21, 8: 21, 9: 21, 10: 21, 11: 21, 12: 21,
        13: 21, 14: 21, 15: 22, 16: 22,
        17: 16, 18: 16, 19: 16, 20: 16, 21: 16, 22: 16, 23: 16, 24: 16, 25: 16, 26: 16,
        27: 17, 28: 17,
        29: 23, 30: 23
    }

    # Function to calculate familiarity array
    def calculate_familiarity(details, quiz_cell_category):
        correct_counts = {cell: 0 for cell in range(1, 31)}
        total_counts = {cell: 0 for cell in range(1, 31)}

        for question in details['questions']['quiz_submission_questions']:
            position = question['position']
            correct = question.get('correct', False)  # Use .get() to handle missing 'correct' key
            if position in quiz_cell_category:
                cell = quiz_cell_category[position]
                total_counts[cell] += 1
                if correct:
                    correct_counts[cell] += 1

        # Calculate familiarity scores for each cell
        familiarity_array = []
        for cell in range(1, 31):
            if total_counts[cell] > 0:
                familiarity_score = correct_counts[cell] / total_counts[cell]
            else:
                familiarity_score = 0
            familiarity_array.append(familiarity_score)

        return familiarity_array

    # Function where if adding the next cell, the total duration is still below the minimum limit, add the next cell.
    # If the total duration is above the minimum limit, keep adding cells. Add until the next cell would exceed the maximum limit.
    # If the next cell would exceed the maximum limit, check if the total duration is within the maximum limit + 30 minutes buffer.
    def cells_meeting_limit(cell_duration, path, hard_lower_limit, soft_upper_limit, leeway=30):
        total_duration = 0
        cells_in_limit = []

        for cell in path:
            # If adding the next cell exceeds the soft upper limit, stop adding.
            if total_duration + cell_duration[cell] > soft_upper_limit:
                # Check if the current total duration is above the hard lower limit.
                if total_duration >= hard_lower_limit:
                    break
                else:
                    # Try adding the next cell only if the new duration is within soft_upper_limit + leeway
                    if total_duration + cell_duration[cell] <= soft_upper_limit + leeway:
                        total_duration += cell_duration[cell]
                        cells_in_limit.append(cell)
                    else:
                        break
            else:
                total_duration += cell_duration[cell]
                cells_in_limit.append(cell)

        return cells_in_limit, total_duration

    # Function to extract cell duration
    def extract_cell_duration(KATableData):
        result = {}
        data = KATableData["data"]
        for KA, processes in data.items():
            for PG, details in processes.items():
                cell = details["Cell"]
                duration = details.get("Duration_min", 0)  # Using get() to handle missing Duration_min
                result[cell] = duration
        return result

    # Calculate familiarity arrays for each student
    familiarity_arrays = {}

    for user_id, details in student_question_details.items():
        familiarity_array = calculate_familiarity(details, quiz_cell_category)
        familiarity_arrays[user_id] = familiarity_array
    print("familiarity_arrays", familiarity_arrays)
    # Initialize the student_cells dictionary
    student_cells = {}

    # Open a connection to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # LLM Ensemble code for each student
    students_without_submissions = []

    cell_duration_dict = extract_cell_duration(KATableData)
    hard_lower_time_limit = time_constraint - 30
    soft_upper_time_limit = time_constraint  # soft upper time limit has a leeway defined below
    leeway = 30

    for user_id in user_ids:
        if user_id not in student_question_details:
            students_without_submissions.append(user_id)
            continue

        # Check if the student's initial_student_path is NULL in the database
        cursor.execute("SELECT initial_student_path FROM Students WHERE student_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if result is not None and result[0] is not None:
            # If initial_student_path is not NULL, skip this student
            print(f"Student ID {user_id} already has an initial_student_path in the database. Skipping...")
            continue

        # Retrieve student preferences and calculated familiarity
        PG_preferences = student_preferences.get(user_id, {}).get("PG_preferences", {})
        KA_preferences = student_preferences.get(user_id, {}).get("KA_preferences", {})
        background_info = student_preferences.get(user_id, {}).get("background_info", {})
        familiarity_array = familiarity_arrays.get(user_id, [])
        
        # Retrieve student score
        student_score = student_question_details[user_id]["score"]
        print(f"Student ID: {user_id}, Score: {student_score}")

        # Construct rank orders from preferences
        PG_preference_string = ", ".join(f"{k}: {v}" for k, v in PG_preferences.items())
        KA_preference_string = ", ".join(f"{k}: {v}" for k, v in KA_preferences.items())

        # Construct the cell mastery pair using the familiarity array
        cell_mastery_pair = familiarity_array

        # Define the template for learner background and prior knowledge
        learner_background_and_prior_knowledge_template = (
            "As a {gender} participant, I serve as a {role} in the construction and built environment. "
            "My professional designation is {major} at {company}, reflecting a rich experience spanning {experience_years} "
            "across {projects}, supported by a foundational education of {qualification}. "
        )

        # Format the learner background with student-specific data
        learner_background_and_prior_knowledge = learner_background_and_prior_knowledge_template.format(**background_info)
       
        pretest_scores = f"{student_score} out of 30"  # Use student's score
        additional_custom_information = "Some cells are not being used. Ensure that only cells 15,16,17,21,22,23 are among those selected"

        # Call the llm_ensemble function for each student
        print(f"Running LLM Ensemble for student ID {user_id}")
        student_path = llm_ensemble(
            PG_preference_string,
            KA_preference_string,
            learner_background_and_prior_knowledge,
            time_constraint,
            pretest_scores,
            cell_mastery_pair,
            additional_custom_information,
            user_id
        )
        time_limited_cells, path_duration = cells_meeting_limit(
            cell_duration_dict,
            student_path,
            hard_lower_time_limit,
            soft_upper_time_limit,
            leeway
        )
        print("time_limited_cells", time_limited_cells)
        
        # Directly assign time_limited_cells to student_cells
        student_cells[user_id] = time_limited_cells
        # Convert the path to a comma-separated string and update the initial_student_path in the database
        path_str = ','.join(map(str, time_limited_cells))
        try:
            cursor.execute("""
                UPDATE Students
                SET initial_student_path = ?
                WHERE student_id = ?
            """, (path_str, user_id))
            conn.commit()
            print(f"Updated initial_student_path for student {user_id} with path: {path_str}")
        except sqlite3.Error as e:
            print(f"An error occurred while updating the database for student {user_id}: {e}")

    # Close the database connection
    conn.close()

    # Output the list of students who have not completed the quiz
    if students_without_submissions:
        print("Students who have not completed the quiz:")
        for user_id in students_without_submissions:
            print(f"Student ID: {user_id}")

    ### Create assignment overrides based on student_cells ###
    
    # Create a dictionary to hold assignment overrides for each student
    student_overrides = {}
    print("student_cells", student_cells)

    for user_id, cells in student_cells.items():
        # Get canvas_id for the student
        canvas_id = user_id_to_canvas_id.get(user_id)
        if not canvas_id:
            print(f"No canvas_id found for user_id {user_id}. Skipping...")
            continue

        student_overrides[user_id] = []
        assignments = []

        # Collect all assignments for the student's cells
        for cell in cells:
            assignments.extend(KU_dict[str(cell)])  # Convert cell to string to match dictionary keys

        # Initialize the due date for the first override

        current_due_date = initial_due_date

        for assignment_id in assignments:
            override_data_template = {
                "assignment_override": {
                    "student_ids": [canvas_id],  # Use canvas_id here
                    "due_at": current_due_date.strftime("%Y-%m-%dT%H:%M:%S%z"),  # Set new due date
                    # "unlock_at": "2024-09-09T10:00:00+0800",  # Set new unlock date
                    # "lock_at": "2024-07-25T23:59:00+0800"  # Set new lock date
                }
            }

            # Construct the full API endpoint URL for creating an assignment override
            override_url = f'{base_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/overrides'

            # Make the POST request to create the override
            response = requests.post(override_url, headers=headers, data=json.dumps(override_data_template))

            # Check the response status and print the result
            if response.status_code == 201:
                print(f"Successfully created an override for assignment {assignment_id}")
                override_response = response.json()
                print("Override response:", override_response)
                student_overrides[user_id].append({
                    "assignment_id": assignment_id,
                    "override_response": override_response
                })
            else:
                print(f"!!Failed to create override for assignment {assignment_id}: {response.status_code}")
                print(response.text)

            # Increment the due date by one minute for the next override
            current_due_date += timedelta(minutes=1)

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print("An error occurred:", e)
            traceback.print_exc()
        # Calculate minutes and seconds for the period
        minutes, seconds = divmod(period, 60)
        if minutes > 0:
            print(f"Waiting for the next execution in {minutes} minute(s) and {seconds} second(s)...")
        else:
            print(f"Waiting for the next execution in {seconds} second(s)...")
        time.sleep(period)
