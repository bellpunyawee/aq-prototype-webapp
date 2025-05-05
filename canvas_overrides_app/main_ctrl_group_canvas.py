import requests
import os
import json
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta
import traceback
import sys

load_dotenv()
access_token = os.getenv('CANVAS_API_KEY')

# The base URL for the Canvas instance
base_url = 'https://canvas.nus.edu.sg'

# The specific course ID, quiz ID, and assignment IDs you want to access
course_id = '73870'
quiz_id = sys.argv[1]  # Enter the quiz id in arg while running the script
pre_assignment_ids = [149062, 149063, 149068, 149070, 149059, 149061, 149066, 149057, 149333, 149384, 149331, 149385, 149388, 149332, 149391, 149334, 149323]  # Control group assignments
post_assignment_ids = [149067, 149389, 149069, 149390, 149060, 149383, 149058, 149382, 149064, 149386, 149065, 149387] # Remaining group assignment

def load_students_to_process():
    try:
        with open(students_to_process, 'r') as file:
            return set(json.load(file))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()
    
student_ids_directory = "canvas_overrides_app/ctrl_group_files"
students_to_process = os.path.join(student_ids_directory, "studentids_to_process.json")
students_ids = load_students_to_process()


# Headers to include the access token
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

# Initialize the due date for the first override
initial_due_date = datetime.strptime("2024-12-31T00:01:00+0800", "%Y-%m-%dT%H:%M:%S%z")

# Directory to store control group files
ctrl_group_dir = "canvas_overrides_app/ctrl_group_files"
processed_students_file = os.path.join(ctrl_group_dir, "processed_students.json")
processed_students_post_file = os.path.join(ctrl_group_dir, "processed_students_post.json")

# Ensure the directory exists
os.makedirs(ctrl_group_dir, exist_ok=True)
    
def load_processed_students(quiz_type):
    try:
        if quiz_type == "pre":
            with open(processed_students_file, 'r') as file:
                return set(json.load(file))
        elif quiz_type == "post":
            with open(processed_students_post_file, 'r') as file:
                return set(json.load(file))
    except (FileNotFoundError, json.JSONDecodeError):

        return set()

# Function to save processed student IDs to the JSON file
def save_processed_students(processed_students, quiz_type):
    if quiz_type == "pre":
        with open(processed_students_file, 'w') as file:
            json.dump(list(processed_students), file)
    elif quiz_type == "post":
        with open(processed_students_post_file, 'w') as file:
            json.dump(list(processed_students), file)


# Function to check if a student has completed the quiz
def fetch_quiz_submission_details(student_id):
    url = f'{base_url}/api/v1/courses/{course_id}/quizzes/{quiz_id}/submissions'
    params = {'per_page': 100}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        submissions_data = response.json()
        for submission in submissions_data['quiz_submissions']:
            if submission['user_id'] == student_id:
                finished_at = submission['finished_at']
                # Check if the quiz is completed
                if finished_at is not None:
                    return True
                else:
                    print(f"Student ID {student_id} has not completed the quiz. Skipping...")
                    return False
    else:
        print(f"Error fetching quiz submissions for student {student_id}: {response.status_code}")
        print(response.text)
        return False

# Function to apply assignment overrides
def apply_assignment_overrides():
    print("Applying assignment overrides...")
    # Load the list of processed students
    quiz_type = ""

    if quiz_id == "50884": # if script is checking for pre-quiz
        assignment_ids = pre_assignment_ids
        quiz_type = "pre"
    elif quiz_id == "50886": # if script is checking for post-quiz
        assignment_ids = post_assignment_ids
        quiz_type = "post"
    else:
        assignment_ids = []
    processed_students = load_processed_students(quiz_type)
    # Iterate over each student to apply assignment overrides
    for student_id in students_ids:
        # Skip if the student has already been processed
        if student_id in processed_students:
            print(f"Student ID {student_id} has already had overrides applied. Skipping...")
            continue

        # Check if the student has completed the quiz
        if fetch_quiz_submission_details(student_id):
            current_due_date = initial_due_date
            for assignment_id in assignment_ids:
                override_data_template = {
                    "assignment_override": {
                        "student_ids": [student_id],  # Apply the override to a specific student
                        "due_at": current_due_date.strftime("%Y-%m-%dT%H:%M:%S%z"),  # Set new due date
                    }
                }

                # Construct the full API endpoint URL for creating an assignment override
                override_url = f'{base_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/overrides'

                # Make the POST request to create the override
                response = requests.post(override_url, headers=headers, data=json.dumps(override_data_template))

                # Check the response status and print the result
                if response.status_code == 201:
                    print(f"Successfully created an override for assignment {assignment_id} for student {student_id}")
                    override_response = response.json()
                    print("Override response:", override_response)
                else:
                    print(f"Failed to create override for assignment {assignment_id} for student {student_id}: {response.status_code}")
                    print(response.text)

                # Increment the due date by one minute for the next assignment
                current_due_date += timedelta(minutes=1)

            # Mark this student as processed
            processed_students.add(student_id)
            save_processed_students(processed_students, quiz_type)
        else:
            print(f"Skipping overrides for student {student_id} as they have not completed the quiz.")

# Main function to run the script in a loop for a defined period
if __name__ == "__main__":
    # period = 5 * 60  # 5 minutes
    period = 10  # Set the interval to 10 seconds

    while True:
        try:
            apply_assignment_overrides()
        except Exception as e:
            print("An error occurred:", e)
            traceback.print_exc()
        
        # Wait for the next execution
        print(f"Waiting for the next execution in {period} seconds...")
        time.sleep(period)
