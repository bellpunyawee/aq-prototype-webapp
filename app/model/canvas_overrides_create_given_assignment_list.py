import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables from .env file (including API key)
load_dotenv()

canvas_api_key = os.getenv('CANVAS_API_KEY')
# canvas_api_key = os.getenv('canvas_api_key_to_create_overrides')
BASE_URL = 'https://canvas.nus.edu.sg'

# Set up headers for API requests
HEADERS = {
    'Authorization': f'Bearer {canvas_api_key}',
    'Content-Type': 'application/json'
}

def create_assignment_given_assignment_list(course_id, assignment_ids, student_ids, unlock_at=None, lock_at=None, due_at=None, increment_minutes=0):
    """
    Create assignment overrides for a list of students in a specific course on Canvas.
    
    Parameters:
        course_id (str): ID of the Canvas course.
        assignment_ids (list): List of assignment IDs to override.
        student_ids (list): List of student IDs to apply the overrides to.
        unlock_at (str): Optional unlock date in ISO format (e.g., '2024-09-09T10:00:00+0800').
        lock_at (str): Optional lock date in ISO format (e.g., '2024-08-04T23:59:00+0800').
        due_at (str): Optional due date in ISO format (e.g., '2024-09-16T00:01:00+0800').
        increment_minutes (int): Minutes to increment the due date for each assignment override.

    Returns:
        None
    """
    # Check course data to confirm valid course
    # course_url = f'{BASE_URL}/api/v1/courses/{course_id}'
    # response = requests.get(course_url, headers=HEADERS)
    # if response.status_code != 200:
    #     print(f"Failed to retrieve course data: {response.status_code}")
    #     print(response.text)
    #     return
    # else:
    #     course_data = response.json()
    #     print("Course data:", course_data)
    
    # Initialize due date if provided
    # current_due_date = datetime.fromisoformat(due_at) if due_at else None
    due_date = "2024-12-31T00:01:00+0800"
    initial_due_date = datetime.strptime(due_date, "%Y-%m-%dT%H:%M:%S%z")
    current_due_date = initial_due_date

    for student_id in student_ids:
        for assignment_id in assignment_ids:
            # Create override template
            override_data_template = {
                "assignment_override": {
                    "student_ids": [student_id],
                    "unlock_at": unlock_at,
                    "lock_at": lock_at,
                    "due_at": current_due_date.strftime("%Y-%m-%dT%H:%M:%S%z") if current_due_date else None
                }
            }

            # API endpoint for creating an assignment override
            override_url = f'{BASE_URL}/api/v1/courses/{course_id}/assignments/{assignment_id}/overrides'

            # POST request to create override
            response = requests.post(override_url, headers=HEADERS, data=json.dumps(override_data_template))

            if response.status_code == 201:
                print(f"Successfully created an override for assignment {assignment_id} for student {student_id}")
                print("Override response:", response.json())
            else:
                print(f"Failed to create override for assignment {assignment_id} for student {student_id}: {response.status_code}")
                print(response.text)

            # Increment the due date by the specified number of minutes if applicable
            if current_due_date and increment_minutes:
                current_due_date += timedelta(minutes=increment_minutes)
