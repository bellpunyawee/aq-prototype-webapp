import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
# access_token = os.getenv('CANVAS_PROD_KEY')

# The base URL for the Canvas instance
# base_url = 'https://canvas.nus.edu.sg'

# Headers to include the access token
# headers = {
#     'Authorization': f'Bearer {access_token}',
#     'Content-Type': 'application/json'
# }

# Function to get all assignments for the course
def get_all_assignments(course_id):
    assignments = []
    # page = 1
    # while True:
    #     url = f'{base_url}/api/v1/courses/{course_id}/assignments?page={page}'
    #     response = requests.get(url, headers=headers)
    #     if response is not None and response.status_code == 200:
    #         data = response.json()
    #         if not data:
    #             break
    #         assignments.extend(data)
    #         page += 1
    #     elif response is not None:
    #         print(f"Failed to retrieve assignments: {response.status_code}")
    #         print(response.text)
    #         break
    #     else:
    #         print("Skipped retrieving assignments due to API call being commented out.")
    #         break
    return assignments

# Function to delete overrides for a specific student and assignment
def delete_overrides(course_id, assignment_id, student_id):
    # override_list_url = f'{base_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/overrides'
    # response = requests.get(override_list_url, headers=headers)
    response = None # Placeholder for get_overrides
    overrides = []


    if response is not None and response.status_code == 200:
        overrides = response.json()
    elif response is not None:
        print(f"Failed to retrieve overrides for assignment {assignment_id}: {response.status_code}")
        print(response.text)
    else:
        print(f"Skipped retrieving overrides for assignment {assignment_id} due to API call being commented out.")


    for override in overrides:
        # Check if 'student_ids' key exists in the override dictionary
        if 'student_ids' in override and student_id in override['student_ids']:
            existing_override_id = override['id']
            print(f"Existing override ID for student {student_id} in assignment {assignment_id}: {existing_override_id}")

            # Delete the existing override
            # delete_override_url = f'{base_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/overrides/{existing_override_id}'
            # delete_response = requests.delete(delete_override_url, headers=headers)
            delete_response = None # Placeholder for delete_override

            if delete_response is not None and (delete_response.status_code == 200 or delete_response.status_code == 204):
                print(f"Successfully deleted the override for assignment {assignment_id}")
            elif delete_response is not None:
                print(f"Failed to delete the override for assignment {assignment_id}: {delete_response.status_code}")
                print(delete_response.text)
            else:
                print(f"Skipped deleting override for assignment {assignment_id} for student_id {student_id} due to API call being commented out.")

# Main function to clean up overrides for a given list of students
def cleanup_overrides(course_id, student_ids_to_cleanup):
    # Get all assignments for the course
    assignments = get_all_assignments(course_id)

    # Delete overrides for each student in each assignment
    for student_id in student_ids_to_cleanup:
        for assignment in assignments:
            delete_overrides(course_id, assignment['id'], student_id)

# If the script is run directly, execute the cleanup process
if __name__ == "__main__":
    # Sample student_ids_to_cleanup list
    student_ids_to_cleanup = []  # Add student IDs here
    course_id = '' # Replace with the actual course ID

    # Call the cleanup_overrides function with the course_id and list of student IDs
    cleanup_overrides(course_id, student_ids_to_cleanup)
