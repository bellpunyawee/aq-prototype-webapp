import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

def create_assignment_overrides(course_id, student_cells, ku_dict, due_date_str="2024-12-31T00:01:00+0800"):
    """
    Function to create assignment overrides for specific students in a Canvas course.
    
    Args:
        course_id (str): The Canvas course ID.
        student_cells (dict): Mapping of student IDs to cell numbers.
        ku_dict (dict): Dictionary mapping cell numbers to assignment IDs.
        due_date_str (str): Initial due date in ISO format (default: "2024-09-16T00:01:00+0800").
    
    Returns:
        dict: A dictionary containing the results of the assignment overrides per student.
    """
    
    load_dotenv()  # Load environment variables
    # access_token = os.getenv('CANVAS_API_KEY')
    
    # The base URL for the Canvas instance
    # base_url = 'https://canvas.nus.edu.sg'
    
    # Headers to include the access token
    # headers = {
    #     'Authorization': f'Bearer {access_token}',
    #     'Content-Type': 'application/json'
    # }
    
    # Parse the initial due date
    initial_due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M:%S%z")
    
    # Make the GET request to the Canvas API to verify the course ID exists
    # url = f'{base_url}/api/v1/courses/{course_id}'
    # response = requests.get(url, headers=headers)
    response = None # Placeholder
    
    # Check the response status and print the course information or error
    if response is not None and response.status_code == 200:
        course_data = response.json()
        print("Course data:", course_data)
    elif response is not None:
        print(f"Failed to retrieve course data: {response.status_code}")
        print(response.text)
        return {}
    else:
        print("Skipped retrieving course data due to API call being commented out.")

    # Dictionary to hold assignment overrides for each student
    student_overrides = {}

    for student_id, cells in student_cells.items():
        student_overrides[student_id] = []
        assignments = []

        # Collect all assignments for the student's cells
        for cell in cells:
            if str(cell) in ku_dict:
                assignments.extend(ku_dict[str(cell)])  # Convert cell to string to match dictionary keys
            else:
                print(f"Cell {cell} not found in KU_dict.")
        
        # Initialize the due date for the first override
        current_due_date = initial_due_date
        
        for assignment_id in assignments:
            override_data_template = {
                "assignment_override": {
                    "student_ids": [student_id],  # Apply the override to a specific student
                    "due_at": current_due_date.strftime("%Y-%m-%dT%H:%M:%S%z"),  # Set new due date
                    # "unlock_at": "2024-09-09T10:00:00+0800",  # Set new unlock date (optional)
                    # "lock_at": "2024-07-25T23:59:00+0800"  # Set new lock date (optional)
                }
            }

            # Construct the full API endpoint URL for creating an assignment override
            # override_url = f'{base_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/overrides'
            
            # Make the POST request to create the override
            # response = requests.post(override_url, headers=headers, data=json.dumps(override_data_template))
            post_response = None # Placeholder
            
            # Check the response status and print the result
            if post_response is not None and post_response.status_code == 201:
                print(f"Successfully created an override for assignment {assignment_id} for student {student_id}")
                override_response = post_response.json()
                student_overrides[student_id].append({
                    "assignment_id": assignment_id,
                    "override_response": override_response
                })
            elif post_response is not None:
                print(f"==Failed to create override for assignment {assignment_id}: {post_response.status_code}")
                print(post_response.text)
            else:
                print(f"Skipped creating override for assignment {assignment_id} for student {student_id} due to API call being commented out.")
            
            # Increment the due date by one minute for the next override
            current_due_date += timedelta(minutes=1)

    return student_overrides

# Main entry point
if __name__ == "__main__":
    # Example KU_dict
    # KU_dict = {
    #     "15": [128822, 128796, 128823, 128797],
    #     "16": [129032, 129042, 129033, 129043, 129034],
    #     "17": [129037, 129047],
    #     "21": [128825, 128826, 129027, 128827, 129028],
    #     "22": [129031, 129041],
    #     "23": [129038, 129048]
    # }
    KU_dict = {
        "0": [149323]
    }

    # Example student cells mapping
    student_cells = {
        "228325": [0],
        "228332": [0],
        "228320": [0],
        "228314": [0],
        "228311": [0]
    }
    
    # Example course ID
    course_id = '73870'
    
    # Call the function to create assignment overrides
    overrides = create_assignment_overrides(course_id, student_cells, KU_dict)
    
    # Print the structured assignments per student
    # print(json.dumps(overrides, indent=4))
